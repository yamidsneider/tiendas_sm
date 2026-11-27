"""Presentador de la sección Respaldos (fase 5 de docs/HOJA_DE_RUTA_APP_COMPLETA.md; solo el jefe).

No usa ninguna interfaz. Muestra la carpeta y las copias guardadas, cambia la carpeta, respalda ahora y restaura.
El trabajo lo hace ServicioDeRespaldos (tiendas_sm/respaldo.py).
"""
from tiendas_sm.presentador import Resultado

FORMATO_FECHA_Y_HORA = "%d/%m/%Y %H:%M"
BYTES_POR_KB = 1024
NOMBRE_DEL_TIPO = {"respaldo": "Respaldo", "antes_de_restaurar": "Copia de antes de restaurar"}


def _tamano(bytes_):
    return f"{max(1, round(bytes_ / BYTES_POR_KB))} KB"


class PresentadorDeRespaldos:
    def __init__(self, app):
        self.app = app

    def datos(self):
        """{carpeta, filas}: filas (nombre, (fecha, tipo, tamaño)); el nombre sirve de id para restaurar."""
        carpeta = self.app.respaldos.carpeta()
        filas = [(r.nombre, (f"{r.fecha:{FORMATO_FECHA_Y_HORA}}", NOMBRE_DEL_TIPO.get(r.nombre.rsplit("_", 1)[0],
                                                                                      "Respaldo"), _tamano(r.tamano)))
                 for r in self.app.respaldos.listar()]
        return {"carpeta": str(carpeta) if carpeta else "", "filas": filas}

    def cambiar_carpeta(self, texto):
        try:
            carpeta = self.app.respaldos.cambiar_carpeta(texto)
        except ValueError as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Los respaldos se guardarán en {carpeta}")

    def respaldar_ahora(self):
        try:
            archivo = self.app.respaldos.respaldar_ahora()
        except (ValueError, OSError) as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Respaldo guardado en {archivo}")

    def respaldar_si_hay_carpeta(self):
        """Fase 5 (respuesta 5.2): después de cerrar la caja. Devuelve el texto para añadir al mensaje del cierre."""
        if self.app.respaldos.carpeta() is None:
            return ""
        resultado = self.respaldar_ahora()
        return f" {resultado.mensaje}." if resultado.exito else f" No se pudo respaldar: {resultado.mensaje}."

    def restaurar(self, nombre):
        try:
            self.app.respaldos.restaurar(nombre)
        except (ValueError, OSError) as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Se restauró {nombre}. Vuelva a ingresar con su usuario y clave")

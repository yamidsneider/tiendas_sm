"""Presentador de la sección Caja (fase 4 de docs/HOJA_DE_RUTA_APP_COMPLETA.md).

No usa ninguna interfaz. Abrir con la base del día, mostrar cuánto debería haber en efectivo, revisar el cierre
(«Faltan $ 2.000», «Sobran $ 500» o «La caja cuadra») sin cerrar, para poder contar de nuevo, y cerrar.
Los cálculos los hace ServicioDeCaja; aquí solo se arma el texto.
"""
from tiendas_sm.presentador import Resultado, a_entero, formato_pesos

FORMATO_FECHA_Y_HORA = "%d/%m/%Y %H:%M"


def texto_de_la_diferencia(diferencia):
    if diferencia < 0:
        return f"Faltan {formato_pesos(-diferencia)}"
    if diferencia > 0:
        return f"Sobran {formato_pesos(diferencia)}"
    return "La caja cuadra"


def _restado(valor):
    """Lo que se resta lleva «-» delante; si es 0 se muestra «$ 0» (no «-$ 0»)."""
    return f"-{formato_pesos(valor)}" if valor else formato_pesos(0)


class PresentadorDeCaja:
    def __init__(self, app):
        self.app = app

    def estado(self):
        turno = self.app.caja.turno_abierto()
        if turno is None:
            return {"abierta": False}
        detalle = self.app.caja.esperado()
        return {"abierta": True, "desde": f"{turno.abierto_en:{FORMATO_FECHA_Y_HORA}}",
                "abrio": self._nombre(turno.id_usuario_abre),
                "detalle": [["Base", formato_pesos(detalle.base)],
                            ["Ventas en efectivo", formato_pesos(detalle.ventas_en_efectivo)],
                            ["Abonos recibidos", formato_pesos(detalle.abonos)],
                            ["Efectivo devuelto", _restado(detalle.efectivo_devuelto)]],
                "esperado": formato_pesos(detalle.esperado)}

    def abrir(self, base_texto, quien):
        try:
            turno = self.app.caja.abrir(a_entero(base_texto, "La base"), quien.id_usuario)
        except ValueError as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Caja abierta con una base de {formato_pesos(turno.base)}")

    def revisar(self, contado_texto):
        """{exito, mensaje, esperado, contado}: no cierra nada (cancelar = contar de nuevo)."""
        try:
            revision = self.app.caja.revisar_cierre(a_entero(contado_texto, "Lo contado"))
        except ValueError as error:
            return {"exito": False, "mensaje": str(error)}
        return {"exito": True, "mensaje": texto_de_la_diferencia(revision.diferencia),
                "esperado": formato_pesos(revision.esperado), "contado": formato_pesos(revision.contado),
                "cuadra": revision.diferencia == 0}

    def cerrar(self, contado_texto, quien):
        try:
            turno = self.app.caja.cerrar(a_entero(contado_texto, "Lo contado"), quien.id_usuario)
        except ValueError as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Caja cerrada. {texto_de_la_diferencia(turno.diferencia)}")

    def historial(self):
        """Filas (id, (abrió, cerró, quién abrió, quién cerró, base, esperado, contado, diferencia))."""
        return [(t.id_turno, (f"{t.abierto_en:{FORMATO_FECHA_Y_HORA}}", f"{t.cerrado_en:{FORMATO_FECHA_Y_HORA}}",
                              self._nombre(t.id_usuario_abre), self._nombre(t.id_usuario_cierra),
                              formato_pesos(t.base), formato_pesos(t.efectivo_esperado),
                              formato_pesos(t.efectivo_contado), texto_de_la_diferencia(t.diferencia)))
                for t in self.app.caja.historial()]

    def _nombre(self, id_usuario):
        try:
            return self.app.usuarios.obtener(id_usuario).nombre
        except ValueError:
            return "—"

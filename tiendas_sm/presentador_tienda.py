"""Presentador de la sección Tienda (fase 6 de docs/HOJA_DE_RUTA_APP_COMPLETA.md; solo el jefe).

No usa ninguna interfaz. Muestra y guarda los datos que salen en el ticket (nombre, NIT, dirección, teléfono y
mensaje) y arma una vista previa del encabezado, igual que en la impresora de 80 mm.
"""
from tiendas_sm.presentador import Resultado


class PresentadorDeLaTienda:
    def __init__(self, app):
        self.app = app

    def datos(self):
        datos = self.app.tienda.datos()
        vista = [*self.app.tienda.encabezado_del_ticket(), "Comprobante interno (no es factura)", "…"]
        mensaje = self.app.tienda.mensaje_del_ticket()
        if mensaje:
            vista += ["", *mensaje]
        return {**datos._asdict(), "vista_previa": "\n".join(vista)}

    def guardar(self, nombre, nit, direccion, telefono, mensaje):
        try:
            self.app.tienda.guardar(nombre, nit, direccion, telefono, mensaje)
        except ValueError as error:
            return Resultado(False, str(error))
        return Resultado(True, "Datos de la tienda guardados")

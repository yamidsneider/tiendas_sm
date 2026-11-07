"""Presentador de la sección Ventas (RF-05; etapa 6 de la interfaz).

No usa Tkinter. Solo consulta: lista las últimas ventas guardadas y vuelve a armar su ticket con las mismas
funciones del punto de venta (armar_ticket y su pie), así sale idéntico al que se entregó al cobrar.
El ticket usa el precio guardado en cada línea, no el precio actual (HU-02).
No anula ventas (DT-08) ni calcula totales o reportes (no aprobados).
"""
from tiendas_sm.dominio import TipoVenta
from tiendas_sm.presentador import armar_ticket, formato_pesos, pie_de_contado, pie_de_credito

FORMATO_FECHA_Y_HORA = "%d/%m/%Y %H:%M"
NOMBRE_DEL_TIPO = {TipoVenta.CONTADO: "Contado", TipoVenta.CREDITO: "Crédito"}
SIN_CLIENTE = "—"                               # la venta de contado no pide cliente


class PresentadorDeVentas:
    def __init__(self, app):
        self.app = app

    def tabla(self):
        """Filas (id_venta, (número, fecha y hora, tipo, cliente, total)), de la más reciente a la más vieja."""
        clientes = {c.id_cliente: c.nombres for c in self.app.clientes.listar()}
        return [(v.id_venta, (f"#{v.id_venta}", f"{v.fecha:{FORMATO_FECHA_Y_HORA}}", NOMBRE_DEL_TIPO[v.tipo],
                              clientes.get(v.id_cliente, SIN_CLIENTE), formato_pesos(v.total)))
                for v in self.app.ventas.listar()]

    def ticket(self, id_venta):
        venta = self.app.ventas.obtener(id_venta)
        if venta is None:
            return ""
        return armar_ticket(venta, self._nombre_de_producto, self._pie(venta))

    def _pie(self, venta):
        if venta.tipo == TipoVenta.CONTADO:
            return pie_de_contado(venta)
        cliente = next(c for c in self.app.clientes.listar() if c.id_cliente == venta.id_cliente)
        cuenta = next(c for c in self.app.credito.cuentas_del_cliente(venta.id_cliente) if c.id_venta == venta.id_venta)
        return pie_de_credito(cliente.nombres, cuenta.fecha_vencimiento)

    def _nombre_de_producto(self, id_producto):
        producto = self.app.productos.obtener(id_producto)
        return producto.nombre if producto else ""

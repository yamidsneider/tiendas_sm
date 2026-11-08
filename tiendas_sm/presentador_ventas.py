"""Presentador de la sección Ventas (RF-05; etapa 6 de la interfaz).

No usa Tkinter. Solo consulta: lista las últimas ventas guardadas y vuelve a armar su ticket con las mismas
funciones del punto de venta (armar_ticket y su pie), así sale idéntico al que se entregó al cobrar.
El ticket usa el precio guardado en cada línea, no el precio actual (HU-02).
Desde aquí se devuelven productos o se anula una venta (respuesta 1.5, cambia DT-08); el ticket muestra las
devoluciones. No calcula totales ni reportes (no aprobados).
"""
import textwrap

from tiendas_sm.dominio import EstadoVenta, FormaDePago, TipoVenta
from tiendas_sm.presentador import (ANCHO_DEL_TICKET, Resultado, a_entero, armar_ticket, formato_pesos,
                                    pie_de_contado, pie_de_credito)

FORMATO_FECHA_Y_HORA = "%d/%m/%Y %H:%M"
NOMBRE_DEL_TIPO = {TipoVenta.CONTADO: "Contado", TipoVenta.CREDITO: "Crédito"}
NOMBRE_DE_LA_FORMA = {FormaDePago.EFECTIVO: "Efectivo", FormaDePago.TRANSFERENCIA: "Transferencia",
                      FormaDePago.MIXTO: "Mixto"}
SIN_CLIENTE = "—"                               # la venta de contado no pide cliente


class PresentadorDeVentas:
    def __init__(self, app):
        self.app = app

    def tabla(self):
        """Filas (id_venta, (número, fecha y hora, tipo, cliente, total)), de la más reciente a la más vieja."""
        clientes = {c.id_cliente: c.nombres for c in self.app.clientes.listar()}
        return [(v.id_venta, (f"#{v.id_venta}", f"{v.fecha:{FORMATO_FECHA_Y_HORA}}", self._como_se_pago(v),
                              clientes.get(v.id_cliente, SIN_CLIENTE), formato_pesos(v.total)))
                for v in self.app.ventas.listar()]

    @staticmethod
    def _como_se_pago(venta):
        """Crédito, o la forma de pago de la venta de contado (respuesta 1.2)."""
        return NOMBRE_DE_LA_FORMA.get(venta.forma_pago, NOMBRE_DEL_TIPO[venta.tipo])

    def ticket(self, id_venta):
        venta = self.app.ventas.obtener(id_venta)
        if venta is None:
            return ""
        return armar_ticket(venta, self._nombre_de_producto, self._pie(venta) + self._devoluciones(venta))

    # ------------------------------------------------------------------ devoluciones (respuesta 1.5)
    def estados(self):
        """{id_venta: «Anulada» o «Con devolución»} de las ventas listadas que tienen alguna devolución."""
        estados = {}
        for venta in self.app.ventas.listar():
            if venta.estado == EstadoVenta.ANULADA:
                estados[venta.id_venta] = "Anulada"
            elif self.app.ventas.devoluciones_de_la_venta(venta.id_venta):
                estados[venta.id_venta] = "Con devolución"
        return estados

    def para_devolver(self, id_venta):
        """Filas (id_producto, (producto, vendidas, devueltas, pendientes, precio con que se vendió))."""
        venta = self.app.ventas.obtener(id_venta)
        if venta is None:
            return []
        devueltas = self.app.ventas.unidades_devueltas(id_venta)
        return [(id_producto, (self._nombre_de_producto(id_producto), vendidas, devueltas.get(id_producto, 0),
                               vendidas - devueltas.get(id_producto, 0), formato_pesos(venta.precio_de(id_producto))))
                for id_producto, vendidas in venta.unidades_por_producto().items()]

    def devolver(self, id_venta, cantidades, motivo):
        """cantidades: {id_producto: texto}; las vacías o en 0 no se devuelven."""
        try:
            lineas = [(id_producto, a_entero(texto, "La cantidad")) for id_producto, texto in cantidades.items()
                      if str(texto).strip() not in ("", "0")]
            devolucion = self.app.ventas.devolver(id_venta, lineas, motivo)
        except ValueError as error:
            return Resultado(False, str(error))
        return self._resultado(f"Devolución registrada en la venta #{id_venta}", devolucion)

    def anular(self, id_venta, motivo):
        try:
            devolucion = self.app.ventas.anular(id_venta, motivo)
        except ValueError as error:
            return Resultado(False, str(error))
        return self._resultado(f"Venta #{id_venta} anulada", devolucion)

    def _resultado(self, inicio, devolucion):
        partes = [inicio]
        if devolucion.descontado_de_la_deuda:
            partes.append(f"Se descontó de la deuda: {formato_pesos(devolucion.descontado_de_la_deuda)}")
        if devolucion.efectivo_devuelto or not devolucion.descontado_de_la_deuda:
            partes.append(f"Devolver en efectivo: {formato_pesos(devolucion.efectivo_devuelto)}")
        return Resultado(True, ". ".join(partes), self.ticket(devolucion.id_venta))

    def _devoluciones(self, venta):
        """Líneas del ticket con cada devolución (a 42 columnas, como el resto del ticket de 80 mm)."""
        lineas = []
        for devolucion in self.app.ventas.devoluciones_de_la_venta(venta.id_venta):
            lineas += ["", f"DEVOLUCIÓN {devolucion.fecha:%Y-%m-%d %H:%M}"]
            lineas += [f"  -{linea.cantidad} x {self._nombre_de_producto(linea.id_producto)}"[:ANCHO_DEL_TICKET]
                       for linea in devolucion.lineas]
            lineas.append(f"Valor devuelto: {formato_pesos(devolucion.valor())}")
            lineas += textwrap.wrap(f"Motivo: {devolucion.motivo}", ANCHO_DEL_TICKET)
        if venta.estado == EstadoVenta.ANULADA:
            lineas += ["", "*** VENTA ANULADA ***"]
        return lineas

    def _pie(self, venta):
        if venta.tipo == TipoVenta.CONTADO:
            return pie_de_contado(venta)
        cliente = next(c for c in self.app.clientes.listar() if c.id_cliente == venta.id_cliente)
        cuenta = next(c for c in self.app.credito.cuentas_del_cliente(venta.id_cliente) if c.id_venta == venta.id_venta)
        return pie_de_credito(cliente.nombres, cuenta.fecha_vencimiento)

    def _nombre_de_producto(self, id_producto):
        producto = self.app.productos.obtener(id_producto)
        return producto.nombre if producto else ""

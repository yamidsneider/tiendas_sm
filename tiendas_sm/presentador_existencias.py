"""Presentador de la sección Existencias (HU-03, RF-03, RF-04; etapa 5 de la interfaz).

No usa Tkinter. Muestra cuántas unidades hay de cada producto, registra entradas de mercancía con
ServicioDeProductos.registrar_entrada (el dominio rechaza 0 o negativo, HU-03) y arma el historial de
movimientos. No hay salida manual (mermas, daños): está por confirmar con el propietario (H-1).
"""
from tiendas_sm.presentador import Resultado, a_entero

MENSAJE_SIN_PRODUCTO = "Elige un producto de la lista"
FORMATO_FECHA_Y_HORA = "%d/%m/%Y %H:%M"
NOMBRE_DEL_MOVIMIENTO = {"ENTRADA": "Entrada", "SALIDA_VENTA": "Salida por venta"}
SIGNO_DEL_MOVIMIENTO = {"ENTRADA": "+", "SALIDA_VENTA": "-"}


def _unidades(cantidad):
    return f"{cantidad} {'unidad' if cantidad == 1 else 'unidades'}"


class PresentadorDeExistencias:
    def __init__(self, app):
        self.app = app

    def tabla(self, texto=""):
        """Filas (id, (producto, disponibles))."""
        buscado = texto.strip().lower()
        return [(p.id_producto, (p.nombre, self.app.cantidad_en_inventario(p.id_producto)))
                for p in self.app.productos.listar() if buscado in p.nombre.lower()]

    def por_reponer(self):
        """RF-12: filas (id, (producto, disponibles, stock mínimo)) de los que llegaron a su mínimo o menos."""
        filas = []
        for producto in self.app.productos.listar():
            disponibles = self.app.cantidad_en_inventario(producto.id_producto)
            if producto.necesita_reponer(disponibles):
                filas.append((producto.id_producto, (producto.nombre, disponibles, producto.stock_minimo)))
        return filas

    def nombre(self, id_producto):
        producto = self.app.productos.obtener(id_producto)
        return producto.nombre if producto else ""

    def registrar_entrada(self, id_producto, cantidad_texto):
        if id_producto is None:
            return Resultado(False, MENSAJE_SIN_PRODUCTO)
        try:
            cantidad = a_entero(cantidad_texto, "La cantidad")
            existencia = self.app.productos.registrar_entrada(id_producto, cantidad)
        except ValueError as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Entrada de {_unidades(cantidad)} de {self.nombre(id_producto)}. "
                               f"Ahora hay {existencia.cantidad_disponible()}")

    def movimientos(self):
        """Filas (id, (fecha y hora, producto, movimiento, cantidad con signo)), del más reciente al más viejo."""
        nombres = {p.id_producto: p.nombre for p in self.app.productos.listar()}
        return [(m.id_movimiento, (f"{m.fecha:{FORMATO_FECHA_Y_HORA}}", nombres.get(m.id_producto, ""),
                                   NOMBRE_DEL_MOVIMIENTO.get(m.tipo, m.tipo),
                                   f"{SIGNO_DEL_MOVIMIENTO.get(m.tipo, '')}{m.cantidad}"))
                for m in self.app.productos.movimientos()]

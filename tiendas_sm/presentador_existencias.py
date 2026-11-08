"""Presentador de la sección Existencias (HU-03, RF-03, RF-04; etapa 5 de la interfaz).

No usa Tkinter. Muestra cuántas unidades hay de cada producto, registra entradas de mercancía con
ServicioDeProductos.registrar_entrada (el dominio rechaza 0 o negativo, HU-03) y arma el historial de
movimientos. No hay salida manual (mermas, daños): está por confirmar con el propietario (H-1).
También lleva los lotes por vencer (RF-10, RF-13): son solo un aviso y no cambian las existencias.
"""
from datetime import date

from tiendas_sm.dominio import Lote
from tiendas_sm.presentador import Resultado, a_entero

MENSAJE_SIN_PRODUCTO = "Elige un producto de la lista"
FORMATO_FECHA_Y_HORA = "%d/%m/%Y %H:%M"
NOMBRE_DEL_MOVIMIENTO = {"ENTRADA": "Entrada", "SALIDA_VENTA": "Salida por venta", "DEVOLUCION": "Devolución"}
SIGNO_DEL_MOVIMIENTO = {"ENTRADA": "+", "SALIDA_VENTA": "-", "DEVOLUCION": "+"}
FORMATO_FECHA = "%d/%m/%Y"
SIN_NUMERO = "Sin número"


def _unidades(cantidad):
    return f"{cantidad} {'unidad' if cantidad == 1 else 'unidades'}"


def _dias(cantidad):
    return f"{cantidad} {'día' if cantidad == 1 else 'días'}"


def _texto_de_los_dias(dias):
    """Cuánto falta para que venza, en palabras."""
    if dias < 0:
        return f"Venció hace {_dias(-dias)}"
    if dias == 0:
        return "Vence hoy"
    return f"{'Falta' if dias == 1 else 'Faltan'} {_dias(dias)}"


def _leer_fecha(texto):
    """El campo de fecha de la página manda AAAA-MM-DD."""
    if not texto.strip():
        raise ValueError("Escribe la fecha de vencimiento")
    try:
        return date.fromisoformat(texto.strip())
    except ValueError:
        raise ValueError("La fecha de vencimiento no es válida") from None


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

    def lotes(self):
        """Filas (id, (producto, lote, vence, cantidad, estado, cuánto falta)), del que vence primero al último."""
        hoy = date.today()
        productos = {p.id_producto: p for p in self.app.productos.listar()}
        filas = []
        for lote in self.app.productos.lotes_activos():
            producto = productos[lote.id_producto]
            filas.append((lote.id_lote, (producto.nombre, lote.numero or SIN_NUMERO,
                                         f"{lote.fecha_vencimiento:{FORMATO_FECHA}}", lote.cantidad,
                                         lote.estado(hoy, producto.dias_aviso),
                                         _texto_de_los_dias(lote.dias_para_vencer(hoy)))))
        return filas

    def cuantos_en_alerta(self):
        """Lotes vencidos o por vencer (los que no están «Al día»)."""
        return sum(1 for _, fila in self.lotes() if fila[4] != Lote.AL_DIA)

    def registrar_lote(self, id_producto, numero, fecha_texto, cantidad_texto):
        if id_producto is None:
            return Resultado(False, MENSAJE_SIN_PRODUCTO)
        try:
            fecha = _leer_fecha(fecha_texto)
            cantidad = a_entero(cantidad_texto, "La cantidad")
            lote = self.app.productos.registrar_lote(id_producto, numero, fecha, cantidad)
        except ValueError as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Lote {lote.numero or SIN_NUMERO.lower()} de {self.nombre(id_producto)} registrado. "
                               f"Vence el {fecha:{FORMATO_FECHA}}")

    def retirar_lote(self, id_lote):
        try:
            lote = self.app.productos.retirar_lote(id_lote)
        except ValueError as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Lote {lote.numero or SIN_NUMERO.lower()} de {self.nombre(lote.id_producto)} "
                               "quitado de la lista")

    def movimientos(self):
        """Filas (id, (fecha y hora, producto, movimiento, cantidad con signo)), del más reciente al más viejo."""
        nombres = {p.id_producto: p.nombre for p in self.app.productos.listar()}
        return [(m.id_movimiento, (f"{m.fecha:{FORMATO_FECHA_Y_HORA}}", nombres.get(m.id_producto, ""),
                                   NOMBRE_DEL_MOVIMIENTO.get(m.tipo, m.tipo),
                                   f"{SIGNO_DEL_MOVIMIENTO.get(m.tipo, '')}{m.cantidad}"))
                for m in self.app.productos.movimientos()]

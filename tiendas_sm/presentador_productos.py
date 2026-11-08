"""Presentador de la sección Productos (HU-01, HU-02, RF-01, RF-02; etapa 4 de la interfaz).

No usa Tkinter. Convierte el texto del formulario a números y llama a ServicioDeProductos. Las reglas
(nombre obligatorio, precios no negativos) las valida el dominio y su mensaje se muestra tal cual.
Cambiar el precio no altera ventas anteriores: cada venta guardó su precio (HU-02).
Pide el stock mínimo de cada producto (RF-12, TD-04; respuesta 4.1). No calcula ganancias ni borra productos (DT-08).
"""
from collections import namedtuple

from tiendas_sm.presentador import Resultado, a_entero, formato_pesos
from tiendas_sm.validaciones import exigir_no_negativo

MENSAJE_SIN_PRODUCTO = "Elige un producto de la lista"

DatosParaEditar = namedtuple("DatosParaEditar", "nombre compra venta minimo")


class PresentadorDeProductos:
    def __init__(self, app):
        self.app = app

    def tabla(self, texto=""):
        """Filas (id, (producto, precio de compra, precio de venta, disponibles))."""
        buscado = texto.strip().lower()
        return [(p.id_producto, (p.nombre, formato_pesos(p.precio_compra), formato_pesos(p.precio_venta),
                                 self.app.cantidad_en_inventario(p.id_producto)))
                for p in self.app.productos.listar() if buscado in p.nombre.lower()]

    def registrar(self, nombre, compra_texto, venta_texto, cantidad_texto, minimo_texto="0"):
        try:
            compra = a_entero(compra_texto, "El precio de compra")
            venta = a_entero(venta_texto, "El precio de venta")
            cantidad = a_entero(cantidad_texto, "La cantidad inicial")
            minimo = a_entero(minimo_texto, "El stock mínimo")
            exigir_no_negativo(cantidad, "La cantidad inicial no puede ser negativa")   # antes de guardar nada
            producto = self.app.productos.registrar_producto(nombre.strip(), compra, venta, cantidad, minimo)
        except ValueError as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Producto registrado: {producto.nombre}")

    def datos_para_editar(self, id_producto):
        """Los datos guardados, como texto para llenar el formulario de Editar producto; None si no existe."""
        producto = self.app.productos.obtener(id_producto)
        if producto is None:
            return None
        return DatosParaEditar(producto.nombre, str(producto.precio_compra), str(producto.precio_venta),
                               str(producto.stock_minimo))

    def editar(self, id_producto, nombre, compra_texto, venta_texto, minimo_texto=None):
        """Sin minimo_texto (la versión Tkinter no lo pide) se conserva el stock mínimo guardado."""
        if id_producto is None:
            return Resultado(False, MENSAJE_SIN_PRODUCTO)
        try:
            compra = a_entero(compra_texto, "El precio de compra")
            venta = a_entero(venta_texto, "El precio de venta")
            minimo = None if minimo_texto is None else a_entero(minimo_texto, "El stock mínimo")
            producto = self.app.productos.actualizar_producto(id_producto, nombre.strip(), compra, venta, minimo)
        except ValueError as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Producto actualizado: {producto.nombre}")

    def precio_actual(self, id_producto):
        producto = self.app.productos.obtener(id_producto)
        if producto is None:
            return ""
        return f"{producto.nombre}\nPrecio actual: {formato_pesos(producto.precio_venta)}"

    def cambiar_precio(self, id_producto, nuevo_texto):
        if id_producto is None:
            return Resultado(False, MENSAJE_SIN_PRODUCTO)
        try:
            producto = self.app.productos.actualizar_precio(id_producto, a_entero(nuevo_texto, "El precio de venta"))
        except ValueError as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Nuevo precio de {producto.nombre}: {formato_pesos(producto.precio_venta)}")

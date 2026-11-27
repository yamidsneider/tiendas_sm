"""Presentador del punto de venta (tarea 8, TD-03, DAD §10.2).

Es la parte de la pantalla que no depende de Tkinter, para poder probarla sin abrir ventanas.
Recibe lo que escribe el vendedor (texto), llama a los servicios de Aplicacion y devuelve filas y
mensajes listos para mostrar. No tiene reglas de negocio: el stock, el crédito y el efectivo los
valida el dominio al confirmar, y sus mensajes se muestran tal como llegan (str(error)).
Lo único propio de aquí: convertir texto a número, dar formato a los pesos y armar el ticket.
"""
import sqlite3
import textwrap
from collections import namedtuple

from tiendas_sm.dominio import CreditoNoPermitido, EfectivoInsuficiente, FormaDePago, StockInsuficiente, Venta
from tiendas_sm.validaciones import exigir_mayor_a_cero

ERRORES_DEL_NEGOCIO = (StockInsuficiente, CreditoNoPermitido, EfectivoInsuficiente, ValueError)
MENSAJE_FALLA_AL_GUARDAR = "No se pudo guardar la venta; no quedó nada a medias. Intente de nuevo."
# Una impresora térmica de 80 mm imprime unos 42 caracteres por renglón con la letra normal (respuesta 1.3).
ANCHO_DEL_TICKET = 42

Resultado = namedtuple("Resultado", "exito mensaje ticket", defaults=(None,))
FilaDeProducto = namedtuple("FilaDeProducto", "id_producto nombre precio disponibles")
LineaDelCarrito = namedtuple("LineaDelCarrito", "id_producto nombre precio cantidad importe disponibles")
DatosDelCliente = namedtuple("DatosDelCliente", "id_cliente nombres limite deuda disponible texto")


def formato_pesos(valor):
    """17300 -> '$ 17.300' (DDS §9.2: separador de miles y símbolo de pesos)."""
    return f"$ {valor:,}".replace(",", ".")


def _plural(cantidad, singular, plural):
    return f"{cantidad} {singular if cantidad == 1 else plural}"


def armar_ticket(venta, nombre_de_producto, pie, encabezado=("TIENDAS S.M",), mensaje=()):
    """DDS §10.3: número, fecha y hora, líneas, total y forma de pago. Se arma desde la venta guardada.

    nombre_de_producto es una función id_producto -> nombre; pie son las líneas finales (forma de pago, etc.).
    La usan el punto de venta (al cobrar) y la sección Ventas (para ver el ticket de una venta pasada).
    Fase 6: encabezado (nombre, NIT, dirección, teléfono) y mensaje final salen de los datos de la tienda.
    """
    lineas = [*encabezado, "Comprobante interno (no es factura)",
              f"Venta #{venta.id_venta} · {venta.fecha:%Y-%m-%d %H:%M}", ""]
    for detalle in venta.detalles:
        lineas += _lineas_del_producto(detalle, nombre_de_producto(detalle.id_producto))
    lineas += ["", f"TOTAL: {formato_pesos(venta.total)}", *pie]
    if mensaje:
        lineas += ["", *mensaje]
    return "\n".join(lineas)


def _lineas_del_producto(detalle, nombre):
    """Ticket de 80 mm: «2 x nombre» (partido si es largo) y debajo el precio unitario y el valor a la derecha."""
    renglones = textwrap.wrap(f"{detalle.cantidad} x {nombre}", ANCHO_DEL_TICKET)
    precio = f"  {formato_pesos(detalle.precio_unitario)} c/u"
    return renglones + [precio + formato_pesos(detalle.subtotal()).rjust(ANCHO_DEL_TICKET - len(precio))]


def pie_de_contado(venta):
    """Respuesta 1.3: con transferencia no hay cambio; en el mixto el cambio sale solo del efectivo."""
    forma = [f"Forma de pago: {venta.forma_pago.value}"]
    cambio = f"Cambio: {formato_pesos(venta.calcular_cambio())}"
    if venta.forma_pago == FormaDePago.TRANSFERENCIA:
        return forma + [f"Pagado por transferencia: {formato_pesos(venta.valor_transferencia)}"]
    if venta.forma_pago == FormaDePago.MIXTO:
        return forma + [f"Transferencia: {formato_pesos(venta.valor_transferencia)}",
                        f"Efectivo recibido: {formato_pesos(venta.valor_recibido)}", cambio]
    return forma + [f"Recibido: {formato_pesos(venta.valor_recibido)}", cambio]


def pie_de_credito(nombres_del_cliente, fecha_vencimiento):
    return ["Forma de pago: CRÉDITO", f"Cliente: {nombres_del_cliente}", f"Vence: {fecha_vencimiento:%Y-%m-%d}"]


def a_entero(texto, campo):
    try:
        return int(str(texto).strip())
    except ValueError:
        raise ValueError(f"{campo} debe ser un número entero") from None


class PresentadorPuntoDeVenta:
    def __init__(self, app):
        self.app = app
        self.carrito = {}            # id_producto -> cantidad pedida (conserva el orden en que se agregó)

    # ------------------------------------------------------------------ búsqueda y carrito
    def buscar(self, texto):
        """Si el texto es el código de barras de un producto, solo ese (respuesta 1.4); si no, busca por nombre."""
        buscado = texto.strip().lower()
        if not buscado:
            return []
        por_codigo = self.app.productos.buscar_por_codigo(texto)
        encontrados = ([por_codigo] if por_codigo else
                       [p for p in self.app.productos.listar() if buscado in p.nombre.lower()])
        encontrados = [p for p in encontrados if p.activo]          # fase 6: los desactivados no se venden
        return [FilaDeProducto(p.id_producto, p.nombre, p.precio_venta, self.app.cantidad_en_inventario(p.id_producto))
                for p in encontrados]

    def agregar(self, id_producto, cantidad_texto):
        """Agrega al carrito sin validar el stock: eso lo hace el dominio al confirmar la venta."""
        try:
            cantidad = a_entero(cantidad_texto, "La cantidad")
            exigir_mayor_a_cero(cantidad)
            producto = self._producto(id_producto)
        except ValueError as error:
            return Resultado(False, str(error))
        self.carrito[id_producto] = self.carrito.get(id_producto, 0) + cantidad
        return Resultado(True, f"Agregado: {producto.nombre}")

    def quitar(self, id_producto):
        self.carrito.pop(id_producto, None)

    def quitar_uno(self, id_producto):
        """Botón «−»: resta una unidad; si queda en 0, la línea sale del carrito. Si no está, no hace nada."""
        if id_producto not in self.carrito:
            return
        if self.carrito[id_producto] > 1:
            self.carrito[id_producto] -= 1
        else:
            self.quitar(id_producto)

    def limpiar(self):
        self.carrito.clear()

    def lineas(self):
        filas = []
        for detalle in self._venta_previa().detalles:
            producto = self._producto(detalle.id_producto)
            filas.append(LineaDelCarrito(producto.id_producto, producto.nombre, detalle.precio_unitario,
                                         detalle.cantidad, detalle.subtotal(),
                                         self.app.cantidad_en_inventario(producto.id_producto)))
        return filas

    def total(self):
        """El mismo cálculo del dominio (Venta.calcular_total), para no repetir la regla en la pantalla."""
        return self._venta_previa().calcular_total()

    def resumen(self):
        if not self.carrito:
            return "Sin productos"
        productos, unidades = len(self.carrito), sum(self.carrito.values())
        return f"{_plural(productos, 'producto', 'productos')} · {_plural(unidades, 'unidad', 'unidades')}"

    # ------------------------------------------------------------------ clientes
    def clientes(self):
        return [self._datos(cliente) for cliente in self.app.clientes.listar()]

    def datos_del_cliente(self, id_cliente):
        return next((datos for datos in self.clientes() if datos.id_cliente == id_cliente), None)

    def _datos(self, cliente):
        deuda = self.app.credito.saldo_pendiente(cliente)
        disponible = cliente.credito_disponible(deuda)
        texto = (f"Límite {formato_pesos(cliente.limite_credito)} · Debe {formato_pesos(deuda)}\n"
                 f"Crédito disponible: {formato_pesos(disponible)}")
        if not cliente.credito_habilitado:
            texto = "No tiene crédito habilitado\n" + texto
        elif self.app.credito.tiene_cuentas_vencidas(cliente):
            texto = "Tiene cuentas vencidas: no se le puede fiar\n" + texto
        return DatosDelCliente(cliente.id_cliente, cliente.nombres, cliente.limite_credito, deuda, disponible, texto)

    # ------------------------------------------------------------------ cobro
    def cambio_previo(self, recibido_texto, transferencia_texto="0"):
        """CU-02 paso 2: muestra el cambio mientras se escribe lo recibido, con las reglas del dominio y sin guardar."""
        try:
            venta = self._venta_previa()
            venta.registrar_pago(a_entero(recibido_texto, "El valor recibido"),
                                 a_entero(transferencia_texto, "La transferencia"))
        except ERRORES_DEL_NEGOCIO as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Cambio: {formato_pesos(venta.calcular_cambio())}")

    def cobrar_de_contado(self, recibido_texto, transferencia_texto="0"):
        try:
            recibido = a_entero(recibido_texto, "El valor recibido")
            transferencia = a_entero(transferencia_texto, "La transferencia")
        except ValueError as error:
            return Resultado(False, str(error))
        venta, error = self._registrar(lambda: self.app.ventas.registrar_venta_de_contado(self._lineas_para_vender(),
                                                                                           recibido, transferencia))
        if error:
            return Resultado(False, error)
        final = ("Pagada por transferencia" if venta.forma_pago == FormaDePago.TRANSFERENCIA
                 else f"Cambio: {formato_pesos(venta.calcular_cambio())}")
        return self._cerrar(venta, f"Venta #{venta.id_venta} registrada. {final}", pie_de_contado(venta))

    def vender_a_credito(self, id_cliente):
        venta, error = self._registrar(lambda: self.app.ventas.registrar_venta_a_credito(id_cliente,
                                                                                          self._lineas_para_vender()))
        if error:
            return Resultado(False, error)
        cuenta = next(c for c in self.app.credito.cuentas_del_cliente(id_cliente) if c.id_venta == venta.id_venta)
        cliente = self.datos_del_cliente(id_cliente)
        vence = f"{cuenta.fecha_vencimiento:%Y-%m-%d}"
        return self._cerrar(venta, f"Venta #{venta.id_venta} registrada a crédito para {cliente.nombres}. Vence: {vence}",
                            pie_de_credito(cliente.nombres, cuenta.fecha_vencimiento))

    def _registrar(self, registrar_venta):
        """Llama al servicio y devuelve (venta, None); si se rechaza, (None, mensaje del dominio tal como llega)."""
        try:
            return registrar_venta(), None
        except ERRORES_DEL_NEGOCIO as error:
            return None, str(error)
        except sqlite3.Error:
            return None, MENSAJE_FALLA_AL_GUARDAR

    def _cerrar(self, venta, mensaje, pie):
        ticket = armar_ticket(venta, lambda id_producto: self._producto(id_producto).nombre, pie,
                              self.app.tienda.encabezado_del_ticket(), self.app.tienda.mensaje_del_ticket())
        self.limpiar()
        return Resultado(True, mensaje, ticket)

    # ------------------------------------------------------------------ apoyo
    def _producto(self, id_producto):
        producto = self.app.productos.obtener(id_producto)
        if producto is None:
            raise ValueError("El producto no existe")
        return producto

    def _venta_previa(self):
        """Venta sin guardar, solo para mostrar importes y total con las reglas del dominio."""
        venta = Venta()
        for id_producto, cantidad in self.carrito.items():
            venta.agregar_detalle(self._producto(id_producto), cantidad)
        return venta

    def _lineas_para_vender(self):
        return list(self.carrito.items())

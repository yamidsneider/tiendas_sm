from collections import namedtuple
from datetime import datetime, timedelta

from tiendas_sm.dominio import (Producto, Cliente, Venta, CuentaPorCobrar, StockInsuficiente, Devolucion, Lote,
                                CreditoNoPermitido, TipoVenta, EstadoVenta, PLAZO_POR_DEFECTO_DIAS)
from tiendas_sm.validaciones import exigir_mayor_a_cero

LineaDeVenta = namedtuple("LineaDeVenta", "id_producto cantidad")
MOVIMIENTOS_A_MOSTRAR = 50          # RF-04: el historial muestra los últimos, no toda la historia
VENTAS_A_MOSTRAR = 50               # sección Ventas: las últimas (no es un reporte)


class ServicioDeProductos:
    def __init__(self, repo_productos):
        self.repo_productos = repo_productos

    def registrar_producto(self, nombre, precio_compra, precio_venta, cantidad_inicial=0, stock_minimo=0, codigo="",
                           dias_aviso=0):
        producto = Producto(None, nombre, precio_compra, precio_venta, stock_minimo, codigo, dias_aviso)
        self._exigir_codigo_libre(producto)
        self.repo_productos.guardar(producto)
        if cantidad_inicial > 0:
            self.registrar_entrada(producto.id_producto, cantidad_inicial)
        return producto

    def obtener(self, id_producto):
        return self.repo_productos.obtener(id_producto)

    def buscar_por_codigo(self, codigo):
        """Respuesta 1.4: lo que manda el lector de código de barras (sin espacios ni Enter); None si no hay."""
        codigo = codigo.strip()
        return self.repo_productos.obtener_por_codigo(codigo) if codigo else None

    def _exigir_codigo_libre(self, producto):
        """Dos productos no pueden tener el mismo código: el lector no sabría cuál agregar."""
        otro = self.buscar_por_codigo(producto.codigo)
        if otro is not None and otro.id_producto != producto.id_producto:
            raise ValueError(f"El código {producto.codigo} ya es del producto {otro.nombre}")

    def listar(self):
        return self.repo_productos.listar()

    def actualizar_precio(self, id_producto, nuevo_precio):
        producto = self.repo_productos.obtener(id_producto)
        if producto is None:
            raise ValueError("El producto no existe")
        producto.actualizar_precio(nuevo_precio)
        self.repo_productos.guardar(producto)
        return producto

    def actualizar_producto(self, id_producto, nombre, precio_compra, precio_venta, stock_minimo=None, codigo=None,
                            dias_aviso=None):
        """Editar producto: se arma un Producto con el mismo id para que el dominio valide igual que al registrar.
        Las existencias no se tocan (cambian con entradas y ventas). Lo que llegue en None (stock mínimo, código,
        días de aviso) conserva lo guardado."""
        actual = self._exigir_producto(id_producto)
        minimo = actual.stock_minimo if stock_minimo is None else stock_minimo
        codigo = actual.codigo if codigo is None else codigo
        aviso = actual.dias_aviso if dias_aviso is None else dias_aviso
        producto = Producto(id_producto, nombre, precio_compra, precio_venta, minimo, codigo, aviso)
        self._exigir_codigo_libre(producto)
        self.repo_productos.guardar(producto)
        return producto

    def registrar_entrada(self, id_producto, cantidad):
        existencia = self.repo_productos.obtener_existencia(id_producto)
        if existencia is None:
            raise ValueError("El producto no existe")
        existencia.aumentar(cantidad)
        self.repo_productos.guardar_existencia(existencia, "ENTRADA", cantidad)
        return existencia

    def movimientos(self, limite=MOVIMIENTOS_A_MOSTRAR):
        return self.repo_productos.listar_movimientos(limite)

    def _exigir_producto(self, id_producto):
        producto = self.repo_productos.obtener(id_producto)
        if producto is None:
            raise ValueError("El producto no existe")
        return producto

    # Lotes (RF-10, RF-13): solo un registro para avisar del vencimiento. No cambian las existencias.
    def registrar_lote(self, id_producto, numero, fecha_vencimiento, cantidad):
        self._exigir_producto(id_producto)
        lote = Lote(None, id_producto, numero, fecha_vencimiento, cantidad)
        self.repo_productos.guardar_lote(lote)
        return lote

    def retirar_lote(self, id_lote):
        lote = self.repo_productos.obtener_lote(id_lote)
        if lote is None:
            raise ValueError("Ese lote ya no está en la lista")
        lote.retirar()
        self.repo_productos.guardar_lote(lote)
        return lote

    def lotes_activos(self):
        return self.repo_productos.lotes_activos()


class ServicioDeClientes:
    def __init__(self, repo_clientes):
        self.repo_clientes = repo_clientes

    def registrar_cliente(self, nombres, credito_habilitado, limite_credito,
                          plazo_credito_dias=PLAZO_POR_DEFECTO_DIAS, telefono="", direccion=""):
        cliente = Cliente(None, nombres, credito_habilitado, limite_credito, plazo_credito_dias, telefono, direccion)
        self.repo_clientes.guardar(cliente)
        return cliente

    def obtener(self, id_cliente):
        return self.repo_clientes.obtener(id_cliente)

    def actualizar_cliente(self, id_cliente, nombres, credito_habilitado, limite_credito, plazo_credito_dias,
                           telefono=None, direccion=None):
        """Editar cliente: se arma un Cliente nuevo con el mismo id para que el dominio valide igual que al registrar.
        Las cuentas ya abiertas no cambian (su vencimiento se calculó al vender). Si no llegan teléfono o
        dirección (None), se conserva lo guardado."""
        actual = self.repo_clientes.obtener(id_cliente)
        if actual is None:
            raise ValueError("El cliente no existe")
        telefono = actual.telefono if telefono is None else telefono
        direccion = actual.direccion if direccion is None else direccion
        cliente = Cliente(id_cliente, nombres, credito_habilitado, limite_credito, plazo_credito_dias, telefono, direccion)
        self.repo_clientes.guardar(cliente)
        return cliente

    def listar(self):
        return self.repo_clientes.listar()


class ControlInventario:
    def __init__(self, repo_productos):
        self.repo_productos = repo_productos

    def hay_disponible(self, producto, cantidad):
        existencia = self.repo_productos.obtener_existencia(producto.id_producto)
        return existencia.cantidad_disponible() >= cantidad

    def cantidad_disponible(self, producto):
        return self.repo_productos.obtener_existencia(producto.id_producto).cantidad_disponible()

    def descontar(self, producto, cantidad):
        existencia = self.repo_productos.obtener_existencia(producto.id_producto)
        existencia.descontar(cantidad)
        return existencia


class ControlCredito:
    def __init__(self, repo_ventas):
        self.repo_ventas = repo_ventas

    def saldo_pendiente(self, cliente):
        return self.repo_ventas.saldo_pendiente_del_cliente(cliente.id_cliente)   # TD-13: una consulta, no N cuentas

    def puede_comprar_a_credito(self, cliente, monto):
        return cliente.puede_endeudarse(monto, self.saldo_pendiente(cliente))

    def tiene_cuentas_vencidas(self, cliente, ahora=None):
        """Respuesta 2.3: a quien tiene una cuenta vencida sin pagar no se le fía más."""
        ahora = ahora or datetime.now()
        return any(cuenta.esta_vencida(ahora) for cuenta in self.cuentas_del_cliente(cliente.id_cliente))

    def crear_cuenta(self, venta, plazo_dias=PLAZO_POR_DEFECTO_DIAS):
        apertura = datetime.now()
        vencimiento = apertura + timedelta(days=plazo_dias)
        return CuentaPorCobrar(None, venta.id_venta, venta.id_cliente, venta.total, apertura, vencimiento)

    def registrar_abono(self, id_cuenta, monto):
        cuenta = self.repo_ventas.obtener_cuenta(id_cuenta)
        if cuenta is None:
            raise ValueError("La cuenta por cobrar no existe")
        cuenta.aplicar_pago(monto)
        self.repo_ventas.guardar_abono(cuenta, monto)
        return cuenta

    def cuentas_del_cliente(self, id_cliente):
        return self.repo_ventas.cuentas_del_cliente(id_cliente)

    def obtener_cuenta(self, id_cuenta):
        return self.repo_ventas.obtener_cuenta(id_cuenta)


class ServicioDeVentas:
    def __init__(self, repo_productos, repo_clientes, repo_ventas, control_inventario, control_credito):
        self.repo_productos = repo_productos
        self.repo_clientes = repo_clientes
        self.repo_ventas = repo_ventas
        self.control_inventario = control_inventario
        self.control_credito = control_credito

    def registrar_venta_a_credito(self, id_cliente, lineas):
        cliente = self._obtener_cliente(id_cliente)
        venta, pedido = self._armar_venta(Venta(cliente.id_cliente, TipoVenta.CREDITO), lineas)
        self._validar_credito(cliente, venta.calcular_total())
        existencias = self._descontar_existencias(pedido)
        venta.confirmar()
        cuenta = self.control_credito.crear_cuenta(venta, cliente.plazo_credito_dias)
        self.repo_ventas.guardar_transaccion(venta, cuenta, existencias)
        return venta

    def registrar_venta_de_contado(self, lineas, recibido, transferencia=0):
        """UC-02: mismas validaciones de existencias que CU-01, pero sin cliente ni cuenta por cobrar.
        recibido es el efectivo; transferencia, lo pagado por Nequi o Daviplata (respuesta 1.2)."""
        venta, pedido = self._armar_venta(Venta(tipo=TipoVenta.CONTADO), lineas)
        venta.registrar_pago(recibido, transferencia)
        existencias = self._descontar_existencias(pedido)
        venta.confirmar()
        self.repo_ventas.guardar_transaccion(venta, None, existencias)
        return venta

    def obtener(self, id_venta):
        return self.repo_ventas.obtener(id_venta)

    # ------------------------------------------------------------------ devoluciones (respuesta 1.5, cambia DT-08)
    def devolver(self, id_venta, lineas, motivo):
        """Devuelve productos de una venta ya cobrada: vuelven al inventario y se devuelve el dinero o se
        descuenta de la deuda. Si ya no queda nada por devolver, la venta queda ANULADA. Todo o nada (RNF-04)."""
        venta = self._venta_que_se_puede_devolver(id_venta)
        devolucion = Devolucion(venta.id_venta, motivo)
        pendientes = self.pendientes_por_devolver(venta)
        for id_producto, cantidad in lineas:
            self._agregar_a_la_devolucion(devolucion, venta, pendientes, id_producto, cantidad)
        if not devolucion.lineas:
            raise ValueError("Elige al menos un producto para devolver")
        cuenta = self._cuenta_de(venta)
        devolucion.repartir(cuenta)
        if not any(pendientes.values()):
            venta.anular()
        self.repo_ventas.guardar_devolucion(devolucion, venta, cuenta, self._existencias_que_regresan(devolucion))
        return devolucion

    def anular(self, id_venta, motivo):
        """Anular = devolver todo lo que queda de la venta."""
        venta = self._venta_que_se_puede_devolver(id_venta)
        return self.devolver(id_venta, list(self.pendientes_por_devolver(venta).items()), motivo)

    def pendientes_por_devolver(self, venta):
        """{id_producto: unidades vendidas que todavía no se han devuelto}."""
        devueltas = self.repo_ventas.unidades_devueltas(venta.id_venta)
        return {id_producto: vendidas - devueltas.get(id_producto, 0)
                for id_producto, vendidas in venta.unidades_por_producto().items()}

    def unidades_devueltas(self, id_venta):
        return self.repo_ventas.unidades_devueltas(id_venta)

    def devoluciones_de_la_venta(self, id_venta):
        return self.repo_ventas.devoluciones_de_la_venta(id_venta)

    def _venta_que_se_puede_devolver(self, id_venta):
        venta = self.repo_ventas.obtener(id_venta)
        if venta is None:
            raise ValueError("La venta no existe")
        if venta.estado == EstadoVenta.ANULADA:
            raise ValueError(f"La venta #{venta.id_venta} ya está anulada")
        return venta

    def _agregar_a_la_devolucion(self, devolucion, venta, pendientes, id_producto, cantidad):
        if id_producto not in pendientes:
            raise ValueError(f"Ese producto no está en la venta #{venta.id_venta}")
        exigir_mayor_a_cero(cantidad)
        if cantidad > pendientes[id_producto]:
            nombre = self._obtener_producto(id_producto).nombre
            raise ValueError(f"De {nombre} solo se pueden devolver {pendientes[id_producto]}")
        devolucion.agregar(id_producto, cantidad, venta.precio_de(id_producto))
        pendientes[id_producto] -= cantidad

    def _cuenta_de(self, venta):
        if venta.tipo != TipoVenta.CREDITO:
            return None
        return next(c for c in self.repo_ventas.cuentas_del_cliente(venta.id_cliente) if c.id_venta == venta.id_venta)

    def _existencias_que_regresan(self, devolucion):
        existencias = {}
        for linea in devolucion.lineas:
            existencia = existencias.get(linea.id_producto) or self.repo_productos.obtener_existencia(linea.id_producto)
            existencia.aumentar(linea.cantidad)
            existencias[linea.id_producto] = existencia
        return list(existencias.values())

    def listar(self, limite=VENTAS_A_MOSTRAR):
        return self.repo_ventas.listar(limite)

    def _obtener_cliente(self, id_cliente):
        cliente = self.repo_clientes.obtener(id_cliente)
        if cliente is None:
            raise ValueError("El cliente no existe")
        return cliente

    def _obtener_producto(self, id_producto):
        producto = self.repo_productos.obtener(id_producto)
        if producto is None:
            raise ValueError("El producto no existe")
        return producto

    def _armar_venta(self, venta, lineas):
        """Llena la venta y valida el stock. 'pedido' guarda, por producto, el total pedido."""
        pedido = {}
        for linea in map(LineaDeVenta._make, lineas):
            producto = self._obtener_producto(linea.id_producto)
            cantidad_total = pedido.get(producto.id_producto, (producto, 0))[1] + linea.cantidad
            pedido[producto.id_producto] = (producto, cantidad_total)
            if not self.control_inventario.hay_disponible(producto, cantidad_total):
                disponible = self.control_inventario.cantidad_disponible(producto)
                raise StockInsuficiente(f"Solo hay {disponible} disponibles de {producto.nombre}")
            venta.agregar_detalle(producto, linea.cantidad)
        return venta, pedido

    def _validar_credito(self, cliente, total):
        if self.control_credito.tiene_cuentas_vencidas(cliente):
            raise CreditoNoPermitido(f"No se le puede fiar a {cliente.nombres}: tiene cuentas vencidas sin pagar")
        if not self.control_credito.puede_comprar_a_credito(cliente, total):
            raise CreditoNoPermitido(f"El cliente no puede comprar a crédito por {total}")

    def _descontar_existencias(self, pedido):
        return [self.control_inventario.descontar(producto, cantidad)
                for producto, cantidad in pedido.values()]

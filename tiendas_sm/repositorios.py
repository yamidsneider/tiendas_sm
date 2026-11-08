from datetime import datetime

from tiendas_sm.dominio import (Producto, Existencia, Cliente, CuentaPorCobrar, EstadoCuenta, MovimientoDeInventario,
                                Venta, DetalleVenta, TipoVenta, EstadoVenta, FormaDePago)
from tiendas_sm.puertos import PuertoDeClientes, PuertoDeProductos, RepositorioDeVentas

# RepositorioDeVentas se reexporta desde puertos.py: las pruebas y otros módulos lo siguen importando de aquí.
__all__ = ["RepositorioDeVentas", "RepositorioDeVentasSqlite", "RepositorioDeProductos", "RepositorioDeClientes"]

MOVIMIENTO_SALIDA_VENTA = "SALIDA_VENTA"


def _ahora():
    return datetime.now().isoformat()


class RepositorioDeProductos(PuertoDeProductos):
    def __init__(self, conexion):
        self.conexion = conexion

    def guardar(self, producto):
        with self.conexion:
            if producto.id_producto is None:
                self._insertar(producto)
            else:
                self._actualizar(producto)
        return producto.id_producto

    def _insertar(self, producto):
        cursor = self.conexion.execute(
            "INSERT INTO productos (nombre, precio_compra, precio_venta, stock_minimo, codigo) VALUES (?,?,?,?,?)",
            (producto.nombre, producto.precio_compra, producto.precio_venta, producto.stock_minimo,
             producto.codigo or None))
        producto.id_producto = cursor.lastrowid
        self.conexion.execute("INSERT INTO existencias (id_producto, cantidad_actual) VALUES (?, 0)",
                              (producto.id_producto,))

    def _actualizar(self, producto):
        self.conexion.execute(
            "UPDATE productos SET nombre=?, precio_compra=?, precio_venta=?, stock_minimo=?, codigo=? "
            "WHERE id_producto=?",
            (producto.nombre, producto.precio_compra, producto.precio_venta, producto.stock_minimo,
             producto.codigo or None, producto.id_producto))

    def obtener(self, id_producto):
        fila = self.conexion.execute("SELECT * FROM productos WHERE id_producto=?", (id_producto,)).fetchone()
        return self._a_producto(fila) if fila else None

    def listar(self):
        filas = self.conexion.execute("SELECT * FROM productos ORDER BY nombre").fetchall()
        return [self._a_producto(fila) for fila in filas]

    def obtener_por_codigo(self, codigo):
        fila = self.conexion.execute("SELECT * FROM productos WHERE codigo=?", (codigo,)).fetchone()
        return self._a_producto(fila) if fila else None

    @staticmethod
    def _a_producto(fila):
        return Producto(fila["id_producto"], fila["nombre"], fila["precio_compra"],
                        fila["precio_venta"], fila["stock_minimo"], fila["codigo"] or "")

    def obtener_existencia(self, id_producto):
        fila = self.conexion.execute("SELECT * FROM existencias WHERE id_producto=?", (id_producto,)).fetchone()
        if fila is None:
            return None
        return Existencia(fila["id_producto"], fila["cantidad_actual"], fila["cantidad_reservada"])

    def guardar_existencia(self, existencia, tipo_movimiento, cantidad):
        with self.conexion:
            self.conexion.execute("UPDATE existencias SET cantidad_actual=? WHERE id_producto=?",
                                  (existencia.cantidad_actual, existencia.id_producto))
            self.conexion.execute(
                "INSERT INTO movimientos_inventario (id_producto, tipo, cantidad, fecha) VALUES (?,?,?,?)",
                (existencia.id_producto, tipo_movimiento, cantidad, _ahora()))

    def listar_movimientos(self, limite):
        filas = self.conexion.execute(
            "SELECT * FROM movimientos_inventario ORDER BY id_movimiento DESC LIMIT ?", (limite,)).fetchall()
        return [MovimientoDeInventario(fila["id_movimiento"], fila["id_producto"], fila["tipo"], fila["cantidad"],
                                       datetime.fromisoformat(fila["fecha"])) for fila in filas]


class RepositorioDeClientes(PuertoDeClientes):
    def __init__(self, conexion):
        self.conexion = conexion

    def guardar(self, cliente):
        """Si el cliente no tiene id es nuevo (INSERT); si ya lo tiene, se actualizan sus datos (Editar cliente)."""
        datos = (cliente.nombres, int(cliente.credito_habilitado), cliente.limite_credito, cliente.plazo_credito_dias,
                 cliente.telefono, cliente.direccion)
        with self.conexion:
            if cliente.id_cliente is None:
                cursor = self.conexion.execute(
                    "INSERT INTO clientes (nombres, credito_habilitado, limite_credito, plazo_credito_dias, telefono, "
                    "direccion) VALUES (?,?,?,?,?,?)", datos)
                cliente.id_cliente = cursor.lastrowid
            else:
                self.conexion.execute(
                    "UPDATE clientes SET nombres=?, credito_habilitado=?, limite_credito=?, plazo_credito_dias=?, "
                    "telefono=?, direccion=? WHERE id_cliente=?", (*datos, cliente.id_cliente))
        return cliente.id_cliente

    def obtener(self, id_cliente):
        fila = self.conexion.execute("SELECT * FROM clientes WHERE id_cliente=?", (id_cliente,)).fetchone()
        return self._a_cliente(fila) if fila else None

    def listar(self):
        filas = self.conexion.execute("SELECT * FROM clientes ORDER BY nombres").fetchall()
        return [self._a_cliente(fila) for fila in filas]

    @staticmethod
    def _a_cliente(fila):
        return Cliente(fila["id_cliente"], fila["nombres"], bool(fila["credito_habilitado"]),
                       fila["limite_credito"], fila["plazo_credito_dias"], fila["telefono"], fila["direccion"])


class RepositorioDeVentasSqlite(RepositorioDeVentas):
    def __init__(self, conexion):
        self.conexion = conexion

    def guardar_transaccion(self, venta, cuenta, existencias):
        with self.conexion:
            self._insertar_venta(venta)
            self._insertar_detalles(venta)
            if cuenta is not None:
                self._insertar_cuenta(venta, cuenta)
            self._actualizar_existencias(existencias)
            self._insertar_salidas(venta)

    def _insertar_venta(self, venta):
        forma_pago = venta.forma_pago.value if venta.forma_pago else None
        cursor = self.conexion.execute(
            "INSERT INTO ventas (id_cliente, fecha, estado, total, tipo, forma_pago, valor_recibido) "
            "VALUES (?,?,?,?,?,?,?)",
            (venta.id_cliente, venta.fecha.isoformat(), venta.estado.value, venta.total,
             venta.tipo.value, forma_pago, venta.valor_recibido))
        venta.id_venta = cursor.lastrowid

    def _insertar_detalles(self, venta):
        for detalle in venta.detalles:
            self.conexion.execute(
                "INSERT INTO detalles_venta (id_venta, numero_linea, id_producto, cantidad, "
                "precio_unitario_venta, subtotal_linea) VALUES (?,?,?,?,?,?)",
                (venta.id_venta, detalle.numero_linea, detalle.id_producto, detalle.cantidad,
                 detalle.precio_unitario, detalle.subtotal()))

    def _insertar_cuenta(self, venta, cuenta):
        cuenta.id_venta = venta.id_venta
        cursor = self.conexion.execute(
            "INSERT INTO cuentas_por_cobrar (id_venta, id_cliente, fecha_apertura, fecha_vencimiento, "
            "monto_credito_original, estado) VALUES (?,?,?,?,?,?)",
            (cuenta.id_venta, cuenta.id_cliente, cuenta.fecha_apertura.isoformat(),
             cuenta.fecha_vencimiento.isoformat(), cuenta.monto_original, cuenta.estado.value))
        cuenta.id_cuenta = cursor.lastrowid

    def _actualizar_existencias(self, existencias):
        for existencia in existencias:
            self.conexion.execute("UPDATE existencias SET cantidad_actual=? WHERE id_producto=?",
                                  (existencia.cantidad_actual, existencia.id_producto))

    def _insertar_salidas(self, venta):
        """TD-01: un movimiento SALIDA_VENTA por producto (suma sus líneas), con la fecha de la venta."""
        vendido = {}
        for detalle in venta.detalles:
            vendido[detalle.id_producto] = vendido.get(detalle.id_producto, 0) + detalle.cantidad
        for id_producto, cantidad in vendido.items():
            self.conexion.execute(
                "INSERT INTO movimientos_inventario (id_producto, tipo, cantidad, fecha) VALUES (?,?,?,?)",
                (id_producto, MOVIMIENTO_SALIDA_VENTA, cantidad, venta.fecha.isoformat()))

    def saldo_pendiente_del_cliente(self, id_cliente):
        """TD-13: misma regla que CuentaPorCobrar.calcular_saldo (monto original − abonos), sumada en una consulta."""
        fila = self.conexion.execute(
            "SELECT COALESCE(SUM(c.monto_credito_original - COALESCE(a.pagado, 0)), 0) FROM cuentas_por_cobrar c "
            "LEFT JOIN (SELECT id_cuenta, SUM(valor) AS pagado FROM abonos GROUP BY id_cuenta) a "
            "ON a.id_cuenta = c.id_cuenta WHERE c.id_cliente = ?", (id_cliente,)).fetchone()
        return fila[0]

    def cuentas_del_cliente(self, id_cliente):
        filas = self.conexion.execute(
            "SELECT * FROM cuentas_por_cobrar WHERE id_cliente=? ORDER BY id_cuenta", (id_cliente,)).fetchall()
        return [self._a_cuenta(fila) for fila in filas]

    def obtener_cuenta(self, id_cuenta):
        fila = self.conexion.execute("SELECT * FROM cuentas_por_cobrar WHERE id_cuenta=?", (id_cuenta,)).fetchone()
        return self._a_cuenta(fila) if fila else None

    def _a_cuenta(self, fila):
        cuenta = CuentaPorCobrar(fila["id_cuenta"], fila["id_venta"], fila["id_cliente"],
                                 fila["monto_credito_original"], datetime.fromisoformat(fila["fecha_apertura"]),
                                 datetime.fromisoformat(fila["fecha_vencimiento"]))  # TD-14: se guardan como texto ISO
        cuenta.estado = EstadoCuenta(fila["estado"])
        abonos = self.conexion.execute(
            "SELECT valor FROM abonos WHERE id_cuenta=? ORDER BY id_abono", (cuenta.id_cuenta,)).fetchall()
        cuenta.abonos = [abono["valor"] for abono in abonos]
        return cuenta

    def contar_ventas(self):
        return self.conexion.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]

    def obtener(self, id_venta):
        fila = self.conexion.execute("SELECT * FROM ventas WHERE id_venta=?", (id_venta,)).fetchone()
        return self._a_venta(fila) if fila else None

    def listar(self, limite):
        filas = self.conexion.execute("SELECT * FROM ventas ORDER BY id_venta DESC LIMIT ?", (limite,)).fetchall()
        return [self._a_venta(fila) for fila in filas]

    def _a_venta(self, fila):
        """Rearma la venta tal como se guardó: precio de cada línea, total, pago y fecha (TD-14: texto ISO)."""
        venta = Venta(fila["id_cliente"], TipoVenta(fila["tipo"]))
        venta.id_venta = fila["id_venta"]
        venta.fecha = datetime.fromisoformat(fila["fecha"])
        venta.estado = EstadoVenta(fila["estado"])
        venta.total = fila["total"]
        venta.forma_pago = FormaDePago(fila["forma_pago"]) if fila["forma_pago"] else None
        venta.valor_recibido = fila["valor_recibido"]
        detalles = self.conexion.execute(
            "SELECT * FROM detalles_venta WHERE id_venta=? ORDER BY numero_linea", (venta.id_venta,)).fetchall()
        venta.detalles = [DetalleVenta(d["numero_linea"], d["id_producto"], d["cantidad"], d["precio_unitario_venta"])
                          for d in detalles]
        return venta

    def guardar_abono(self, cuenta, valor):
        with self.conexion:
            self.conexion.execute("INSERT INTO abonos (id_cuenta, valor, fecha) VALUES (?,?,?)",
                                  (cuenta.id_cuenta, valor, _ahora()))
            self.conexion.execute("UPDATE cuentas_por_cobrar SET estado=? WHERE id_cuenta=?",
                                  (cuenta.estado.value, cuenta.id_cuenta))

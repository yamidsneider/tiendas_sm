import sqlite3
from datetime import date, datetime

from tiendas_sm.dominio import (Producto, Existencia, Cliente, CuentaPorCobrar, EstadoCuenta, MovimientoDeInventario,
                                Venta, DetalleVenta, TipoVenta, EstadoVenta, FormaDePago, Devolucion, Lote,
                                ResumenDeVentas, ProductoMasVendido, TurnoDeCaja, Usuario, MovimientoDeCuenta,
                                Proveedor, Compra, tomar_fefo)
from tiendas_sm.puertos import (PuertoDeCaja, PuertoDeClientes, PuertoDeCompras, PuertoDeConfiguracion,
                                PuertoDeProductos,
                                PuertoDeReportes, PuertoDeUsuarios, RepositorioDeVentas)

# RepositorioDeVentas se reexporta desde puertos.py: las pruebas y otros módulos lo siguen importando de aquí.
__all__ = ["RepositorioDeVentas", "RepositorioDeVentasSqlite", "RepositorioDeProductos", "RepositorioDeClientes",
           "RepositorioDeReportesSqlite", "RepositorioDeUsuarios", "RepositorioDeCaja", "RepositorioDeCompras"]

MOVIMIENTO_SALIDA_VENTA = "SALIDA_VENTA"
MOVIMIENTO_DEVOLUCION = "DEVOLUCION"
MOVIMIENTO_SALIDA_MANUAL = "SALIDA_MANUAL"      # fase 3


def _ahora():
    return datetime.now().isoformat()


def _fila_a_lote(fila):
    return Lote(fila["id_lote"], fila["id_producto"], fila["numero"], date.fromisoformat(fila["fecha_vencimiento"]),
                fila["cantidad"], bool(fila["activo"]), fila["saldo"])


def _descontar_de_lotes(conexion, id_producto, cantidad):
    """Fase 9: dentro de la misma transacción que la venta o la salida, descuenta FEFO de los lotes del producto
    (la regla está en el dominio: tomar_fefo). Lo que no alcance sale de las unidades sin lote."""
    filas = conexion.execute("SELECT * FROM lotes WHERE id_producto=? AND activo=1 AND saldo > 0",
                             (id_producto,)).fetchall()
    lotes = [_fila_a_lote(fila) for fila in filas]
    tomar_fefo(lotes, cantidad)
    for lote in lotes:
        conexion.execute("UPDATE lotes SET saldo=?, activo=? WHERE id_lote=?", (lote.saldo, int(lote.activo), lote.id_lote))


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
            "INSERT INTO productos (nombre, precio_compra, precio_venta, stock_minimo, codigo, dias_aviso, activo) "
            "VALUES (?,?,?,?,?,?,?)",
            (producto.nombre, producto.precio_compra, producto.precio_venta, producto.stock_minimo,
             producto.codigo or None, producto.dias_aviso, int(producto.activo)))
        producto.id_producto = cursor.lastrowid
        self.conexion.execute("INSERT INTO existencias (id_producto, cantidad_actual) VALUES (?, 0)",
                              (producto.id_producto,))

    def _actualizar(self, producto):
        self.conexion.execute(
            "UPDATE productos SET nombre=?, precio_compra=?, precio_venta=?, stock_minimo=?, codigo=?, dias_aviso=?, "
            "activo=? WHERE id_producto=?",
            (producto.nombre, producto.precio_compra, producto.precio_venta, producto.stock_minimo,
             producto.codigo or None, producto.dias_aviso, int(producto.activo), producto.id_producto))

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
                        fila["precio_venta"], fila["stock_minimo"], fila["codigo"] or "", fila["dias_aviso"],
                        bool(fila["activo"]))

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

    def guardar_salida_manual(self, existencia, cantidad, motivo, id_usuario, id_autorizo, costo_unitario):
        with self.conexion:
            self.conexion.execute("UPDATE existencias SET cantidad_actual=? WHERE id_producto=?",
                                  (existencia.cantidad_actual, existencia.id_producto))
            self.conexion.execute(
                "INSERT INTO movimientos_inventario (id_producto, tipo, cantidad, fecha, motivo, id_usuario, id_autorizo, "
                "costo_unitario) VALUES (?,?,?,?,?,?,?,?)",
                (existencia.id_producto, MOVIMIENTO_SALIDA_MANUAL, cantidad, _ahora(), motivo, id_usuario, id_autorizo,
                 costo_unitario))
            _descontar_de_lotes(self.conexion, existencia.id_producto, cantidad)    # fase 9: FEFO

    def listar_movimientos(self, limite):
        filas = self.conexion.execute(
            "SELECT * FROM movimientos_inventario ORDER BY id_movimiento DESC LIMIT ?", (limite,)).fetchall()
        return [MovimientoDeInventario(fila["id_movimiento"], fila["id_producto"], fila["tipo"], fila["cantidad"],
                                       datetime.fromisoformat(fila["fecha"]), fila["motivo"]) for fila in filas]

    def guardar_lote(self, lote):
        with self.conexion:
            if lote.id_lote is None:
                cursor = self.conexion.execute(
                    "INSERT INTO lotes (id_producto, numero, fecha_vencimiento, cantidad, activo, saldo) "
                    "VALUES (?,?,?,?,?,?)",
                    (lote.id_producto, lote.numero, lote.fecha_vencimiento.isoformat(), lote.cantidad, int(lote.activo),
                     lote.saldo))
                lote.id_lote = cursor.lastrowid
            else:
                self.conexion.execute("UPDATE lotes SET activo=?, saldo=? WHERE id_lote=?",
                                      (int(lote.activo), lote.saldo, lote.id_lote))
        return lote.id_lote

    def obtener_lote(self, id_lote):
        fila = self.conexion.execute("SELECT * FROM lotes WHERE id_lote=?", (id_lote,)).fetchone()
        return self._a_lote(fila) if fila else None

    def lotes_activos(self):
        filas = self.conexion.execute(
            "SELECT * FROM lotes WHERE activo=1 ORDER BY fecha_vencimiento, id_lote").fetchall()
        return [self._a_lote(fila) for fila in filas]

    @staticmethod
    def _a_lote(fila):
        return _fila_a_lote(fila)


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
            for id_producto, cantidad in venta.unidades_por_producto().items():      # fase 9: FEFO
                _descontar_de_lotes(self.conexion, id_producto, cantidad)

    def _insertar_venta(self, venta):
        forma_pago = venta.forma_pago.value if venta.forma_pago else None
        cursor = self.conexion.execute(
            "INSERT INTO ventas (id_cliente, fecha, estado, total, tipo, forma_pago, valor_recibido, valor_transferencia) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (venta.id_cliente, venta.fecha.isoformat(), venta.estado.value, venta.total,
             venta.tipo.value, forma_pago, venta.valor_recibido, venta.valor_transferencia))
        venta.id_venta = cursor.lastrowid

    def _insertar_detalles(self, venta):
        for detalle in venta.detalles:
            self.conexion.execute(
                "INSERT INTO detalles_venta (id_venta, numero_linea, id_producto, cantidad, "
                "precio_unitario_venta, subtotal_linea, costo_unitario) VALUES (?,?,?,?,?,?,?)",
                (venta.id_venta, detalle.numero_linea, detalle.id_producto, detalle.cantidad,
                 detalle.precio_unitario, detalle.subtotal(), detalle.costo_unitario))

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

    def movimientos_de_cuenta(self, id_cliente):
        """Fase 7: compras fiadas, abonos y devoluciones que bajaron la deuda. orden desempata el mismo instante."""
        filas = self.conexion.execute(SQL_MOVIMIENTOS_DE_CUENTA, (id_cliente,) * 3).fetchall()
        return [MovimientoDeCuenta(datetime.fromisoformat(f["fecha"]), f["tipo"], f["id_venta"], f["valor"])
                for f in filas]

    def saldo_pendiente_del_cliente(self, id_cliente):
        """TD-13: misma regla que CuentaPorCobrar.calcular_saldo (monto original − abonos), sumada en una consulta."""
        fila = self.conexion.execute(
            "SELECT COALESCE(SUM(c.monto_credito_original - COALESCE(a.pagado, 0) - c.valor_devuelto), 0) "
            "FROM cuentas_por_cobrar c "
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
        cuenta.valor_devuelto = fila["valor_devuelto"]
        abonos = self.conexion.execute(
            "SELECT valor FROM abonos WHERE id_cuenta=? ORDER BY id_abono", (cuenta.id_cuenta,)).fetchall()
        cuenta.abonos = [abono["valor"] for abono in abonos]
        return cuenta

    def unidades_devueltas(self, id_venta):
        filas = self.conexion.execute(
            "SELECT d.id_producto, SUM(d.cantidad) AS cantidad FROM detalles_devolucion d "
            "JOIN devoluciones v ON v.id_devolucion = d.id_devolucion WHERE v.id_venta=? GROUP BY d.id_producto",
            (id_venta,)).fetchall()
        return {fila["id_producto"]: fila["cantidad"] for fila in filas}

    def devoluciones_de_la_venta(self, id_venta):
        filas = self.conexion.execute("SELECT * FROM devoluciones WHERE id_venta=? ORDER BY id_devolucion",
                                      (id_venta,)).fetchall()
        return [self._a_devolucion(fila) for fila in filas]

    def _a_devolucion(self, fila):
        devolucion = Devolucion(fila["id_venta"], fila["motivo"], datetime.fromisoformat(fila["fecha"]))
        devolucion.id_devolucion = fila["id_devolucion"]
        devolucion.descontado_de_la_deuda = fila["descontado_de_la_deuda"]
        devolucion.efectivo_devuelto = fila["efectivo_devuelto"]
        for linea in self.conexion.execute("SELECT * FROM detalles_devolucion WHERE id_devolucion=? ORDER BY id_detalle",
                                           (devolucion.id_devolucion,)):
            devolucion.agregar(linea["id_producto"], linea["cantidad"], linea["precio_unitario"])
        return devolucion

    def guardar_devolucion(self, devolucion, venta, cuenta, existencias):
        """RNF-04: devolución, movimientos, existencias, cuenta y estado de la venta en una sola transacción."""
        fecha = devolucion.fecha.isoformat()
        with self.conexion:
            cursor = self.conexion.execute(
                "INSERT INTO devoluciones (id_venta, fecha, motivo, valor, descontado_de_la_deuda, efectivo_devuelto) "
                "VALUES (?,?,?,?,?,?)", (devolucion.id_venta, fecha, devolucion.motivo, devolucion.valor(),
                                         devolucion.descontado_de_la_deuda, devolucion.efectivo_devuelto))
            devolucion.id_devolucion = cursor.lastrowid
            for linea in devolucion.lineas:
                self.conexion.execute(
                    "INSERT INTO detalles_devolucion (id_devolucion, id_producto, cantidad, precio_unitario) VALUES (?,?,?,?)",
                    (devolucion.id_devolucion, linea.id_producto, linea.cantidad, linea.precio_unitario))
                self.conexion.execute(
                    "INSERT INTO movimientos_inventario (id_producto, tipo, cantidad, fecha) VALUES (?,?,?,?)",
                    (linea.id_producto, MOVIMIENTO_DEVOLUCION, linea.cantidad, fecha))
            self._actualizar_existencias(existencias)
            if cuenta is not None:
                self.conexion.execute("UPDATE cuentas_por_cobrar SET valor_devuelto=?, estado=? WHERE id_cuenta=?",
                                      (cuenta.valor_devuelto, cuenta.estado.value, cuenta.id_cuenta))
            self.conexion.execute("UPDATE ventas SET estado=? WHERE id_venta=?", (venta.estado.value, venta.id_venta))

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
        venta.valor_transferencia = fila["valor_transferencia"] or 0 if venta.forma_pago else None
        detalles = self.conexion.execute(
            "SELECT * FROM detalles_venta WHERE id_venta=? ORDER BY numero_linea", (venta.id_venta,)).fetchall()
        venta.detalles = [DetalleVenta(d["numero_linea"], d["id_producto"], d["cantidad"], d["precio_unitario_venta"],
                                       d["costo_unitario"]) for d in detalles]
        return venta

    def guardar_abono(self, cuenta, valor):
        with self.conexion:
            self.conexion.execute("INSERT INTO abonos (id_cuenta, valor, fecha) VALUES (?,?,?)",
                                  (cuenta.id_cuenta, valor, _ahora()))
            self.conexion.execute("UPDATE cuentas_por_cobrar SET estado=? WHERE id_cuenta=?",
                                  (cuenta.estado.value, cuenta.id_cuenta))


# ---------------------------------------------------------------------- estado de cuenta (fase 7)
SQL_MOVIMIENTOS_DE_CUENTA = (
    "SELECT fecha, tipo, id_venta, valor FROM ("
    "SELECT fecha_apertura AS fecha, 'Compra' AS tipo, id_venta, monto_credito_original AS valor, 1 AS orden "
    "FROM cuentas_por_cobrar WHERE id_cliente = ? "
    "UNION ALL SELECT a.fecha, 'Abono', c.id_venta, a.valor, 2 FROM abonos a "
    "JOIN cuentas_por_cobrar c ON c.id_cuenta = a.id_cuenta WHERE c.id_cliente = ? "
    "UNION ALL SELECT d.fecha, 'Devolución', d.id_venta, d.descontado_de_la_deuda, 3 FROM devoluciones d "
    "JOIN cuentas_por_cobrar c ON c.id_venta = d.id_venta WHERE c.id_cliente = ? AND d.descontado_de_la_deuda > 0"
    ") ORDER BY fecha, orden")


# ---------------------------------------------------------------------- reportes (fase 1)
# Las fechas se guardan como texto ISO (TD-14), así que «fecha >= desde AND fecha < hasta» compara bien como texto.
SQL_TOTALES_DE_VENTAS = (
    "SELECT COUNT(*) AS numero, COALESCE(SUM(total), 0) AS vendido, "
    "COALESCE(SUM(CASE WHEN tipo = 'CONTADO' THEN total - COALESCE(valor_transferencia, 0) END), 0) AS efectivo, "
    "COALESCE(SUM(CASE WHEN tipo = 'CONTADO' THEN COALESCE(valor_transferencia, 0) END), 0) AS transferencia, "
    "COALESCE(SUM(CASE WHEN tipo = 'CREDITO' THEN total END), 0) AS credito "
    "FROM ventas WHERE fecha >= ? AND fecha < ?")
SQL_TOTALES_DE_DEVOLUCIONES = ("SELECT COALESCE(SUM(valor), 0), COALESCE(SUM(efectivo_devuelto), 0) "
                               "FROM devoluciones WHERE fecha >= ? AND fecha < ?")
SQL_TOTAL_DE_ABONOS = "SELECT COALESCE(SUM(valor), 0) FROM abonos WHERE fecha >= ? AND fecha < ?"
SQL_TOTAL_DE_COMPRAS = "SELECT COALESCE(SUM(total), 0) FROM compras WHERE fecha >= ? AND fecha < ?"   # fase 8
SQL_SALIDAS_AL_COSTO = ("SELECT COALESCE(SUM(cantidad * COALESCE(costo_unitario, 0)), 0) FROM movimientos_inventario "
                        "WHERE tipo = 'SALIDA_MANUAL' AND fecha >= ? AND fecha < ?")
# Ganancia de lo vendido: precio de venta − costo guardado (o el precio de compra actual si la línea es vieja).
SQL_GANANCIA_VENDIDA = (
    "SELECT COALESCE(SUM(d.cantidad * (d.precio_unitario_venta - COALESCE(d.costo_unitario, p.precio_compra))), 0), "
    "COALESCE(MAX(d.costo_unitario IS NULL), 0) "
    "FROM detalles_venta d JOIN ventas v ON v.id_venta = d.id_venta JOIN productos p ON p.id_producto = d.id_producto "
    "WHERE v.fecha >= ? AND v.fecha < ?")
# Ganancia que se pierde con lo devuelto: con el mismo costo de la línea de la venta original.
SQL_GANANCIA_DEVUELTA = (
    "SELECT COALESCE(SUM(dd.cantidad * (dd.precio_unitario - COALESCE("
    "(SELECT MAX(d.costo_unitario) FROM detalles_venta d WHERE d.id_venta = dv.id_venta AND d.id_producto = dd.id_producto), "
    "p.precio_compra))), 0) "
    "FROM detalles_devolucion dd JOIN devoluciones dv ON dv.id_devolucion = dd.id_devolucion "
    "JOIN productos p ON p.id_producto = dd.id_producto WHERE dv.fecha >= ? AND dv.fecha < ?")
# Unidades netas por producto: lo vendido en el rango menos lo devuelto en el rango.
SQL_MAS_VENDIDOS = (
    "SELECT p.id_producto, p.nombre, SUM(m.unidades) AS unidades, SUM(m.valor) AS valor FROM ("
    "SELECT d.id_producto, d.cantidad AS unidades, d.subtotal_linea AS valor FROM detalles_venta d "
    "JOIN ventas v ON v.id_venta = d.id_venta WHERE v.fecha >= ? AND v.fecha < ? "
    "UNION ALL "
    "SELECT dd.id_producto, -dd.cantidad, -dd.cantidad * dd.precio_unitario FROM detalles_devolucion dd "
    "JOIN devoluciones dv ON dv.id_devolucion = dd.id_devolucion WHERE dv.fecha >= ? AND dv.fecha < ?"
    ") m JOIN productos p ON p.id_producto = m.id_producto "
    "GROUP BY p.id_producto HAVING SUM(m.unidades) > 0 ORDER BY unidades DESC, valor DESC, p.nombre LIMIT ?")


class RepositorioDeReportesSqlite(PuertoDeReportes):
    """Fase 1: solo consultas con parámetros (?), sin armar SQL con texto del usuario."""

    def __init__(self, conexion):
        self.conexion = conexion

    def resumen_de_ventas(self, desde, hasta):
        rango = (desde.isoformat(), hasta.isoformat())
        ventas = self.conexion.execute(SQL_TOTALES_DE_VENTAS, rango).fetchone()
        devuelto, efectivo_devuelto = self.conexion.execute(SQL_TOTALES_DE_DEVOLUCIONES, rango).fetchone()
        abonos = self.conexion.execute(SQL_TOTAL_DE_ABONOS, rango).fetchone()[0]
        ganancia, estimada = self.conexion.execute(SQL_GANANCIA_VENDIDA, rango).fetchone()
        ganancia_devuelta = self.conexion.execute(SQL_GANANCIA_DEVUELTA, rango).fetchone()[0]
        salidas = self.conexion.execute(SQL_SALIDAS_AL_COSTO, rango).fetchone()[0]
        compras = self.conexion.execute(SQL_TOTAL_DE_COMPRAS, rango).fetchone()[0]
        return ResumenDeVentas(ventas["numero"], ventas["vendido"], devuelto, efectivo_devuelto, ventas["efectivo"],
                               ventas["transferencia"], ventas["credito"], abonos, ganancia - ganancia_devuelta,
                               bool(estimada), salidas, compras)

    def mas_vendidos(self, desde, hasta, limite):
        rango = (desde.isoformat(), hasta.isoformat())
        filas = self.conexion.execute(SQL_MAS_VENDIDOS, rango + rango + (limite,)).fetchall()
        return [ProductoMasVendido(f["id_producto"], f["nombre"], f["unidades"], f["valor"]) for f in filas]


# ---------------------------------------------------------------------- usuarios (fase 2)
class RepositorioDeUsuarios(PuertoDeUsuarios):
    def __init__(self, conexion):
        self.conexion = conexion

    def guardar(self, usuario):
        datos = (usuario.nombre, usuario.usuario, usuario.rol.value, usuario.clave_hash, usuario.sal, int(usuario.activo))
        try:
            with self.conexion:
                if usuario.id_usuario is None:
                    cursor = self.conexion.execute(
                        "INSERT INTO usuarios (nombre, usuario, rol, clave_hash, sal, activo) VALUES (?,?,?,?,?,?)", datos)
                    usuario.id_usuario = cursor.lastrowid
                else:
                    self.conexion.execute("UPDATE usuarios SET nombre=?, usuario=?, rol=?, clave_hash=?, sal=?, activo=? "
                                          "WHERE id_usuario=?", datos + (usuario.id_usuario,))
        except sqlite3.IntegrityError:
            raise ValueError(f"Ya existe el usuario «{usuario.usuario}»") from None
        return usuario

    def obtener(self, id_usuario):
        fila = self.conexion.execute("SELECT * FROM usuarios WHERE id_usuario=?", (id_usuario,)).fetchone()
        return self._a_usuario(fila) if fila else None

    def obtener_por_usuario(self, usuario):
        fila = self.conexion.execute("SELECT * FROM usuarios WHERE usuario=?", (usuario,)).fetchone()
        return self._a_usuario(fila) if fila else None

    def listar(self):
        filas = self.conexion.execute("SELECT * FROM usuarios ORDER BY nombre COLLATE NOCASE").fetchall()
        return [self._a_usuario(fila) for fila in filas]

    @staticmethod
    def _a_usuario(fila):
        return Usuario(fila["id_usuario"], fila["nombre"], fila["usuario"], fila["rol"], fila["clave_hash"], fila["sal"],
                       bool(fila["activo"]))


# ---------------------------------------------------------------------- configuración (fase 5; la usará la fase 6)
class RepositorioDeConfiguracion(PuertoDeConfiguracion):
    """Pares clave/valor en texto (por ejemplo la carpeta de los respaldos). Es infraestructura: el núcleo no la usa."""

    def __init__(self, conexion):
        self.conexion = conexion

    def obtener(self, clave, por_defecto=None):
        fila = self.conexion.execute("SELECT valor FROM configuracion WHERE clave=?", (clave,)).fetchone()
        return fila[0] if fila else por_defecto

    def guardar(self, clave, valor):
        with self.conexion:
            self.conexion.execute("INSERT INTO configuracion (clave, valor) VALUES (?,?) "
                                  "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor", (clave, valor))


# ---------------------------------------------------------------------- caja (fase 4)
def _fecha_o_nada(texto):
    return datetime.fromisoformat(texto) if texto else None


class RepositorioDeCaja(PuertoDeCaja):
    def __init__(self, conexion):
        self.conexion = conexion

    def guardar(self, turno):
        cerrado = turno.cerrado_en.isoformat() if turno.cerrado_en else None
        with self.conexion:
            if turno.id_turno is None:
                cursor = self.conexion.execute(
                    "INSERT INTO turnos_caja (base, abierto_en, id_usuario_abre) VALUES (?,?,?)",
                    (turno.base, turno.abierto_en.isoformat(), turno.id_usuario_abre))
                turno.id_turno = cursor.lastrowid
            else:
                self.conexion.execute(
                    "UPDATE turnos_caja SET cerrado_en=?, id_usuario_cierra=?, efectivo_esperado=?, efectivo_contado=? "
                    "WHERE id_turno=?", (cerrado, turno.id_usuario_cierra, turno.efectivo_esperado,
                                         turno.efectivo_contado, turno.id_turno))
        return turno

    def turno_abierto(self):
        fila = self.conexion.execute("SELECT * FROM turnos_caja WHERE cerrado_en IS NULL "
                                     "ORDER BY id_turno DESC LIMIT 1").fetchone()
        return self._a_turno(fila) if fila else None

    def listar_cerrados(self, limite):
        filas = self.conexion.execute("SELECT * FROM turnos_caja WHERE cerrado_en IS NOT NULL "
                                      "ORDER BY id_turno DESC LIMIT ?", (limite,)).fetchall()
        return [self._a_turno(fila) for fila in filas]

    @staticmethod
    def _a_turno(fila):
        return TurnoDeCaja(fila["id_turno"], fila["base"], datetime.fromisoformat(fila["abierto_en"]),
                           fila["id_usuario_abre"], _fecha_o_nada(fila["cerrado_en"]), fila["id_usuario_cierra"],
                           fila["efectivo_esperado"], fila["efectivo_contado"])


# ---------------------------------------------------------------------- proveedores y compras (fase 8)
class RepositorioDeCompras(PuertoDeCompras):
    def __init__(self, conexion):
        self.conexion = conexion

    def guardar_proveedor(self, proveedor):
        with self.conexion:
            cursor = self.conexion.execute("INSERT INTO proveedores (nombre, telefono, nit) VALUES (?,?,?)",
                                           (proveedor.nombre, proveedor.telefono, proveedor.nit))
        proveedor.id_proveedor = cursor.lastrowid
        return proveedor

    def obtener_proveedor(self, id_proveedor):
        fila = self.conexion.execute("SELECT * FROM proveedores WHERE id_proveedor=?", (id_proveedor,)).fetchone()
        return Proveedor(fila["id_proveedor"], fila["nombre"], fila["telefono"], fila["nit"]) if fila else None

    def listar_proveedores(self):
        filas = self.conexion.execute("SELECT * FROM proveedores ORDER BY nombre COLLATE NOCASE").fetchall()
        return [Proveedor(f["id_proveedor"], f["nombre"], f["telefono"], f["nit"]) for f in filas]

    def guardar_compra(self, compra, existencias, productos, motivo):
        """RNF-04: si algo falla, no queda nada a medias. motivo es una función id_compra -> texto del movimiento."""
        fecha = compra.fecha.isoformat()
        with self.conexion:
            cursor = self.conexion.execute(
                "INSERT INTO compras (id_proveedor, id_usuario, fecha, factura, total) VALUES (?,?,?,?,?)",
                (compra.id_proveedor, compra.id_usuario, fecha, compra.factura, compra.total()))
            compra.id_compra = cursor.lastrowid
            for linea in compra.lineas:
                self.conexion.execute(
                    "INSERT INTO detalles_compra (id_compra, id_producto, cantidad, costo_unitario) VALUES (?,?,?,?)",
                    (compra.id_compra, linea.id_producto, linea.cantidad, linea.costo_unitario))
                self.conexion.execute(
                    "INSERT INTO movimientos_inventario (id_producto, tipo, cantidad, fecha, motivo, id_usuario, "
                    "costo_unitario) VALUES (?, 'ENTRADA', ?, ?, ?, ?, ?)",
                    (linea.id_producto, linea.cantidad, fecha, motivo(compra.id_compra), compra.id_usuario,
                     linea.costo_unitario))
            for existencia in existencias:
                self.conexion.execute("UPDATE existencias SET cantidad_actual=? WHERE id_producto=?",
                                      (existencia.cantidad_actual, existencia.id_producto))
            for producto in productos:
                self.conexion.execute("UPDATE productos SET precio_compra=? WHERE id_producto=?",
                                      (producto.precio_compra, producto.id_producto))
        return compra

    def obtener_compra(self, id_compra):
        fila = self.conexion.execute("SELECT * FROM compras WHERE id_compra=?", (id_compra,)).fetchone()
        return self._a_compra(fila) if fila else None

    def listar_compras(self, limite):
        filas = self.conexion.execute("SELECT * FROM compras ORDER BY id_compra DESC LIMIT ?", (limite,)).fetchall()
        return [self._a_compra(fila) for fila in filas]

    def _a_compra(self, fila):
        compra = Compra(fila["id_compra"], fila["id_proveedor"], fila["id_usuario"], fila["factura"],
                        datetime.fromisoformat(fila["fecha"]))
        for linea in self.conexion.execute("SELECT * FROM detalles_compra WHERE id_compra=? ORDER BY id_detalle",
                                           (compra.id_compra,)):
            compra.agregar(linea["id_producto"], linea["cantidad"], linea["costo_unitario"])
        return compra

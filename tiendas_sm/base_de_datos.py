import sqlite3

ESQUEMA_SQL = """
CREATE TABLE IF NOT EXISTS productos (
    id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL, precio_compra INTEGER NOT NULL,
    precio_venta INTEGER NOT NULL, stock_minimo INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS existencias (
    id_producto INTEGER PRIMARY KEY REFERENCES productos(id_producto),
    cantidad_actual INTEGER NOT NULL, cantidad_reservada INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS movimientos_inventario (
    id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producto INTEGER NOT NULL REFERENCES productos(id_producto),
    tipo TEXT NOT NULL, cantidad INTEGER NOT NULL, fecha TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    nombres TEXT NOT NULL, credito_habilitado INTEGER NOT NULL,
    limite_credito INTEGER NOT NULL, plazo_credito_dias INTEGER NOT NULL,
    telefono TEXT NOT NULL DEFAULT '', direccion TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS ventas (
    id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER REFERENCES clientes(id_cliente),
    fecha TEXT NOT NULL, estado TEXT NOT NULL, total INTEGER NOT NULL,
    tipo TEXT NOT NULL, forma_pago TEXT, valor_recibido INTEGER, valor_transferencia INTEGER);
CREATE TABLE IF NOT EXISTS detalles_venta (
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venta INTEGER NOT NULL REFERENCES ventas(id_venta),
    numero_linea INTEGER NOT NULL,
    id_producto INTEGER NOT NULL REFERENCES productos(id_producto),
    cantidad INTEGER NOT NULL, precio_unitario_venta INTEGER NOT NULL,
    subtotal_linea INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS cuentas_por_cobrar (
    id_cuenta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venta INTEGER NOT NULL REFERENCES ventas(id_venta),
    id_cliente INTEGER NOT NULL REFERENCES clientes(id_cliente),
    fecha_apertura TEXT NOT NULL, fecha_vencimiento TEXT NOT NULL,
    monto_credito_original INTEGER NOT NULL, estado TEXT NOT NULL, valor_devuelto INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS devoluciones (
    id_devolucion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venta INTEGER NOT NULL REFERENCES ventas(id_venta),
    fecha TEXT NOT NULL, motivo TEXT NOT NULL, valor INTEGER NOT NULL,
    descontado_de_la_deuda INTEGER NOT NULL, efectivo_devuelto INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS detalles_devolucion (
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_devolucion INTEGER NOT NULL REFERENCES devoluciones(id_devolucion),
    id_producto INTEGER NOT NULL REFERENCES productos(id_producto),
    cantidad INTEGER NOT NULL, precio_unitario INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS idx_devoluciones_por_venta ON devoluciones(id_venta);
CREATE TABLE IF NOT EXISTS abonos (
    id_abono INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cuenta INTEGER NOT NULL REFERENCES cuentas_por_cobrar(id_cuenta),
    valor INTEGER NOT NULL, fecha TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_cuentas_por_cliente ON cuentas_por_cobrar(id_cliente);
CREATE INDEX IF NOT EXISTS idx_abonos_por_cuenta ON abonos(id_cuenta);
CREATE TABLE IF NOT EXISTS lotes (
    id_lote INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producto INTEGER NOT NULL REFERENCES productos(id_producto),
    numero TEXT NOT NULL DEFAULT '', fecha_vencimiento TEXT NOT NULL,
    cantidad INTEGER NOT NULL, activo INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL, usuario TEXT NOT NULL UNIQUE, rol TEXT NOT NULL,
    clave_hash TEXT NOT NULL, sal TEXT NOT NULL, activo INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS turnos_caja (
    id_turno INTEGER PRIMARY KEY AUTOINCREMENT,
    base INTEGER NOT NULL, abierto_en TEXT NOT NULL, id_usuario_abre INTEGER REFERENCES usuarios(id_usuario),
    cerrado_en TEXT, id_usuario_cierra INTEGER REFERENCES usuarios(id_usuario),
    efectivo_esperado INTEGER, efectivo_contado INTEGER);
CREATE TABLE IF NOT EXISTS configuracion (
    clave TEXT PRIMARY KEY, valor TEXT NOT NULL);
"""

# Columnas que la venta de contado (UC-02) agregó a ventas. Una base creada antes no las tiene: se agregan
# sin perder datos. Las ventas viejas eran todas a crédito, por eso tipo toma 'CREDITO' por defecto.
COLUMNAS_NUEVAS_DE_VENTAS = (
    ("tipo", "TEXT NOT NULL DEFAULT 'CREDITO'"),
    ("forma_pago", "TEXT"),
    ("valor_recibido", "INTEGER"),
    ("valor_transferencia", "INTEGER"),       # respuesta 1.2: pago por transferencia o mixto
)
# Respuesta 3.1 del propietario: teléfono y dirección (opcionales). Los clientes viejos quedan con texto vacío.
COLUMNAS_NUEVAS_DE_CLIENTES = (
    ("telefono", "TEXT NOT NULL DEFAULT ''"),
    ("direccion", "TEXT NOT NULL DEFAULT ''"),
)
# Respuesta 1.4: código de barras opcional. NULL cuando no hay, así el índice único deja varios productos sin código.
COLUMNAS_NUEVAS_DE_PRODUCTOS = (
    ("codigo", "TEXT"),
    ("stock_minimo", "INTEGER NOT NULL DEFAULT 0"),
    ("dias_aviso", "INTEGER NOT NULL DEFAULT 0"),     # RF-13: días de aviso de vencimiento, uno por producto
)
# Respuesta 1.5: lo que se descontó de la deuda por devoluciones (0 en las cuentas viejas).
COLUMNAS_NUEVAS_DE_CUENTAS = (("valor_devuelto", "INTEGER NOT NULL DEFAULT 0"),)
# Fase 1 (reportes): precio de compra al vender. NULL en las líneas viejas: el reporte usa el precio de compra actual.
COLUMNAS_NUEVAS_DE_DETALLES = (("costo_unitario", "INTEGER"),)
# Fase 3 (salida manual): motivo, quién la registró, quién la autorizó y el precio de compra de ese momento.
# Los movimientos viejos quedan con motivo vacío y lo demás en NULL.
COLUMNAS_NUEVAS_DE_MOVIMIENTOS = (
    ("motivo", "TEXT NOT NULL DEFAULT ''"),
    ("id_usuario", "INTEGER"),
    ("id_autorizo", "INTEGER"),
    ("costo_unitario", "INTEGER"),
)
INDICE_DEL_CODIGO = "CREATE UNIQUE INDEX IF NOT EXISTS idx_productos_codigo ON productos(codigo)"


COLUMNAS_NUEVAS = (
    ("ventas", COLUMNAS_NUEVAS_DE_VENTAS),
    ("clientes", COLUMNAS_NUEVAS_DE_CLIENTES),
    ("productos", COLUMNAS_NUEVAS_DE_PRODUCTOS),
    ("cuentas_por_cobrar", COLUMNAS_NUEVAS_DE_CUENTAS),
    ("detalles_venta", COLUMNAS_NUEVAS_DE_DETALLES),
    ("movimientos_inventario", COLUMNAS_NUEVAS_DE_MOVIMIENTOS),
)


def preparar_esquema(conexion):
    """Crea lo que falte y migra una base vieja sin perder datos. Se usa al abrir y después de restaurar (fase 5),
    porque un respaldo viejo puede no tener las tablas o columnas nuevas."""
    conexion.executescript(ESQUEMA_SQL)
    for tabla, columnas in COLUMNAS_NUEVAS:
        _agregar_columnas(conexion, tabla, columnas)
    with conexion:
        conexion.execute(INDICE_DEL_CODIGO)                     # después de la migración: la columna ya existe


def _agregar_columnas(conexion, tabla, columnas):
    """Migración: agrega a una base vieja las columnas que le falten, sin perder datos.
    tabla y columnas son constantes de este archivo (nunca texto del usuario)."""
    existentes = {fila[1] for fila in conexion.execute(f"PRAGMA table_info({tabla})")}
    with conexion:
        for nombre, definicion in columnas:
            if nombre not in existentes:
                conexion.execute(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion}")


class BaseDeDatos:
    def __init__(self, ruta=":memory:"):
        self.conexion = sqlite3.connect(ruta)
        self.conexion.row_factory = sqlite3.Row
        self.conexion.execute("PRAGMA foreign_keys = ON")
        preparar_esquema(self.conexion)

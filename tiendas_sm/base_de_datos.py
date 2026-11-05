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
    limite_credito INTEGER NOT NULL, plazo_credito_dias INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS ventas (
    id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER REFERENCES clientes(id_cliente),
    fecha TEXT NOT NULL, estado TEXT NOT NULL, total INTEGER NOT NULL,
    tipo TEXT NOT NULL, forma_pago TEXT, valor_recibido INTEGER);
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
    monto_credito_original INTEGER NOT NULL, estado TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS abonos (
    id_abono INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cuenta INTEGER NOT NULL REFERENCES cuentas_por_cobrar(id_cuenta),
    valor INTEGER NOT NULL, fecha TEXT NOT NULL);
"""

# Columnas que la venta de contado (UC-02) agregó a ventas. Una base creada antes no las tiene: se agregan
# sin perder datos. Las ventas viejas eran todas a crédito, por eso tipo toma 'CREDITO' por defecto.
COLUMNAS_NUEVAS_DE_VENTAS = (
    ("tipo", "TEXT NOT NULL DEFAULT 'CREDITO'"),
    ("forma_pago", "TEXT"),
    ("valor_recibido", "INTEGER"),
)


class BaseDeDatos:
    def __init__(self, ruta=":memory:"):
        self.conexion = sqlite3.connect(ruta)
        self.conexion.row_factory = sqlite3.Row
        self.conexion.execute("PRAGMA foreign_keys = ON")
        self.conexion.executescript(ESQUEMA_SQL)
        self._migrar_ventas()

    def _migrar_ventas(self):
        existentes = {fila["name"] for fila in self.conexion.execute("PRAGMA table_info(ventas)")}
        with self.conexion:
            for nombre, definicion in COLUMNAS_NUEVAS_DE_VENTAS:
                if nombre not in existentes:
                    self.conexion.execute(f"ALTER TABLE ventas ADD COLUMN {nombre} {definicion}")

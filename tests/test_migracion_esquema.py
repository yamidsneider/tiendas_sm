"""Migración del esquema de ventas (tarea 7, DIF-06).

La venta de contado agregó a la tabla ventas las columnas tipo, forma_pago y valor_recibido. Una base
creada antes (con el esquema viejo) debe poder abrirse sin perder datos: se agregan las columnas que
falten con ALTER TABLE. Las ventas viejas eran todas a crédito (antes no existía la de contado).
Se usa una base temporal que se borra al terminar. Datos ficticios.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.base_de_datos import BaseDeDatos

ESQUEMA_VIEJO_DE_VENTAS = """
CREATE TABLE ventas (
    id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER REFERENCES clientes(id_cliente),
    fecha TEXT NOT NULL, estado TEXT NOT NULL, total INTEGER NOT NULL);
INSERT INTO ventas (id_cliente, fecha, estado, total) VALUES (NULL, '2026-10-01T10:00:00', 'CONFIRMADA', 8000);
"""


class PruebasDeMigracion(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.ruta = str(Path(self.carpeta.name) / "vieja.db")
        conexion = sqlite3.connect(self.ruta)
        conexion.executescript(ESQUEMA_VIEJO_DE_VENTAS)
        conexion.close()

    def tearDown(self):
        self.carpeta.cleanup()

    def columnas_de_ventas(self, conexion):
        return [fila[1] for fila in conexion.execute("PRAGMA table_info(ventas)")]

    def test_agrega_las_columnas_que_faltan_sin_perder_la_venta_vieja(self):
        base = BaseDeDatos(self.ruta)
        self.assertIn("tipo", self.columnas_de_ventas(base.conexion))
        self.assertIn("forma_pago", self.columnas_de_ventas(base.conexion))
        self.assertIn("valor_recibido", self.columnas_de_ventas(base.conexion))
        vieja = base.conexion.execute("SELECT total, tipo, forma_pago, valor_recibido FROM ventas").fetchone()
        self.assertEqual(tuple(vieja), (8000, "CREDITO", None, None))
        base.conexion.close()

    def test_abrir_dos_veces_no_falla_ni_duplica_columnas(self):
        BaseDeDatos(self.ruta).conexion.close()
        base = BaseDeDatos(self.ruta)
        columnas = self.columnas_de_ventas(base.conexion)
        self.assertEqual(columnas.count("tipo"), 1)
        base.conexion.close()

    def test_despues_de_migrar_se_puede_vender_de_contado(self):
        app = Aplicacion(self.ruta)
        producto = app.productos.registrar_producto("Producto A", 1500, 2500, 5)
        venta = app.ventas.registrar_venta_de_contado([(producto.id_producto, 1)], 3000)
        self.assertEqual(venta.calcular_cambio(), 500)
        self.assertEqual(app.numero_de_ventas(), 2)
        app.conexion.close()


if __name__ == "__main__":
    unittest.main()

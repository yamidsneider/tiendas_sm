"""Escenarios de calidad de la FPI-18 (Guía 2) como pruebas automáticas (tarea 6, ADR-02).

E-02  Tolerancia a fallos: si el proceso muere a mitad de una venta, no queda nada a medias.
E-03  Desempeño: con 1.000 productos, listar() < 2 s y una venta de 5 líneas < 1 s (RNF-02).
E-05  Trazabilidad: entradas − salidas = cantidad actual, y toda venta tiene su SALIDA_VENTA (TD-01).

Solo biblioteca estándar. Las bases de E-02 se crean en una carpeta temporal que se borra al terminar.
Datos ficticios.
"""
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from tiendas_sm.aplicacion import Aplicacion

RAIZ_DEL_PROYECTO = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------------------------- E-02
INTENTOS_CON_FALLA = 20
CODIGO_DE_SALIDA_SIMULADO = 3        # distinto de 1, que es el código de una excepción sin capturar
EXISTENCIA_INICIAL = 10
# Proceso hijo: registra una venta a crédito y muere con os._exit justo después de insertar la cuenta,
# dentro de la transacción y antes del commit (como si se fuera la luz o se cerrara la aplicación a la fuerza).
SCRIPT_QUE_MUERE_A_MITAD = """
import os, sys
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.repositorios import RepositorioDeVentasSqlite

insertar_original = RepositorioDeVentasSqlite._insertar_cuenta
def insertar_y_morir(self, venta, cuenta):
    insertar_original(self, venta, cuenta)
    os._exit({codigo})
RepositorioDeVentasSqlite._insertar_cuenta = insertar_y_morir

app = Aplicacion(sys.argv[1])
app.ventas.registrar_venta_a_credito(int(sys.argv[2]), [(int(sys.argv[3]), 2)])
""".format(codigo=CODIGO_DE_SALIDA_SIMULADO)

# ---------------------------------------------------------------------------------------------- E-03
NUMERO_DE_PRODUCTOS = 1000
LIMITE_LISTAR_SEGUNDOS = 2.0          # RNF-02 (valor propuesto en la FPI-05/FPI-18)
LIMITE_VENTA_SEGUNDOS = 1.0
LINEAS_DE_LA_VENTA = 5


class PruebaE02ToleranciaAFallos(unittest.TestCase):
    def test_e02_si_el_proceso_muere_a_mitad_de_la_venta_no_queda_nada_a_medias(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as carpeta:
            ruta = str(Path(carpeta) / "e02.db")
            app = Aplicacion(ruta)
            producto = app.productos.registrar_producto("Producto A", 1500, 2500, EXISTENCIA_INICIAL)
            cliente = app.clientes.registrar_cliente("Cliente de prueba", True, 100000)
            app.conexion.close()

            for _ in range(INTENTOS_CON_FALLA):
                proceso = subprocess.run(
                    [sys.executable, "-c", SCRIPT_QUE_MUERE_A_MITAD, ruta, str(cliente.id_cliente),
                     str(producto.id_producto)], cwd=RAIZ_DEL_PROYECTO, capture_output=True, text=True, timeout=60)
                self.assertEqual(proceso.returncode, CODIGO_DE_SALIDA_SIMULADO, proceso.stderr)

            conexion = sqlite3.connect(ruta)
            try:
                contar = lambda tabla: conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
                self.assertEqual((contar("ventas"), contar("detalles_venta"), contar("cuentas_por_cobrar")), (0, 0, 0))
                existencia = conexion.execute("SELECT cantidad_actual FROM existencias WHERE id_producto=?",
                                              (producto.id_producto,)).fetchone()[0]
                self.assertEqual(existencia, EXISTENCIA_INICIAL)
                self.assertEqual(conexion.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            finally:
                conexion.close()


class PruebaE03Desempeno(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.productos = [self.app.productos.registrar_producto(f"Producto de prueba {numero:04d}", 1000, 1500, 50)
                          for numero in range(NUMERO_DE_PRODUCTOS)]

    def test_e03_listar_mil_productos_tarda_menos_de_dos_segundos(self):
        inicio = time.perf_counter()
        listados = self.app.productos.listar()
        segundos = time.perf_counter() - inicio
        self.assertEqual(len(listados), NUMERO_DE_PRODUCTOS)
        self.assertLess(segundos, LIMITE_LISTAR_SEGUNDOS, f"listar() tardó {segundos:.3f} s")

    def test_e03_una_venta_de_cinco_lineas_tarda_menos_de_un_segundo(self):
        lineas = [(producto.id_producto, 1) for producto in self.productos[:LINEAS_DE_LA_VENTA]]
        inicio = time.perf_counter()
        venta = self.app.ventas.registrar_venta_de_contado(lineas, 100000)
        segundos = time.perf_counter() - inicio
        self.assertEqual(len(venta.detalles), LINEAS_DE_LA_VENTA)
        self.assertLess(segundos, LIMITE_VENTA_SEGUNDOS, f"la venta tardó {segundos:.3f} s")


class PruebaE05Trazabilidad(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.a = self.app.productos.registrar_producto("Producto A", 1500, 2500, 10)
        self.b = self.app.productos.registrar_producto("Producto B", 2000, 3000, 5)
        self.c = self.app.productos.registrar_producto("Producto C", 500, 800)       # sin entrada inicial
        cliente = self.app.clientes.registrar_cliente("Cliente de prueba", True, 100000)
        self.app.productos.registrar_entrada(self.a.id_producto, 7)
        self.app.productos.registrar_entrada(self.c.id_producto, 3)
        self.app.ventas.registrar_venta_a_credito(cliente.id_cliente, [(self.a.id_producto, 4), (self.b.id_producto, 2),
                                                                       (self.a.id_producto, 1)])
        self.app.ventas.registrar_venta_de_contado([(self.b.id_producto, 3), (self.c.id_producto, 3)], 20000)
        self.app.ventas.registrar_venta_de_contado([(self.a.id_producto, 2)], 5000)

    def consulta(self, sql, parametros=()):
        return self.app.conexion.execute(sql, parametros).fetchall()

    def test_e05_entradas_menos_salidas_es_la_cantidad_actual_de_cada_producto(self):
        for producto in (self.a, self.b, self.c):
            with self.subTest(producto=producto.nombre):
                (entradas, salidas), = self.consulta(
                    "SELECT COALESCE(SUM(CASE WHEN tipo='ENTRADA' THEN cantidad END), 0), "
                    "COALESCE(SUM(CASE WHEN tipo='SALIDA_VENTA' THEN cantidad END), 0) "
                    "FROM movimientos_inventario WHERE id_producto=?", (producto.id_producto,))
                self.assertEqual(entradas - salidas, self.app.cantidad_en_inventario(producto.id_producto))

    def test_e05_toda_unidad_vendida_tiene_su_salida_venta(self):
        """Por producto: lo vendido en todas las ventas (detalles) = lo registrado como SALIDA_VENTA.

        Se compara por producto y no venta por venta porque movimientos_inventario no guarda el número de la
        venta y, en Windows, dos ventas seguidas pueden quedar con la misma fecha y hora (hallazgo de esta prueba).
        """
        vendido = self.consulta("SELECT id_producto, SUM(cantidad) FROM detalles_venta GROUP BY id_producto "
                                "ORDER BY id_producto")
        salidas = self.consulta("SELECT id_producto, SUM(cantidad) FROM movimientos_inventario "
                                "WHERE tipo='SALIDA_VENTA' GROUP BY id_producto ORDER BY id_producto")
        self.assertEqual([tuple(fila) for fila in salidas], [tuple(fila) for fila in vendido])

    def test_e05_cada_venta_tiene_al_menos_un_movimiento_con_su_fecha(self):
        ventas_sin_movimiento = self.consulta(
            "SELECT id_venta FROM ventas WHERE NOT EXISTS (SELECT 1 FROM movimientos_inventario m "
            "WHERE m.tipo='SALIDA_VENTA' AND m.fecha = ventas.fecha)")
        self.assertEqual(len(self.consulta("SELECT id_venta FROM ventas")), 3)
        self.assertEqual(ventas_sin_movimiento, [])

if __name__ == "__main__":
    unittest.main()

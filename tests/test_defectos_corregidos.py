"""Pruebas de REGRESIÓN de los defectos gestionados en la FPI-15.

Cada defecto tiene sus pruebas: primero se escribieron para REPRODUCIR el error (fallaban) y
después de la corrección pasan. Quedan en la suite para que el defecto no vuelva a aparecer.

BUG-01  Ids que no existen provocan AttributeError en lugar de un mensaje claro   (antes DT-06)
BUG-02  El vencimiento del crédito ignora el plazo del cliente (siempre 30 días)  (antes DT-02)
DT-09   El cliente se guarda con nombre vacío, límite negativo o plazo menor a 1 día (UC-05 del DDS)
TD-01   Las ventas descuentan existencias sin registrar su movimiento de inventario (RF-04, RN-07, RNF-10, E-05)
"""
import sqlite3
import unittest
from datetime import datetime
from unittest.mock import Mock

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import Cliente
from tiendas_sm.servicios import ControlCredito, ServicioDeProductos


class PruebasBug01IdsInexistentes(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()

    def test_entrada_a_un_producto_inexistente_da_un_mensaje_claro(self):
        with self.assertRaises(ValueError) as contexto:
            self.app.productos.registrar_entrada(999, 5)
        self.assertIn("producto no existe", str(contexto.exception).lower())

    def test_actualizar_el_precio_de_un_producto_inexistente_da_un_mensaje_claro(self):
        with self.assertRaises(ValueError) as contexto:
            self.app.productos.actualizar_precio(999, 100)
        self.assertIn("producto no existe", str(contexto.exception).lower())

    def test_abonar_a_una_cuenta_inexistente_da_un_mensaje_claro(self):
        with self.assertRaises(ValueError) as contexto:
            self.app.credito.registrar_abono(999, 100)
        self.assertIn("cuenta", str(contexto.exception).lower())

    def test_el_error_no_deja_movimientos_a_medias(self):
        with self.assertRaises(ValueError):
            self.app.productos.registrar_entrada(999, 5)
        movimientos = self.app.conexion.execute("SELECT COUNT(*) FROM movimientos_inventario").fetchone()[0]
        self.assertEqual(movimientos, 0)

    def test_unitaria_sin_base_de_datos_existencia_inexistente(self):
        repo = Mock()
        repo.obtener_existencia.return_value = None
        with self.assertRaises(ValueError):
            ServicioDeProductos(repo).registrar_entrada(1, 5)
        repo.guardar_existencia.assert_not_called()

    def test_unitaria_sin_base_de_datos_cuenta_inexistente(self):
        repo = Mock()
        repo.obtener_cuenta.return_value = None
        with self.assertRaises(ValueError):
            ControlCredito(repo).registrar_abono(1, 100)
        repo.guardar_abono.assert_not_called()


class PruebasBug02PlazoDelCredito(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.producto = self.app.productos.registrar_producto("Producto", 1000, 2000, 10)

    def dias_de_plazo(self, plazo_del_cliente):
        if plazo_del_cliente is None:
            cliente = self.app.clientes.registrar_cliente("Cliente de prueba", True, 100000)
        else:
            cliente = self.app.clientes.registrar_cliente("Cliente de prueba", True, 100000,
                                                           plazo_credito_dias=plazo_del_cliente)
        self.app.ventas.registrar_venta_a_credito(cliente.id_cliente, [(self.producto.id_producto, 1)])
        cuenta = self.app.credito.cuentas_del_cliente(cliente.id_cliente)[0]
        apertura = datetime.fromisoformat(str(cuenta.fecha_apertura))
        vencimiento = datetime.fromisoformat(str(cuenta.fecha_vencimiento))
        return (vencimiento - apertura).days

    def test_cliente_con_plazo_de_15_dias(self):
        self.assertEqual(self.dias_de_plazo(15), 15)

    def test_cliente_con_plazo_de_45_dias(self):
        self.assertEqual(self.dias_de_plazo(45), 45)

    def test_cliente_sin_plazo_propio_usa_el_plazo_por_defecto_de_30_dias(self):
        self.assertEqual(self.dias_de_plazo(None), 30)


class PruebasDt09ClienteSinValidar(unittest.TestCase):
    """UC-05 del DDS: nombre obligatorio, límite no negativo y plazo de al menos un día."""

    def setUp(self):
        self.app = Aplicacion()

    def numero_de_clientes(self):
        return self.app.conexion.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]

    def rechaza_sin_guardar(self, mensaje, nombres="Cliente de prueba", limite=50000, plazo=30):
        with self.assertRaises(ValueError) as error:
            self.app.clientes.registrar_cliente(nombres, True, limite, plazo_credito_dias=plazo)
        self.assertEqual(str(error.exception), mensaje)
        self.assertEqual(self.numero_de_clientes(), 0)

    def test_rechaza_nombre_vacio_o_solo_espacios(self):
        for nombre in ("", "   ", None):
            self.rechaza_sin_guardar("El nombre es obligatorio", nombres=nombre)

    def test_rechaza_limite_negativo(self):
        self.rechaza_sin_guardar("El límite de crédito no puede ser negativo", limite=-1)

    def test_rechaza_plazo_menor_a_un_dia(self):
        for plazo in (0, -5):
            self.rechaza_sin_guardar("El plazo de crédito debe ser de al menos 1 día", plazo=plazo)

    def test_valores_limite_validos_limite_cero_y_plazo_de_un_dia(self):
        cliente = self.app.clientes.registrar_cliente("Sin crédito", False, 0, plazo_credito_dias=1)
        self.assertIsNotNone(cliente.id_cliente)
        self.assertEqual(self.numero_de_clientes(), 1)

    def test_unitaria_sin_base_de_datos(self):
        with self.assertRaises(ValueError):
            Cliente(None, " ", True, 50000, 30)


class PruebasTd01MovimientoDeVenta(unittest.TestCase):
    """Cada venta (a crédito o de contado) deja un movimiento SALIDA_VENTA por producto, en la misma transacción."""

    def setUp(self):
        self.app = Aplicacion()
        self.a = self.app.productos.registrar_producto("Producto A", 1500, 2500, 10)
        self.b = self.app.productos.registrar_producto("Producto B", 2000, 3000, 5)
        self.cliente = self.app.clientes.registrar_cliente("Cliente de prueba", True, 100000)

    def salidas(self):
        return self.app.conexion.execute(
            "SELECT id_producto, cantidad, fecha FROM movimientos_inventario "
            "WHERE tipo='SALIDA_VENTA' ORDER BY id_producto").fetchall()

    def simular_falla(self, tabla):
        self.app.conexion.execute(
            f"CREATE TRIGGER falla_simulada BEFORE INSERT ON {tabla} "
            "BEGIN SELECT RAISE(ABORT, 'falla simulada'); END")

    def test_venta_a_credito_registra_una_salida_por_producto_sumando_lineas_repetidas(self):
        venta = self.app.ventas.registrar_venta_a_credito(
            self.cliente.id_cliente, [(self.a.id_producto, 2), (self.b.id_producto, 1), (self.a.id_producto, 3)])
        fecha = venta.fecha.isoformat()
        self.assertEqual([tuple(fila) for fila in self.salidas()],
                         [(self.a.id_producto, 5, fecha), (self.b.id_producto, 1, fecha)])

    def test_venta_de_contado_tambien_registra_su_salida(self):
        venta = self.app.ventas.registrar_venta_de_contado([(self.b.id_producto, 2)], 6000)
        self.assertEqual([tuple(fila) for fila in self.salidas()],
                         [(self.b.id_producto, 2, venta.fecha.isoformat())])

    def test_si_falla_la_venta_a_credito_no_queda_ningun_movimiento(self):
        self.simular_falla("cuentas_por_cobrar")
        with self.assertRaises(sqlite3.Error):
            self.app.ventas.registrar_venta_a_credito(self.cliente.id_cliente, [(self.a.id_producto, 2)])
        self.assertEqual(self.salidas(), [])

    def test_si_falla_la_venta_de_contado_no_queda_ningun_movimiento(self):
        self.simular_falla("detalles_venta")
        with self.assertRaises(sqlite3.Error):
            self.app.ventas.registrar_venta_de_contado([(self.a.id_producto, 2)], 5000)
        self.assertEqual(self.salidas(), [])

    def test_rnf04_si_falla_el_movimiento_se_revierte_toda_la_venta(self):
        self.app.conexion.execute(
            "CREATE TRIGGER falla_en_movimiento BEFORE INSERT ON movimientos_inventario "
            "WHEN NEW.tipo='SALIDA_VENTA' BEGIN SELECT RAISE(ABORT, 'falla simulada'); END")
        with self.assertRaises(sqlite3.Error):
            self.app.ventas.registrar_venta_a_credito(self.cliente.id_cliente, [(self.a.id_producto, 2)])
        self.assertEqual(self.app.numero_de_ventas(), 0)
        self.assertEqual(self.app.cantidad_en_inventario(self.a.id_producto), 10)
        cuentas = self.app.conexion.execute("SELECT COUNT(*) FROM cuentas_por_cobrar").fetchone()[0]
        self.assertEqual(cuentas, 0)

    def test_e05_entradas_menos_salidas_es_igual_a_la_cantidad_actual(self):
        self.app.productos.registrar_entrada(self.a.id_producto, 4)
        self.app.ventas.registrar_venta_a_credito(self.cliente.id_cliente, [(self.a.id_producto, 3)])
        self.app.ventas.registrar_venta_de_contado([(self.a.id_producto, 2), (self.b.id_producto, 5)], 20000)
        for producto in (self.a, self.b):
            with self.subTest(producto=producto.nombre):
                entradas, salidas = self.app.conexion.execute(
                    "SELECT COALESCE(SUM(CASE WHEN tipo='ENTRADA' THEN cantidad END), 0), "
                    "COALESCE(SUM(CASE WHEN tipo='SALIDA_VENTA' THEN cantidad END), 0) "
                    "FROM movimientos_inventario WHERE id_producto=?", (producto.id_producto,)).fetchone()
                self.assertEqual(entradas - salidas, self.app.cantidad_en_inventario(producto.id_producto))


if __name__ == "__main__":
    unittest.main(verbosity=2)

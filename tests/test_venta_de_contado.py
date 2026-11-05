"""Pruebas de la venta de contado (UC-02 del DDS / CU-02 del DAD, RF-05 y RF-06).

Se escribieron ANTES del código. Cubren el flujo principal y las excepciones del UC-02:
existencias suficientes, venta con productos, efectivo que alcanza, cambio y todo o nada
(RN-01, RN-02, RN-05, RN-06; CA-06, CA-07, CA-08). Solo la forma de pago en efectivo:
transferencia y pago mixto son la ampliación CR-02, sin aprobar. Datos ficticios.
"""
import sqlite3
import unittest
from unittest.mock import ANY, Mock, create_autospec

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import (EfectivoInsuficiente, Existencia, FormaDePago, Producto, StockInsuficiente,
                                TipoVenta, Venta)
from tiendas_sm.repositorios import RepositorioDeVentas
from tiendas_sm.servicios import ServicioDeVentas


class PruebasDeVentaDeContado(unittest.TestCase):
    """Flujo completo con SQLite real en memoria."""

    def setUp(self):
        self.app = Aplicacion()
        self.a = self.app.productos.registrar_producto("Producto A", 1500, 2500, 10)
        self.b = self.app.productos.registrar_producto("Producto B", 2000, 3000, 1)

    def vender(self, lineas, recibido):
        return self.app.ventas.registrar_venta_de_contado(lineas, recibido)

    def contar(self, tabla):
        return self.app.conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]

    def test_ca06_total_e_inventario_de_venta_con_dos_productos(self):
        venta = self.vender([(self.a.id_producto, 2), (self.b.id_producto, 1)], 10000)
        self.assertEqual(venta.total, 8000)
        self.assertEqual(self.app.cantidad_en_inventario(self.a.id_producto), 8)
        self.assertEqual(self.app.cantidad_en_inventario(self.b.id_producto), 0)

    def test_el_cambio_es_lo_recibido_menos_el_total(self):
        venta = self.vender([(self.a.id_producto, 2)], 10000)
        self.assertEqual(venta.calcular_cambio(), 5000)

    def test_valor_limite_recibir_exactamente_el_total_deja_cambio_cero(self):
        venta = self.vender([(self.a.id_producto, 2)], 5000)
        self.assertEqual(venta.calcular_cambio(), 0)

    def test_valor_limite_un_peso_menos_que_el_total_se_rechaza_sin_cambiar_nada(self):
        with self.assertRaises(EfectivoInsuficiente) as error:
            self.vender([(self.a.id_producto, 2)], 4999)
        self.assertEqual(str(error.exception), "El efectivo recibido (4999) no alcanza para el total, que es 5000")
        self.assertEqual(self.app.numero_de_ventas(), 0)
        self.assertEqual(self.app.cantidad_en_inventario(self.a.id_producto), 10)

    def test_ca07_stock_insuficiente_informa_cuantas_hay_y_no_cambia_nada(self):
        with self.assertRaises(StockInsuficiente) as error:
            self.vender([(self.b.id_producto, 3)], 20000)
        self.assertEqual(str(error.exception), "Solo hay 1 disponibles de Producto B")
        self.assertEqual(self.app.numero_de_ventas(), 0)
        self.assertEqual(self.app.cantidad_en_inventario(self.b.id_producto), 1)

    def test_ca08_venta_sin_productos_se_rechaza_y_no_guarda_nada(self):
        with self.assertRaises(ValueError):
            self.vender([], 1000)
        self.assertEqual(self.app.numero_de_ventas(), 0)

    def test_no_crea_cuenta_por_cobrar_ni_pide_cliente(self):
        venta = self.vender([(self.a.id_producto, 1)], 2500)
        self.assertIsNone(venta.id_cliente)
        self.assertEqual(self.contar("cuentas_por_cobrar"), 0)

    def test_guarda_tipo_forma_de_pago_y_valor_recibido(self):
        venta = self.vender([(self.a.id_producto, 1)], 3000)
        fila = self.app.conexion.execute(
            "SELECT tipo, forma_pago, valor_recibido, total, estado FROM ventas WHERE id_venta=?",
            (venta.id_venta,)).fetchone()
        self.assertEqual(tuple(fila), ("CONTADO", "EFECTIVO", 3000, 2500, "CONFIRMADA"))

    def test_rn05_guarda_el_precio_vigente_de_cada_linea(self):
        self.vender([(self.a.id_producto, 1)], 2500)
        self.app.productos.actualizar_precio(self.a.id_producto, 2700)
        precio_vendido = self.app.conexion.execute(
            "SELECT precio_unitario_venta FROM detalles_venta").fetchone()[0]
        self.assertEqual(precio_vendido, 2500)

    def test_rn06_si_falla_al_guardar_no_queda_nada_a_medias(self):
        self.app.conexion.execute(
            "CREATE TRIGGER falla_simulada BEFORE INSERT ON detalles_venta "
            "BEGIN SELECT RAISE(ABORT, 'falla simulada'); END")
        with self.assertRaises(sqlite3.Error):
            self.vender([(self.a.id_producto, 2)], 5000)
        self.assertEqual(self.app.numero_de_ventas(), 0)
        self.assertEqual(self.app.cantidad_en_inventario(self.a.id_producto), 10)

    def test_la_venta_a_credito_queda_guardada_como_credito(self):
        cliente = self.app.clientes.registrar_cliente("Cliente de prueba", True, 50000)
        venta = self.app.ventas.registrar_venta_a_credito(cliente.id_cliente, [(self.a.id_producto, 1)])
        fila = self.app.conexion.execute(
            "SELECT tipo, forma_pago, valor_recibido FROM ventas WHERE id_venta=?", (venta.id_venta,)).fetchone()
        self.assertEqual(tuple(fila), ("CREDITO", None, None))


class PruebasDelPagoEnEfectivo(unittest.TestCase):
    """Unitarias de la clase Venta, sin base de datos."""

    def venta_de(self, cantidad, precio):
        venta = Venta(tipo=TipoVenta.CONTADO)
        venta.agregar_detalle(Producto(1, "Producto A", 0, precio), cantidad)
        return venta

    def test_registra_la_forma_de_pago_y_lo_recibido(self):
        venta = self.venta_de(2, 2500)
        venta.registrar_pago_en_efectivo(6000)
        self.assertEqual(venta.forma_pago, FormaDePago.EFECTIVO)
        self.assertEqual(venta.valor_recibido, 6000)
        self.assertEqual(venta.calcular_cambio(), 1000)

    def test_rechaza_efectivo_negativo(self):
        with self.assertRaises(EfectivoInsuficiente):
            self.venta_de(1, 2500).registrar_pago_en_efectivo(-1)

    def test_una_venta_nueva_es_a_credito_por_defecto_para_no_cambiar_cu01(self):
        self.assertEqual(Venta(1).tipo, TipoVenta.CREDITO)


class PruebasDeVentaDeContadoConMock(unittest.TestCase):
    """El repositorio es un mock: verificamos que se guarde una sola vez y sin cuenta por cobrar."""

    def setUp(self):
        repo_productos = Mock()
        repo_productos.obtener.return_value = Producto(1, "Producto A", 1500, 2500)
        control_inventario = Mock()
        control_inventario.hay_disponible.return_value = True
        control_inventario.descontar.return_value = Existencia(1, 8)
        self.repo_ventas = create_autospec(RepositorioDeVentas, instance=True)
        self.servicio = ServicioDeVentas(repo_productos, Mock(), self.repo_ventas, control_inventario, Mock())

    def test_se_guarda_una_sola_vez_sin_cuenta(self):
        venta = self.servicio.registrar_venta_de_contado([(1, 2)], 5000)
        self.repo_ventas.guardar_transaccion.assert_called_once_with(venta, None, ANY)  # None: sin cuenta

    def test_si_el_efectivo_no_alcanza_no_se_descuenta_ni_se_guarda(self):
        with self.assertRaises(EfectivoInsuficiente):
            self.servicio.registrar_venta_de_contado([(1, 2)], 100)
        self.servicio.control_inventario.descontar.assert_not_called()
        self.repo_ventas.guardar_transaccion.assert_not_called()


if __name__ == "__main__":
    unittest.main()

"""Pruebas de REGRESIÓN de los defectos gestionados en la FPI-15.

Cada defecto tiene sus pruebas: primero se escribieron para REPRODUCIR el error (fallaban) y
después de la corrección pasan. Quedan en la suite para que el defecto no vuelva a aparecer.

BUG-01  Ids que no existen provocan AttributeError en lugar de un mensaje claro   (antes DT-06)
BUG-02  El vencimiento del crédito ignora el plazo del cliente (siempre 30 días)  (antes DT-02)
"""
import unittest
from datetime import datetime
from unittest.mock import Mock

from tiendas_sm.aplicacion import Aplicacion
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


if __name__ == "__main__":
    unittest.main(verbosity=2)

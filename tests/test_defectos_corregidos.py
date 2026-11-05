"""Pruebas de REGRESIÓN de los defectos gestionados en la FPI-15.

Cada defecto tiene sus pruebas: primero se escribieron para REPRODUCIR el error (fallaban) y
después de la corrección pasan. Quedan en la suite para que el defecto no vuelva a aparecer.

BUG-01  Ids que no existen provocan AttributeError en lugar de un mensaje claro   (antes DT-06)
BUG-02  El vencimiento del crédito ignora el plazo del cliente (siempre 30 días)  (antes DT-02)
DT-09   El cliente se guarda con nombre vacío, límite negativo o plazo menor a 1 día (UC-05 del DDS)
"""
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


if __name__ == "__main__":
    unittest.main(verbosity=2)

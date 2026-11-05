"""Integración INCREMENTAL ASCENDENTE (Bottom-Up) de TIENDAS S.M (FPI-14).

Se combinan los módulos de abajo hacia arriba y cada nivel se prueba antes de pasar al siguiente.
Si falla el nivel N pero el N-1 pasó, el defecto está en la unión nueva. Así se evita el Big Bang.

Nivel 1  dominio (sin base de datos)                      -> tests/test_unitarias_dobles.py
Nivel 2  dominio + persistencia SQLite real              -> PruebasNivel2
Nivel 3  + controles de inventario y de crédito          -> PruebasNivel3
Nivel 4  + ServicioDeVentas (flujo completo CU-01)        -> tests/test_comportamiento.py y test_caja_negra.py
Nivel 5  + interfaz de escritorio (Tkinter)               -> pendiente (aún no existe)
"""
import unittest

from tiendas_sm.base_de_datos import BaseDeDatos
from tiendas_sm.dominio import Cliente, Producto
from tiendas_sm.repositorios import (RepositorioDeClientes, RepositorioDeProductos,
                                     RepositorioDeVentasSqlite)
from tiendas_sm.servicios import ControlCredito, ControlInventario


class PruebasNivel2(unittest.TestCase):
    """Dominio + repositorios con SQLite real (todavía sin controles ni servicios)."""

    def setUp(self):
        self.conexion = BaseDeDatos().conexion
        self.repo_productos = RepositorioDeProductos(self.conexion)
        self.repo_clientes = RepositorioDeClientes(self.conexion)

    def test_un_producto_guardado_se_recupera_igual(self):
        producto = Producto(None, "Arroz", 2000, 2500)
        self.repo_productos.guardar(producto)
        recuperado = self.repo_productos.obtener(producto.id_producto)
        self.assertEqual((recuperado.nombre, recuperado.precio_venta), ("Arroz", 2500))

    def test_un_producto_nuevo_nace_con_existencia_cero(self):
        producto = Producto(None, "Arroz", 2000, 2500)
        self.repo_productos.guardar(producto)
        self.assertEqual(self.repo_productos.obtener_existencia(producto.id_producto).cantidad_actual, 0)

    def test_un_cliente_guardado_se_recupera_con_su_limite(self):
        cliente = Cliente(None, "Cliente de prueba", True, 50000, 30)
        self.repo_clientes.guardar(cliente)
        recuperado = self.repo_clientes.obtener(cliente.id_cliente)
        self.assertTrue(recuperado.credito_habilitado)
        self.assertEqual(recuperado.limite_credito, 50000)

    def test_obtener_un_id_inexistente_devuelve_none(self):
        self.assertIsNone(self.repo_productos.obtener(999))
        self.assertIsNone(self.repo_clientes.obtener(999))

    def test_listar_clientes_sin_registros_devuelve_lista_vacia(self):
        self.assertEqual(self.repo_clientes.listar(), [])

    def test_listar_clientes_los_devuelve_por_nombre_con_limite_y_plazo(self):
        self.repo_clientes.guardar(Cliente(None, "Zoila de prueba", False, 0, 30))
        self.repo_clientes.guardar(Cliente(None, "Andrés de prueba", True, 80000, 15))
        clientes = self.repo_clientes.listar()
        self.assertEqual([c.nombres for c in clientes], ["Andrés de prueba", "Zoila de prueba"])
        self.assertEqual((clientes[0].credito_habilitado, clientes[0].limite_credito, clientes[0].plazo_credito_dias),
                         (True, 80000, 15))
        self.assertIsNotNone(clientes[0].id_cliente)


class PruebasNivel3(unittest.TestCase):
    """Controles reales + repositorios reales (todavía sin ServicioDeVentas)."""

    def setUp(self):
        conexion = BaseDeDatos().conexion
        self.repo_productos = RepositorioDeProductos(conexion)
        self.repo_clientes = RepositorioDeClientes(conexion)
        self.repo_ventas = RepositorioDeVentasSqlite(conexion)
        self.control_inventario = ControlInventario(self.repo_productos)
        self.control_credito = ControlCredito(self.repo_ventas)

    def test_control_de_inventario_lee_las_existencias_guardadas(self):
        producto = Producto(None, "Arroz", 2000, 2500)
        self.repo_productos.guardar(producto)
        existencia = self.repo_productos.obtener_existencia(producto.id_producto)
        existencia.aumentar(5)
        self.repo_productos.guardar_existencia(existencia, "ENTRADA", 5)
        self.assertTrue(self.control_inventario.hay_disponible(producto, 5))
        self.assertFalse(self.control_inventario.hay_disponible(producto, 6))
        self.assertEqual(self.control_inventario.cantidad_disponible(producto), 5)

    def test_cliente_sin_deudas_tiene_saldo_cero(self):
        cliente = Cliente(None, "Cliente de prueba", True, 50000, 30)
        self.repo_clientes.guardar(cliente)
        self.assertEqual(self.control_credito.saldo_pendiente(cliente), 0)
        self.assertTrue(self.control_credito.puede_comprar_a_credito(cliente, 50000))


if __name__ == "__main__":
    unittest.main(verbosity=2)

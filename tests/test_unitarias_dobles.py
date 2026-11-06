"""Pruebas UNITARIAS de TIENDAS S.M (FPI-14): cada clase se prueba aislada de la base de datos.

Tipos de prueba que se usan (y por qué):
- Sin doble: lógica pura del dominio (no depende de nada externo).
- STUB: objeto con respuestas fijas que solo alimenta a la clase probada. No se verifica cómo se usa.
- MOCK: se usa SOLO cuando la interacción ES el comportamiento que se quiere comprobar
  (por ejemplo, "si el stock no alcanza, NO se guarda nada").
Las pruebas no dependen de SQLite: si el repositorio cambia, estas pruebas no se rompen.
"""
import unittest
from unittest.mock import create_autospec, Mock

from tiendas_sm.dominio import (Cliente, CreditoNoPermitido, CuentaPorCobrar, Existencia, EstadoCuenta,
                                Producto, StockInsuficiente, Venta)
from tiendas_sm.repositorios import RepositorioDeVentas
from tiendas_sm.servicios import ControlCredito, ControlInventario, ServicioDeProductos, ServicioDeVentas


# ---------------------------------------------------------------- STUBS (respuestas fijas)
class RepositorioDeVentasStub:
    """Stub: devuelve siempre las cuentas que se le entregaron al crearlo."""
    def __init__(self, cuentas=()):
        self._cuentas = list(cuentas)

    def cuentas_del_cliente(self, id_cliente):
        return self._cuentas

    def saldo_pendiente_del_cliente(self, id_cliente):      # TD-13: el contrato del repositorio ahora incluye el saldo
        return sum(cuenta.calcular_saldo() for cuenta in self._cuentas)


class RepositorioDeProductosStub:
    """Stub: devuelve siempre la misma existencia."""
    def __init__(self, existencia):
        self._existencia = existencia

    def obtener_existencia(self, id_producto):
        return self._existencia


def cuenta_con_saldo(saldo):
    return CuentaPorCobrar(1, 1, 1, saldo, "2026-01-01", "2026-01-31")


def cliente(credito_habilitado=True, limite=50000):
    return Cliente(1, "Cliente de prueba", credito_habilitado, limite, 30)


# ---------------------------------------------------------------- sin dobles: dominio puro

class PruebasDeProducto(unittest.TestCase):
    """Producto.__init__ tiene V(G) = 5: estos 5 casos recorren sus 5 caminos independientes."""

    def test_camino1_producto_valido(self):
        producto = Producto(None, "Arroz", 2000, 2500)
        self.assertEqual((producto.nombre, producto.precio_venta), ("Arroz", 2500))

    def test_camino2_nombre_nulo(self):
        with self.assertRaises(ValueError):
            Producto(None, None, 2000, 2500)

    def test_camino3_nombre_solo_espacios(self):
        with self.assertRaises(ValueError):
            Producto(None, "   ", 2000, 2500)

    def test_camino4_precio_de_compra_negativo(self):
        with self.assertRaises(ValueError):
            Producto(None, "Arroz", -1, 2500)

    def test_camino5_precio_de_venta_negativo(self):
        with self.assertRaises(ValueError):
            Producto(None, "Arroz", 2000, -1)

    def test_valor_limite_precio_cero_es_valido(self):
        self.assertEqual(Producto(None, "Muestra gratis", 0, 0).precio_venta, 0)

class PruebasDeExistencia(unittest.TestCase):
    def test_descontar_resta_la_cantidad(self):
        existencia = Existencia(1, 10)
        existencia.descontar(3)
        self.assertEqual(existencia.cantidad_actual, 7)

    def test_descontar_rechaza_cantidad_mayor_a_la_que_hay(self):
        existencia = Existencia(1, 4)
        with self.assertRaises(StockInsuficiente):
            existencia.descontar(5)
        self.assertEqual(existencia.cantidad_actual, 4)

    def test_descontar_exactamente_lo_que_hay_es_valido(self):
        existencia = Existencia(1, 4)
        existencia.descontar(4)
        self.assertEqual(existencia.cantidad_actual, 0)

    def test_descontar_rechaza_cero_y_negativos(self):
        existencia = Existencia(1, 4)
        for cantidad in (0, -1):
            with self.assertRaises(ValueError):
                existencia.descontar(cantidad)

    def test_cantidad_disponible_descuenta_lo_reservado(self):
        self.assertEqual(Existencia(1, 10, 3).cantidad_disponible(), 7)


class PruebasDeCliente(unittest.TestCase):
    def test_puede_endeudarse_dentro_del_limite(self):
        self.assertTrue(cliente().puede_endeudarse(30000, saldo_pendiente=20000))

    def test_el_limite_exacto_es_valido_y_un_peso_mas_no(self):
        self.assertTrue(cliente().puede_endeudarse(30000, saldo_pendiente=20000))   # 20.000 + 30.000 = 50.000
        self.assertFalse(cliente().puede_endeudarse(30001, saldo_pendiente=20000))  # 50.001 > 50.000

    def test_sin_credito_habilitado_nunca_puede(self):
        self.assertFalse(cliente(credito_habilitado=False).puede_endeudarse(1, saldo_pendiente=0))


class PruebasDeCuentaPorCobrar(unittest.TestCase):
    def test_un_abono_reduce_el_saldo(self):
        cuenta = cuenta_con_saldo(50000)
        cuenta.aplicar_pago(20000)
        self.assertEqual(cuenta.calcular_saldo(), 30000)
        self.assertEqual(cuenta.estado, EstadoCuenta.ABIERTA)

    def test_pagar_todo_la_deja_pagada(self):
        cuenta = cuenta_con_saldo(50000)
        cuenta.aplicar_pago(50000)
        self.assertEqual(cuenta.estado, EstadoCuenta.PAGADA)

    def test_rechaza_abono_mayor_al_saldo_y_no_lo_registra(self):
        cuenta = cuenta_con_saldo(50000)
        with self.assertRaises(ValueError):
            cuenta.aplicar_pago(50001)
        self.assertEqual(cuenta.abonos, [])


class PruebasDeVenta(unittest.TestCase):
    def test_el_total_es_la_suma_de_precio_por_cantidad(self):
        venta = Venta(1)
        venta.agregar_detalle(Producto(1, "A", 1500, 2500), 2)
        venta.agregar_detalle(Producto(2, "B", 2000, 3000), 1)
        self.assertEqual(venta.calcular_total(), 8000)

    def test_no_se_puede_confirmar_una_venta_sin_productos(self):
        with self.assertRaises(ValueError):
            Venta(1).confirmar()


# ---------------------------------------------------------------- con STUB: respuestas fijas
class PruebasDeControlCreditoConStub(unittest.TestCase):
    def test_el_saldo_pendiente_suma_las_cuentas_del_cliente(self):
        control = ControlCredito(RepositorioDeVentasStub([cuenta_con_saldo(12000), cuenta_con_saldo(8000)]))
        self.assertEqual(control.saldo_pendiente(cliente()), 20000)

    def test_la_deuda_previa_consume_el_limite(self):
        control = ControlCredito(RepositorioDeVentasStub([cuenta_con_saldo(20000)]))
        self.assertTrue(control.puede_comprar_a_credito(cliente(), 30000))
        self.assertFalse(control.puede_comprar_a_credito(cliente(), 30001))


class PruebasDeControlInventarioConStub(unittest.TestCase):
    def test_hay_disponible_considera_lo_reservado(self):
        control = ControlInventario(RepositorioDeProductosStub(Existencia(1, 5, 2)))  # disponible = 3
        producto = Producto(1, "A", 1000, 2000)
        self.assertTrue(control.hay_disponible(producto, 3))
        self.assertFalse(control.hay_disponible(producto, 4))


# ---------------------------------------------------------------- con MOCK: la interacción es el comportamiento
def armar_servicio_de_ventas(hay_stock=True, credito_permitido=True):
    """Servicio con TODAS sus dependencias reemplazadas. Los controles son stubs (respuestas fijas);
    solo el repositorio de ventas es un mock, porque queremos verificar si se guardó o no."""
    producto = Producto(1, "Producto A", 1500, 2500)
    repo_productos = Mock()
    repo_productos.obtener.return_value = producto
    repo_clientes = Mock()
    repo_clientes.obtener.return_value = cliente()
    repo_ventas = create_autospec(RepositorioDeVentas, instance=True)      # mock con la interfaz real
    control_inventario = Mock()
    control_inventario.hay_disponible.return_value = hay_stock
    control_inventario.cantidad_disponible.return_value = 1
    control_inventario.descontar.return_value = Existencia(1, 8)
    control_credito = Mock()
    control_credito.puede_comprar_a_credito.return_value = credito_permitido
    control_credito.crear_cuenta.return_value = cuenta_con_saldo(5000)
    servicio = ServicioDeVentas(repo_productos, repo_clientes, repo_ventas, control_inventario, control_credito)
    return servicio, repo_ventas


class PruebasDeServicioDeVentasConMock(unittest.TestCase):
    def test_venta_valida_se_guarda_una_sola_vez_con_el_total_correcto(self):
        servicio, repo_ventas = armar_servicio_de_ventas()
        venta = servicio.registrar_venta_a_credito(1, [(1, 2)])
        repo_ventas.guardar_transaccion.assert_called_once()
        venta_guardada = repo_ventas.guardar_transaccion.call_args.args[0]
        self.assertIs(venta_guardada, venta)
        self.assertEqual(venta_guardada.total, 5000)

    def test_si_no_alcanza_el_stock_no_se_guarda_nada(self):
        servicio, repo_ventas = armar_servicio_de_ventas(hay_stock=False)
        with self.assertRaises(StockInsuficiente):
            servicio.registrar_venta_a_credito(1, [(1, 2)])
        repo_ventas.guardar_transaccion.assert_not_called()

    def test_si_el_credito_no_esta_permitido_no_se_guarda_nada(self):
        servicio, repo_ventas = armar_servicio_de_ventas(credito_permitido=False)
        with self.assertRaises(CreditoNoPermitido):
            servicio.registrar_venta_a_credito(1, [(1, 2)])
        repo_ventas.guardar_transaccion.assert_not_called()

    def test_un_cliente_inexistente_no_guarda_nada(self):
        servicio, repo_ventas = armar_servicio_de_ventas()
        servicio.repo_clientes.obtener.return_value = None
        with self.assertRaises(ValueError):
            servicio.registrar_venta_a_credito(99, [(1, 1)])
        repo_ventas.guardar_transaccion.assert_not_called()

class PruebasDeCaminosDeArmarVenta(unittest.TestCase):
    """ServicioDeVentas._armar_venta tiene V(G) = 3: tres caminos independientes."""

    def test_camino1_sin_lineas_no_se_puede_confirmar(self):          # el bucle no se ejecuta
        servicio, repo_ventas = armar_servicio_de_ventas()
        with self.assertRaises(ValueError):
            servicio.registrar_venta_a_credito(1, [])
        repo_ventas.guardar_transaccion.assert_not_called()

    def test_camino2_linea_con_stock_se_agrega(self):                  # el bucle entra y hay stock
        servicio, _ = armar_servicio_de_ventas()
        venta = servicio.registrar_venta_a_credito(1, [(1, 2)])
        self.assertEqual(len(venta.detalles), 1)

    def test_camino3_linea_sin_stock_se_rechaza(self):                 # el bucle entra y NO hay stock
        servicio, _ = armar_servicio_de_ventas(hay_stock=False)
        with self.assertRaises(StockInsuficiente):
            servicio.registrar_venta_a_credito(1, [(1, 2)])

    def test_el_mismo_producto_en_dos_lineas_suma_las_cantidades(self):
        servicio, repo_ventas = armar_servicio_de_ventas()
        servicio.control_inventario.hay_disponible.side_effect = lambda producto, cantidad: cantidad <= 3
        with self.assertRaises(StockInsuficiente):                     # 2 + 2 = 4 > 3 aunque cada línea sola cabe
            servicio.registrar_venta_a_credito(1, [(1, 2), (1, 2)])
        repo_ventas.guardar_transaccion.assert_not_called()


class PruebasDeServicioDeProductosConMock(unittest.TestCase):
    def test_la_entrada_se_guarda_como_movimiento_de_entrada(self):
        repo = Mock()
        repo.obtener_existencia.return_value = Existencia(1, 5)
        ServicioDeProductos(repo).registrar_entrada(1, 10)
        existencia, tipo, cantidad = repo.guardar_existencia.call_args.args
        self.assertEqual((existencia.cantidad_actual, tipo, cantidad), (15, "ENTRADA", 10))


if __name__ == "__main__":
    unittest.main(verbosity=2)

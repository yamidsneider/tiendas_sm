"""Cuentas vencidas: lista de atrasados y no fiar a quien está atrasado (respuestas 2.2 y 2.3 del propietario).

Cada cliente tiene su plazo máximo de pago (ya existía). Una cuenta ABIERTA cuya fecha de vencimiento ya pasó
está vencida. A un cliente con una cuenta vencida no se le puede fiar más hasta que la pague. No se cobran
intereses. Para simular el paso del tiempo, la prueba cambia la fecha de vencimiento guardada en la base en
memoria. Se escribieron antes del código. Datos ficticios.
"""
import unittest
from datetime import datetime, timedelta

from interfaz_web.api import ApiDeLaTienda
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import CreditoNoPermitido, CuentaPorCobrar, EstadoCuenta
from tiendas_sm.presentador import PresentadorPuntoDeVenta
from tiendas_sm.presentador_creditos import PresentadorDeCreditos

MENSAJE_ATRASADO = "No se le puede fiar a Cliente ficticio Ana: tiene cuentas vencidas sin pagar"


class PruebasDeLaCuenta(unittest.TestCase):
    def cuenta(self, vencimiento):
        return CuentaPorCobrar(1, 1, 1, 10000, datetime(2026, 10, 1, 9, 0), vencimiento)

    def test_vencida_cuando_ya_paso_la_fecha(self):
        cuenta = self.cuenta(datetime(2026, 10, 16, 9, 0))
        self.assertTrue(cuenta.esta_vencida(datetime(2026, 10, 19, 8, 0)))
        self.assertEqual(cuenta.dias_de_atraso(datetime(2026, 10, 19, 8, 0)), 3)

    def test_no_vencida_antes_de_la_fecha(self):
        cuenta = self.cuenta(datetime(2026, 10, 16, 9, 0))
        self.assertFalse(cuenta.esta_vencida(datetime(2026, 10, 16, 8, 59)))
        self.assertEqual(cuenta.dias_de_atraso(datetime(2026, 10, 10)), 0)

    def test_una_cuenta_pagada_nunca_esta_vencida(self):
        cuenta = self.cuenta(datetime(2026, 10, 16, 9, 0))
        cuenta.aplicar_pago(10000)
        self.assertEqual(cuenta.estado, EstadoCuenta.PAGADA)
        self.assertFalse(cuenta.esta_vencida(datetime(2026, 12, 1)))


class BaseDeVencidas(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio", 2000, 2500, 20)
        self.ana = self.app.clientes.registrar_cliente("Cliente ficticio Ana", True, 100000, plazo_credito_dias=15)
        self.beto = self.app.clientes.registrar_cliente("Cliente ficticio Beto", True, 100000, plazo_credito_dias=15)
        self.app.ventas.registrar_venta_a_credito(self.ana.id_cliente, [(self.arroz.id_producto, 2)])
        self.cuenta_ana, = self.app.credito.cuentas_del_cliente(self.ana.id_cliente)
        self.vencer(self.cuenta_ana.id_cuenta, dias=3)

    def vencer(self, id_cuenta, dias):
        """Simula que pasó el tiempo: la cuenta venció hace «dias» días."""
        fecha = (datetime.now() - timedelta(days=dias)).isoformat()
        with self.app.conexion:
            self.app.conexion.execute("UPDATE cuentas_por_cobrar SET fecha_vencimiento=? WHERE id_cuenta=?",
                                      (fecha, id_cuenta))


class PruebasDeLaRegla(BaseDeVencidas):
    def test_no_se_fia_a_quien_tiene_una_cuenta_vencida(self):
        with self.assertRaises(CreditoNoPermitido) as error:
            self.app.ventas.registrar_venta_a_credito(self.ana.id_cliente, [(self.arroz.id_producto, 1)])
        self.assertEqual(str(error.exception), MENSAJE_ATRASADO)
        self.assertEqual(self.app.cantidad_en_inventario(self.arroz.id_producto), 18)   # no se descontó nada

    def test_al_pagar_la_cuenta_vencida_se_le_vuelve_a_fiar(self):
        self.app.credito.registrar_abono(self.cuenta_ana.id_cuenta, 5000)
        self.app.ventas.registrar_venta_a_credito(self.ana.id_cliente, [(self.arroz.id_producto, 1)])
        self.assertEqual(len(self.app.credito.cuentas_del_cliente(self.ana.id_cliente)), 2)

    def test_un_abono_parcial_no_basta(self):
        self.app.credito.registrar_abono(self.cuenta_ana.id_cuenta, 1000)
        with self.assertRaises(CreditoNoPermitido):
            self.app.ventas.registrar_venta_a_credito(self.ana.id_cliente, [(self.arroz.id_producto, 1)])

    def test_otro_cliente_al_dia_si_puede_comprar(self):
        self.app.ventas.registrar_venta_a_credito(self.beto.id_cliente, [(self.arroz.id_producto, 1)])
        self.assertTrue(self.app.credito.tiene_cuentas_vencidas(self.ana))
        self.assertFalse(self.app.credito.tiene_cuentas_vencidas(self.beto))


class PruebasDeLaPantallaDeCreditos(BaseDeVencidas):
    def setUp(self):
        super().setUp()
        self.pc = PresentadorDeCreditos(self.app)

    def test_la_tabla_marca_la_cuenta_como_vencida(self):
        self.assertEqual(dict(self.pc.tabla())[self.cuenta_ana.id_cuenta][3], "Vencida")

    def test_lista_de_atrasados_con_dias_de_atraso(self):
        self.app.ventas.registrar_venta_a_credito(self.beto.id_cliente, [(self.arroz.id_producto, 4)])
        cuenta_beto, = self.app.credito.cuentas_del_cliente(self.beto.id_cliente)
        self.vencer(cuenta_beto.id_cuenta, dias=1)
        atrasados = self.pc.atrasados()
        self.assertEqual([iid for iid, _ in atrasados], [self.cuenta_ana.id_cuenta, cuenta_beto.id_cuenta])  # más atrasado primero
        cliente, saldo, _vence, atraso = atrasados[0][1]
        self.assertEqual((cliente, saldo, atraso), ("Cliente ficticio Ana", "$ 5.000", "3 días"))
        self.assertEqual(atrasados[1][1][3], "1 día")

    def test_el_punto_de_venta_avisa_al_elegir_al_cliente(self):
        texto = PresentadorPuntoDeVenta(self.app).datos_del_cliente(self.ana.id_cliente).texto
        self.assertIn("Tiene cuentas vencidas: no se le puede fiar", texto)

    def test_la_api_entrega_los_atrasados(self):
        api = ApiDeLaTienda(self.app)
        self.assertEqual([f["id"] for f in api.atrasados()], [self.cuenta_ana.id_cuenta])


if __name__ == "__main__":
    unittest.main()

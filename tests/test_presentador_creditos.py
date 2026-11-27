"""Pruebas del presentador de la sección Créditos y abonos (HU-06, RF-09; etapa 3 de la interfaz).

No usa Tkinter. Los números de HU-06: deuda 50.000 − abono 20.000 = saldo 30.000; un abono mayor al saldo
se rechaza mostrando el saldo; pagar todo deja la cuenta PAGADA. No se marca mora ni «vencida»: esas
reglas están por confirmar con el propietario. Se escribieron antes del código. Datos ficticios.
"""
import unittest

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.presentador_creditos import PresentadorDeCreditos


class BaseDeCreditos(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.mercado = self.app.productos.registrar_producto("Mercado ficticio", 20000, 25000, 10)
        self.ana = self.app.clientes.registrar_cliente("Cliente ficticio Ana", True, 200000, plazo_credito_dias=15)
        self.beto = self.app.clientes.registrar_cliente("Cliente ficticio Beto", True, 200000, plazo_credito_dias=30)
        self.venta_ana = self.app.ventas.registrar_venta_a_credito(self.ana.id_cliente,
                                                                   [(self.mercado.id_producto, 2)])   # 50.000
        self.venta_beto = self.app.ventas.registrar_venta_a_credito(self.beto.id_cliente,
                                                                    [(self.mercado.id_producto, 1)])  # 25.000
        self.cuenta_ana = self.app.credito.cuentas_del_cliente(self.ana.id_cliente)[0].id_cuenta
        self.cuenta_beto = self.app.credito.cuentas_del_cliente(self.beto.id_cliente)[0].id_cuenta
        self.pc = PresentadorDeCreditos(self.app)


class PruebasDeLaLista(BaseDeCreditos):
    def test_lista_las_cuentas_abiertas_con_cliente_saldo_y_estado(self):
        filas = dict(self.pc.tabla())
        cliente, saldo, vence, estado = filas[self.cuenta_ana]
        self.assertEqual((cliente, saldo, estado), ("Cliente ficticio Ana", "$ 50.000", "Abierta"))
        self.assertRegex(vence, r"^\d{2}/\d{2}/\d{4}$")

    def test_las_pagadas_solo_se_ven_si_se_piden(self):
        self.pc.abonar(self.cuenta_beto, "25000")
        self.assertEqual([iid for iid, _ in self.pc.tabla()], [self.cuenta_ana])
        self.assertEqual(dict(self.pc.tabla(ver_pagadas=True))[self.cuenta_beto][3], "Pagada")

    def test_resumen_del_total_por_cobrar(self):
        self.assertEqual(self.pc.resumen(), "Por cobrar: $ 75.000 en 2 cuentas")


class PruebasDelAbono(BaseDeCreditos):
    def test_abono_parcial_hu06(self):
        resultado = self.pc.abonar(self.cuenta_ana, "20000")
        self.assertTrue(resultado.exito)
        self.assertEqual(resultado.mensaje, "Abono de $ 20.000 registrado. Saldo: $ 30.000")
        self.assertEqual(dict(self.pc.tabla())[self.cuenta_ana][1], "$ 30.000")

    def test_abono_mayor_al_saldo_se_rechaza_mostrando_el_saldo(self):
        resultado = self.pc.abonar(self.cuenta_ana, "60000")
        self.assertFalse(resultado.exito)
        self.assertIn("50000", resultado.mensaje)                    # el mensaje del dominio, tal cual
        self.assertEqual(dict(self.pc.tabla())[self.cuenta_ana][1], "$ 50.000")

    def test_pagar_todo_deja_la_cuenta_pagada(self):
        resultado = self.pc.abonar(self.cuenta_ana, "50000")
        self.assertEqual(resultado.mensaje, "Abono de $ 50.000 registrado. La cuenta quedó PAGADA")

    def test_monto_invalido_o_sin_cuenta(self):
        self.assertEqual(self.pc.abonar(self.cuenta_ana, "veinte").mensaje, "El abono debe ser un número entero")
        self.assertEqual(self.pc.abonar(self.cuenta_ana, "0").mensaje, "La cantidad debe ser mayor a cero")
        self.assertEqual(self.pc.abonar(None, "1000").mensaje, "Elige una cuenta de la lista")


class PruebasDelDetalle(BaseDeCreditos):
    def test_detalle_con_total_abonado_y_saldo(self):
        self.pc.abonar(self.cuenta_ana, "20000")
        texto = self.pc.detalle(self.cuenta_ana)
        self.assertIn("Cliente ficticio Ana", texto)
        self.assertIn(f"Venta #{self.venta_ana.id_venta}", texto)
        self.assertIn("Total $ 50.000 · Abonado $ 20.000 · Saldo $ 30.000", texto)
        self.assertIn("1 abono", texto)

    def test_cuenta_que_no_existe(self):
        self.assertEqual(self.pc.detalle(999), "")


if __name__ == "__main__":
    unittest.main()

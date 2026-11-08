"""Pago por transferencia y pago mixto (respuestas 1.2 y 1.3 del propietario; amplía UC-02).

La transferencia (Nequi, Daviplata) no está conectada a ningún sistema: el vendedor mira el celular y confirma.
Reglas aprobadas por el desarrollador: la parte por transferencia no puede pasar del total (no se da cambio por
transferencia); el efectivo cubre lo que falta y el cambio sale solo del efectivo. El ticket de una venta por
transferencia no muestra cambio. Se escribieron antes del código. Datos ficticios.
"""
import unittest

from interfaz_web.api import ApiDeLaTienda
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import EfectivoInsuficiente, FormaDePago
from tiendas_sm.presentador import PresentadorPuntoDeVenta
from tiendas_sm.presentador_ventas import PresentadorDeVentas


class BaseDelPago(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio", 2000, 2500, 20)
        self.lineas = [(self.arroz.id_producto, 4)]             # total 10.000


class PruebasDelDominio(BaseDelPago):
    def test_solo_transferencia_por_el_total_no_tiene_cambio(self):
        venta = self.app.ventas.registrar_venta_de_contado(self.lineas, 0, transferencia=10000)
        self.assertEqual((venta.forma_pago, venta.valor_transferencia, venta.calcular_cambio()),
                         (FormaDePago.TRANSFERENCIA, 10000, 0))

    def test_mixto_el_cambio_sale_del_efectivo(self):
        venta = self.app.ventas.registrar_venta_de_contado(self.lineas, 5000, transferencia=6000)
        self.assertEqual((venta.forma_pago, venta.valor_recibido, venta.calcular_cambio()),
                         (FormaDePago.MIXTO, 5000, 1000))

    def test_la_transferencia_no_puede_pasar_del_total(self):
        with self.assertRaises(ValueError) as error:
            self.app.ventas.registrar_venta_de_contado(self.lineas, 0, transferencia=12000)
        self.assertEqual(str(error.exception), "La transferencia (12000) no puede ser mayor al total, que es 10000")
        self.assertEqual(self.app.cantidad_en_inventario(self.arroz.id_producto), 20)

    def test_si_entre_los_dos_no_alcanza_se_rechaza(self):
        with self.assertRaises(EfectivoInsuficiente) as error:
            self.app.ventas.registrar_venta_de_contado(self.lineas, 2000, transferencia=6000)
        self.assertEqual(str(error.exception), "El pago (8000) no alcanza para el total, que es 10000")

    def test_valores_negativos_se_rechazan(self):
        with self.assertRaises(ValueError):
            self.app.ventas.registrar_venta_de_contado(self.lineas, 12000, transferencia=-2000)

    def test_solo_efectivo_sigue_igual(self):
        venta = self.app.ventas.registrar_venta_de_contado(self.lineas, 20000)
        self.assertEqual((venta.forma_pago, venta.valor_transferencia, venta.calcular_cambio()),
                         (FormaDePago.EFECTIVO, 0, 10000))

    def test_se_guarda_y_se_vuelve_a_leer(self):
        venta = self.app.ventas.registrar_venta_de_contado(self.lineas, 5000, transferencia=6000)
        guardada = self.app.ventas.obtener(venta.id_venta)
        self.assertEqual((guardada.forma_pago, guardada.valor_recibido, guardada.valor_transferencia),
                         (FormaDePago.MIXTO, 5000, 6000))


class PruebasDelTicket(BaseDelPago):
    def setUp(self):
        super().setUp()
        self.pv = PresentadorPuntoDeVenta(self.app)
        self.pv.agregar(self.arroz.id_producto, "4")

    def test_ticket_de_transferencia_dice_pagado_y_no_muestra_cambio(self):
        resultado = self.pv.cobrar_de_contado("0", "10000")
        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertIn("Forma de pago: TRANSFERENCIA", resultado.ticket)
        self.assertIn("Pagado por transferencia: $ 10.000", resultado.ticket)
        self.assertNotIn("Cambio", resultado.ticket)
        self.assertEqual(resultado.mensaje, "Venta #1 registrada. Pagada por transferencia")

    def test_ticket_mixto_muestra_las_dos_partes_y_el_cambio(self):
        resultado = self.pv.cobrar_de_contado("5000", "6000")
        for texto in ("Forma de pago: MIXTO", "Transferencia: $ 6.000", "Efectivo recibido: $ 5.000", "Cambio: $ 1.000"):
            self.assertIn(texto, resultado.ticket)

    def test_el_ticket_de_la_seccion_ventas_sale_igual(self):
        ticket = self.pv.cobrar_de_contado("0", "10000").ticket
        self.assertEqual(PresentadorDeVentas(self.app).ticket(1), ticket)

    def test_el_cambio_previo_tiene_en_cuenta_la_transferencia(self):
        self.assertEqual(self.pv.cambio_previo("5000", "6000").mensaje, "Cambio: $ 1.000")
        self.assertFalse(self.pv.cambio_previo("0", "12000").exito)

    def test_la_tabla_de_ventas_muestra_la_forma_de_pago(self):
        self.pv.cobrar_de_contado("0", "10000")
        self.assertEqual(PresentadorDeVentas(self.app).tabla()[0][1][2], "Transferencia")


class PruebasDeLaApi(BaseDelPago):
    def test_cobrar_y_cambio_reciben_la_transferencia(self):
        api = ApiDeLaTienda(self.app)
        api.agregar(self.arroz.id_producto, "4")
        self.assertEqual(api.cambio("5000", "6000")["mensaje"], "Cambio: $ 1.000")
        respuesta = api.cobrar_de_contado("5000", "6000")
        self.assertTrue(respuesta["exito"], respuesta["mensaje"])
        self.assertIn("Forma de pago: MIXTO", respuesta["ticket"])


if __name__ == "__main__":
    unittest.main()

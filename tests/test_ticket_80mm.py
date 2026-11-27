"""Ticket para impresora térmica de 80 mm (respuesta 1.3 del propietario, DDS §10.3).

Una impresora de 80 mm imprime unos 42 caracteres por renglón con la letra normal. El ticket se arma para que
ningún renglón pase de ese ancho: los nombres largos se parten y el valor de cada línea va a la derecha.
El cambio solo aparece en la venta de contado en efectivo; en la venta a crédito no hay recibido ni cambio.
Datos ficticios.
"""
import unittest

from interfaz_web.pagina import armar_pagina
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.presentador import ANCHO_DEL_TICKET, PresentadorPuntoDeVenta

NOMBRE_LARGO = "Galletas de chocolate surtidas paquete familiar x 12 unidades"


class PruebasDelTicketDe80mm(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.largo = self.app.productos.registrar_producto(NOMBRE_LARGO, 9000, 12500, 10)
        self.cliente = self.app.clientes.registrar_cliente("Cliente de prueba", True, 100000)
        self.pv = PresentadorPuntoDeVenta(self.app)

    def ticket_de_contado(self):
        self.pv.agregar(self.largo.id_producto, "2")
        return self.pv.cobrar_de_contado("30000").ticket

    def test_el_ancho_es_el_de_una_impresora_de_80_mm(self):
        self.assertEqual(ANCHO_DEL_TICKET, 42)

    def test_ningun_renglon_pasa_del_ancho_aunque_el_nombre_sea_largo(self):
        renglones = self.ticket_de_contado().splitlines()
        self.assertEqual([r for r in renglones if len(r) > ANCHO_DEL_TICKET], [])
        self.assertIn("2 x Galletas de chocolate surtidas paquete", renglones)

    def test_el_valor_de_la_linea_va_alineado_a_la_derecha(self):
        renglones = self.ticket_de_contado().splitlines()
        valor, = [r for r in renglones if r.endswith("$ 25.000") and "$ 12.500" in r]
        self.assertEqual(len(valor), ANCHO_DEL_TICKET)

    def test_contado_muestra_recibido_y_cambio(self):
        ticket = self.ticket_de_contado()
        for texto in ("Recibido: $ 30.000", "Cambio: $ 5.000", "TOTAL: $ 25.000"):
            self.assertIn(texto, ticket)

    def test_credito_no_muestra_recibido_ni_cambio(self):
        self.pv.agregar(self.largo.id_producto, "1")
        ticket = self.pv.vender_a_credito(self.cliente.id_cliente).ticket
        self.assertIn("Forma de pago: CRÉDITO", ticket)
        self.assertNotIn("Recibido", ticket)
        self.assertNotIn("Cambio", ticket)


class PruebasDeLaImpresion(unittest.TestCase):
    def setUp(self):
        pagina = armar_pagina()
        self.impresion = pagina[pagina.index("@media print"):]

    def test_la_hoja_es_de_80_mm_de_ancho(self):
        self.assertIn("@page{size:80mm auto", self.impresion)

    def test_el_ticket_ocupa_el_ancho_que_imprime_el_rollo(self):
        self.assertIn(".papel{width:72mm", self.impresion)


if __name__ == "__main__":
    unittest.main()

"""Pruebas de la sección Ventas: lectura de ventas guardadas y presentador (RF-05; etapa 6 de la interfaz).

Solo consulta: lista las últimas ventas y vuelve a mostrar su ticket, idéntico al que dio el punto de
venta. No anula ventas (DT-08) ni saca totales o reportes (no aprobados). No usa Tkinter.
Se escribieron antes del código. Datos ficticios.
"""
import unittest

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.presentador import PresentadorPuntoDeVenta
from tiendas_sm.presentador_ventas import PresentadorDeVentas


class BaseDeVentas(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio 500 g", 2000, 2500, 20)
        self.ana = self.app.clientes.registrar_cliente("Cliente ficticio Ana", True, 100000, plazo_credito_dias=15)
        self.pv = PresentadorPuntoDeVenta(self.app)
        self.pv.agregar(self.arroz.id_producto, "2")
        self.ticket_contado = self.pv.cobrar_de_contado("10000").ticket
        self.pv.agregar(self.arroz.id_producto, "1")
        self.ticket_credito = self.pv.vender_a_credito(self.ana.id_cliente).ticket
        self.contado, self.credito = 1, 2
        self.pve = PresentadorDeVentas(self.app)


class PruebasDeLaLecturaEnElServicio(BaseDeVentas):
    def test_obtener_trae_la_venta_con_sus_detalles(self):
        venta = self.app.ventas.obtener(self.contado)
        self.assertEqual((venta.total, venta.valor_recibido, venta.calcular_cambio()), (5000, 10000, 5000))
        self.assertEqual([(d.id_producto, d.cantidad, d.precio_unitario) for d in venta.detalles],
                         [(self.arroz.id_producto, 2, 2500)])
        self.assertIsNone(self.app.ventas.obtener(999))

    def test_listar_de_la_mas_reciente_a_la_mas_vieja_con_limite(self):
        self.assertEqual([v.id_venta for v in self.app.ventas.listar()], [self.credito, self.contado])
        self.assertEqual([v.id_venta for v in self.app.ventas.listar(limite=1)], [self.credito])


class PruebasDeLaTabla(BaseDeVentas):
    def test_filas_con_numero_fecha_tipo_cliente_y_total(self):
        (id_credito, credito), (id_contado, contado) = self.pve.tabla()
        self.assertEqual((id_credito, id_contado), (self.credito, self.contado))
        self.assertEqual(credito[0], "#2")
        self.assertRegex(credito[1], r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$")
        self.assertEqual(credito[2:], ("Crédito", "Cliente ficticio Ana", "$ 2.500"))
        self.assertEqual(contado[2:], ("Efectivo", "—", "$ 5.000"))


class PruebasDelTicket(BaseDeVentas):
    def test_el_ticket_es_el_mismo_que_dio_el_punto_de_venta(self):
        self.assertEqual(self.pve.ticket(self.contado), self.ticket_contado)
        self.assertEqual(self.pve.ticket(self.credito), self.ticket_credito)

    def test_el_ticket_conserva_el_precio_de_la_venta_hu02(self):
        self.app.productos.actualizar_precio(self.arroz.id_producto, 9999)
        self.assertEqual(self.pve.ticket(self.contado), self.ticket_contado)

    def test_venta_que_no_existe(self):
        self.assertEqual(self.pve.ticket(999), "")


if __name__ == "__main__":
    unittest.main()

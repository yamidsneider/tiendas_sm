"""Pruebas de Existencias: historial de movimientos y presentador (HU-03, RF-03, RF-04; etapa 5 de la interfaz).

HU-03: 5 + 10 = 15; una entrada de 0 o negativa se rechaza. El historial lee los movimientos que ya se
guardaban (ENTRADA y SALIDA_VENTA, TD-01); no se agrega la salida manual (por confirmar, H-1).
No usa Tkinter. Se escribieron antes del código. Datos ficticios.
"""
import unittest

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.presentador_existencias import PresentadorDeExistencias


class BaseDeExistencias(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio 500 g", 2000, 2500, 5)
        self.panela = self.app.productos.registrar_producto("Panela ficticia", 2200, 3000, 0)
        self.pe = PresentadorDeExistencias(self.app)


class PruebasDelHistorialEnElServicio(BaseDeExistencias):
    def test_lista_entradas_y_salidas_del_mas_reciente_al_mas_viejo(self):
        self.app.ventas.registrar_venta_de_contado([(self.arroz.id_producto, 2)], 5000)
        movimientos = self.app.productos.movimientos()
        self.assertEqual([(m.id_producto, m.tipo, m.cantidad) for m in movimientos],
                         [(self.arroz.id_producto, "SALIDA_VENTA", 2), (self.arroz.id_producto, "ENTRADA", 5)])

    def test_respeta_el_limite(self):
        for _ in range(3):
            self.app.productos.registrar_entrada(self.panela.id_producto, 1)
        self.assertEqual(len(self.app.productos.movimientos(limite=2)), 2)


class PruebasDeLaTablaDeExistencias(BaseDeExistencias):
    def test_lista_productos_con_disponibles(self):
        self.assertEqual(self.pe.tabla(), [(self.arroz.id_producto, ("Arroz ficticio 500 g", 5)),
                                           (self.panela.id_producto, ("Panela ficticia", 0))])

    def test_busca_por_nombre(self):
        self.assertEqual([iid for iid, _ in self.pe.tabla("panela")], [self.panela.id_producto])


class PruebasDeLaEntrada(BaseDeExistencias):
    def test_entrada_suma_al_inventario_hu03(self):
        resultado = self.pe.registrar_entrada(self.arroz.id_producto, "10")
        self.assertTrue(resultado.exito)
        self.assertEqual(resultado.mensaje, "Entrada de 10 unidades de Arroz ficticio 500 g. Ahora hay 15")
        self.assertEqual(self.app.cantidad_en_inventario(self.arroz.id_producto), 15)

    def test_entrada_cero_o_negativa_se_rechaza_hu03(self):
        for cantidad in ("0", "-3"):
            with self.subTest(cantidad=cantidad):
                resultado = self.pe.registrar_entrada(self.arroz.id_producto, cantidad)
                self.assertFalse(resultado.exito)
                self.assertEqual(resultado.mensaje, "La cantidad debe ser mayor a cero")
        self.assertEqual(self.app.cantidad_en_inventario(self.arroz.id_producto), 5)

    def test_texto_o_producto_sin_elegir(self):
        self.assertEqual(self.pe.registrar_entrada(self.arroz.id_producto, "diez").mensaje,
                         "La cantidad debe ser un número entero")
        self.assertEqual(self.pe.registrar_entrada(None, "10").mensaje, "Elige un producto de la lista")

    def test_una_unidad_en_singular(self):
        self.assertEqual(self.pe.registrar_entrada(self.panela.id_producto, "1").mensaje,
                         "Entrada de 1 unidad de Panela ficticia. Ahora hay 1")


class PruebasDeLosMovimientosEnPantalla(BaseDeExistencias):
    def test_movimientos_con_fecha_producto_tipo_y_signo(self):
        self.app.ventas.registrar_venta_de_contado([(self.arroz.id_producto, 2)], 5000)
        (_, salida), (_, entrada) = self.pe.movimientos()
        self.assertEqual(salida[1:], ("Arroz ficticio 500 g", "Salida por venta", "-2"))
        self.assertEqual(entrada[1:], ("Arroz ficticio 500 g", "Entrada", "+5"))
        self.assertRegex(salida[0], r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$")


if __name__ == "__main__":
    unittest.main()

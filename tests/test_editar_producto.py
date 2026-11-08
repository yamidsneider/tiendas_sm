"""Editar producto (recomendación aprobada por el desarrollador, noviembre de 2026).

Se pueden cambiar nombre, precio de compra y precio de venta. Las existencias NO se editan aquí (se cambian con
entradas y ventas, para que quede el movimiento) y el stock mínimo sigue por confirmar (TD-04). Las ventas
anteriores conservan su precio (HU-02). Se escribieron antes del código. Datos ficticios.
"""
import unittest

from interfaz_web.api import ApiDeLaTienda
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.presentador_productos import PresentadorDeProductos
from tiendas_sm.presentador_ventas import PresentadorDeVentas


class BaseDeEdicion(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio 500 g", 2000, 2500, 20)

    def guardado(self):
        return self.app.productos.obtener(self.arroz.id_producto)


class PruebasDelServicio(BaseDeEdicion):
    def test_actualiza_nombre_y_precios_sin_tocar_las_existencias(self):
        self.app.productos.actualizar_producto(self.arroz.id_producto, "Arroz ficticio 1 kg", 3800, 4600)
        producto = self.guardado()
        self.assertEqual((producto.nombre, producto.precio_compra, producto.precio_venta),
                         ("Arroz ficticio 1 kg", 3800, 4600))
        self.assertEqual(self.app.cantidad_en_inventario(self.arroz.id_producto), 20)
        self.assertEqual(len(self.app.productos.listar()), 1)

    def test_aplica_las_reglas_del_registro_y_no_guarda_nada_si_falla(self):
        for datos in (("", 2000, 2500), ("Arroz", -1, 2500), ("Arroz", 2000, -1)):
            with self.subTest(datos=datos), self.assertRaises(ValueError):
                self.app.productos.actualizar_producto(self.arroz.id_producto, *datos)
        self.assertEqual(self.guardado().nombre, "Arroz ficticio 500 g")

    def test_producto_que_no_existe(self):
        with self.assertRaisesRegex(ValueError, "El producto no existe"):
            self.app.productos.actualizar_producto(999, "Nada", 1, 1)

    def test_las_ventas_anteriores_conservan_su_precio_hu02(self):
        self.app.ventas.registrar_venta_de_contado([(self.arroz.id_producto, 2)], 5000)
        ticket = PresentadorDeVentas(self.app).ticket(1)
        self.app.productos.actualizar_producto(self.arroz.id_producto, "Arroz ficticio 500 g", 2000, 9999)
        self.assertIn("TOTAL: $ 5.000", PresentadorDeVentas(self.app).ticket(1))
        self.assertEqual(PresentadorDeVentas(self.app).ticket(1), ticket)


class PruebasDelPresentador(BaseDeEdicion):
    def setUp(self):
        super().setUp()
        self.pp = PresentadorDeProductos(self.app)

    def test_datos_para_editar_trae_lo_guardado_como_texto(self):
        datos = self.pp.datos_para_editar(self.arroz.id_producto)
        self.assertEqual((datos.nombre, datos.compra, datos.venta), ("Arroz ficticio 500 g", "2000", "2500"))
        self.assertIsNone(self.pp.datos_para_editar(999))

    def test_editar_convierte_el_texto_y_muestra_el_mensaje(self):
        resultado = self.pp.editar(self.arroz.id_producto, " Arroz ficticio 1 kg ", "3800", "4600")
        self.assertEqual((resultado.exito, resultado.mensaje), (True, "Producto actualizado: Arroz ficticio 1 kg"))
        self.assertEqual(self.guardado().precio_venta, 4600)

    def test_editar_con_datos_invalidos_muestra_el_mensaje(self):
        self.assertEqual(self.pp.editar(self.arroz.id_producto, "Arroz", "barato", "2500").mensaje,
                         "El precio de compra debe ser un número entero")
        self.assertEqual(self.pp.editar(self.arroz.id_producto, " ", "2000", "2500").mensaje, "El nombre es obligatorio")
        self.assertFalse(self.pp.editar(None, "Arroz", "2000", "2500").exito)


class PruebasDeLaApi(BaseDeEdicion):
    def test_datos_y_editar_desde_la_pagina(self):
        api = ApiDeLaTienda(self.app)
        self.assertEqual(api.datos_producto(self.arroz.id_producto),
                         {"nombre": "Arroz ficticio 500 g", "compra": "2000", "venta": "2500"})
        self.assertIsNone(api.datos_producto(999))
        self.assertTrue(api.editar_producto(self.arroz.id_producto, "Arroz ficticio", "2100", "2600")["exito"])
        self.assertEqual(self.guardado().precio_compra, 2100)


if __name__ == "__main__":
    unittest.main()

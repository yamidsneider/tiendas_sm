"""Stock mínimo por producto y aviso de «por reponer» (RF-12, TD-04; respuesta 4.1 del propietario).

El propietario da el stock mínimo al crear cada producto. Cuando quedan esas unidades o menos, el producto
aparece «por reponer». Un mínimo de 0 significa que ese producto no avisa. Se escribieron antes del código.
Datos ficticios.
"""
import unittest

from interfaz_web.api import ApiDeLaTienda
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import Producto
from tiendas_sm.presentador_existencias import PresentadorDeExistencias
from tiendas_sm.presentador_productos import PresentadorDeProductos


class PruebasDeLaRegla(unittest.TestCase):
    def test_avisa_cuando_quedan_el_minimo_o_menos(self):
        producto = Producto(1, "Producto ficticio", 1000, 1500, stock_minimo=5)
        self.assertTrue(producto.necesita_reponer(5))
        self.assertTrue(producto.necesita_reponer(0))
        self.assertFalse(producto.necesita_reponer(6))

    def test_minimo_cero_no_avisa_nunca(self):
        self.assertFalse(Producto(1, "Producto ficticio", 1000, 1500).necesita_reponer(0))


class BaseDelStockMinimo(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.pp = PresentadorDeProductos(self.app)
        self.pe = PresentadorDeExistencias(self.app)
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio", 2000, 2500, 3, stock_minimo=5)
        self.panela = self.app.productos.registrar_producto("Panela ficticia", 2200, 3000, 10, stock_minimo=5)
        self.sal = self.app.productos.registrar_producto("Sal ficticia", 800, 1200, 0)


class PruebasDeProductos(BaseDelStockMinimo):
    def test_registrar_guarda_el_stock_minimo(self):
        resultado = self.pp.registrar("Leche ficticia", "2500", "3200", "12", "4")
        self.assertTrue(resultado.exito, resultado.mensaje)
        leche, = [p for p in self.app.productos.listar() if p.nombre == "Leche ficticia"]
        self.assertEqual(leche.stock_minimo, 4)

    def test_un_minimo_negativo_muestra_el_mensaje_del_dominio(self):
        resultado = self.pp.registrar("Leche ficticia", "2500", "3200", "12", "-1")
        self.assertEqual((resultado.exito, resultado.mensaje), (False, "El stock mínimo no puede ser negativo"))

    def test_editar_trae_y_cambia_el_stock_minimo(self):
        self.assertEqual(self.pp.datos_para_editar(self.arroz.id_producto).minimo, "5")
        resultado = self.pp.editar(self.arroz.id_producto, "Arroz ficticio", "2000", "2500", "2")
        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertEqual(self.app.productos.obtener(self.arroz.id_producto).stock_minimo, 2)


class PruebasDelAvisoEnExistencias(BaseDelStockMinimo):
    def test_por_reponer_lista_solo_los_que_llegaron_al_minimo(self):
        self.assertEqual(self.pe.por_reponer(), [(self.arroz.id_producto, ("Arroz ficticio", 3, 5))])

    def test_al_entrar_mercancia_sale_de_la_lista(self):
        self.app.productos.registrar_entrada(self.arroz.id_producto, 10)
        self.assertEqual(self.pe.por_reponer(), [])

    def test_una_venta_que_deja_el_minimo_lo_pone_en_la_lista(self):
        self.app.ventas.registrar_venta_de_contado([(self.panela.id_producto, 5)], 15000)
        self.assertIn(self.panela.id_producto, [iid for iid, _ in self.pe.por_reponer()])


class PruebasDeLaApi(BaseDelStockMinimo):
    def setUp(self):
        super().setUp()
        self.api = ApiDeLaTienda(self.app)

    def test_registrar_y_editar_reciben_el_minimo(self):
        self.assertTrue(self.api.registrar_producto("Leche ficticia", "2500", "3200", "12", "4")["exito"])
        self.assertEqual(self.api.datos_producto(self.arroz.id_producto)["minimo"], "5")
        self.assertTrue(self.api.editar_producto(self.arroz.id_producto, "Arroz ficticio", "2000", "2500", "1")["exito"])
        self.assertEqual(self.app.productos.obtener(self.arroz.id_producto).stock_minimo, 1)

    def test_existencias_marca_las_filas_por_reponer(self):
        filas = {f["id"]: f["reponer"] for f in self.api.existencias("")}
        self.assertEqual(filas, {self.arroz.id_producto: True, self.panela.id_producto: False, self.sal.id_producto: False})
        self.assertEqual(self.api.por_reponer(), [{"id": self.arroz.id_producto, "valores": ["Arroz ficticio", 3, 5]}])


if __name__ == "__main__":
    unittest.main()

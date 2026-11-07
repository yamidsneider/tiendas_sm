"""Pruebas del presentador de la sección Productos (HU-01, HU-02, RF-01, RF-02; etapa 4 de la interfaz).

No usa Tkinter. Registra con nombre, precios y cantidad inicial (HU-01) y cambia el precio de venta sin
alterar las ventas anteriores (HU-02). No pide stock mínimo (general o por producto: por confirmar, TD-04),
no calcula ganancias ni borra productos (DT-08). Se escribieron antes del código. Datos ficticios.
"""
import unittest

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.presentador import PresentadorPuntoDeVenta
from tiendas_sm.presentador_productos import PresentadorDeProductos


class BaseDeProductos(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio 500 g", 2000, 2500, 10)
        self.panela = self.app.productos.registrar_producto("Panela ficticia", 2200, 3000, 0)
        self.pp = PresentadorDeProductos(self.app)

    def producto(self, nombre):
        return next(p for p in self.app.productos.listar() if p.nombre == nombre)


class PruebasDeLaLista(BaseDeProductos):
    def test_lista_con_precios_en_pesos_y_disponibles(self):
        self.assertEqual(dict(self.pp.tabla())[self.arroz.id_producto],
                         ("Arroz ficticio 500 g", "$ 2.000", "$ 2.500", 10))

    def test_busca_por_nombre(self):
        self.assertEqual([iid for iid, _ in self.pp.tabla(" PANELA")], [self.panela.id_producto])


class PruebasDelRegistro(BaseDeProductos):
    def test_registra_con_nombre_precios_y_cantidad_inicial_hu01(self):
        resultado = self.pp.registrar("  Café ficticio 250 g ", "8500", "11000", "6")
        self.assertTrue(resultado.exito)
        self.assertEqual(resultado.mensaje, "Producto registrado: Café ficticio 250 g")
        cafe = self.producto("Café ficticio 250 g")
        self.assertEqual((cafe.precio_compra, cafe.precio_venta), (8500, 11000))
        self.assertEqual(self.app.cantidad_en_inventario(cafe.id_producto), 6)

    def test_cantidad_inicial_cero_se_permite(self):
        self.assertTrue(self.pp.registrar("Sal ficticia", "1000", "1500", "0").exito)

    def test_rechazos_con_el_mensaje_del_dominio_y_sin_guardar(self):
        casos = (("", "1000", "1500", "1", "El nombre es obligatorio"),
                 ("Sal ficticia", "-1", "1500", "1", "Los precios no pueden ser negativos"),
                 ("Sal ficticia", "1000", "mil", "1", "El precio de venta debe ser un número entero"),
                 ("Sal ficticia", "1000", "1500", "-2", "La cantidad inicial no puede ser negativa"))
        for nombre, compra, venta, cantidad, mensaje in casos:
            with self.subTest(mensaje=mensaje):
                resultado = self.pp.registrar(nombre, compra, venta, cantidad)
                self.assertFalse(resultado.exito)
                self.assertEqual(resultado.mensaje, mensaje)
        self.assertEqual(len(self.app.productos.listar()), 2)


class PruebasDelCambioDePrecio(BaseDeProductos):
    def test_cambia_el_precio_de_venta_y_el_punto_de_venta_lo_usa(self):
        resultado = self.pp.cambiar_precio(self.arroz.id_producto, "2800")
        self.assertTrue(resultado.exito)
        self.assertEqual(resultado.mensaje, "Nuevo precio de Arroz ficticio 500 g: $ 2.800")
        self.assertEqual(PresentadorPuntoDeVenta(self.app).buscar("arroz")[0].precio, 2800)

    def test_las_ventas_anteriores_conservan_su_precio_hu02(self):
        venta = self.app.ventas.registrar_venta_de_contado([(self.arroz.id_producto, 2)], 5000)
        self.pp.cambiar_precio(self.arroz.id_producto, "2800")
        self.assertEqual(venta.calcular_total(), 5000)
        precio_guardado = self.app.conexion.execute(
            "SELECT precio_unitario_venta FROM detalles_venta WHERE id_venta=?", (venta.id_venta,)).fetchone()[0]
        self.assertEqual(precio_guardado, 2500)

    def test_rechazos_del_cambio_de_precio(self):
        self.assertEqual(self.pp.cambiar_precio(self.arroz.id_producto, "-5").mensaje, "El precio no puede ser negativo")
        self.assertEqual(self.pp.cambiar_precio(self.arroz.id_producto, "").mensaje,
                         "El precio de venta debe ser un número entero")
        self.assertEqual(self.pp.cambiar_precio(None, "100").mensaje, "Elige un producto de la lista")
        self.assertEqual(self.producto("Arroz ficticio 500 g").precio_venta, 2500)

    def test_precio_actual_para_el_formulario(self):
        self.assertEqual(self.pp.precio_actual(self.arroz.id_producto), "Arroz ficticio 500 g\nPrecio actual: $ 2.500")
        self.assertEqual(self.pp.precio_actual(999), "")


if __name__ == "__main__":
    unittest.main()

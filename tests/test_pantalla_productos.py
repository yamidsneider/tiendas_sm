"""Pruebas de la pantalla Productos en Tkinter (HU-01, HU-02; etapa 4 de la interfaz).

La lógica se prueba sin ventanas en test_presentador_productos.py; aquí solo que la pantalla la use bien.
Necesitan pantalla: sin ella (CI de GitHub) se SALTAN. Datos ficticios.
"""
import unittest

from tiendas_sm.aplicacion import Aplicacion

try:
    import tkinter as tk
except ImportError:                                   # Python sin Tkinter: solo esto justifica saltar
    tk = None
if tk is not None:                                    # un módulo propio que falte SÍ debe hacer fallar la prueba
    from interfaz_tk.pantalla_productos import PantallaProductos
    from interfaz_tk.ventana_principal import VentanaPrincipal
    from tiendas_sm.presentador_productos import PresentadorDeProductos


class PruebasDeLaPantallaProductos(unittest.TestCase):
    def setUp(self):
        if tk is None:
            self.skipTest("Tkinter no está instalado")
        try:
            self.raiz = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"No hay pantalla para abrir ventanas: {error}")
        self.raiz.withdraw()
        self.app = Aplicacion()
        self.arroz = str(self.app.productos.registrar_producto("Arroz ficticio 500 g", 2000, 2500, 10).id_producto)
        self.pantalla = PantallaProductos(self.raiz, PresentadorDeProductos(self.app))
        self.pantalla.mostrar()

    def tearDown(self):
        self.raiz.destroy()

    def test_guardar_un_producto_lo_agrega_y_limpia_el_formulario(self):
        self.pantalla.nombre.set("Sal ficticia")
        self.pantalla.precio_compra.set("1000")
        self.pantalla.precio_venta.set("1500")
        self.pantalla.cantidad_inicial.set("5")
        self.pantalla.guardar()
        self.assertEqual(len(self.pantalla.tabla.get_children()), 2)
        self.assertIn("registrado", self.pantalla.mensaje.cget("text"))
        self.assertEqual(self.pantalla.nombre.get(), "")

    def test_error_al_guardar_se_muestra(self):
        self.pantalla.guardar()
        self.assertEqual(self.pantalla.mensaje.cget("text"), "El precio de compra debe ser un número entero")

    def test_cambiar_el_precio_del_producto_elegido(self):
        self.pantalla.tabla.selection_set(self.arroz)
        self.pantalla.mostrar_precio_actual()
        self.assertIn("Precio actual: $ 2.500", self.pantalla.precio_elegido.cget("text"))
        self.pantalla.nuevo_precio.set("2800")
        self.pantalla.cambiar_precio()
        self.assertEqual(self.pantalla.tabla.item(self.arroz, "values")[2], "$ 2.800")
        self.assertIn("$ 2.800", self.pantalla.mensaje_precio.cget("text"))
        self.assertEqual(self.pantalla.nuevo_precio.get(), "")

    def test_cambiar_precio_sin_elegir_producto_avisa(self):
        self.pantalla.nuevo_precio.set("2800")
        self.pantalla.cambiar_precio()
        self.assertEqual(self.pantalla.mensaje_precio.cget("text"), "Elige un producto de la lista")

    def test_la_ventana_principal_abre_la_seccion(self):
        principal = VentanaPrincipal(self.raiz, self.app)
        principal.mostrar("Productos")
        self.assertIsInstance(principal.pantallas["Productos"], PantallaProductos)


if __name__ == "__main__":
    unittest.main()

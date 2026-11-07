"""Pruebas de la pantalla Existencias en Tkinter (HU-03, RF-04; etapa 5 de la interfaz).

La lógica se prueba sin ventanas en test_presentador_existencias.py; aquí solo que la pantalla la use bien.
Necesitan pantalla: sin ella (CI de GitHub) se SALTAN. Datos ficticios.
"""
import unittest

from tiendas_sm.aplicacion import Aplicacion

try:
    import tkinter as tk
except ImportError:                                   # Python sin Tkinter: solo esto justifica saltar
    tk = None
if tk is not None:                                    # un módulo propio que falte SÍ debe hacer fallar la prueba
    from interfaz_tk.pantalla_existencias import PantallaExistencias
    from interfaz_tk.ventana_principal import VentanaPrincipal
    from tiendas_sm.presentador_existencias import PresentadorDeExistencias


class PruebasDeLaPantallaExistencias(unittest.TestCase):
    def setUp(self):
        if tk is None:
            self.skipTest("Tkinter no está instalado")
        try:
            self.raiz = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"No hay pantalla para abrir ventanas: {error}")
        self.raiz.withdraw()
        self.app = Aplicacion()
        self.arroz = str(self.app.productos.registrar_producto("Arroz ficticio 500 g", 2000, 2500, 5).id_producto)
        self.pantalla = PantallaExistencias(self.raiz, PresentadorDeExistencias(self.app))
        self.pantalla.mostrar()

    def tearDown(self):
        self.raiz.destroy()

    def test_registrar_una_entrada_actualiza_la_tabla_y_el_historial(self):
        self.pantalla.tabla.selection_set(self.arroz)
        self.pantalla.mostrar_elegido()
        self.pantalla.cantidad.set("10")
        self.pantalla.registrar_entrada()
        self.assertEqual(self.pantalla.tabla.item(self.arroz, "values")[1], "15")
        self.assertEqual(len(self.pantalla.historial.get_children()), 2)
        self.assertIn("Ahora hay 15", self.pantalla.mensaje.cget("text"))
        self.assertEqual(self.pantalla.cantidad.get(), "")

    def test_entrada_rechazada_conserva_la_cantidad(self):
        self.pantalla.tabla.selection_set(self.arroz)
        self.pantalla.cantidad.set("0")
        self.pantalla.registrar_entrada()
        self.assertEqual(self.pantalla.mensaje.cget("text"), "La cantidad debe ser mayor a cero")
        self.assertEqual(self.pantalla.cantidad.get(), "0")

    def test_elegir_un_producto_lo_muestra_en_el_formulario(self):
        self.pantalla.tabla.selection_set(self.arroz)
        self.pantalla.mostrar_elegido()
        self.assertIn("Arroz ficticio 500 g", self.pantalla.elegido.cget("text"))

    def test_la_ventana_principal_abre_la_seccion(self):
        principal = VentanaPrincipal(self.raiz, self.app)
        principal.mostrar("Existencias")
        self.assertIsInstance(principal.pantallas["Existencias"], PantallaExistencias)


if __name__ == "__main__":
    unittest.main()

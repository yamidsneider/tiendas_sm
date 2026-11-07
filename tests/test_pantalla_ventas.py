"""Pruebas de la pantalla Ventas en Tkinter (RF-05; etapa 6 de la interfaz).

La lógica se prueba sin ventanas en test_presentador_ventas.py; aquí solo que la pantalla la use bien.
Necesitan pantalla: sin ella (CI de GitHub) se SALTAN. Datos ficticios.
"""
import unittest

from tiendas_sm.aplicacion import Aplicacion

try:
    import tkinter as tk
except ImportError:                                   # Python sin Tkinter: solo esto justifica saltar
    tk = None
if tk is not None:                                    # un módulo propio que falte SÍ debe hacer fallar la prueba
    from interfaz_tk.pantalla_ventas import PantallaVentas
    from interfaz_tk.ventana_principal import VentanaPrincipal
    from tiendas_sm.presentador_ventas import PresentadorDeVentas


class PruebasDeLaPantallaVentas(unittest.TestCase):
    def setUp(self):
        if tk is None:
            self.skipTest("Tkinter no está instalado")
        try:
            self.raiz = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"No hay pantalla para abrir ventanas: {error}")
        self.raiz.withdraw()
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio 500 g", 2000, 2500, 20)
        self.app.ventas.registrar_venta_de_contado([(self.arroz.id_producto, 2)], 5000)
        self.pantalla = PantallaVentas(self.raiz, PresentadorDeVentas(self.app))
        self.pantalla.mostrar()

    def tearDown(self):
        self.raiz.destroy()

    def texto_del_ticket(self):
        return self.pantalla.ticket.get("1.0", "end-1c")

    def test_elegir_una_venta_muestra_su_ticket_sin_dejarlo_editar(self):
        self.pantalla.tabla.selection_set("1")
        self.pantalla.mostrar_ticket()
        self.assertIn("Venta #1", self.texto_del_ticket())
        self.assertIn("TOTAL: $ 5.000", self.texto_del_ticket())
        self.assertEqual(str(self.pantalla.ticket.cget("state")), "disabled")

    def test_al_volver_a_la_seccion_aparece_la_venta_nueva(self):
        self.app.ventas.registrar_venta_de_contado([(self.arroz.id_producto, 1)], 2500)
        self.pantalla.ocultar()
        self.pantalla.mostrar()
        self.assertEqual(self.pantalla.tabla.get_children(), ("2", "1"))

    def test_la_ventana_principal_abre_la_seccion(self):
        principal = VentanaPrincipal(self.raiz, self.app)
        principal.mostrar("Ventas")
        self.assertIsInstance(principal.pantallas["Ventas"], PantallaVentas)


if __name__ == "__main__":
    unittest.main()

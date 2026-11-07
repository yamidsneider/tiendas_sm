"""Pruebas de la pantalla Clientes en Tkinter (HU-05, RF-07; etapa 2 de la interfaz).

La lógica ya se prueba sin ventanas en test_presentador_clientes.py; aquí solo se revisa que la pantalla
la use bien. Necesitan pantalla: sin ella (CI de GitHub) se SALTAN. Datos ficticios.
"""
import unittest

from tiendas_sm.aplicacion import Aplicacion

try:
    import tkinter as tk
except ImportError:                                   # Python sin Tkinter: solo esto justifica saltar
    tk = None
if tk is not None:                                    # un módulo propio que falte SÍ debe hacer fallar la prueba
    from interfaz_tk.pantalla_clientes import PantallaClientes
    from interfaz_tk.ventana_principal import VentanaPrincipal
    from tiendas_sm.presentador_clientes import PresentadorDeClientes


class BaseDeLaPantalla(unittest.TestCase):
    def setUp(self):
        if tk is None:
            self.skipTest("Tkinter no está instalado")
        try:
            self.raiz = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"No hay pantalla para abrir ventanas: {error}")
        self.raiz.withdraw()
        self.app = Aplicacion()
        self.ana = self.app.clientes.registrar_cliente("Cliente ficticio Ana", True, 100000, plazo_credito_dias=15)
        self.pantalla = PantallaClientes(self.raiz, PresentadorDeClientes(self.app))
        self.pantalla.mostrar()

    def tearDown(self):
        self.raiz.destroy()

    def filas(self):
        return self.pantalla.tabla.get_children()


class PruebasDeLaPantallaClientes(BaseDeLaPantalla):
    def test_muestra_los_clientes_guardados(self):
        self.assertEqual(self.filas(), (str(self.ana.id_cliente),))

    def test_guardar_un_cliente_lo_agrega_a_la_lista_y_limpia_el_formulario(self):
        self.pantalla.nombres.set("Cliente ficticio Beto")
        self.pantalla.limite.set("50000")
        self.pantalla.guardar()
        self.assertEqual(len(self.filas()), 2)
        self.assertIn("registrado", self.pantalla.mensaje.cget("text"))
        self.assertEqual(self.pantalla.nombres.get(), "")

    def test_un_error_se_muestra_y_no_guarda(self):
        self.pantalla.nombres.set("")
        self.pantalla.guardar()
        self.assertEqual(self.pantalla.mensaje.cget("text"), "El nombre es obligatorio")
        self.assertEqual(len(self.filas()), 1)

    def test_sin_credito_el_limite_queda_en_cero_y_no_se_edita(self):
        self.pantalla.credito.set(False)
        self.pantalla.cambiar_credito()
        self.assertEqual(self.pantalla.limite.get(), "0")
        self.assertEqual(str(self.pantalla.campo_limite.cget("state")), "disabled")

    def test_elegir_un_cliente_muestra_su_detalle(self):
        self.pantalla.tabla.selection_set(str(self.ana.id_cliente))
        self.pantalla.mostrar_detalle()
        self.assertIn("No tiene cuentas pendientes", self.pantalla.detalle.cget("text"))

    def test_la_ventana_principal_ya_no_dice_proximamente_en_clientes(self):
        principal = VentanaPrincipal(self.raiz, self.app)
        principal.mostrar("Clientes")
        self.assertIsInstance(principal.pantallas["Clientes"], PantallaClientes)


if __name__ == "__main__":
    unittest.main()

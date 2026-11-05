"""Pruebas de humo de la ventana Tkinter del punto de venta (tarea 8).

Abren la ventana oculta, llenan los campos y presionan los botones llamando a sus métodos.
Necesitan pantalla: si no la hay (por ejemplo en el CI de GitHub, que corre en Linux sin
pantalla), se SALTAN con skipTest y se cuentan como "skipped", no como aprobadas.
La lógica que importa ya está probada sin ventanas en test_presentador.py.
"""
import unittest

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.presentador import PresentadorPuntoDeVenta

try:
    import tkinter as tk
    from interfaz_tk.ventana_punto_de_venta import DialogoDeContado, DialogoDeCredito, VentanaPuntoDeVenta
except ImportError:                                   # Python sin Tkinter
    tk = None


class PruebasDeLaVentana(unittest.TestCase):
    def setUp(self):
        if tk is None:
            self.skipTest("Tkinter no está instalado")
        try:
            self.raiz = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"No hay pantalla para abrir ventanas: {error}")
        self.raiz.withdraw()
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz 500 g", 2000, 2500, 10)
        self.panela = self.app.productos.registrar_producto("Panela", 2000, 3000, 1)
        self.cliente = self.app.clientes.registrar_cliente("Cliente de prueba", True, 100000)
        self.ventana = VentanaPuntoDeVenta(self.raiz, PresentadorPuntoDeVenta(self.app))

    def tearDown(self):
        self.raiz.destroy()

    def agregar(self, nombre, cantidad="1"):
        self.ventana.texto_busqueda.set(nombre)
        self.ventana.cantidad.set(cantidad)
        self.ventana.agregar_seleccionado()

    def test_al_abrir_no_se_puede_cobrar_una_venta_vacia(self):
        self.assertEqual(str(self.ventana.boton_contado.cget("state")), "disabled")
        self.ventana.abrir_cobro_de_contado()                       # como si se presionara F9
        self.assertIsNone(self.ventana.dialogo)
        self.assertEqual(self.ventana.mensaje.cget("text"), "Agrega al menos un producto antes de cobrar")

    def test_buscar_y_agregar_actualiza_la_venta_y_el_total(self):
        self.ventana.texto_busqueda.set("arroz")
        self.assertEqual(len(self.ventana.resultados.get_children()), 1)
        self.agregar("arroz", "2")
        self.assertEqual(len(self.ventana.carrito.get_children()), 1)
        self.assertEqual(self.ventana.etiqueta_total.cget("text"), "$ 5.000")
        self.assertEqual(str(self.ventana.boton_contado.cget("state")), "normal")

    def test_cobro_de_contado_muestra_el_cambio_y_el_ticket(self):
        self.agregar("arroz", "2")
        self.ventana.abrir_cobro_de_contado()
        dialogo = self.ventana.dialogo
        self.assertIsInstance(dialogo, DialogoDeContado)
        dialogo.recibido.set("10000")
        self.assertEqual(dialogo.etiqueta_cambio.cget("text"), "Cambio: $ 5.000")
        dialogo.confirmar()
        self.assertIsNone(self.ventana.dialogo)
        self.assertIsNotNone(self.ventana.ventana_ticket)
        self.assertEqual(self.ventana.carrito.get_children(), ())
        self.assertEqual(self.app.numero_de_ventas(), 1)

    def test_si_el_dominio_rechaza_el_mensaje_se_ve_en_el_dialogo_y_se_puede_reintentar(self):
        self.agregar("panela", "3")                                  # solo hay 1
        self.ventana.abrir_cobro_de_contado()
        dialogo = self.ventana.dialogo
        dialogo.recibido.set("20000")
        dialogo.confirmar()
        self.assertIs(self.ventana.dialogo, dialogo)
        self.assertEqual(dialogo.etiqueta_error.cget("text"), "Solo hay 1 disponibles de Panela")
        self.assertEqual(str(dialogo.boton_confirmar.cget("state")), "normal")
        self.assertEqual(self.app.numero_de_ventas(), 0)

    def test_venta_a_credito_eligiendo_el_cliente(self):
        self.agregar("arroz", "1")
        self.ventana.abrir_venta_a_credito()                         # como si se presionara F4
        dialogo = self.ventana.dialogo
        self.assertIsInstance(dialogo, DialogoDeCredito)
        dialogo.selector.current(0)
        dialogo.mostrar_cliente()
        self.assertIn("Crédito disponible: $ 100.000", dialogo.etiqueta_cliente.cget("text"))
        dialogo.confirmar()
        self.assertIsNone(self.ventana.dialogo)
        self.assertEqual(len(self.app.credito.cuentas_del_cliente(self.cliente.id_cliente)), 1)


if __name__ == "__main__":
    unittest.main()

"""Pruebas de la pantalla Créditos y abonos en Tkinter (HU-06, RF-09; etapa 3 de la interfaz).

La lógica se prueba sin ventanas en test_presentador_creditos.py; aquí solo que la pantalla la use bien.
Necesitan pantalla: sin ella (CI de GitHub) se SALTAN. Datos ficticios.
"""
import unittest

from tiendas_sm.aplicacion import Aplicacion

try:
    import tkinter as tk
except ImportError:                                   # Python sin Tkinter: solo esto justifica saltar
    tk = None
if tk is not None:                                    # un módulo propio que falte SÍ debe hacer fallar la prueba
    from interfaz_tk.pantalla_creditos import PantallaCreditos
    from interfaz_tk.ventana_principal import VentanaPrincipal
    from tiendas_sm.presentador_creditos import PresentadorDeCreditos


class PruebasDeLaPantallaCreditos(unittest.TestCase):
    def setUp(self):
        if tk is None:
            self.skipTest("Tkinter no está instalado")
        try:
            self.raiz = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"No hay pantalla para abrir ventanas: {error}")
        self.raiz.withdraw()
        self.app = Aplicacion()
        mercado = self.app.productos.registrar_producto("Mercado ficticio", 20000, 25000, 10)
        ana = self.app.clientes.registrar_cliente("Cliente ficticio Ana", True, 200000)
        self.app.ventas.registrar_venta_a_credito(ana.id_cliente, [(mercado.id_producto, 2)])
        self.cuenta = str(self.app.credito.cuentas_del_cliente(ana.id_cliente)[0].id_cuenta)
        self.pantalla = PantallaCreditos(self.raiz, PresentadorDeCreditos(self.app))
        self.pantalla.mostrar()

    def tearDown(self):
        self.raiz.destroy()

    def elegir_cuenta(self):
        self.pantalla.tabla.selection_set(self.cuenta)
        self.pantalla.mostrar_detalle()

    def test_muestra_la_cuenta_abierta_y_el_resumen(self):
        self.assertEqual(self.pantalla.tabla.get_children(), (self.cuenta,))
        self.assertEqual(self.pantalla.etiqueta_resumen.cget("text"), "Por cobrar: $ 50.000 en 1 cuenta")

    def test_abonar_actualiza_el_saldo_y_limpia_el_monto(self):
        self.elegir_cuenta()
        self.pantalla.monto.set("20000")
        self.pantalla.abonar()
        self.assertEqual(self.pantalla.tabla.item(self.cuenta, "values")[1], "$ 30.000")
        self.assertIn("Saldo: $ 30.000", self.pantalla.mensaje.cget("text"))
        self.assertEqual(self.pantalla.monto.get(), "")
        self.assertIn("Abonado $ 20.000", self.pantalla.detalle.cget("text"))

    def test_abono_rechazado_conserva_el_monto_para_corregirlo(self):
        self.elegir_cuenta()
        self.pantalla.monto.set("60000")
        self.pantalla.abonar()
        self.assertIn("50000", self.pantalla.mensaje.cget("text"))
        self.assertEqual(self.pantalla.monto.get(), "60000")

    def test_al_pagar_todo_la_cuenta_sale_de_la_lista_de_abiertas(self):
        self.elegir_cuenta()
        self.pantalla.monto.set("50000")
        self.pantalla.abonar()
        self.assertEqual(self.pantalla.tabla.get_children(), ())
        self.pantalla.ver_pagadas.set(True)
        self.pantalla.refrescar()
        self.assertEqual(self.pantalla.tabla.item(self.cuenta, "values")[3], "Pagada")

    def test_sin_cuenta_elegida_avisa(self):
        self.pantalla.monto.set("1000")
        self.pantalla.abonar()
        self.assertEqual(self.pantalla.mensaje.cget("text"), "Elige una cuenta de la lista")

    def test_la_ventana_principal_abre_la_seccion(self):
        principal = VentanaPrincipal(self.raiz, self.app)
        principal.mostrar("Créditos y abonos")
        self.assertIsInstance(principal.pantallas["Créditos y abonos"], PantallaCreditos)


if __name__ == "__main__":
    unittest.main()

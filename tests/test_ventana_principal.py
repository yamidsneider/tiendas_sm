"""Pruebas de la ventana principal con menú lateral y del tema visual (interfaz, opción A).

El diseño sigue el borrador HTML del desarrollador (paleta verde, menú lateral), sin emojis. Necesitan
pantalla: sin ella (CI de GitHub) se SALTAN con skipTest y cuentan como "skipped", no como aprobadas.
"""
import unittest

from tiendas_sm.aplicacion import Aplicacion

try:
    import tkinter as tk
except ImportError:                                   # Python sin Tkinter: solo esto justifica saltar
    tk = None
if tk is not None:                                    # un módulo propio que falte SÍ debe hacer fallar la prueba
    from interfaz_tk.tema import PALETA, aplicar_tema
    from interfaz_tk.ventana_principal import SECCIONES, VentanaPrincipal

ULTIMO_CARACTER_LATINO = 0x024F                       # letras con tilde y ñ sí; emojis y símbolos no


class BaseConVentana(unittest.TestCase):
    def setUp(self):
        if tk is None:
            self.skipTest("Tkinter no está instalado")
        try:
            self.raiz = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"No hay pantalla para abrir ventanas: {error}")
        self.raiz.withdraw()

    def tearDown(self):
        self.raiz.destroy()


class PruebasDelTema(BaseConVentana):
    def test_la_paleta_es_la_del_borrador_html(self):
        self.assertEqual(PALETA["v900"], "#0a3b2a")
        self.assertEqual(PALETA["v600"], "#1f9d63")
        self.assertEqual(PALETA["fondo"], "#eef5f1")
        self.assertEqual(PALETA["rojo"], "#d64545")

    def test_aplicar_el_tema_usa_una_base_que_respeta_los_colores(self):
        estilo = aplicar_tema(self.raiz)
        self.assertEqual(estilo.theme_use(), "clam")       # el tema nativo de Windows ignora los colores
        self.assertEqual(estilo.lookup("Primario.TButton", "background"), PALETA["v600"])


class PruebasDeLaVentanaPrincipal(BaseConVentana):
    def setUp(self):
        super().setUp()
        self.app = Aplicacion()
        self.app.productos.registrar_producto("Arroz 500 g", 2000, 2500, 10)
        self.principal = VentanaPrincipal(self.raiz, self.app)

    def test_el_menu_tiene_las_seis_secciones_aprobadas_en_orden(self):
        self.assertEqual(SECCIONES, ("Punto de venta", "Ventas", "Productos", "Existencias", "Clientes",
                                     "Créditos y abonos"))
        self.assertEqual([boton.cget("text") for boton in self.principal.botones.values()], list(SECCIONES))

    def test_el_menu_no_usa_emojis(self):
        for seccion in SECCIONES:
            self.assertTrue(all(ord(letra) <= ULTIMO_CARACTER_LATINO for letra in seccion), seccion)

    def test_al_abrir_se_ve_el_punto_de_venta_marcado_en_el_menu(self):
        self.assertEqual(self.principal.seccion_actual, "Punto de venta")
        self.assertEqual(self.principal.pantallas["Punto de venta"].marco.winfo_manager(), "pack")
        self.assertEqual(self.principal.botones["Punto de venta"].cget("bg"), PALETA["v600"])
        self.assertEqual(self.principal.titulo.cget("text"), "Punto de venta")

    def test_cambiar_de_seccion_oculta_el_punto_de_venta(self):
        self.principal.mostrar("Ventas")                        # etapa 6: ya no queda ninguna «Próximamente»
        punto_de_venta = self.principal.pantallas["Punto de venta"]
        self.assertEqual(punto_de_venta.marco.winfo_manager(), "")
        self.assertFalse(punto_de_venta.activa)
        self.assertEqual(self.principal.pantallas["Ventas"].marco.winfo_manager(), "pack")
        self.assertEqual(self.principal.botones["Punto de venta"].cget("bg"), PALETA["v900"])

    def test_los_atajos_del_punto_de_venta_no_actuan_en_otra_seccion(self):
        punto_de_venta = self.principal.pantallas["Punto de venta"]
        llamadas = []
        atajo = punto_de_venta._si_activa(lambda: llamadas.append("F9"))
        self.principal.mostrar("Productos")
        atajo()
        self.assertEqual(llamadas, [])
        self.principal.mostrar("Punto de venta")
        atajo()
        self.assertEqual(llamadas, ["F9"])

    def test_volver_al_punto_de_venta_conserva_la_venta_en_curso(self):
        punto_de_venta = self.principal.pantallas["Punto de venta"]
        punto_de_venta.texto_busqueda.set("arroz")
        punto_de_venta.agregar_seleccionado()
        self.principal.mostrar("Ventas")
        self.principal.mostrar("Punto de venta")
        self.assertIs(self.principal.pantallas["Punto de venta"], punto_de_venta)
        self.assertEqual(len(punto_de_venta.carrito.get_children()), 1)


if __name__ == "__main__":
    unittest.main()

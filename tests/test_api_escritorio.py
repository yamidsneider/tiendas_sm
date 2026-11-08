"""Pruebas de la API que usa la página de la app de escritorio (opción B en DECISIONES).

La página (HTML + JavaScript) no tiene reglas: llama a estos métodos y muestra lo que devuelven. Aquí se prueba
que cada método use el presentador correcto y devuelva datos simples (listas, diccionarios, texto) que JavaScript
entienda. No abre ventanas ni necesita pywebview, así corre también en el CI. Se escribieron antes del código.
Datos ficticios.
"""
import threading
import unittest

from interfaz_web.api import ApiDeLaTienda, HiloDeLaBase
from tiendas_sm.aplicacion import Aplicacion


class BaseDeLaApi(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio 500 g", 2000, 2500, 20)
        self.ana = self.app.clientes.registrar_cliente("Cliente ficticio Ana", True, 100000, plazo_credito_dias=15)
        self.api = ApiDeLaTienda(self.app)


class PruebasDelPuntoDeVenta(BaseDeLaApi):
    def test_buscar_devuelve_productos_con_precio_y_disponibles(self):
        self.assertEqual(self.api.buscar("arroz"), [{"id": self.arroz.id_producto, "nombre": "Arroz ficticio 500 g",
                                                     "precio": "$ 2.500", "disponibles": 20}])
        self.assertEqual(self.api.buscar("   "), [])

    def test_agregar_devuelve_el_resultado_y_el_carrito_con_total(self):
        respuesta = self.api.agregar(self.arroz.id_producto, "3")
        self.assertTrue(respuesta["exito"])
        carrito = respuesta["carrito"]
        self.assertEqual((carrito["total"], carrito["resumen"], carrito["vacio"]), ("$ 7.500", "1 producto · 3 unidades", False))
        self.assertEqual(carrito["lineas"], [{"id": self.arroz.id_producto, "nombre": "Arroz ficticio 500 g",
                                              "precio": "$ 2.500", "cantidad": 3, "importe": "$ 7.500", "disponibles": 20}])

    def test_agregar_una_cantidad_invalida_muestra_el_mensaje(self):
        respuesta = self.api.agregar(self.arroz.id_producto, "cero")
        self.assertEqual((respuesta["exito"], respuesta["mensaje"]), (False, "La cantidad debe ser un número entero"))
        self.assertTrue(respuesta["carrito"]["vacio"])

    def test_quitar_y_limpiar(self):
        self.api.agregar(self.arroz.id_producto, "1")
        self.assertTrue(self.api.quitar(self.arroz.id_producto)["vacio"])
        self.api.agregar(self.arroz.id_producto, "1")
        self.assertTrue(self.api.limpiar()["vacio"])

    def test_cambio_mientras_se_escribe_lo_recibido(self):
        self.api.agregar(self.arroz.id_producto, "2")
        self.assertEqual(self.api.cambio("10000"), {"exito": True, "mensaje": "Cambio: $ 5.000", "ticket": None})
        self.assertFalse(self.api.cambio("1000")["exito"])

    def test_cobrar_de_contado_devuelve_el_ticket_y_vacia_el_carrito(self):
        self.api.agregar(self.arroz.id_producto, "2")
        respuesta = self.api.cobrar_de_contado("5000")
        self.assertTrue(respuesta["exito"])
        self.assertIn("TOTAL: $ 5.000", respuesta["ticket"])
        self.assertTrue(respuesta["carrito"]["vacio"])

    def test_venta_a_credito_y_clientes_para_elegir(self):
        clientes = self.api.clientes_para_credito()
        self.assertEqual([c["nombres"] for c in clientes], ["Cliente ficticio Ana"])
        self.assertIn("Crédito disponible: $ 100.000", clientes[0]["texto"])
        self.api.agregar(self.arroz.id_producto, "4")
        respuesta = self.api.vender_a_credito(self.ana.id_cliente)
        self.assertTrue(respuesta["exito"], respuesta["mensaje"])
        self.assertIn("Forma de pago: CRÉDITO", respuesta["ticket"])

    def test_el_stock_insuficiente_llega_con_el_mensaje_del_dominio(self):
        self.api.agregar(self.arroz.id_producto, "50")
        respuesta = self.api.cobrar_de_contado("999999")
        self.assertFalse(respuesta["exito"])
        self.assertIn("20", respuesta["mensaje"])
        self.assertFalse(respuesta["carrito"]["vacio"])          # la venta no se pierde: se puede corregir


class PruebasDeLasSecciones(BaseDeLaApi):
    def test_ventas_y_su_ticket(self):
        self.api.agregar(self.arroz.id_producto, "1")
        ticket = self.api.cobrar_de_contado("2500")["ticket"]
        (fila,) = self.api.ventas()
        self.assertEqual((fila["id"], fila["valores"][0], fila["valores"][2:]), (1, "#1", ["Contado", "—", "$ 2.500"]))
        self.assertEqual(self.api.ticket(1), ticket)

    def test_productos_registrar_y_cambiar_precio(self):
        self.assertTrue(self.api.registrar_producto("Panela ficticia", "2000", "3000", "5")["exito"])
        self.assertFalse(self.api.registrar_producto("", "2000", "3000", "5")["exito"])
        filas = self.api.productos("panela")
        self.assertEqual(filas[0]["valores"], ["Panela ficticia", "$ 2.000", "$ 3.000", 5])
        self.assertTrue(self.api.cambiar_precio(self.arroz.id_producto, "2700")["exito"])
        self.assertIn("$ 2.700", self.api.precio_actual(self.arroz.id_producto))

    def test_existencias_entrada_y_movimientos(self):
        respuesta = self.api.registrar_entrada(self.arroz.id_producto, "5")
        self.assertTrue(respuesta["exito"])
        self.assertEqual(self.api.existencias("arroz")[0]["valores"], ["Arroz ficticio 500 g", 25])
        self.assertEqual(self.api.movimientos()[0]["valores"][1:], ["Arroz ficticio 500 g", "Entrada", "+5"])
        self.assertFalse(self.api.registrar_entrada(None, "5")["exito"])

    def test_clientes_registrar_y_detalle(self):
        self.assertEqual(self.api.plazo_por_defecto(), "30")
        self.assertTrue(self.api.registrar_cliente("Cliente ficticio Beto", True, "50000", "30")["exito"])
        self.assertEqual([f["valores"][0] for f in self.api.clientes("beto")], ["Cliente ficticio Beto"])
        self.assertIn("No tiene cuentas pendientes", self.api.detalle_cliente(self.ana.id_cliente))

    def test_creditos_resumen_detalle_y_abono(self):
        self.api.agregar(self.arroz.id_producto, "4")
        self.api.vender_a_credito(self.ana.id_cliente)
        respuesta = self.api.creditos(False)
        self.assertEqual(respuesta["resumen"], "Por cobrar: $ 10.000 en 1 cuenta")
        id_cuenta = respuesta["filas"][0]["id"]
        self.assertIn("Saldo $ 10.000", self.api.detalle_credito(id_cuenta))
        self.assertTrue(self.api.abonar(id_cuenta, "10000")["exito"])
        self.assertEqual(self.api.creditos(False)["filas"], [])
        self.assertEqual(len(self.api.creditos(True)["filas"]), 1)


class PruebasDeLaConexionConLaVentana(unittest.TestCase):
    def test_la_ventana_no_ve_los_objetos_internos(self):
        """pywebview publica los atributos sin «_»; la API no debe dejar ver la app ni los presentadores."""
        api = ApiDeLaTienda(Aplicacion())
        self.assertEqual([nombre for nombre in vars(api) if not nombre.startswith("_")], [])

    def test_las_llamadas_desde_otros_hilos_usan_un_solo_hilo_para_la_base(self):
        """pywebview atiende cada llamada en un hilo distinto; SQLite solo acepta el hilo que abrió la conexión."""
        hilo = HiloDeLaBase()
        try:
            app = hilo.ejecutar(Aplicacion)
            hilo.ejecutar(lambda: app.productos.registrar_producto("Arroz ficticio", 2000, 2500, 3))
            api = ApiDeLaTienda(app, hilo.ejecutar)
            resultados = []
            otro = threading.Thread(target=lambda: resultados.append(api.productos("")))
            otro.start()
            otro.join()
            self.assertEqual(resultados[0][0]["valores"][0], "Arroz ficticio")
        finally:
            hilo.cerrar()

    def test_un_error_en_el_hilo_llega_a_quien_llamo(self):
        hilo = HiloDeLaBase()
        try:
            with self.assertRaises(ZeroDivisionError):
                hilo.ejecutar(lambda: 1 / 0)
        finally:
            hilo.cerrar()


if __name__ == "__main__":
    unittest.main()

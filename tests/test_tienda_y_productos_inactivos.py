"""Datos de la tienda en el ticket y desactivar productos (fase 6 de docs/HOJA_DE_RUTA_APP_COMPLETA.md).

*Preliminar (decisión del desarrollador sin respuesta del propietario, noviembre de 2026):*
- Datos de la tienda: nombre (obligatorio; por defecto «TIENDAS S.M»), NIT, dirección, teléfono y un mensaje al pie,
  todos opcionales menos el nombre. Salen arriba y abajo del ticket de 80 mm (42 caracteres por renglón). Solo el jefe.
- Desactivar un producto (no se borra, DT-08): no aparece en el punto de venta ni se puede vender, sale de «Por
  reponer», sigue en Productos y Existencias marcado «Inactivo» y en los reportes conserva su historia. Se puede activar.
Se escribieron antes del código. Datos ficticios.
"""
import unittest

from interfaz_web.api import ApiDeLaTienda
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import Permiso, Rol
from tiendas_sm.presentador import PresentadorPuntoDeVenta
from tiendas_sm.presentador_existencias import PresentadorDeExistencias
from tiendas_sm.presentador_tienda import PresentadorDeLaTienda

CLAVE = "clave-ficticia-1"


class BaseDeLaTienda(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio", 1000, 2000, 10, stock_minimo=20,
                                                          codigo="7700001")
        self.panela = self.app.productos.registrar_producto("Panela ficticia", 1000, 1500, 10)


class PruebasDeLosDatosDeLaTienda(BaseDeLaTienda):
    def test_por_defecto_el_nombre_es_tiendas_sm(self):
        datos = self.app.tienda.datos()
        self.assertEqual((datos.nombre, datos.nit, datos.direccion, datos.telefono, datos.mensaje),
                         ("TIENDAS S.M", "", "", "", ""))

    def test_guardar_y_leer(self):
        self.app.tienda.guardar("Tienda Doña Rosa ficticia", "900123456-7", "Calle 1 # 2-3", "300 000 0000", "Gracias")
        datos = self.app.tienda.datos()
        self.assertEqual((datos.nombre, datos.nit, datos.telefono), ("Tienda Doña Rosa ficticia", "900123456-7",
                                                                     "300 000 0000"))

    def test_el_nombre_es_obligatorio(self):
        with self.assertRaises(ValueError) as error:
            self.app.tienda.guardar("  ", "", "", "", "")
        self.assertEqual(str(error.exception), "Escribe el nombre de la tienda")

    def test_el_telefono_solo_lleva_numeros(self):
        with self.assertRaises(ValueError):
            self.app.tienda.guardar("Tienda ficticia", "", "", "tres cero cero", "")

    def test_el_encabezado_del_ticket_solo_lleva_lo_que_hay(self):
        self.app.tienda.guardar("Tienda ficticia", "900123456-7", "", "300 000 0000", "")
        self.assertEqual(self.app.tienda.encabezado_del_ticket(),
                         ["Tienda ficticia", "NIT: 900123456-7", "Tel: 300 000 0000"])

    def test_el_encabezado_cabe_en_80_mm(self):
        self.app.tienda.guardar("Tienda ficticia", "", "Carrera 45 número 123-456 barrio Los Almendros, al lado de la "
                                                       "panadería", "", "")
        self.assertTrue(all(len(linea) <= 42 for linea in self.app.tienda.encabezado_del_ticket()))

    def test_el_ticket_usa_los_datos_y_el_mensaje(self):
        self.app.tienda.guardar("Tienda ficticia", "", "Calle 1 # 2-3", "", "Gracias por su compra")
        punto = PresentadorPuntoDeVenta(self.app)
        punto.agregar(self.panela.id_producto, "1")
        ticket = punto.cobrar_de_contado("2000").ticket
        lineas = ticket.split("\n")
        self.assertEqual(lineas[:2], ["Tienda ficticia", "Calle 1 # 2-3"])
        self.assertEqual(lineas[-1], "Gracias por su compra")
        self.assertNotIn("TIENDAS S.M", ticket)

    def test_presentador_guarda_y_muestra(self):
        presentador = PresentadorDeLaTienda(self.app)
        self.assertFalse(presentador.guardar("", "", "", "", "").exito)
        resultado = presentador.guardar("Tienda ficticia", "", "", "", "")
        self.assertEqual((resultado.exito, resultado.mensaje), (True, "Datos de la tienda guardados"))
        self.assertEqual(presentador.datos()["nombre"], "Tienda ficticia")
        self.assertIn("Tienda ficticia", presentador.datos()["vista_previa"])


class PruebasDeDesactivar(BaseDeLaTienda):
    def test_un_producto_nuevo_esta_activo(self):
        self.assertTrue(self.app.productos.obtener(self.arroz.id_producto).activo)

    def test_desactivar_y_activar(self):
        self.app.productos.cambiar_estado(self.arroz.id_producto, False)
        self.assertFalse(self.app.productos.obtener(self.arroz.id_producto).activo)
        self.app.productos.cambiar_estado(self.arroz.id_producto, True)
        self.assertTrue(self.app.productos.obtener(self.arroz.id_producto).activo)

    def test_el_punto_de_venta_no_lo_encuentra_ni_por_nombre_ni_por_codigo(self):
        self.app.productos.cambiar_estado(self.arroz.id_producto, False)
        punto = PresentadorPuntoDeVenta(self.app)
        self.assertEqual(punto.buscar("arroz"), [])
        self.assertEqual(punto.buscar("7700001"), [])
        self.assertEqual([p.nombre for p in punto.buscar("ficti")], ["Panela ficticia"])

    def test_no_se_puede_vender_aunque_ya_estuviera_en_el_carrito(self):
        punto = PresentadorPuntoDeVenta(self.app)
        punto.agregar(self.arroz.id_producto, "1")
        self.app.productos.cambiar_estado(self.arroz.id_producto, False)
        resultado = punto.cobrar_de_contado("5000")
        self.assertEqual((resultado.exito, resultado.mensaje),
                         (False, "Arroz ficticio está desactivado: no se puede vender"))
        self.assertEqual(self.app.numero_de_ventas(), 0)

    def test_sale_de_por_reponer_pero_sigue_en_existencias(self):
        existencias = PresentadorDeExistencias(self.app)
        self.assertEqual([f[1][0] for f in existencias.por_reponer()], ["Arroz ficticio"])
        self.app.productos.cambiar_estado(self.arroz.id_producto, False)
        self.assertEqual(existencias.por_reponer(), [])
        self.assertIn("Arroz ficticio", [f[1][0] for f in existencias.tabla()])

    def test_editar_no_lo_vuelve_a_activar(self):
        self.app.productos.cambiar_estado(self.arroz.id_producto, False)
        self.app.productos.actualizar_producto(self.arroz.id_producto, "Arroz ficticio 1 kg", 1000, 2200)
        self.assertFalse(self.app.productos.obtener(self.arroz.id_producto).activo)

    def test_las_ventas_viejas_siguen_en_los_reportes(self):
        self.app.ventas.registrar_venta_de_contado([(self.arroz.id_producto, 1)], 2000)
        self.app.productos.cambiar_estado(self.arroz.id_producto, False)
        self.assertEqual([p.nombre for p in self.app.reportes.reporte("hoy").mas_vendidos], ["Arroz ficticio"])


class PruebasDeLaApi(BaseDeLaTienda):
    def setUp(self):
        super().setUp()
        self.app.usuarios.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE)
        self.app.usuarios.crear_usuario("Empleado ficticio", "pedro", Rol.EMPLEADO, CLAVE)
        self.api = ApiDeLaTienda(self.app)

    def test_solo_el_jefe_configura_la_tienda(self):
        self.assertFalse(Rol.EMPLEADO.puede(Permiso.CONFIGURAR_TIENDA))
        self.api.iniciar_sesion("pedro", CLAVE)
        self.assertEqual(self.api.guardar_datos_tienda("X", "", "", "", "")["mensaje"], "Solo el jefe puede hacer esto")
        self.assertEqual(self.api.activar_producto(self.arroz.id_producto, False)["mensaje"],
                         "Solo el jefe puede hacer esto")

    def test_el_jefe_guarda_los_datos_y_desactiva(self):
        self.api.iniciar_sesion("jefe", CLAVE)
        self.assertTrue(self.api.guardar_datos_tienda("Tienda ficticia", "", "", "", "")["exito"])
        self.assertEqual(self.api.datos_tienda()["nombre"], "Tienda ficticia")
        respuesta = self.api.activar_producto(self.arroz.id_producto, False)
        self.assertEqual((respuesta["exito"], respuesta["mensaje"]), (True, "Arroz ficticio desactivado"))
        filas = {f["valores"][0]: f["activo"] for f in self.api.productos("")}
        self.assertEqual(filas, {"Arroz ficticio": False, "Panela ficticia": True})


if __name__ == "__main__":
    unittest.main()

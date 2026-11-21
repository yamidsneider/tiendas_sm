"""Salida manual de mercancía (fase 3 de docs/HOJA_DE_RUTA_APP_COMPLETA.md; respuesta 4.4 del propietario).

Mercancía que sale sin venderse (dañada, vencida, consumo de la casa): baja las existencias con un movimiento
SALIDA_MANUAL que guarda el motivo, quién la registró, quién la autorizó y el precio de compra de ese momento
(para el reporte de pérdidas). Respuesta 4.4: «salida manual con clave del jefe». El jefe la registra directo; el
empleado solo si el jefe escribe ahí mismo su usuario y su clave.
*Preliminar (decisión del desarrollador, por confirmar con el propietario):* motivos Dañado, Vencido, Consumo propio y
Otro (con detalle obligatorio). Se escribieron antes del código. Datos ficticios.
"""
import unittest

from interfaz_web.api import ApiDeLaTienda
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import MotivoDeSalida, Permiso, Rol, texto_del_motivo
from tiendas_sm.presentador_existencias import PresentadorDeExistencias
from tiendas_sm.presentador_reportes import PresentadorDeReportes

CLAVE_JEFE = "clave-ficticia-1"
CLAVE_EMPLEADO = "clave-ficticia-2"


class BaseDeSalidas(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.leche = self.app.productos.registrar_producto("Leche ficticia", 3000, 4000, 10)
        self.jefe = self.app.usuarios.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE_JEFE)
        self.pedro = self.app.usuarios.crear_usuario("Empleado ficticio", "pedro", Rol.EMPLEADO, CLAVE_EMPLEADO)

    def stock(self):
        return self.app.cantidad_en_inventario(self.leche.id_producto)


class PruebasDelMotivo(unittest.TestCase):
    def test_los_motivos(self):
        self.assertEqual([m.value for m in MotivoDeSalida], ["Dañado", "Vencido", "Consumo propio", "Otro"])

    def test_otro_exige_el_detalle(self):
        with self.assertRaises(ValueError) as error:
            texto_del_motivo(MotivoDeSalida.OTRO, "  ")
        self.assertEqual(str(error.exception), "Escribe el detalle del motivo")
        self.assertEqual(texto_del_motivo(MotivoDeSalida.OTRO, "Se la comió el gato"), "Otro: Se la comió el gato")

    def test_el_detalle_es_opcional_en_los_demas(self):
        self.assertEqual(texto_del_motivo(MotivoDeSalida.DANADO, ""), "Dañado")
        self.assertEqual(texto_del_motivo(MotivoDeSalida.VENCIDO, "caja de abajo"), "Vencido: caja de abajo")

    def test_solo_el_jefe_tiene_el_permiso_de_salida(self):
        self.assertTrue(Rol.JEFE.puede(Permiso.REGISTRAR_SALIDA))
        self.assertFalse(Rol.EMPLEADO.puede(Permiso.REGISTRAR_SALIDA))


class PruebasDelServicio(BaseDeSalidas):
    def test_baja_las_existencias_y_deja_el_movimiento_con_su_motivo(self):
        self.app.productos.registrar_salida(self.leche.id_producto, 2, "Dañado", self.jefe.id_usuario, self.jefe.id_usuario)
        self.assertEqual(self.stock(), 8)
        movimiento = self.app.productos.movimientos()[0]
        self.assertEqual((movimiento.tipo, movimiento.cantidad, movimiento.motivo), ("SALIDA_MANUAL", 2, "Dañado"))

    def test_no_saca_mas_de_lo_que_hay(self):
        with self.assertRaises(ValueError) as error:
            self.app.productos.registrar_salida(self.leche.id_producto, 11, "Dañado", self.jefe.id_usuario,
                                                self.jefe.id_usuario)
        self.assertEqual(str(error.exception), "Solo hay 10 disponibles de Leche ficticia")
        self.assertEqual(self.stock(), 10)

    def test_guarda_quien_la_hizo_quien_autorizo_y_el_costo(self):
        self.app.productos.registrar_salida(self.leche.id_producto, 1, "Vencido", self.pedro.id_usuario,
                                            self.jefe.id_usuario)
        fila = self.app.conexion.execute("SELECT id_usuario, id_autorizo, costo_unitario FROM movimientos_inventario "
                                         "WHERE tipo = 'SALIDA_MANUAL'").fetchone()
        self.assertEqual(tuple(fila), (self.pedro.id_usuario, self.jefe.id_usuario, 3000))

    def test_cantidad_cero_no_se_acepta(self):
        with self.assertRaises(ValueError):
            self.app.productos.registrar_salida(self.leche.id_producto, 0, "Dañado", self.jefe.id_usuario,
                                                self.jefe.id_usuario)


class PruebasDeLaAutorizacion(BaseDeSalidas):
    def salida(self, quien, jefe="", clave="", motivo="Dañado", detalle=""):
        return PresentadorDeExistencias(self.app).registrar_salida(self.leche.id_producto, "2", motivo, detalle, quien,
                                                                   jefe, clave)

    def test_el_jefe_no_necesita_autorizacion(self):
        resultado = self.salida(self.jefe)
        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertEqual(resultado.mensaje, "Salida de 2 unidades de Leche ficticia (Dañado). Ahora hay 8")

    def test_el_empleado_sin_la_clave_del_jefe_no_puede(self):
        resultado = self.salida(self.pedro)
        self.assertEqual((resultado.exito, resultado.mensaje), (False, "Usuario o clave del jefe incorrectos"))
        self.assertEqual(self.stock(), 10)

    def test_la_clave_de_otro_empleado_no_autoriza(self):
        resultado = self.salida(self.pedro, "pedro", CLAVE_EMPLEADO)
        self.assertEqual((resultado.exito, resultado.mensaje), (False, "Usuario o clave del jefe incorrectos"))

    def test_el_empleado_con_la_clave_del_jefe_si_puede(self):
        self.assertTrue(self.salida(self.pedro, "jefe", CLAVE_JEFE).exito)
        self.assertEqual(self.stock(), 8)

    def test_motivo_desconocido(self):
        resultado = self.salida(self.jefe, motivo="Regalo")
        self.assertEqual((resultado.exito, resultado.mensaje), (False, "Elige el motivo de la salida"))

    def test_el_historial_dice_salida_manual_y_el_motivo(self):
        self.salida(self.jefe, motivo="Otro", detalle="Muestra para un cliente")
        fila = PresentadorDeExistencias(self.app).movimientos()[0][1]
        self.assertEqual(fila[2:], ("Salida manual (Otro: Muestra para un cliente)", "-2"))


class PruebasDelReporte(BaseDeSalidas):
    def test_el_reporte_muestra_las_salidas_al_costo(self):
        self.app.productos.registrar_salida(self.leche.id_producto, 2, "Vencido", self.jefe.id_usuario, self.jefe.id_usuario)
        self.assertIn(("Salidas de mercancía (al costo)", "$ 6.000"), PresentadorDeReportes(self.app).reporte("hoy")["formas"])


class PruebasDeLaApi(BaseDeSalidas):
    def test_el_empleado_registra_la_salida_con_la_clave_del_jefe(self):
        api = ApiDeLaTienda(self.app)
        api.iniciar_sesion("pedro", CLAVE_EMPLEADO)
        self.assertFalse(api.registrar_salida(self.leche.id_producto, "1", "Dañado", "", "", "")["exito"])
        respuesta = api.registrar_salida(self.leche.id_producto, "1", "Dañado", "", "jefe", CLAVE_JEFE)
        self.assertTrue(respuesta["exito"], respuesta["mensaje"])
        self.assertEqual(self.stock(), 9)

    def test_motivos_para_la_pantalla(self):
        api = ApiDeLaTienda(self.app)
        api.iniciar_sesion("jefe", CLAVE_JEFE)
        self.assertEqual(api.motivos_de_salida(), ["Dañado", "Vencido", "Consumo propio", "Otro"])


if __name__ == "__main__":
    unittest.main()

"""Caja: abrir turno con base y cerrarlo con arqueo (fase 4 de docs/HOJA_DE_RUTA_APP_COMPLETA.md, CR-02 caja).

Respuestas del desarrollador (21 de noviembre de 2026): la caja se abre al empezar el día escribiendo la base (cambia
cada día) y se cierra cuando haga falta o al final del día; se puede cerrar la app y dejar el turno abierto (queda en
la base de datos). Al cerrar se escribe lo contado, se muestra cuánto falta o sobra y se puede confirmar el cierre o
cancelar para contar de nuevo.
*Preliminar (decisión del desarrollador):* esperado en efectivo = base + ventas de contado en efectivo + abonos −
efectivo devuelto (los abonos se cuentan como efectivo: hoy no se registra cómo se pagaron). Jefe y empleado abren y
cierran; el historial de cierres es del jefe. Con la caja cerrada se puede vender, pero se avisa.
Se escribieron antes del código. Datos ficticios.
"""
import unittest
from datetime import datetime, timedelta

from interfaz_web.api import ApiDeLaTienda
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import Permiso, Rol
from tiendas_sm.presentador_caja import PresentadorDeCaja

CLAVE = "clave-ficticia-1"
MOTIVO = "Prueba"


class BaseDeCaja(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.caja = self.app.caja
        self.jefe = self.app.usuarios.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE)
        self.pedro = self.app.usuarios.crear_usuario("Empleado ficticio", "pedro", Rol.EMPLEADO, CLAVE)
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio", 1000, 2000, 50)
        self.ana = self.app.clientes.registrar_cliente("Cliente ficticia Ana", True, 100000)
        self.hace_un_rato = datetime.now() - timedelta(minutes=1)

    def abrir(self, base=50000):
        return self.caja.abrir(base, self.pedro.id_usuario, self.hace_un_rato)

    def mover_el_dia(self):
        """Efectivo 4.000 + mixto (1.000 efectivo, 1.000 transferencia) + fiado 2.000 + abono 1.500 + devolución 2.000."""
        contado = self.app.ventas.registrar_venta_de_contado([(self.arroz.id_producto, 2)], 4000)
        self.app.ventas.registrar_venta_de_contado([(self.arroz.id_producto, 1)], 1000, 1000)
        self.app.ventas.registrar_venta_a_credito(self.ana.id_cliente, [(self.arroz.id_producto, 1)])
        cuenta, = self.app.credito.cuentas_del_cliente(self.ana.id_cliente)
        self.app.credito.registrar_abono(cuenta.id_cuenta, 1500)
        self.app.ventas.devolver(contado.id_venta, [(self.arroz.id_producto, 1)], MOTIVO)


class PruebasDeAbrir(BaseDeCaja):
    def test_sin_abrir_no_hay_turno(self):
        self.assertIsNone(self.caja.turno_abierto())

    def test_abrir_con_la_base_del_dia(self):
        turno = self.abrir(80000)
        self.assertEqual((turno.base, turno.id_usuario_abre, turno.esta_abierto()), (80000, self.pedro.id_usuario, True))
        self.assertEqual(self.caja.turno_abierto().id_turno, turno.id_turno)

    def test_no_se_abren_dos_turnos(self):
        self.abrir()
        with self.assertRaises(ValueError) as error:
            self.abrir()
        self.assertIn("Ya hay una caja abierta", str(error.exception))

    def test_la_base_no_puede_ser_negativa(self):
        with self.assertRaises(ValueError) as error:
            self.abrir(-1)
        self.assertEqual(str(error.exception), "La base no puede ser negativa")

    def test_el_turno_sigue_abierto_al_volver_a_abrir_la_app(self):
        """Se puede cerrar la app sin cerrar el turno: queda guardado en la base."""
        turno = self.abrir()
        otra_vez = self.app.caja.__class__(self.caja.repo_caja, self.caja.repo_reportes)
        self.assertEqual(otra_vez.turno_abierto().id_turno, turno.id_turno)


class PruebasDelEsperado(BaseDeCaja):
    def test_esperado_suma_base_efectivo_y_abonos_y_resta_lo_devuelto(self):
        self.abrir(50000)
        self.mover_el_dia()
        detalle = self.caja.esperado()
        self.assertEqual((detalle.base, detalle.ventas_en_efectivo, detalle.abonos, detalle.efectivo_devuelto),
                         (50000, 5000, 1500, 2000))
        self.assertEqual(detalle.esperado, 50000 + 5000 + 1500 - 2000)

    def test_lo_de_antes_de_abrir_no_cuenta(self):
        self.app.ventas.registrar_venta_de_contado([(self.arroz.id_producto, 1)], 2000)
        self.caja.abrir(10000, self.pedro.id_usuario)
        self.assertEqual(self.caja.esperado().esperado, 10000)

    def test_sin_caja_abierta_no_hay_esperado(self):
        with self.assertRaises(ValueError) as error:
            self.caja.esperado()
        self.assertEqual(str(error.exception), "No hay una caja abierta")


class PruebasDelCierre(BaseDeCaja):
    def test_revisar_dice_cuanto_falta_sin_cerrar(self):
        self.abrir(50000)
        self.mover_el_dia()
        revision = self.caja.revisar_cierre(52000)
        self.assertEqual((revision.esperado, revision.contado, revision.diferencia), (54500, 52000, -2500))
        self.assertIsNotNone(self.caja.turno_abierto())                  # cancelar = contar de nuevo

    def test_cerrar_guarda_el_arqueo_y_deja_la_caja_cerrada(self):
        self.abrir(50000)
        self.mover_el_dia()
        turno = self.caja.cerrar(55000, self.jefe.id_usuario)
        self.assertEqual((turno.efectivo_esperado, turno.efectivo_contado, turno.diferencia), (54500, 55000, 500))
        self.assertEqual(turno.id_usuario_cierra, self.jefe.id_usuario)
        self.assertFalse(turno.esta_abierto())
        self.assertIsNone(self.caja.turno_abierto())
        self.assertEqual([t.id_turno for t in self.caja.historial()], [turno.id_turno])

    def test_no_se_cierra_sin_caja_abierta(self):
        with self.assertRaises(ValueError):
            self.caja.cerrar(1000, self.jefe.id_usuario)

    def test_lo_contado_no_puede_ser_negativo(self):
        self.abrir()
        with self.assertRaises(ValueError) as error:
            self.caja.revisar_cierre(-5)
        self.assertEqual(str(error.exception), "Lo contado no puede ser negativo")

    def test_despues_de_cerrar_se_abre_un_turno_nuevo(self):
        self.abrir(50000)
        self.caja.cerrar(50000, self.jefe.id_usuario)
        self.assertEqual(self.caja.abrir(30000, self.pedro.id_usuario).base, 30000)


class PruebasDeLosPermisos(unittest.TestCase):
    def test_los_dos_roles_manejan_la_caja(self):
        self.assertTrue(Rol.EMPLEADO.puede(Permiso.MANEJAR_CAJA))
        self.assertTrue(Rol.JEFE.puede(Permiso.MANEJAR_CAJA))


class PruebasDelPresentador(BaseDeCaja):
    def test_estado_con_la_caja_cerrada(self):
        self.assertEqual(PresentadorDeCaja(self.app).estado(), {"abierta": False})

    def test_estado_con_la_caja_abierta(self):
        self.abrir(50000)
        self.mover_el_dia()
        estado = PresentadorDeCaja(self.app).estado()
        self.assertTrue(estado["abierta"])
        self.assertEqual(estado["abrio"], "Empleado ficticio")
        self.assertEqual(estado["esperado"], "$ 54.500")
        self.assertEqual(estado["detalle"], [["Base", "$ 50.000"], ["Ventas en efectivo", "$ 5.000"],
                                             ["Abonos recibidos", "$ 1.500"], ["Efectivo devuelto", "-$ 2.000"]])

    def test_sin_devoluciones_no_muestra_menos_cero(self):
        self.abrir(10000)
        self.assertEqual(PresentadorDeCaja(self.app).estado()["detalle"][3], ["Efectivo devuelto", "$ 0"])

    def test_abrir_desde_la_pantalla(self):
        presentador = PresentadorDeCaja(self.app)
        self.assertFalse(presentador.abrir("cincuenta", self.pedro).exito)
        resultado = presentador.abrir("50000", self.pedro)
        self.assertEqual((resultado.exito, resultado.mensaje), (True, "Caja abierta con una base de $ 50.000"))

    def test_revisar_dice_falta_sobra_o_cuadra(self):
        self.abrir(50000)
        presentador = PresentadorDeCaja(self.app)
        self.assertEqual(presentador.revisar("48000")["mensaje"], "Faltan $ 2.000")
        self.assertEqual(presentador.revisar("50500")["mensaje"], "Sobran $ 500")
        self.assertEqual(presentador.revisar("50000")["mensaje"], "La caja cuadra")
        self.assertFalse(presentador.revisar("")["exito"])

    def test_cerrar_desde_la_pantalla(self):
        self.abrir(50000)
        resultado = PresentadorDeCaja(self.app).cerrar("48000", self.jefe)
        self.assertEqual((resultado.exito, resultado.mensaje), (True, "Caja cerrada. Faltan $ 2.000"))

    def test_historial_de_cierres(self):
        self.abrir(50000)
        self.caja.cerrar(48000, self.jefe.id_usuario)
        _, fila = PresentadorDeCaja(self.app).historial()[0]
        self.assertEqual(fila[2:], ("Empleado ficticio", "Jefe ficticio", "$ 50.000", "$ 50.000", "$ 48.000",
                                    "Faltan $ 2.000"))


class PruebasDeLaApi(BaseDeCaja):
    def test_el_empleado_abre_revisa_y_cierra(self):
        api = ApiDeLaTienda(self.app)
        api.iniciar_sesion("pedro", CLAVE)
        self.assertFalse(api.estado_caja()["abierta"])
        self.assertTrue(api.abrir_caja("20000")["exito"])
        self.assertEqual(api.revisar_cierre("20000")["mensaje"], "La caja cuadra")
        self.assertTrue(api.cerrar_caja("20000")["exito"])
        self.assertFalse(api.estado_caja()["abierta"])

    def test_el_historial_es_del_jefe(self):
        api = ApiDeLaTienda(self.app)
        api.iniciar_sesion("pedro", CLAVE)
        self.assertEqual(api.historial_caja()["mensaje"], "Solo el jefe puede hacer esto")
        api.cerrar_sesion()
        api.iniciar_sesion("jefe", CLAVE)
        self.assertEqual(api.historial_caja(), [])


if __name__ == "__main__":
    unittest.main()

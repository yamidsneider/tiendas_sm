"""Respaldos en una carpeta del PC y restaurar desde la app (fase 5 de docs/HOJA_DE_RUTA_APP_COMPLETA.md).

Respuesta del desarrollador (21 de noviembre de 2026): la copia se guarda en una carpeta del mismo PC.
Por defecto Documentos\\TIENDAS_SM respaldos (la pone iniciar_tienda.py); el jefe la puede cambiar. Se copia al cerrar la
app, al cerrar la caja (respuesta 5.2: «respaldo al cerrar turno») y con «Respaldar ahora». Cada copia se revisa antes
(integrity_check) y se conservan las 30 más recientes. Restaurar (solo el jefe) revisa el archivo, guarda antes una copia
«antes_de_restaurar» del estado actual y cierra la sesión (los usuarios pueden haber cambiado).
Todo con carpetas temporales y datos ficticios. Se escribieron antes del código.
"""
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from interfaz_web.api import ApiDeLaTienda
from iniciar_tienda import cerrar_y_respaldar
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import Permiso, Rol
from tiendas_sm.respaldo import RESPALDOS_EN_LA_CARPETA

CLAVE = "clave-ficticia-1"
AHORA = datetime(2026, 11, 21, 20, 15, 30)


class BaseDeRespaldos(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.carpeta = Path(self.temporal.name) / "respaldos"
        self.app = Aplicacion(carpeta_de_respaldos=self.carpeta)
        self.respaldos = self.app.respaldos
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio", 1000, 2000, 10)

    def tearDown(self):
        self.app.conexion.close()
        self.temporal.cleanup()

    def vender(self):
        return self.app.ventas.registrar_venta_de_contado([(self.arroz.id_producto, 1)], 2000)


class PruebasDeLaCarpeta(BaseDeRespaldos):
    def test_usa_la_carpeta_por_defecto(self):
        self.assertEqual(self.respaldos.carpeta(), self.carpeta)

    def test_sin_carpeta_no_hay_respaldo(self):
        app = Aplicacion()
        self.assertIsNone(app.respaldos.carpeta())
        with self.assertRaises(ValueError) as error:
            app.respaldos.respaldar_ahora()
        self.assertEqual(str(error.exception), "Elija primero la carpeta de los respaldos")

    def test_el_jefe_cambia_la_carpeta_y_se_crea(self):
        nueva = Path(self.temporal.name) / "otra" / "carpeta"
        self.respaldos.cambiar_carpeta(str(nueva))
        self.assertEqual(self.respaldos.carpeta(), nueva)
        self.assertTrue(nueva.is_dir())

    def test_la_carpeta_debe_ser_una_ruta_completa(self):
        for mala in ("", "   ", "respaldos"):
            with self.subTest(carpeta=mala), self.assertRaises(ValueError) as error:
                self.respaldos.cambiar_carpeta(mala)
            self.assertIn("ruta completa", str(error.exception))


class PruebasDeRespaldar(BaseDeRespaldos):
    def test_respaldar_ahora_crea_una_copia_con_las_ventas(self):
        self.vender()
        archivo = self.respaldos.respaldar_ahora(AHORA)
        self.assertEqual(archivo, self.carpeta / "respaldo_2026-11-21T201530.db")
        copia = Aplicacion(str(archivo))
        self.assertEqual(copia.numero_de_ventas(), 1)
        copia.conexion.close()

    def test_conserva_solo_los_mas_recientes(self):
        for minuto in range(RESPALDOS_EN_LA_CARPETA + 3):
            self.respaldos.respaldar_ahora(datetime(2026, 11, 21, 8, minuto))
        archivos = sorted(self.carpeta.glob("respaldo_*.db"))
        self.assertEqual(len(archivos), RESPALDOS_EN_LA_CARPETA)
        self.assertEqual(archivos[0].name, "respaldo_2026-11-21T080300.db")

    def test_lista_los_respaldos_del_mas_nuevo_al_mas_viejo(self):
        self.respaldos.respaldar_ahora(datetime(2026, 11, 20, 9, 0))
        self.respaldos.respaldar_ahora(datetime(2026, 11, 21, 9, 0))
        self.assertEqual([r.nombre for r in self.respaldos.listar()],
                         ["respaldo_2026-11-21T090000.db", "respaldo_2026-11-20T090000.db"])

    def test_al_cerrar_la_app_tambien_copia_a_la_carpeta(self):
        ruta = Path(self.temporal.name) / "tienda.db"
        app = Aplicacion(str(ruta), carpeta_de_respaldos=self.carpeta)
        app.productos.registrar_producto("Panela ficticia", 1000, 1500, 3)
        cerrar_y_respaldar(app, ruta)
        self.assertEqual(len(list(self.carpeta.glob("respaldo_*.db"))), 1)


class PruebasDeRestaurar(BaseDeRespaldos):
    def test_restaurar_vuelve_al_estado_del_respaldo(self):
        self.vender()
        nombre = self.respaldos.respaldar_ahora(AHORA).name
        self.vender()
        self.assertEqual(self.app.numero_de_ventas(), 2)
        self.respaldos.restaurar(nombre, datetime(2026, 11, 21, 21, 0))
        self.assertEqual(self.app.numero_de_ventas(), 1)

    def test_antes_de_restaurar_guarda_el_estado_actual(self):
        nombre = self.respaldos.respaldar_ahora(AHORA).name
        self.vender()
        self.respaldos.restaurar(nombre, datetime(2026, 11, 21, 21, 0))
        seguridad = self.carpeta / "antes_de_restaurar_2026-11-21T210000.db"
        self.assertTrue(seguridad.exists())
        copia = Aplicacion(str(seguridad))
        self.assertEqual(copia.numero_de_ventas(), 1)
        copia.conexion.close()

    def test_no_restaura_un_archivo_danado(self):
        danado = self.carpeta / "respaldo_2026-01-01T000000.db"
        self.carpeta.mkdir(parents=True, exist_ok=True)
        danado.write_bytes(b"esto no es una base de datos" * 200)
        with self.assertRaises(ValueError) as error:
            self.respaldos.restaurar(danado.name)
        self.assertEqual(str(error.exception), "Ese respaldo está dañado o no es de TIENDAS S.M; elija otro")

    def test_solo_restaura_archivos_de_la_lista(self):
        for nombre in ("../tienda.db", "C:\\otra\\base.db", "cualquier.db"):
            with self.subTest(nombre=nombre), self.assertRaises(ValueError) as error:
                self.respaldos.restaurar(nombre)
            self.assertEqual(str(error.exception), "Ese respaldo no está en la carpeta")


class PruebasDeLaApi(BaseDeRespaldos):
    def setUp(self):
        super().setUp()
        self.app.usuarios.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE)
        self.app.usuarios.crear_usuario("Empleado ficticio", "pedro", Rol.EMPLEADO, CLAVE)
        self.api = ApiDeLaTienda(self.app)

    def test_solo_el_jefe_maneja_los_respaldos(self):
        self.assertFalse(Rol.EMPLEADO.puede(Permiso.GESTIONAR_RESPALDOS))
        self.api.iniciar_sesion("pedro", CLAVE)
        self.assertEqual(self.api.respaldar_ahora()["mensaje"], "Solo el jefe puede hacer esto")

    def test_el_jefe_respalda_y_ve_la_lista(self):
        self.api.iniciar_sesion("jefe", CLAVE)
        respuesta = self.api.respaldar_ahora()
        self.assertTrue(respuesta["exito"], respuesta["mensaje"])
        self.assertIn("Respaldo guardado en", respuesta["mensaje"])
        datos = self.api.respaldos()
        self.assertEqual(datos["carpeta"], str(self.carpeta))
        self.assertEqual(len(datos["filas"]), 1)

    def test_cerrar_la_caja_hace_un_respaldo(self):
        self.api.iniciar_sesion("pedro", CLAVE)
        self.api.abrir_caja("10000")
        respuesta = self.api.cerrar_caja("10000")
        self.assertTrue(respuesta["exito"])
        self.assertIn("Respaldo guardado", respuesta["mensaje"])
        self.assertEqual(len(list(self.carpeta.glob("respaldo_*.db"))), 1)

    def test_restaurar_cierra_la_sesion(self):
        self.api.iniciar_sesion("jefe", CLAVE)
        self.assertEqual(self.api.respaldos()["filas"], [])
        self.api.respaldar_ahora()
        nombre = self.api.respaldos()["filas"][0]["id"]
        respuesta = self.api.restaurar_respaldo(nombre)
        self.assertTrue(respuesta["exito"], respuesta["mensaje"])
        self.assertIsNone(respuesta["estado"]["usuario"])
        self.assertIsNone(self.api.estado_sesion()["usuario"])


if __name__ == "__main__":
    unittest.main()

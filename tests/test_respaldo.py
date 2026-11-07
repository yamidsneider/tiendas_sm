"""FPI-30 (ADR-14, INC-SIM-01): respaldo automático verificado al cerrar y revisión de integridad al abrir.

Causa raíz del simulacro: el respaldo era manual y nadie revisaba la base al arrancar. Todo se prueba con
archivos temporales y datos ficticios. La base dañada se fabrica como en el simulacro: basura en la página 2.
"""
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime
from pathlib import Path

from iniciar_tienda import cerrar_y_respaldar
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.respaldo import (MENSAJE_BASE_DANADA, RESPALDOS_A_CONSERVAR, respaldar, revisar_al_abrir,
                                 revisar_integridad)
from tiendas_sm.telemetria import Telemetria

TAMANO_DE_PAGINA = 4096
AHORA = datetime(2026, 11, 6, 21, 30)


def crear_base_con_ventas(ruta, ventas=3):
    app = Aplicacion(str(ruta))
    producto = app.productos.registrar_producto("Producto ficticio", 1000, 1500, 20)
    for _ in range(ventas):
        app.ventas.registrar_venta_de_contado([(producto.id_producto, 1)], 2000)
    app.conexion.close()


def danar_pagina_2(ruta):
    with open(ruta, "r+b") as archivo:
        archivo.seek(TAMANO_DE_PAGINA)
        archivo.write(b"\x00\xff" * (TAMANO_DE_PAGINA // 2))


def contar_ventas(ruta):
    with closing(sqlite3.connect(ruta)) as conexion:
        return conexion.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]


class BaseTemporal(unittest.TestCase):
    def setUp(self):
        self.carpeta_temporal = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.carpeta = Path(self.carpeta_temporal.name)
        self.base = self.carpeta / "tiendas_sm.db"
        self.lineas = []
        self.telemetria = Telemetria(escribir=self.lineas.append, tasa_muestreo=0.0)

    def tearDown(self):
        self.carpeta_temporal.cleanup()

    def respaldos(self):
        return sorted(p.name for p in self.carpeta.glob("respaldo_*.db"))

    def errores_registrados(self):
        return [json.loads(linea)["error.tipo"] for linea in self.lineas]


class PruebasDeLaRevisionDeIntegridad(BaseTemporal):
    def test_base_sana_da_ok(self):
        crear_base_con_ventas(self.base)
        self.assertEqual(revisar_integridad(self.base), "ok")
        self.assertEqual(revisar_integridad(self.base, "integrity_check"), "ok")

    def test_base_con_la_pagina_2_danada_no_da_ok(self):
        crear_base_con_ventas(self.base)
        danar_pagina_2(self.base)
        self.assertNotEqual(revisar_integridad(self.base), "ok")
        self.assertNotEqual(revisar_integridad(self.base, "integrity_check"), "ok")

    def test_solo_acepta_las_dos_revisiones_de_sqlite(self):
        with self.assertRaises(ValueError):
            revisar_integridad(self.base, "DROP TABLE ventas")


class PruebasDelRespaldoAlCerrar(BaseTemporal):
    def test_base_sana_se_respalda_en_la_misma_carpeta_con_fecha_y_hora(self):
        crear_base_con_ventas(self.base, ventas=3)
        destino = respaldar(self.base, self.telemetria, ahora=AHORA)
        self.assertEqual(destino, self.carpeta / "respaldo_2026-11-06T2130.db")
        self.assertEqual(revisar_integridad(destino, "integrity_check"), "ok")
        self.assertEqual(contar_ventas(destino), 3)

    def test_conserva_solo_los_7_respaldos_mas_recientes(self):
        crear_base_con_ventas(self.base)
        for dia in range(1, 9):                                   # 8 respaldos viejos: del 1 al 8 de octubre
            (self.carpeta / f"respaldo_2026-10-{dia:02d}T2100.db").write_bytes(b"")
        otro = self.carpeta / "tiendas_sm.db.danado_2026-10-01T0900"
        otro.write_bytes(b"")                                     # un archivo que no es respaldo: no se toca
        respaldar(self.base, self.telemetria, ahora=AHORA)
        self.assertEqual(len(self.respaldos()), RESPALDOS_A_CONSERVAR)
        self.assertEqual(self.respaldos()[-1], "respaldo_2026-11-06T2130.db")
        self.assertNotIn("respaldo_2026-10-01T2100.db", self.respaldos())
        self.assertTrue(otro.exists())
        self.assertTrue(self.base.exists())

    def test_base_danada_no_se_respalda_y_queda_en_la_telemetria(self):
        crear_base_con_ventas(self.base)
        danar_pagina_2(self.base)
        self.assertIsNone(respaldar(self.base, self.telemetria, ahora=AHORA))
        self.assertEqual(self.respaldos(), [])
        self.assertEqual(self.errores_registrados(), ["BaseDeDatosDanada"])

    def test_sin_base_no_crea_nada(self):
        self.assertIsNone(respaldar(self.base, self.telemetria, ahora=AHORA))
        self.assertEqual(list(self.carpeta.iterdir()), [])


class PruebasDeLaRevisionAlAbrir(BaseTemporal):
    def test_base_sana_se_abre_sin_mensaje(self):
        crear_base_con_ventas(self.base)
        self.assertIsNone(revisar_al_abrir(self.base, self.telemetria))

    def test_base_nueva_que_aun_no_existe_se_abre_y_no_se_crea_al_revisar(self):
        self.assertIsNone(revisar_al_abrir(self.base, self.telemetria))
        self.assertFalse(self.base.exists())

    def test_base_danada_da_el_mensaje_del_runbook_y_queda_en_la_telemetria(self):
        crear_base_con_ventas(self.base)
        danar_pagina_2(self.base)
        mensaje = revisar_al_abrir(self.base, self.telemetria)
        self.assertEqual(mensaje, MENSAJE_BASE_DANADA)
        self.assertIn("No venda en el sistema", mensaje)
        self.assertIn("Runbook", mensaje)
        self.assertEqual(self.errores_registrados(), ["BaseDeDatosDanada"])


class PruebasDelCierreDeLaAplicacion(BaseTemporal):
    def test_al_cerrar_se_cierra_la_conexion_y_se_respalda(self):
        crear_base_con_ventas(self.base, ventas=2)
        app = Aplicacion(str(self.base))
        destino = cerrar_y_respaldar(app, self.base, self.telemetria, ahora=AHORA)
        with self.assertRaises(sqlite3.ProgrammingError):        # la conexión de la aplicación quedó cerrada
            app.conexion.execute("SELECT 1")
        self.assertEqual(contar_ventas(destino), 2)


if __name__ == "__main__":
    unittest.main()

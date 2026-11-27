"""Lotes ligados al inventario con FEFO (fase 9 de docs/HOJA_DE_RUTA_APP_COMPLETA.md; DT-01; cambia la decisión del grupo B).

Respuestas del desarrollador (26 de noviembre de 2026): al vender se descuenta primero el lote que vence antes (FEFO), y a
la mercancía que entra sin lote se le asigna uno manualmente.
- Cada lote tiene un saldo (unidades que le quedan). «Sin lote» = existencias − saldos de los lotes activos.
- Vender y la salida manual descuentan FEFO; si los lotes no alcanzan, el resto sale de lo «sin lote». Un lote en 0 sale
  de la lista solo.
- Asignar lote: toma unidades sin lote; no cambia las existencias. Una entrada con fecha de vencimiento ya entra como lote.
- Compras, entradas sin fecha y devoluciones quedan «sin lote» hasta que se les asigne uno (*preliminar*).
- «Ya no está» solo con el lote sin unidades. Base vieja: los lotes reciben saldo por orden de vencimiento hasta donde
  alcancen las existencias.
Se escribieron antes del código. Datos ficticios.
"""
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from interfaz_web.api import ApiDeLaTienda
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import Lote, tomar_fefo
from tiendas_sm.presentador_existencias import PresentadorDeExistencias

HOY = date.today()
CLAVE = "clave-ficticia-1"


def dentro_de(dias):
    return HOY + timedelta(days=dias)


class PruebasDeLaReglaFefo(unittest.TestCase):
    def test_toma_primero_el_que_vence_antes_y_devuelve_lo_que_falta(self):
        tarde, pronto = Lote(1, 1, "B", dentro_de(20), 5), Lote(2, 1, "A", dentro_de(3), 4)
        falta = tomar_fefo([tarde, pronto], 7)
        self.assertEqual((pronto.saldo, tarde.saldo, falta), (0, 2, 0))
        self.assertFalse(pronto.activo)                     # quedó en 0: sale de la lista
        self.assertTrue(tarde.activo)

    def test_si_los_lotes_no_alcanzan_el_resto_es_sin_lote(self):
        lote = Lote(1, 1, "A", dentro_de(3), 2)
        self.assertEqual(tomar_fefo([lote], 5), 3)
        self.assertEqual(lote.saldo, 0)

    def test_un_lote_nuevo_empieza_con_todo_su_saldo(self):
        self.assertEqual(Lote(None, 1, "A", dentro_de(3), 6).saldo, 6)


class BaseDeLotes(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.leche = self.app.productos.registrar_producto("Leche ficticia", 2000, 2800, 10, dias_aviso=5)
        self.existencias = PresentadorDeExistencias(self.app)

    def lote(self, numero, dias, cantidad):
        return self.app.productos.registrar_lote(self.leche.id_producto, numero, dentro_de(dias), cantidad)

    def saldos(self):
        return {lote.numero: lote.saldo for lote in self.app.productos.lotes_activos()}

    def sin_lote(self):
        return self.app.productos.unidades_sin_lote(self.leche.id_producto)


class PruebasDeAsignarLote(BaseDeLotes):
    def test_al_principio_todo_esta_sin_lote(self):
        self.assertEqual(self.sin_lote(), 10)

    def test_asignar_lote_toma_unidades_sin_lote_y_no_cambia_existencias(self):
        self.lote("L-1", 5, 6)
        self.assertEqual((self.sin_lote(), self.app.cantidad_en_inventario(self.leche.id_producto)), (4, 10))

    def test_no_se_asigna_mas_de_lo_que_hay_sin_lote(self):
        self.lote("L-1", 5, 6)
        with self.assertRaises(ValueError) as error:
            self.lote("L-2", 9, 5)
        self.assertEqual(str(error.exception), "Solo hay 4 unidades sin lote de Leche ficticia")

    def test_entrada_con_fecha_entra_como_lote(self):
        self.app.productos.registrar_entrada(self.leche.id_producto, 12, "L-9", dentro_de(15))
        self.assertEqual(self.app.cantidad_en_inventario(self.leche.id_producto), 22)
        self.assertEqual((self.saldos(), self.sin_lote()), ({"L-9": 12}, 10))

    def test_entrada_sin_fecha_queda_sin_lote(self):
        self.app.productos.registrar_entrada(self.leche.id_producto, 5)
        self.assertEqual((self.saldos(), self.sin_lote()), ({}, 15))


class PruebasDelDescuentoAlVender(BaseDeLotes):
    def vender(self, cantidad):
        return self.app.ventas.registrar_venta_de_contado([(self.leche.id_producto, cantidad)], 2800 * cantidad)

    def test_la_venta_descuenta_primero_el_lote_que_vence_antes(self):
        self.lote("TARDE", 20, 4)
        self.lote("PRONTO", 3, 3)
        self.vender(5)
        self.assertEqual(self.saldos(), {"TARDE": 2})                        # PRONTO quedó en 0 y salió
        self.assertEqual((self.sin_lote(), self.app.cantidad_en_inventario(self.leche.id_producto)), (3, 5))

    def test_si_los_lotes_se_acaban_vende_de_lo_sin_lote(self):
        self.lote("L-1", 3, 2)
        self.vender(5)
        self.assertEqual((self.saldos(), self.sin_lote()), ({}, 5))

    def test_la_salida_manual_tambien_descuenta_fefo(self):
        jefe = self.app.usuarios.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE)
        self.lote("VENCIDO", -1, 3)
        self.lote("BUENO", 30, 3)
        self.app.productos.registrar_salida(self.leche.id_producto, 3, "Vencido", jefe.id_usuario, jefe.id_usuario)
        self.assertEqual(self.saldos(), {"BUENO": 3})

    def test_la_devolucion_vuelve_sin_lote(self):
        self.lote("L-1", 3, 4)
        venta = self.vender(2)
        self.app.ventas.devolver(venta.id_venta, [(self.leche.id_producto, 2)], "Prueba")
        self.assertEqual((self.saldos(), self.sin_lote()), ({"L-1": 2}, 8))

    def test_una_compra_queda_sin_lote(self):
        proveedor = self.app.compras.registrar_proveedor("Proveedor ficticio")
        jefe = self.app.usuarios.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE)
        self.app.compras.registrar_compra(proveedor.id_proveedor, [(self.leche.id_producto, 6, 2000)], jefe.id_usuario)
        self.assertEqual(self.sin_lote(), 16)


class PruebasDeYaNoEsta(BaseDeLotes):
    def test_con_unidades_no_se_quita(self):
        lote = self.lote("L-1", 3, 4)
        with self.assertRaises(ValueError) as error:
            self.app.productos.retirar_lote(lote.id_lote)
        self.assertEqual(str(error.exception),
                         "Al lote L-1 le quedan 4 unidades: véndalas o regístrelas como salida")


class PruebasDelPresentadorYLaApi(BaseDeLotes):
    def test_la_lista_muestra_el_saldo(self):
        self.lote("L-1", 3, 6)
        self.app.ventas.registrar_venta_de_contado([(self.leche.id_producto, 2)], 5600)
        self.assertEqual(self.existencias.lotes()[0][1][3], 4)

    def test_sin_lote_por_producto(self):
        self.lote("L-1", 3, 6)
        self.assertEqual(self.existencias.sin_lote(), {self.leche.id_producto: 4})

    def test_entrada_con_lote_desde_el_formulario(self):
        fecha = dentro_de(10)
        resultado = self.existencias.registrar_entrada(self.leche.id_producto, "5", "L-5", fecha.isoformat())
        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertIn(f"lote L-5 (vence el {fecha:%d/%m/%Y})", resultado.mensaje)
        self.assertEqual(self.saldos(), {"L-5": 5})

    def test_entrada_con_fecha_mal_escrita(self):
        resultado = self.existencias.registrar_entrada(self.leche.id_producto, "5", "L-5", "31-02-2027")
        self.assertEqual((resultado.exito, resultado.mensaje), (False, "La fecha de vencimiento no es válida"))
        self.assertEqual(self.app.cantidad_en_inventario(self.leche.id_producto), 10)

    def test_la_api_dice_cuanto_hay_sin_lote(self):
        self.app.usuarios.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE)
        api = ApiDeLaTienda(self.app)
        api.iniciar_sesion("jefe", CLAVE)
        self.lote("L-1", 3, 6)
        fila, = api.existencias("leche")
        self.assertEqual(fila["sin_lote"], 4)
        self.assertTrue(api.registrar_entrada(self.leche.id_producto, "2", "L-2", dentro_de(9).isoformat())["exito"])
        self.assertEqual(self.saldos(), {"L-1": 6, "L-2": 2})


class PruebasDeLaMigracion(unittest.TestCase):
    def test_los_lotes_viejos_reciben_saldo_hasta_donde_alcanzan_las_existencias(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as carpeta:
            ruta = str(Path(carpeta) / "vieja.db")
            app = Aplicacion(ruta)
            leche = app.productos.registrar_producto("Leche ficticia", 2000, 2800, 10)
            app.conexion.close()
            conexion = sqlite3.connect(ruta)                       # como la base de antes: lotes sin saldo
            conexion.executescript("""
                ALTER TABLE lotes RENAME TO lotes_nuevos;
                CREATE TABLE lotes (id_lote INTEGER PRIMARY KEY AUTOINCREMENT, id_producto INTEGER NOT NULL,
                    numero TEXT NOT NULL DEFAULT '', fecha_vencimiento TEXT NOT NULL, cantidad INTEGER NOT NULL,
                    activo INTEGER NOT NULL DEFAULT 1);
                DROP TABLE lotes_nuevos;""")
            with conexion:
                conexion.executemany(
                    "INSERT INTO lotes (id_producto, numero, fecha_vencimiento, cantidad) VALUES (?,?,?,?)",
                    [(leche.id_producto, "TARDE", dentro_de(30).isoformat(), 8),
                     (leche.id_producto, "PRONTO", dentro_de(2).isoformat(), 6),
                     (leche.id_producto, "SOBRA", dentro_de(60).isoformat(), 5)])
            conexion.close()
            app = Aplicacion(ruta)
            saldos = {lote.numero: lote.saldo for lote in app.productos.lotes_activos()}
            self.assertEqual(saldos, {"PRONTO": 6, "TARDE": 4})             # 6 + 4 = 10 existencias; SOBRA queda en 0
            self.assertEqual(app.productos.unidades_sin_lote(leche.id_producto), 0)
            app.conexion.close()
            app = Aplicacion(ruta)                                           # abrirla otra vez no repite el reparto
            self.assertEqual({lote.numero: lote.saldo for lote in app.productos.lotes_activos()}, saldos)
            app.conexion.close()


if __name__ == "__main__":
    unittest.main()

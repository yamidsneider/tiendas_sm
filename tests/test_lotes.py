"""Lotes con fecha de vencimiento y sus avisos (RF-10, RF-13; respuestas del propietario, grupo B).

Fase 9 (cambia la decisión del grupo B): el lote ya está ligado al inventario (ver test_lotes_fefo.py). Registrar un
lote es asignárselo a unidades que estaban sin lote: no cambia las existencias, pero no puede pasar de lo que hay
sin lote. Cada producto tiene sus días de aviso. La lista sale ordenada por vencimiento. Un lote que se vende
completo sale solo de la lista; «Ya no está» solo con el lote sin unidades.
Se escribieron antes del código. Datos ficticios.
"""
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import Lote
from tiendas_sm.presentador_existencias import PresentadorDeExistencias
from tiendas_sm.presentador_productos import PresentadorDeProductos
from sesion_de_prueba import api_con_jefe

HOY = date.today()


def dentro_de(dias):
    return HOY + timedelta(days=dias)


class PruebasDelDominio(unittest.TestCase):
    def test_estado_segun_los_dias_de_aviso(self):
        self.assertEqual(Lote(None, 1, "L-1", dentro_de(-1), 5).estado(HOY, 7), "Vencido")
        self.assertEqual(Lote(None, 1, "L-2", dentro_de(0), 5).estado(HOY, 7), "Por vencer")
        self.assertEqual(Lote(None, 1, "L-3", dentro_de(7), 5).estado(HOY, 7), "Por vencer")
        self.assertEqual(Lote(None, 1, "L-4", dentro_de(8), 5).estado(HOY, 7), "Al día")

    def test_dias_para_vencer(self):
        self.assertEqual(Lote(None, 1, "L-1", dentro_de(3), 5).dias_para_vencer(HOY), 3)

    def test_la_cantidad_debe_ser_mayor_a_cero(self):
        with self.assertRaises(ValueError):
            Lote(None, 1, "L-1", dentro_de(3), 0)

    def test_los_dias_de_aviso_no_pueden_ser_negativos(self):
        app = Aplicacion()
        with self.assertRaises(ValueError) as error:
            app.productos.registrar_producto("Leche ficticia", 2000, 2800, 0, dias_aviso=-1)
        self.assertEqual(str(error.exception), "Los días de aviso no pueden ser negativos")


class PruebasDelServicio(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.leche = self.app.productos.registrar_producto("Leche ficticia", 2000, 2800, 10, dias_aviso=5)
        self.queso = self.app.productos.registrar_producto("Queso ficticio", 5000, 7000, 4, dias_aviso=3)

    def test_registrar_un_lote_no_cambia_las_existencias(self):
        self.app.productos.registrar_lote(self.leche.id_producto, "L-100", dentro_de(10), 6)
        self.assertEqual(self.app.cantidad_en_inventario(self.leche.id_producto), 10)
        self.assertEqual(len(self.app.productos.movimientos()), 2)           # solo las 2 entradas iniciales

    def test_la_lista_sale_ordenada_por_vencimiento(self):
        self.app.productos.registrar_lote(self.leche.id_producto, "L-B", dentro_de(20), 4)
        self.app.productos.registrar_lote(self.queso.id_producto, "L-A", dentro_de(2), 2)
        self.app.productos.registrar_lote(self.leche.id_producto, "L-C", dentro_de(9), 6)
        self.assertEqual([lote.numero for lote in self.app.productos.lotes_activos()], ["L-A", "L-C", "L-B"])

    def test_el_lote_vendido_completo_sale_solo_de_la_lista(self):
        self.app.productos.registrar_lote(self.leche.id_producto, "L-1", dentro_de(1), 6)
        self.app.ventas.registrar_venta_de_contado([(self.leche.id_producto, 6)], 6 * 2800)
        self.assertEqual(self.app.productos.lotes_activos(), [])
        self.assertEqual(self.app.cantidad_en_inventario(self.leche.id_producto), 4)

    def test_retirar_un_lote_que_ya_salio_se_rechaza(self):
        lote = self.app.productos.registrar_lote(self.leche.id_producto, "L-1", dentro_de(1), 6)
        self.app.ventas.registrar_venta_de_contado([(self.leche.id_producto, 6)], 6 * 2800)
        with self.assertRaises(ValueError) as error:
            self.app.productos.retirar_lote(lote.id_lote)
        self.assertEqual(str(error.exception), "Ese lote ya no está en la lista")

    def test_lote_de_un_producto_que_no_existe(self):
        with self.assertRaises(ValueError) as error:
            self.app.productos.registrar_lote(999, "L-1", dentro_de(1), 6)
        self.assertEqual(str(error.exception), "El producto no existe")

    def test_editar_el_producto_conserva_o_cambia_los_dias_de_aviso(self):
        self.app.productos.actualizar_producto(self.leche.id_producto, "Leche ficticia", 2000, 2900)
        self.assertEqual(self.app.productos.obtener(self.leche.id_producto).dias_aviso, 5)
        self.app.productos.actualizar_producto(self.leche.id_producto, "Leche ficticia", 2000, 2900, dias_aviso=9)
        self.assertEqual(self.app.productos.obtener(self.leche.id_producto).dias_aviso, 9)


class PruebasDelPresentador(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.leche = self.app.productos.registrar_producto("Leche ficticia", 2000, 2800, 10, dias_aviso=5)
        self.existencias = PresentadorDeExistencias(self.app)

    def test_registrar_lote_desde_el_formulario(self):
        fecha = dentro_de(3)
        resultado = self.existencias.registrar_lote(self.leche.id_producto, " L-7 ", fecha.isoformat(), "8")
        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertEqual(resultado.mensaje, f"Lote L-7 de Leche ficticia registrado. Vence el {fecha:%d/%m/%Y}")
        self.assertEqual(self.existencias.lotes(), [
            (1, ("Leche ficticia", "L-7", f"{fecha:%d/%m/%Y}", 8, "Por vencer", "Faltan 3 días"))])

    def test_textos_de_los_dias(self):
        for numero, dias in (("L-1", -2), ("L-2", 0), ("L-3", 1)):
            self.app.productos.registrar_lote(self.leche.id_producto, numero, dentro_de(dias), 1)
        self.assertEqual([fila[1][5] for fila in self.existencias.lotes()],
                         ["Venció hace 2 días", "Vence hoy", "Falta 1 día"])

    def test_sin_numero_de_lote_se_permite(self):
        resultado = self.existencias.registrar_lote(self.leche.id_producto, "", dentro_de(3).isoformat(), "1")
        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertEqual(self.existencias.lotes()[0][1][1], "Sin número")

    def test_errores_del_formulario(self):
        self.assertEqual(self.existencias.registrar_lote(None, "L-1", dentro_de(3).isoformat(), "1").mensaje,
                         "Elige un producto de la lista")
        self.assertEqual(self.existencias.registrar_lote(self.leche.id_producto, "L-1", "", "1").mensaje,
                         "Escribe la fecha de vencimiento")
        self.assertEqual(self.existencias.registrar_lote(self.leche.id_producto, "L-1", "31-02-2027", "1").mensaje,
                         "La fecha de vencimiento no es válida")
        self.assertFalse(self.existencias.registrar_lote(self.leche.id_producto, "L-1", dentro_de(3).isoformat(),
                                                         "0").exito)

    def test_por_vencer_cuenta_vencidos_y_por_vencer(self):
        self.app.productos.registrar_lote(self.leche.id_producto, "L-1", dentro_de(-1), 1)
        self.app.productos.registrar_lote(self.leche.id_producto, "L-2", dentro_de(4), 1)
        self.app.productos.registrar_lote(self.leche.id_producto, "L-3", dentro_de(30), 1)
        self.assertEqual(self.existencias.cuantos_en_alerta(), 2)

    def test_ya_no_esta_con_unidades_se_rechaza(self):
        self.app.productos.registrar_lote(self.leche.id_producto, "L-1", dentro_de(1), 1)
        self.assertEqual(self.existencias.retirar_lote(1).mensaje,
                         "Al lote L-1 le queda 1 unidad: véndala o regístrela como salida")

    def test_el_formulario_del_producto_pide_los_dias_de_aviso(self):
        productos = PresentadorDeProductos(self.app)
        resultado = productos.registrar("Yogur ficticio", "1500", "2200", "0", "0", "", "4")
        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertEqual(self.app.productos.listar()[-1].dias_aviso, 4)
        self.assertEqual(productos.datos_para_editar(self.leche.id_producto).aviso, "5")
        self.assertTrue(productos.editar(self.leche.id_producto, "Leche ficticia", "2000", "2800", "0", "", "8").exito)
        self.assertEqual(self.app.productos.obtener(self.leche.id_producto).dias_aviso, 8)


class PruebasDeLaApi(unittest.TestCase):
    def test_registrar_listar_y_quitar(self):
        app = Aplicacion()
        api = api_con_jefe(app)
        respuesta = api.registrar_producto("Leche ficticia", "2000", "2800", "6", "0", "", "5")
        self.assertTrue(respuesta["exito"], respuesta["mensaje"])
        self.assertEqual(api.datos_producto(1)["aviso"], "5")
        self.assertTrue(api.registrar_lote("1", "L-1", dentro_de(2).isoformat(), "6")["exito"])
        lotes = api.lotes()
        self.assertEqual((lotes["alerta"], lotes["filas"][0]["valores"][4]), (1, "Por vencer"))
        self.assertFalse(api.retirar_lote(lotes["filas"][0]["id"])["exito"])     # le quedan 6 unidades


class PruebasDeLaMigracion(unittest.TestCase):
    def test_un_producto_viejo_queda_sin_dias_de_aviso(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as carpeta:
            ruta = str(Path(carpeta) / "vieja.db")
            conexion = sqlite3.connect(ruta)
            conexion.executescript("""
                CREATE TABLE productos (id_producto INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL,
                    precio_compra INTEGER NOT NULL, precio_venta INTEGER NOT NULL);
                INSERT INTO productos VALUES (1, 'Viejo ficticio', 1000, 1500);""")
            conexion.close()
            app = Aplicacion(ruta)
            self.assertEqual(app.productos.obtener(1).dias_aviso, 0)
            self.assertEqual(app.productos.lotes_activos(), [])
            app.conexion.close()


if __name__ == "__main__":
    unittest.main()

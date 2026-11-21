"""Código de barras (respuesta 1.4 del propietario).

El lector escribe el código y oprime Enter solo. Por eso el buscador del punto de venta encuentra el producto
por su código exacto; la búsqueda por nombre sigue igual. El código es opcional y no se puede repetir entre
productos. Una base creada antes no tiene la columna: se agrega vacía. Se escribieron antes del código.
Los códigos son inventados.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from interfaz_web.pagina import CARPETA_ESTATICA
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.presentador import PresentadorPuntoDeVenta
from tiendas_sm.presentador_productos import PresentadorDeProductos
from sesion_de_prueba import api_con_jefe

CODIGO_ARROZ = "0000000000017"                 # inventado
CODIGO_PANELA = "0000000000024"                # inventado


class BaseDelCodigo(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio", 2000, 2500, 10, codigo=CODIGO_ARROZ)
        self.panela = self.app.productos.registrar_producto("Panela ficticia", 2200, 3000, 5)


class PruebasDelServicio(BaseDelCodigo):
    def test_se_guarda_sin_espacios_y_es_opcional(self):
        leche = self.app.productos.registrar_producto("Leche ficticia", 2500, 3200, codigo=f"  {CODIGO_PANELA} ")
        self.assertEqual(self.app.productos.obtener(leche.id_producto).codigo, CODIGO_PANELA)
        self.assertEqual(self.app.productos.obtener(self.panela.id_producto).codigo, "")

    def test_busca_por_codigo_exacto(self):
        self.assertEqual(self.app.productos.buscar_por_codigo(CODIGO_ARROZ).id_producto, self.arroz.id_producto)
        self.assertIsNone(self.app.productos.buscar_por_codigo("999"))
        self.assertIsNone(self.app.productos.buscar_por_codigo("   "))

    def test_no_se_repite_entre_productos(self):
        with self.assertRaises(ValueError) as error:
            self.app.productos.registrar_producto("Otro ficticio", 1000, 1500, codigo=CODIGO_ARROZ)
        self.assertEqual(str(error.exception), f"El código {CODIGO_ARROZ} ya es del producto Arroz ficticio")

    def test_dos_productos_sin_codigo_no_chocan(self):
        self.app.productos.registrar_producto("Sal ficticia", 800, 1200)
        self.assertEqual(len(self.app.productos.listar()), 3)

    def test_editar_conserva_o_cambia_el_codigo(self):
        self.app.productos.actualizar_producto(self.arroz.id_producto, "Arroz ficticio", 2000, 2600)
        self.assertEqual(self.app.productos.obtener(self.arroz.id_producto).codigo, CODIGO_ARROZ)
        self.app.productos.actualizar_producto(self.arroz.id_producto, "Arroz ficticio", 2000, 2600, codigo=CODIGO_ARROZ)
        self.app.productos.actualizar_producto(self.panela.id_producto, "Panela ficticia", 2200, 3000, codigo=CODIGO_PANELA)
        self.assertEqual(self.app.productos.buscar_por_codigo(CODIGO_PANELA).id_producto, self.panela.id_producto)
        with self.assertRaises(ValueError):
            self.app.productos.actualizar_producto(self.panela.id_producto, "Panela ficticia", 2200, 3000,
                                                   codigo=CODIGO_ARROZ)


class PruebasDelPuntoDeVenta(BaseDelCodigo):
    def test_el_buscador_encuentra_por_codigo_y_sigue_buscando_por_nombre(self):
        pv = PresentadorPuntoDeVenta(self.app)
        self.assertEqual([f.nombre for f in pv.buscar(CODIGO_ARROZ)], ["Arroz ficticio"])
        self.assertEqual([f.nombre for f in pv.buscar(f" {CODIGO_ARROZ}\n")], ["Arroz ficticio"])
        self.assertEqual([f.nombre for f in pv.buscar("panela")], ["Panela ficticia"])

    def test_la_api_busca_por_codigo(self):
        self.assertEqual([p["id"] for p in api_con_jefe(self.app).buscar(CODIGO_ARROZ)], [self.arroz.id_producto])


class PruebasDeProductos(BaseDelCodigo):
    def test_registrar_y_editar_desde_el_formulario(self):
        pp = PresentadorDeProductos(self.app)
        self.assertTrue(pp.registrar("Leche ficticia", "2500", "3200", "0", "0", CODIGO_PANELA).exito)
        self.assertEqual(pp.datos_para_editar(self.arroz.id_producto).codigo, CODIGO_ARROZ)
        repetido = pp.editar(self.arroz.id_producto, "Arroz ficticio", "2000", "2500", "0", CODIGO_PANELA)
        self.assertEqual((repetido.exito, repetido.mensaje),
                         (False, f"El código {CODIGO_PANELA} ya es del producto Leche ficticia"))

    def test_la_api_recibe_el_codigo(self):
        api = api_con_jefe(self.app)
        self.assertTrue(api.registrar_producto("Leche ficticia", "2500", "3200", "0", "0", CODIGO_PANELA)["exito"])
        self.assertEqual(api.datos_producto(self.arroz.id_producto)["codigo"], CODIGO_ARROZ)
        self.assertTrue(api.editar_producto(self.arroz.id_producto, "Arroz ficticio", "2000", "2500", "0", "")["exito"])
        self.assertEqual(self.app.productos.obtener(self.arroz.id_producto).codigo, "")


class PruebasDeLaPagina(unittest.TestCase):
    def test_el_enter_del_lector_no_guarda_el_formulario(self):
        codigo = (CARPETA_ESTATICA / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="f-codigo"', codigo)
        self.assertIn("data-lector", codigo)
        self.assertIn("ev.target.dataset.lector", codigo)


class PruebasDeLaMigracion(unittest.TestCase):
    def test_una_base_vieja_abre_con_el_codigo_vacio(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as carpeta:
            ruta = str(Path(carpeta) / "vieja.db")
            conexion = sqlite3.connect(ruta)
            conexion.executescript("""
                CREATE TABLE productos (id_producto INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL,
                    precio_compra INTEGER NOT NULL, precio_venta INTEGER NOT NULL, stock_minimo INTEGER NOT NULL DEFAULT 0);
                INSERT INTO productos (nombre, precio_compra, precio_venta) VALUES ('Producto ficticio viejo', 100, 200);""")
            conexion.close()
            app = Aplicacion(ruta)
            producto, = app.productos.listar()
            self.assertEqual((producto.nombre, producto.codigo), ("Producto ficticio viejo", ""))
            app.conexion.close()


if __name__ == "__main__":
    unittest.main()

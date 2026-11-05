"""Pruebas del arranque de la aplicación: ruta de datos y datos de ejemplo ficticios (tarea 8).

No abren ventanas. La base se crea en una carpeta temporal que se borra al terminar.
"""
import tempfile
import unittest
from pathlib import Path

from iniciar_tienda import abrir_aplicacion, ruta_de_datos
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.datos_de_ejemplo import CLIENTES_DE_EJEMPLO, PRODUCTOS_DE_EJEMPLO, cargar_datos_de_ejemplo


class PruebasDeLaRutaDeDatos(unittest.TestCase):
    def test_en_windows_usa_localappdata(self):
        ruta = ruta_de_datos({"LOCALAPPDATA": r"C:\Usuarios\prueba\AppData\Local"})
        self.assertEqual(ruta, Path(r"C:\Usuarios\prueba\AppData\Local") / "TIENDAS_SM" / "tiendas_sm.db")

    def test_sin_localappdata_usa_la_carpeta_personal(self):
        self.assertEqual(ruta_de_datos({}), Path.home() / "TIENDAS_SM" / "tiendas_sm.db")


class PruebasDeDatosDeEjemplo(unittest.TestCase):
    def test_carga_los_datos_ficticios_en_una_base_vacia(self):
        app = Aplicacion()
        self.assertTrue(cargar_datos_de_ejemplo(app))
        self.assertEqual(len(app.productos.listar()), len(PRODUCTOS_DE_EJEMPLO))
        self.assertEqual(len(app.clientes.listar()), len(CLIENTES_DE_EJEMPLO))

    def test_no_carga_nada_si_la_base_ya_tiene_datos(self):
        app = Aplicacion()
        app.productos.registrar_producto("Producto propio", 1000, 1500)
        self.assertFalse(cargar_datos_de_ejemplo(app))
        self.assertEqual(len(app.productos.listar()), 1)
        self.assertEqual(app.clientes.listar(), [])


class PruebasDeAbrirLaAplicacion(unittest.TestCase):
    def test_crea_la_carpeta_y_los_datos_se_conservan_al_volver_a_abrir(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as carpeta:
            ruta = Path(carpeta) / "TIENDAS_SM" / "tiendas_sm.db"
            app, cargo = abrir_aplicacion(ruta, con_datos_de_ejemplo=True)
            app.conexion.close()
            self.assertTrue(cargo)
            self.assertTrue(ruta.exists())
            otra_vez, cargo_otra_vez = abrir_aplicacion(ruta, con_datos_de_ejemplo=True)   # no duplica los datos
            self.assertFalse(cargo_otra_vez)
            self.assertEqual(len(otra_vez.productos.listar()), len(PRODUCTOS_DE_EJEMPLO))
            otra_vez.conexion.close()


if __name__ == "__main__":
    unittest.main()

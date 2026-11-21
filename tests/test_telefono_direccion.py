"""Teléfono y dirección del cliente (respuesta 3.1 del propietario).

Son datos personales: son opcionales, se guardan solo en este equipo y aquí se usan valores inventados.
Una base creada antes no tiene esas columnas: al abrirla se agregan vacías sin perder los clientes
(igual que la migración de ventas, DIF-06). Se escribieron antes del código.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.base_de_datos import BaseDeDatos
from tiendas_sm.dominio import Cliente
from tiendas_sm.presentador_clientes import PresentadorDeClientes
from sesion_de_prueba import api_con_jefe

TELEFONO = "300 000 0001"                       # inventado
DIRECCION = "Calle Ficticia 1 # 2-3"            # inventada


class PruebasDelDominio(unittest.TestCase):
    def test_son_opcionales_y_se_limpian_los_espacios(self):
        sin_datos = Cliente(None, "Cliente ficticio", True, 1000, 15)
        self.assertEqual((sin_datos.telefono, sin_datos.direccion), ("", ""))
        con_datos = Cliente(None, "Cliente ficticio", True, 1000, 15, telefono=f"  {TELEFONO} ", direccion=f" {DIRECCION}  ")
        self.assertEqual((con_datos.telefono, con_datos.direccion), (TELEFONO, DIRECCION))

    def test_el_telefono_solo_lleva_numeros_espacios_mas_y_guion(self):
        Cliente(None, "Cliente ficticio", True, 1000, 15, telefono="+57 300-000-0001")
        with self.assertRaises(ValueError) as error:
            Cliente(None, "Cliente ficticio", True, 1000, 15, telefono="trescientos")
        self.assertEqual(str(error.exception), "El teléfono solo puede tener números, espacios, + y -")


class BaseDeClientes(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.pc = PresentadorDeClientes(self.app)


class PruebasDelPresentador(BaseDeClientes):
    def test_registrar_guarda_telefono_y_direccion(self):
        self.assertTrue(self.pc.registrar("Cliente ficticio", True, "50000", "15", TELEFONO, DIRECCION).exito)
        cliente, = self.app.clientes.listar()
        self.assertEqual((cliente.telefono, cliente.direccion), (TELEFONO, DIRECCION))

    def test_un_telefono_invalido_muestra_el_mensaje(self):
        resultado = self.pc.registrar("Cliente ficticio", True, "50000", "15", "abc", "")
        self.assertEqual((resultado.exito, resultado.mensaje),
                         (False, "El teléfono solo puede tener números, espacios, + y -"))

    def test_editar_los_trae_y_los_cambia(self):
        self.pc.registrar("Cliente ficticio", True, "50000", "15", TELEFONO, DIRECCION)
        cliente, = self.app.clientes.listar()
        datos = self.pc.datos_para_editar(cliente.id_cliente)
        self.assertEqual((datos.telefono, datos.direccion), (TELEFONO, DIRECCION))
        self.assertTrue(self.pc.editar(cliente.id_cliente, "Cliente ficticio", True, "50000", "15", "", "Otra calle ficticia").exito)
        self.assertEqual((self.app.clientes.obtener(cliente.id_cliente).telefono,
                          self.app.clientes.obtener(cliente.id_cliente).direccion), ("", "Otra calle ficticia"))

    def test_editar_sin_esos_datos_los_conserva(self):
        """La versión Tkinter no los pide: si no llegan, se queda lo guardado."""
        self.pc.registrar("Cliente ficticio", True, "50000", "15", TELEFONO, DIRECCION)
        cliente, = self.app.clientes.listar()
        self.assertTrue(self.pc.editar(cliente.id_cliente, "Cliente ficticio", True, "60000", "15").exito)
        self.assertEqual(self.app.clientes.obtener(cliente.id_cliente).telefono, TELEFONO)

    def test_el_detalle_los_muestra(self):
        self.pc.registrar("Cliente ficticio", True, "50000", "15", TELEFONO, DIRECCION)
        cliente, = self.app.clientes.listar()
        detalle = self.pc.detalle(cliente.id_cliente)
        self.assertIn(f"Teléfono: {TELEFONO}", detalle)
        self.assertIn(f"Dirección: {DIRECCION}", detalle)


class PruebasDeLaApi(BaseDeClientes):
    def test_registrar_datos_y_editar(self):
        api = api_con_jefe(self.app)
        self.assertTrue(api.registrar_cliente("Cliente ficticio", True, "50000", "15", TELEFONO, DIRECCION)["exito"])
        cliente, = self.app.clientes.listar()
        datos = api.datos_cliente(cliente.id_cliente)
        self.assertEqual((datos["telefono"], datos["direccion"]), (TELEFONO, DIRECCION))
        self.assertTrue(api.editar_cliente(cliente.id_cliente, "Cliente ficticio", True, "50000", "15", TELEFONO, "")["exito"])
        self.assertEqual(self.app.clientes.obtener(cliente.id_cliente).direccion, "")


class PruebasDeLaMigracion(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.ruta = str(Path(self.carpeta.name) / "vieja.db")
        conexion = sqlite3.connect(self.ruta)
        conexion.executescript("""
            CREATE TABLE clientes (id_cliente INTEGER PRIMARY KEY AUTOINCREMENT, nombres TEXT NOT NULL,
                credito_habilitado INTEGER NOT NULL, limite_credito INTEGER NOT NULL, plazo_credito_dias INTEGER NOT NULL);
            INSERT INTO clientes (nombres, credito_habilitado, limite_credito, plazo_credito_dias)
                VALUES ('Cliente ficticio viejo', 1, 50000, 30);""")
        conexion.close()

    def tearDown(self):
        self.carpeta.cleanup()

    def test_una_base_vieja_abre_con_los_clientes_y_los_campos_vacios(self):
        app = Aplicacion(self.ruta)
        cliente, = app.clientes.listar()
        self.assertEqual((cliente.nombres, cliente.telefono, cliente.direccion), ("Cliente ficticio viejo", "", ""))
        app.conexion.close()

    def test_abrir_dos_veces_no_duplica_columnas(self):
        BaseDeDatos(self.ruta).conexion.close()
        base = BaseDeDatos(self.ruta)
        columnas = [fila[1] for fila in base.conexion.execute("PRAGMA table_info(clientes)")]
        self.assertEqual((columnas.count("telefono"), columnas.count("direccion")), (1, 1))
        base.conexion.close()


if __name__ == "__main__":
    unittest.main()

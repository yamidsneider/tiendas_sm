"""Usuarios y roles (fase 2 de docs/HOJA_DE_RUTA_APP_COMPLETA.md, CR-01, RNF-03).

Respuestas del desarrollador (21 de noviembre de 2026): la tienda tiene 2 empleados; la clave se pide al abrir la app
y cada usuario solo puede hacer lo que su rol permite. Hay dos roles: jefe y empleado.
*Preliminar (propuesta, por confirmar con el propietario):* el empleado vende (contado y fiado), consulta, registra
entradas y lotes, y recibe abonos. Solo el jefe devuelve o anula ventas, crea o edita productos y precios, crea o
edita clientes (cupo y plazo), ve los reportes y administra los usuarios.
Seguridad: la clave nunca se guarda tal cual (PBKDF2 con sal, de la biblioteca estándar); no hay usuarios ni claves
en el código: el primer jefe se crea en la pantalla de la primera vez. Se escribieron antes del código. Datos ficticios.
"""
import unittest

from interfaz_web.api import ApiDeLaTienda
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import Permiso, Rol
from tiendas_sm.servicios import Sesion

CLAVE = "clave-ficticia-1"
OTRA_CLAVE = "clave-ficticia-2"
ACCESO_INCORRECTO = "Usuario o clave incorrectos"
SOLO_EL_JEFE = "Solo el jefe puede hacer esto"
SIN_INGRESAR = "Primero ingrese con su usuario y clave"
# Los únicos métodos de la API que se pueden usar sin haber ingresado.
LIBRES = {"estado_sesion", "crear_primer_jefe", "iniciar_sesion", "cerrar_sesion"}


class BaseDeUsuarios(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.usuarios = self.app.usuarios
        self.jefe = self.usuarios.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE)


class PruebasDelPrimerJefe(unittest.TestCase):
    def test_sin_usuarios_se_crea_el_primer_jefe(self):
        app = Aplicacion()
        self.assertFalse(app.usuarios.hay_usuarios())
        jefe = app.usuarios.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE)
        self.assertEqual((jefe.rol, jefe.activo), (Rol.JEFE, True))
        self.assertTrue(app.usuarios.hay_usuarios())

    def test_el_primer_jefe_solo_se_crea_una_vez(self):
        app = Aplicacion()
        app.usuarios.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE)
        with self.assertRaises(ValueError) as error:
            app.usuarios.crear_primer_jefe("Intruso ficticio", "otro", CLAVE)
        self.assertEqual(str(error.exception), "Ya hay usuarios: el jefe crea los demás en la sección Usuarios")


class PruebasDeLaClave(BaseDeUsuarios):
    def test_la_clave_no_se_guarda_tal_cual_y_cada_usuario_tiene_su_sal(self):
        self.usuarios.crear_usuario("Empleado ficticio", "pedro", Rol.EMPLEADO, CLAVE)
        filas = self.app.conexion.execute("SELECT clave_hash, sal FROM usuarios").fetchall()
        self.assertTrue(all(CLAVE not in fila["clave_hash"] for fila in filas))
        self.assertNotEqual(filas[0]["sal"], filas[1]["sal"])
        self.assertNotEqual(filas[0]["clave_hash"], filas[1]["clave_hash"])     # misma clave, distinta huella

    def test_ingresar_con_la_clave_correcta(self):
        self.assertEqual(self.usuarios.iniciar_sesion("jefe", CLAVE).id_usuario, self.jefe.id_usuario)

    def test_el_usuario_no_distingue_mayusculas_ni_espacios_alrededor(self):
        self.assertEqual(self.usuarios.iniciar_sesion("  JEFE ", CLAVE).id_usuario, self.jefe.id_usuario)

    def test_clave_mala_o_usuario_que_no_existe_dan_el_mismo_mensaje(self):
        for usuario, clave in (("jefe", OTRA_CLAVE), ("nadie", CLAVE)):
            with self.subTest(usuario=usuario), self.assertRaises(ValueError) as error:
                self.usuarios.iniciar_sesion(usuario, clave)
            self.assertEqual(str(error.exception), ACCESO_INCORRECTO)

    def test_clave_muy_corta(self):
        with self.assertRaises(ValueError) as error:
            self.usuarios.crear_usuario("Empleado ficticio", "pedro", Rol.EMPLEADO, "123")
        self.assertEqual(str(error.exception), "La clave debe tener al menos 4 caracteres")

    def test_cambiar_la_clave(self):
        self.usuarios.cambiar_clave(self.jefe.id_usuario, OTRA_CLAVE)
        with self.assertRaises(ValueError):
            self.usuarios.iniciar_sesion("jefe", CLAVE)
        self.assertEqual(self.usuarios.iniciar_sesion("jefe", OTRA_CLAVE).id_usuario, self.jefe.id_usuario)


class PruebasDeLosDatosDelUsuario(BaseDeUsuarios):
    def test_el_usuario_es_unico(self):
        with self.assertRaises(ValueError) as error:
            self.usuarios.crear_usuario("Otro jefe ficticio", "Jefe", Rol.JEFE, CLAVE)
        self.assertEqual(str(error.exception), "Ya existe el usuario «jefe»")

    def test_el_usuario_solo_lleva_letras_numeros_punto_o_guion(self):
        for malo in ("pedro perez", "", "pe/dro"):
            with self.subTest(usuario=malo), self.assertRaises(ValueError):
                self.usuarios.crear_usuario("Empleado ficticio", malo, Rol.EMPLEADO, CLAVE)

    def test_el_nombre_es_obligatorio(self):
        with self.assertRaises(ValueError):
            self.usuarios.crear_usuario("  ", "pedro", Rol.EMPLEADO, CLAVE)

    def test_lista_los_usuarios_por_nombre(self):
        self.usuarios.crear_usuario("Ana empleada ficticia", "ana", Rol.EMPLEADO, CLAVE)
        self.assertEqual([u.usuario for u in self.usuarios.listar()], ["ana", "jefe"])


class PruebasDeActivarYDesactivar(BaseDeUsuarios):
    def test_un_usuario_desactivado_no_puede_ingresar(self):
        pedro = self.usuarios.crear_usuario("Empleado ficticio", "pedro", Rol.EMPLEADO, CLAVE)
        self.usuarios.activar(pedro.id_usuario, False, self.jefe)
        with self.assertRaises(ValueError) as error:
            self.usuarios.iniciar_sesion("pedro", CLAVE)
        self.assertEqual(str(error.exception), ACCESO_INCORRECTO)
        self.usuarios.activar(pedro.id_usuario, True, self.jefe)
        self.assertEqual(self.usuarios.iniciar_sesion("pedro", CLAVE).nombre, "Empleado ficticio")

    def test_nadie_se_desactiva_a_si_mismo(self):
        self.usuarios.crear_usuario("Otro jefe ficticio", "jefa", Rol.JEFE, CLAVE)
        with self.assertRaises(ValueError) as error:
            self.usuarios.activar(self.jefe.id_usuario, False, self.jefe)
        self.assertEqual(str(error.exception), "No puede desactivar su propio usuario")

    def test_siempre_queda_al_menos_un_jefe_activo(self):
        jefa = self.usuarios.crear_usuario("Otra jefa ficticia", "jefa", Rol.JEFE, CLAVE)
        self.usuarios.activar(jefa.id_usuario, False, self.jefe)
        self.assertFalse(self.usuarios.obtener(jefa.id_usuario).activo)
        pedro = self.usuarios.crear_usuario("Empleado ficticio", "pedro", Rol.EMPLEADO, CLAVE)
        with self.assertRaises(ValueError) as error:
            self.usuarios.activar(self.jefe.id_usuario, False, pedro)
        self.assertEqual(str(error.exception), "Debe quedar al menos un jefe activo")


class PruebasDeLosPermisos(BaseDeUsuarios):
    def test_el_empleado_vende_consulta_recibe_mercancia_y_abonos(self):
        for permiso in (Permiso.VENDER, Permiso.CONSULTAR, Permiso.REGISTRAR_ENTRADA, Permiso.REGISTRAR_ABONO):
            self.assertTrue(Rol.EMPLEADO.puede(permiso), permiso)

    def test_el_empleado_no_hace_lo_del_jefe(self):
        for permiso in (Permiso.DEVOLVER, Permiso.GESTIONAR_PRODUCTOS, Permiso.GESTIONAR_CLIENTES,
                        Permiso.VER_REPORTES, Permiso.GESTIONAR_USUARIOS):
            self.assertFalse(Rol.EMPLEADO.puede(permiso), permiso)

    def test_el_jefe_puede_todo(self):
        self.assertTrue(all(Rol.JEFE.puede(permiso) for permiso in Permiso))

    def test_la_sesion_dice_por_que_no_se_puede(self):
        sesion = Sesion()
        self.assertEqual(sesion.negar(Permiso.VENDER), SIN_INGRESAR)
        sesion.iniciar(self.usuarios.crear_usuario("Empleado ficticio", "pedro", Rol.EMPLEADO, CLAVE))
        self.assertIsNone(sesion.negar(Permiso.VENDER))
        self.assertEqual(sesion.negar(Permiso.DEVOLVER), SOLO_EL_JEFE)
        sesion.cerrar()
        self.assertEqual(sesion.negar(Permiso.VENDER), SIN_INGRESAR)


class PruebasDeLaApi(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio", 2000, 2500, 20)
        self.api = ApiDeLaTienda(self.app)

    def crear_jefe_y_empleado(self):
        self.api.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE, CLAVE)
        self.assertTrue(self.api.crear_usuario("Empleado ficticio", "pedro", "EMPLEADO", CLAVE, CLAVE)["exito"])
        self.api.cerrar_sesion()

    def test_la_primera_vez_no_hay_usuarios_ni_sesion(self):
        self.assertEqual(self.api.estado_sesion(), {"hay_usuarios": False, "usuario": None})

    def test_crear_el_primer_jefe_deja_la_sesion_abierta(self):
        self.assertFalse(self.api.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE, OTRA_CLAVE)["exito"])
        respuesta = self.api.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE, CLAVE)
        self.assertTrue(respuesta["exito"], respuesta["mensaje"])
        usuario = respuesta["estado"]["usuario"]
        self.assertEqual((usuario["nombre"], usuario["rol"]), ("Jefe ficticio", "Jefe"))
        self.assertIn("ver_reportes", usuario["permisos"])

    def test_sin_ingresar_no_se_puede_usar_nada(self):
        self.crear_jefe_y_empleado()
        for respuesta in (self.api.buscar("arroz"), self.api.productos(""), self.api.reporte("hoy")):
            self.assertEqual((respuesta["exito"], respuesta["mensaje"]), (False, SIN_INGRESAR))

    def test_clave_mala_no_abre_la_sesion(self):
        self.crear_jefe_y_empleado()
        respuesta = self.api.iniciar_sesion("pedro", OTRA_CLAVE)
        self.assertEqual((respuesta["exito"], respuesta["mensaje"]), (False, ACCESO_INCORRECTO))
        self.assertIsNone(self.api.estado_sesion()["usuario"])

    def test_el_empleado_vende_pero_no_devuelve_ni_ve_reportes(self):
        self.crear_jefe_y_empleado()
        self.assertTrue(self.api.iniciar_sesion("pedro", CLAVE)["exito"])
        self.api.agregar(self.arroz.id_producto, "1")
        venta = self.api.cobrar_de_contado("2500")
        self.assertTrue(venta["exito"], venta["mensaje"])
        for respuesta in (self.api.anular(1, "Prueba"), self.api.reporte("hoy"), self.api.usuarios(),
                          self.api.registrar_producto("Panela ficticia", "1", "2", "3"),
                          self.api.cambiar_precio(self.arroz.id_producto, "9000")):
            self.assertEqual((respuesta["exito"], respuesta["mensaje"]), (False, SOLO_EL_JEFE))
        self.assertNotIn("ver_reportes", self.api.estado_sesion()["usuario"]["permisos"])

    def test_cerrar_sesion_vacia_el_carrito(self):
        self.api.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE, CLAVE)
        self.api.agregar(self.arroz.id_producto, "1")
        self.api.cerrar_sesion()
        self.api.iniciar_sesion("jefe", CLAVE)
        self.assertTrue(self.api.carrito()["vacio"])

    def test_el_jefe_administra_los_usuarios(self):
        self.api.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE, CLAVE)
        self.assertTrue(self.api.crear_usuario("Empleado ficticio", "pedro", "EMPLEADO", CLAVE, CLAVE)["exito"])
        self.assertFalse(self.api.crear_usuario("Otro ficticio", "luis", "EMPLEADO", CLAVE, OTRA_CLAVE)["exito"])
        filas = self.api.usuarios()
        self.assertEqual([f["valores"] for f in filas], [["Empleado ficticio", "pedro", "Empleado", "Activo"],
                                                         ["Jefe ficticio", "jefe", "Jefe", "Activo"]])
        pedro = filas[0]["id"]
        self.assertTrue(self.api.activar_usuario(pedro, False)["exito"])
        self.assertTrue(self.api.cambiar_clave_usuario(pedro, OTRA_CLAVE, OTRA_CLAVE)["exito"])
        self.assertFalse(self.api.activar_usuario(filas[1]["id"], False)["exito"])     # a sí mismo, no

    def test_cada_metodo_de_la_api_exige_un_permiso(self):
        """Barrera de seguridad: si alguien agrega un método nuevo sin @requiere, esta prueba falla."""
        publicos = {nombre for nombre in dir(ApiDeLaTienda)
                    if not nombre.startswith("_") and callable(getattr(ApiDeLaTienda, nombre))}
        sin_permiso = sorted(n for n in publicos - LIBRES if getattr(getattr(ApiDeLaTienda, n), "permiso", None) is None)
        self.assertEqual(sin_permiso, [])
        self.assertGreater(len(publicos - LIBRES), 30)            # la revisión sí encontró los métodos


if __name__ == "__main__":
    unittest.main()

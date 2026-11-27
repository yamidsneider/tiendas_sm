"""Presentador del ingreso y de la sección Usuarios (fase 2 de la hoja de ruta, CR-01, RNF-03).

No usa ninguna interfaz. Guarda la Sesion de la ventana (quién ingresó) y convierte lo que escribe la persona en
llamadas a ServicioDeUsuarios; los mensajes de error del dominio llegan tal cual a la pantalla.
"""
from tiendas_sm.dominio import PERMISOS_POR_ROL, Rol
from tiendas_sm.presentador import Resultado
from tiendas_sm.servicios import Sesion

CLAVES_DISTINTAS = "Las dos claves no coinciden"


class PresentadorDeUsuarios:
    def __init__(self, app, sesion=None):
        self.app = app
        self.sesion = sesion or Sesion()

    # ------------------------------------------------------------------ ingreso
    def estado(self):
        usuario = self.sesion.usuario
        return {"hay_usuarios": self.app.usuarios.hay_usuarios(),
                "usuario": None if usuario is None else {
                    "nombre": usuario.nombre, "usuario": usuario.usuario, "rol": usuario.rol.nombre_visible,
                    "permisos": sorted(p.value for p in PERMISOS_POR_ROL[usuario.rol])}}

    def crear_primer_jefe(self, nombre, usuario, clave, confirmacion):
        return self._ingresar_con(lambda: self.app.usuarios.crear_primer_jefe(nombre, usuario, clave),
                                  clave, confirmacion, "Bienvenido")

    def iniciar_sesion(self, usuario, clave):
        return self._ingresar_con(lambda: self.app.usuarios.iniciar_sesion(usuario, clave), clave, clave, "Hola")

    def _ingresar_con(self, accion, clave, confirmacion, saludo):
        if clave != confirmacion:
            return Resultado(False, CLAVES_DISTINTAS)
        try:
            usuario = accion()
        except ValueError as error:
            return Resultado(False, str(error))
        self.sesion.iniciar(usuario)
        return Resultado(True, f"{saludo}, {usuario.nombre}")

    def cerrar_sesion(self):
        self.sesion.cerrar()

    # ------------------------------------------------------------------ sección Usuarios (solo el jefe)
    def tabla(self):
        """Filas (id_usuario, (nombre, usuario, rol, estado)), ordenadas por nombre."""
        return [(u.id_usuario, (u.nombre, u.usuario, u.rol.nombre_visible, "Activo" if u.activo else "Desactivado"))
                for u in self.app.usuarios.listar()]

    def crear(self, nombre, usuario, rol, clave, confirmacion):
        if clave != confirmacion:
            return Resultado(False, CLAVES_DISTINTAS)
        try:
            creado = self.app.usuarios.crear_usuario(nombre, usuario, _rol(rol), clave)
        except ValueError as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Usuario «{creado.usuario}» creado como {creado.rol.nombre_visible.lower()}")

    def cambiar_clave(self, id_usuario, clave, confirmacion):
        if clave != confirmacion:
            return Resultado(False, CLAVES_DISTINTAS)
        try:
            usuario = self.app.usuarios.cambiar_clave(id_usuario, clave)
        except ValueError as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Clave de «{usuario.usuario}» cambiada")

    def activar(self, id_usuario, activo):
        try:
            usuario = self.app.usuarios.activar(id_usuario, activo, self.sesion.usuario)
        except ValueError as error:
            return Resultado(False, str(error))
        return Resultado(True, f"«{usuario.usuario}» {'activado' if activo else 'desactivado'}")


def _rol(texto):
    try:
        return Rol(str(texto).upper())
    except ValueError:
        raise ValueError("Elige el rol: jefe o empleado") from None

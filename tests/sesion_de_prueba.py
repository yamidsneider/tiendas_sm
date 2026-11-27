"""Ayuda para las pruebas de la API (fase 2): la API exige ingresar con usuario y clave.

api_con_jefe crea un jefe ficticio (solo si la base no tiene usuarios) e ingresa con él, así las pruebas de cada
sección siguen probando lo mismo que antes. La clave es un dato de prueba, no una clave real.
"""
from interfaz_web.api import ApiDeLaTienda, _ejecutar_aqui

JEFE_DE_PRUEBA = "jefe"
CLAVE_DE_PRUEBA = "prueba-1234"


def api_con_jefe(app, ejecutar=_ejecutar_aqui):
    api = ApiDeLaTienda(app, ejecutar)
    if not api.estado_sesion()["hay_usuarios"]:
        api.crear_primer_jefe("Jefe ficticio", JEFE_DE_PRUEBA, CLAVE_DE_PRUEBA, CLAVE_DE_PRUEBA)
    else:
        api.iniciar_sesion(JEFE_DE_PRUEBA, CLAVE_DE_PRUEBA)
    return api

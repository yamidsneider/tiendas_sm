"""Abre la aplicación de escritorio de TIENDAS S.M (opción B: ventana con la visual del borrador HTML).

Uso:  python iniciar_tienda.py                      abre la tienda con los datos guardados
      python iniciar_tienda.py --datos-de-ejemplo   además carga datos FICTICIOS si la base está vacía
También funciona igual desde TIENDAS_SM.exe (armado con construir_exe.py).
Fase 2 (CR-01): la ventana pide usuario y clave. La opción --tkinter ya no abre la versión anterior, porque esa
versión no pide clave y se saltaría los permisos de cada rol; si se pasa, se abre la ventana normal.

Los datos se guardan en la carpeta de datos del usuario (DDS §14):
%LOCALAPPDATA%\\TIENDAS_SM\\tiendas_sm.db en Windows. Al cerrar se crea un respaldo verificado en la misma carpeta (FPI-30).
"""
import logging
import os
import sys
from collections import namedtuple
from logging.handlers import RotatingFileHandler
from pathlib import Path

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.datos_de_ejemplo import cargar_datos_de_ejemplo
from tiendas_sm.respaldo import respaldar, revisar_al_abrir
from tiendas_sm.telemetria import Telemetria

CARPETA_DE_DATOS = "TIENDAS_SM"
ARCHIVO_DE_DATOS = "tiendas_sm.db"
OPCION_DATOS_DE_EJEMPLO = "--datos-de-ejemplo"
OPCION_TKINTER = "--tkinter"
TITULO = "TIENDAS S.M"
TAMANO_DE_LA_VENTANA = (1280, 780)
TAMANO_MINIMO = (1000, 600)                  # cabe en una pantalla de 1024 x 600 (E-01)
COLOR_DE_FONDO = "#eef5f1"                   # el --fondo del borrador: no se ve un destello blanco al abrir
ARCHIVO_DE_TELEMETRIA = "telemetria.jsonl"
TASA_DE_MUESTREO = 0.2                       # ADR-13: errores al 100 %, ventas exitosas al 20 %
TAMANO_MAXIMO_LOG = 1_000_000                # ADR-13: 1 MB por archivo...
MENSAJE_DE_ERROR_DE_WINDOWS = 0x10           # MB_ICONERROR: ventana de aviso con el ícono de error
ARCHIVOS_DE_RESPALDO = 3                     # ...y 3 anteriores: máximo 4 MB (≈ 14 a 19 meses a 80 ventas/día)


def ruta_de_datos(entorno=os.environ):
    """En Windows usa %LOCALAPPDATA%; si no existe esa variable (otro sistema), la carpeta personal."""
    base = Path(entorno.get("LOCALAPPDATA") or Path.home())
    return base / CARPETA_DE_DATOS / ARCHIVO_DE_DATOS


def configurar_telemetria(carpeta):
    """FPI-29: log JSON con rotación por tamaño, junto a la base. Nunca contiene datos personales."""
    registro = logging.getLogger("tiendas_sm.telemetria")
    registro.setLevel(logging.INFO)
    registro.propagate = False
    if not registro.handlers:
        manejador = RotatingFileHandler(carpeta / ARCHIVO_DE_TELEMETRIA, maxBytes=TAMANO_MAXIMO_LOG,
                                        backupCount=ARCHIVOS_DE_RESPALDO, encoding="utf-8")
        manejador.setFormatter(logging.Formatter("%(message)s"))
        registro.addHandler(manejador)
    return Telemetria(escribir=registro.info, tasa_muestreo=TASA_DE_MUESTREO)


def abrir_aplicacion(ruta, con_datos_de_ejemplo, telemetria=None):
    """Crea la carpeta si falta y abre la base. Devuelve (app, True si cargó los datos de ejemplo)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    app = Aplicacion(str(ruta), telemetria=telemetria)
    return app, con_datos_de_ejemplo and cargar_datos_de_ejemplo(app)


def cerrar_y_respaldar(app, ruta, telemetria=None, ahora=None):
    """FPI-30 (INC-SIM-01): al cerrar, se suelta la base y se respalda solo si está sana. Devuelve el respaldo o None."""
    app.conexion.close()
    return respaldar(ruta, telemetria, ahora)


Tienda = namedtuple("Tienda", "hilo app api cargo_ejemplo")


def preparar_tienda(ruta, con_datos_de_ejemplo, telemetria=None):
    """Abre la base DENTRO del hilo de la base (SQLite solo acepta ese hilo) y arma la API para la página."""
    from interfaz_web.api import ApiDeLaTienda, HiloDeLaBase
    hilo = HiloDeLaBase()
    app, cargo_ejemplo = hilo.ejecutar(lambda: abrir_aplicacion(ruta, con_datos_de_ejemplo, telemetria))
    return Tienda(hilo, app, ApiDeLaTienda(app, hilo.ejecutar), cargo_ejemplo)


def cerrar_tienda(tienda, ruta, telemetria=None):
    """Cierra la base en su mismo hilo y hace el respaldo verificado (FPI-30). Devuelve el respaldo o None."""
    try:
        return tienda.hilo.ejecutar(lambda: cerrar_y_respaldar(tienda.app, ruta, telemetria))
    finally:
        tienda.hilo.cerrar()


def usar_escala_de_windows():
    """En Windows con escala de pantalla (125 %, 150 %…) evita que la ventana se vea borrosa."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (ImportError, AttributeError, OSError):
        pass                                                  # otro sistema operativo: no hace falta


def main(argumentos):
    usar_escala_de_windows()
    ruta = ruta_de_datos()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    telemetria = configurar_telemetria(ruta.parent)
    problema = revisar_al_abrir(ruta, telemetria)            # FPI-30: no se vende sobre una base dañada
    if problema:
        mostrar_base_danada(problema)
        return
    con_datos_de_ejemplo = OPCION_DATOS_DE_EJEMPLO in argumentos
    if OPCION_TKINTER in argumentos:
        print("La versión Tkinter no pide usuario y clave (fase 2): se abre la ventana normal.")
    abrir_ventana(ruta, con_datos_de_ejemplo, telemetria)


def abrir_ventana(ruta, con_datos_de_ejemplo, telemetria):
    """Ventana nativa de Windows (pywebview) con la página del borrador; al cerrarla se respalda la base."""
    import webview                                            # se importa aquí: las pruebas y el CI no lo necesitan
    from interfaz_web.pagina import armar_pagina

    tienda = preparar_tienda(ruta, con_datos_de_ejemplo, telemetria)
    informar_inicio(ruta, tienda.cargo_ejemplo)
    try:
        webview.create_window(TITULO, html=armar_pagina(), js_api=tienda.api, width=TAMANO_DE_LA_VENTANA[0],
                              height=TAMANO_DE_LA_VENTANA[1], min_size=TAMANO_MINIMO, background_color=COLOR_DE_FONDO)
        webview.start()                                       # se queda aquí hasta que se cierra la ventana
    finally:
        informar_respaldo(cerrar_tienda(tienda, ruta, telemetria))


def informar_inicio(ruta, cargo_ejemplo):
    print(f"Base de datos: {ruta}")                           # en el .exe no hay consola: print no hace nada
    if cargo_ejemplo:
        print("Se cargaron datos de ejemplo ficticios.")


def informar_respaldo(respaldo):
    print(f"Respaldo: {respaldo}" if respaldo else "No se creó el respaldo: revise la base con el Runbook.")


def mostrar_base_danada(mensaje):
    """Aviso de Windows (sin Tkinter ni pywebview); en otro sistema se escribe en la consola."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, mensaje, TITULO, MENSAJE_DE_ERROR_DE_WINDOWS)
    except (ImportError, AttributeError, OSError):
        print(mensaje, file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])

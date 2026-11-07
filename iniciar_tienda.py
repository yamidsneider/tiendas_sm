"""Abre la aplicación de escritorio de TIENDAS S.M (punto de venta, tarea 8).

Uso:  python iniciar_tienda.py                      abre la tienda con los datos guardados
      python iniciar_tienda.py --datos-de-ejemplo   además carga datos FICTICIOS si la base está vacía

Los datos se guardan en la carpeta de datos del usuario (DDS §14):
%LOCALAPPDATA%\\TIENDAS_SM\\tiendas_sm.db en Windows. Al cerrar se crea un respaldo verificado en la misma carpeta (FPI-30).
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.datos_de_ejemplo import cargar_datos_de_ejemplo
from tiendas_sm.respaldo import respaldar, revisar_al_abrir
from tiendas_sm.telemetria import Telemetria

CARPETA_DE_DATOS = "TIENDAS_SM"
ARCHIVO_DE_DATOS = "tiendas_sm.db"
OPCION_DATOS_DE_EJEMPLO = "--datos-de-ejemplo"
ARCHIVO_DE_TELEMETRIA = "telemetria.jsonl"
TASA_DE_MUESTREO = 0.2                       # ADR-13: errores al 100 %, ventas exitosas al 20 %
TAMANO_MAXIMO_LOG = 1_000_000                # ADR-13: 1 MB por archivo...
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


def usar_escala_de_windows():
    """En Windows con escala de pantalla (125 %, 150 %…) evita que la ventana se vea borrosa."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (ImportError, AttributeError, OSError):
        pass                                                  # otro sistema operativo: no hace falta


def main(argumentos):
    import tkinter as tk                                      # se importa aquí para que las pruebas no lo necesiten
    from interfaz_tk.ventana_punto_de_venta import VentanaPuntoDeVenta
    from tiendas_sm.presentador import PresentadorPuntoDeVenta

    usar_escala_de_windows()
    ruta = ruta_de_datos()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    telemetria = configurar_telemetria(ruta.parent)
    problema = revisar_al_abrir(ruta, telemetria)            # FPI-30: no se vende sobre una base dañada
    if problema:
        mostrar_base_danada(tk, problema)
        return
    app, cargo_ejemplo = abrir_aplicacion(ruta, OPCION_DATOS_DE_EJEMPLO in argumentos, telemetria)
    print(f"Base de datos: {ruta}")
    if cargo_ejemplo:
        print("Se cargaron datos de ejemplo ficticios.")
    raiz = tk.Tk()
    VentanaPuntoDeVenta(raiz, PresentadorPuntoDeVenta(app))
    try:
        raiz.mainloop()
    finally:
        respaldo = cerrar_y_respaldar(app, ruta, telemetria)
        print(f"Respaldo: {respaldo}" if respaldo else "No se creó el respaldo: revise la base con el Runbook.")


def mostrar_base_danada(tk, mensaje):
    from tkinter import messagebox
    raiz = tk.Tk()
    raiz.withdraw()
    messagebox.showerror("TIENDAS S.M", mensaje, parent=raiz)
    raiz.destroy()


if __name__ == "__main__":
    main(sys.argv[1:])

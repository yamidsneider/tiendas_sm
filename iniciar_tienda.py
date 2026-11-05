"""Abre la aplicación de escritorio de TIENDAS S.M (punto de venta, tarea 8).

Uso:  python iniciar_tienda.py                      abre la tienda con los datos guardados
      python iniciar_tienda.py --datos-de-ejemplo   además carga datos FICTICIOS si la base está vacía

Los datos se guardan en la carpeta de datos del usuario (DDS §14):
%LOCALAPPDATA%\\TIENDAS_SM\\tiendas_sm.db en Windows. Para un respaldo manual (RNF-08) basta copiar ese archivo.
"""
import os
import sys
from pathlib import Path

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.datos_de_ejemplo import cargar_datos_de_ejemplo

CARPETA_DE_DATOS = "TIENDAS_SM"
ARCHIVO_DE_DATOS = "tiendas_sm.db"
OPCION_DATOS_DE_EJEMPLO = "--datos-de-ejemplo"


def ruta_de_datos(entorno=os.environ):
    """En Windows usa %LOCALAPPDATA%; si no existe esa variable (otro sistema), la carpeta personal."""
    base = Path(entorno.get("LOCALAPPDATA") or Path.home())
    return base / CARPETA_DE_DATOS / ARCHIVO_DE_DATOS


def abrir_aplicacion(ruta, con_datos_de_ejemplo):
    """Crea la carpeta si falta y abre la base. Devuelve (app, True si cargó los datos de ejemplo)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    app = Aplicacion(str(ruta))
    return app, con_datos_de_ejemplo and cargar_datos_de_ejemplo(app)


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
    app, cargo_ejemplo = abrir_aplicacion(ruta, OPCION_DATOS_DE_EJEMPLO in argumentos)
    print(f"Base de datos: {ruta}")
    if cargo_ejemplo:
        print("Se cargaron datos de ejemplo ficticios.")
    raiz = tk.Tk()
    VentanaPuntoDeVenta(raiz, PresentadorPuntoDeVenta(app))
    try:
        raiz.mainloop()
    finally:
        app.conexion.close()


if __name__ == "__main__":
    main(sys.argv[1:])

"""Arma dist/TIENDAS_SM.exe con PyInstaller (opción B en DECISIONES).

Uso (una sola vez, en la carpeta del proyecto):
    python -m venv .venv
    .venv\\Scripts\\python -m pip install -r requirements-escritorio.txt
    .venv\\Scripts\\python construir_exe.py

El .exe trae Python, pywebview y la página adentro; quien lo use no necesita instalar nada.
Los datos NO van dentro del .exe: se guardan en %LOCALAPPDATA%\\TIENDAS_SM, como siempre.
"""
import os

import PyInstaller.__main__

OPCIONES = [
    "iniciar_tienda.py",
    "--name=TIENDAS_SM",
    "--onefile",                                              # un solo archivo .exe
    "--windowed",                                             # sin la ventana negra de consola
    "--noconfirm",                                            # reemplaza el .exe anterior sin preguntar
    f"--add-data=interfaz_web/estatico{os.pathsep}interfaz_web/estatico",   # la página va dentro del .exe
]

if __name__ == "__main__":
    PyInstaller.__main__.run(OPCIONES)

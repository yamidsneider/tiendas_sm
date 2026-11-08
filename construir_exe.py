"""Arma dist/TIENDAS_SM.exe con PyInstaller (opción B en DECISIONES) y, si se pide, el acceso directo en el escritorio.

Uso (en la carpeta del proyecto):
    python -m venv .venv
    .venv\\Scripts\\python -m pip install -r requirements-escritorio.txt
    .venv\\Scripts\\python construir_exe.py                    arma el .exe
    .venv\\Scripts\\python construir_exe.py --acceso-directo   además crea «TIENDAS S.M» en el escritorio

El .exe trae Python, pywebview y la página adentro; quien lo use no necesita instalar nada.
Los datos NO van dentro del .exe: se guardan en %LOCALAPPDATA%\\TIENDAS_SM, como siempre.
El ícono (interfaz_web/icono.ico) lo genera scripts/generar_icono.py.
"""
import os
import subprocess
import sys
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
EXE = CARPETA / "dist" / "TIENDAS_SM.exe"
ICONO = Path("interfaz_web") / "icono.ico"
OPCION_ACCESO_DIRECTO = "--acceso-directo"
NOMBRE_DEL_ACCESO_DIRECTO = "TIENDAS S.M.lnk"

OPCIONES = [
    "iniciar_tienda.py",
    "--name=TIENDAS_SM",
    "--onefile",                                              # un solo archivo .exe
    "--windowed",                                             # sin la ventana negra de consola
    "--noconfirm",                                            # reemplaza el .exe anterior sin preguntar
    f"--icon={ICONO}",                                        # el ícono del archivo y de la barra de tareas
    f"--add-data=interfaz_web/estatico{os.pathsep}interfaz_web/estatico",   # la página va dentro del .exe
]


def _texto_para_powershell(ruta):
    """Entre comillas simples de PowerShell, una comilla simple se escribe doble."""
    return str(ruta).replace("'", "''")


def crear_acceso_directo(exe=EXE):
    """Crea el acceso directo en el escritorio del usuario con el objeto WScript.Shell de Windows."""
    orden = ("$escritorio=[Environment]::GetFolderPath('Desktop');"
             f"$a=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $escritorio '{NOMBRE_DEL_ACCESO_DIRECTO}'));"
             f"$a.TargetPath='{_texto_para_powershell(exe)}';$a.WorkingDirectory='{_texto_para_powershell(exe.parent)}';"
             f"$a.IconLocation='{_texto_para_powershell(exe)},0';$a.Description='TIENDAS S.M';$a.Save()")
    subprocess.run(["powershell", "-NoProfile", "-Command", orden], check=True)


def main(argumentos):
    import PyInstaller.__main__                               # solo existe en el entorno .venv de escritorio
    os.chdir(CARPETA)
    PyInstaller.__main__.run(OPCIONES)
    if OPCION_ACCESO_DIRECTO in argumentos:
        crear_acceso_directo()
        print("Acceso directo creado en el escritorio: TIENDAS S.M")


if __name__ == "__main__":
    main(sys.argv[1:])

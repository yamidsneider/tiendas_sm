"""Selección de pruebas de regresión según los archivos que cambiaron (FPI-15).

Uso:
  python correr_regresion.py tiendas_sm/servicios.py          # solo lo relacionado con ese cambio
  python correr_regresion.py --desde-git                      # usa los archivos cambiados respecto a main
  python correr_regresion.py --todo                           # toda la suite

Idea: un cambio puede dañar el módulo modificado y todo lo que lo usa. El mapa dice, para cada módulo,
qué archivos de pruebas lo ejercitan directa o indirectamente. El pipeline de CI corre SIEMPRE la suite
completa (hoy tarda menos de 1 segundo); este script sirve para correr rápido en el computador y para
justificar la selección cuando la suite crezca.
"""
import subprocess
import sys
import unittest

PRUEBAS = {
    "unitarias": "tests.test_unitarias_dobles",
    "integracion": "tests.test_integracion_incremental",
    "comportamiento": "tests.test_comportamiento",
    "caja_negra": "tests.test_caja_negra",
    "defectos": "tests.test_defectos_corregidos",
    "contado": "tests.test_venta_de_contado",
    "arquitectura": "tests.test_arquitectura",
    "presentador": "tests.test_presentador",
    "arranque": "tests.test_iniciar_tienda",
    "ventana": "tests.test_interfaz_tk",
    "escenarios": "tests.test_escenarios_calidad",
    "migracion": "tests.test_migracion_esquema",
    "medidor": "tests.test_medir_cobertura",
}
TODAS = list(PRUEBAS.values())

# módulo cambiado -> pruebas que lo ejercitan (directa o indirectamente)
MAPA = {
    "tiendas_sm/validaciones.py": TODAS,                      # lo usan casi todas las clases del dominio
    "tiendas_sm/dominio.py": TODAS,                           # base de todo el sistema
    "tiendas_sm/repositorios.py": [PRUEBAS[k] for k in ("integracion", "comportamiento", "caja_negra", "defectos", "contado", "escenarios")],
    "tiendas_sm/base_de_datos.py": [PRUEBAS[k] for k in ("integracion", "comportamiento", "caja_negra", "defectos", "contado", "escenarios",
                                                         "migracion")],
    "tiendas_sm/servicios.py": TODAS,                         # controles, ventas y productos
    "tiendas_sm/puertos.py": TODAS,                           # contratos que usan servicios y repositorios
    "tiendas_sm/presentador.py": [PRUEBAS[k] for k in ("presentador", "ventana")],
    "tiendas_sm/datos_de_ejemplo.py": [PRUEBAS["arranque"]],
    "interfaz_tk/ventana_punto_de_venta.py": [PRUEBAS["ventana"]],
    "iniciar_tienda.py": [PRUEBAS["arranque"]],
    "medir_cobertura.py": [PRUEBAS["medidor"]],
    "tiendas_sm/aplicacion.py": [PRUEBAS[k] for k in ("comportamiento", "caja_negra", "defectos", "contado")],
}
DOCUMENTACION = ("README.md", "docs/", ".github/", "evidencia_")


def archivos_desde_git():
    salida = subprocess.run(["git", "diff", "--name-only", "origin/main...HEAD"], capture_output=True, text=True)
    return [linea for linea in salida.stdout.split() if linea]


def seleccionar(archivos):
    elegidas, sin_mapa = [], []
    for archivo in archivos:
        archivo = archivo.replace("\\", "/")
        if archivo.startswith("tests/"):
            modulo = "tests." + archivo[len("tests/"):-3]
            elegidas.append(modulo)
        elif archivo in MAPA:
            elegidas += MAPA[archivo]
        elif archivo.startswith(DOCUMENTACION):
            continue                                           # no afecta al comportamiento
        else:
            sin_mapa.append(archivo)
    return sorted(set(elegidas)), sin_mapa


def main(argumentos):
    if not argumentos or argumentos == ["--todo"]:
        modulos, sin_mapa = TODAS, []
    else:
        archivos = archivos_desde_git() if argumentos == ["--desde-git"] else argumentos
        modulos, sin_mapa = seleccionar(archivos)
    if sin_mapa:
        print("Archivos sin regla en el mapa (se corre toda la suite por seguridad):", sin_mapa)
        modulos = TODAS
    if not modulos:
        print("Los cambios no afectan al comportamiento: no hace falta correr pruebas de regresión.")
        return 0
    print("Pruebas de regresión seleccionadas:")
    for modulo in modulos:
        print("  -", modulo)
    suite = unittest.defaultTestLoader.loadTestsFromNames(modulos)
    resultado = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

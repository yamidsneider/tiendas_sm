"""Cobertura de líneas con el módulo estándar `trace` (no requiere instalar nada).
Uso: python medir_cobertura.py [--minimo 90]   (desde la carpeta del proyecto)
Con --minimo, termina con error si la cobertura es menor (así lo usa el pipeline de CI)."""
import io
import sys
import trace
import unittest
from pathlib import Path

PAQUETE = Path("tiendas_sm").resolve()


def lineas_validas(numeros):
    """TD-05: en Python 3.13 trace puede entregar None como número de línea; se descartan junto con la 0."""
    return {numero for numero in numeros if numero}


def lineas_ejecutables(ruta):
    return lineas_validas(trace._find_executable_linenos(str(ruta)))


def main(minimo=None):
    seguimiento = trace.Trace(count=1, trace=0, ignoredirs=[sys.prefix, sys.exec_prefix])

    def correr_pruebas():
        # el descubrimiento (que importa el código) también debe quedar dentro de la medición
        suite = unittest.defaultTestLoader.discover("tests")
        return unittest.TextTestRunner(stream=io.StringIO()).run(suite)

    resultado = seguimiento.runfunc(correr_pruebas)
    print(f"Pruebas ejecutadas: {resultado.testsRun} | fallos: {len(resultado.failures)} | errores: {len(resultado.errors)}")
    contadas = {}
    for (archivo, linea), veces in seguimiento.results().counts.items():
        contadas.setdefault(Path(archivo).resolve(), set()).update(lineas_validas([linea]))
    total = cubiertas = 0
    print(f"{'archivo':24}{'ejecutables':>12}{'cubiertas':>11}{'%':>7}  líneas sin cubrir")
    for ruta in sorted(PAQUETE.glob("*.py")):
        ejecutables = lineas_ejecutables(ruta)
        if not ejecutables:
            continue
        hechas = ejecutables & contadas.get(ruta, set())
        faltan = sorted(ejecutables - hechas)
        total += len(ejecutables); cubiertas += len(hechas)
        print(f"{ruta.name:24}{len(ejecutables):>12}{len(hechas):>11}{100*len(hechas)/len(ejecutables):>6.0f}%  {faltan if faltan else ''}")
    porcentaje = 100 * cubiertas / total
    print(f"\nTOTAL: {cubiertas}/{total} líneas = {porcentaje:.1f}% de cobertura de líneas")
    if resultado.failures or resultado.errors:
        print("Hay pruebas que fallan: la cobertura no es válida.")
        return 1
    if minimo is not None and porcentaje < minimo:
        print(f"ERROR: la cobertura {porcentaje:.1f}% es menor que el mínimo exigido ({minimo}%).")
        return 1
    return 0


if __name__ == "__main__":
    umbral = float(sys.argv[sys.argv.index("--minimo") + 1]) if "--minimo" in sys.argv else None
    sys.exit(main(umbral))

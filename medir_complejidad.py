"""Complejidad ciclomática V(G) = decisiones + 1 (McCabe), contando if, for, while, and/or,
except y condiciones de comprensiones. Uso: python medir_complejidad.py tiendas_sm [umbral]"""
import ast
import sys
from pathlib import Path


def decisiones(funcion):
    total = 0
    for nodo in ast.walk(funcion):
        if isinstance(nodo, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.IfExp)):
            total += 1
        elif isinstance(nodo, ast.BoolOp):
            total += len(nodo.values) - 1
        elif isinstance(nodo, ast.comprehension):
            total += 1 + len(nodo.ifs)
    return total


def main(carpeta, umbral=1):
    filas = []
    for ruta in sorted(Path(carpeta).rglob("*.py")):
        for nodo in ast.walk(ast.parse(ruta.read_text(encoding="utf8"))):
            if isinstance(nodo, ast.FunctionDef):
                filas.append((decisiones(nodo) + 1, ruta.name, nodo.name))
    filas.sort(reverse=True)
    print(f"{'V(G)':>5}  {'archivo':20}{'función'}")
    for v, archivo, nombre in filas:
        if v >= umbral:
            print(f"{v:>5}  {archivo:20}{nombre}")
    print(f"\nfunciones: {len(filas)} | promedio V(G): {sum(f[0] for f in filas)/len(filas):.2f} | máximo: {filas[0][0]}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)

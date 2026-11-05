"""Prueba de arquitectura (ADR-04, FPI-20, "hexagonal ligero").

El núcleo (dominio, servicios y los contratos de puertos.py) no debe depender de la
base de datos: ni de sqlite3 ni del módulo de repositorios. Se revisan los import con
el módulo ast (se lee el código, no se ejecuta). Si alguien agrega uno de esos
import en el núcleo, esta prueba falla y dice en qué archivo.
"""
import ast
import unittest
from pathlib import Path

PAQUETE = Path(__file__).resolve().parent.parent / "tiendas_sm"
ARCHIVOS_DEL_NUCLEO = ("dominio.py", "servicios.py", "puertos.py")
IMPORTS_PROHIBIDOS = ("sqlite3", "tiendas_sm.repositorios")


def modulos_importados(ruta):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            yield from (alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            yield nodo.module


def es_prohibido(modulo):
    return any(modulo == prohibido or modulo.startswith(prohibido + ".") for prohibido in IMPORTS_PROHIBIDOS)


class PruebasDeArquitectura(unittest.TestCase):
    def test_el_nucleo_no_importa_la_base_de_datos(self):
        for nombre in ARCHIVOS_DEL_NUCLEO:
            with self.subTest(archivo=nombre):
                prohibidos = [m for m in modulos_importados(PAQUETE / nombre) if es_prohibido(m)]
                self.assertEqual(prohibidos, [], f"{nombre} no debe importar {prohibidos}")

    def test_la_revision_detecta_un_import_prohibido(self):
        """Comprueba que la prueba de arriba sí sabe fallar (no pasa por estar mal escrita)."""
        self.assertTrue(es_prohibido("sqlite3"))
        self.assertTrue(es_prohibido("tiendas_sm.repositorios"))
        self.assertFalse(es_prohibido("tiendas_sm.dominio"))


if __name__ == "__main__":
    unittest.main()

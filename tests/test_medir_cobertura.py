"""TD-05: medir_cobertura.py fallaba en Python 3.13 con
"TypeError: '<' not supported between instances of 'int' and 'NoneType'", porque el módulo trace
puede entregar números de línea None y luego se ordenan. Aquí se simula esa entrada (este equipo
solo tiene Python 3.12), así que la prueba no depende de la versión instalada.
"""
import unittest

from medir_cobertura import lineas_validas


class PruebasTd05LineasNone(unittest.TestCase):
    def test_descarta_none_y_la_linea_cero(self):
        self.assertEqual(lineas_validas([3, None, 0, 1, None, 3]), {1, 3})

    def test_el_resultado_se_puede_ordenar_como_hace_el_reporte(self):
        self.assertEqual(sorted(lineas_validas([None, 7, 2])), [2, 7])

    def test_sin_lineas_devuelve_un_conjunto_vacio(self):
        self.assertEqual(lineas_validas([None, 0]), set())


if __name__ == "__main__":
    unittest.main()

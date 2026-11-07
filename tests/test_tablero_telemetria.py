"""FPI-30 (ADR-14): el tablero separa los rechazos de negocio de las fallas técnicas, con la lista de slo_mensual.py.

Un «Solo hay N disponibles» es el sistema funcionando bien; un OperationalError es una falla. Además, solo las
ventas cuentan como ventas: los spans de la revisión de la base (abrir_base, respaldar_base) no.
"""
import unittest

from slo_mensual import RECHAZOS_DE_NEGOCIO, calcular
from tablero_telemetria import generar, resumir


def registro(estado="OK", tipo=None, nombre="registrar_venta", ms=2.0):
    r = {"marca_tiempo": "2026-11-06T15:00:00.000+00:00", "nombre": nombre, "estado": estado, "duracion_ms": ms}
    if tipo:
        r["error.tipo"] = tipo
    return r


class PruebasDelTablero(unittest.TestCase):
    def test_rechazo_de_negocio_no_cuenta_como_falla(self):
        fila = resumir([registro()] * 8 + [registro("ERROR", "StockInsuficiente")] * 2, tasa=1.0)[0]
        self.assertEqual(fila["fallas_tecnicas"], 0)
        self.assertEqual(fila["rechazos_de_negocio"], 2)
        self.assertEqual(fila["pct_fallas"], 0.0)

    def test_falla_tecnica_si_cuenta(self):
        fila = resumir([registro()] * 9 + [registro("ERROR", "OperationalError")], tasa=1.0)[0]
        self.assertEqual(fila["fallas_tecnicas"], 1)
        self.assertEqual(fila["pct_fallas"], 10.0)

    def test_usa_la_misma_lista_que_el_slo(self):
        for tipo in RECHAZOS_DE_NEGOCIO:
            with self.subTest(tipo=tipo):
                self.assertEqual(resumir([registro("ERROR", tipo)], tasa=1.0)[0]["fallas_tecnicas"], 0)

    def test_los_spans_de_la_base_no_son_ventas(self):
        registros = [registro()] * 4 + [registro(nombre="respaldar_base")] * 3 + [
            registro("ERROR", "BaseDeDatosDanada", nombre="abrir_base")]
        fila = resumir(registros, tasa=1.0)[0]
        self.assertEqual(fila["ventas_estimadas"], 4)
        self.assertEqual(fila["fallas_tecnicas"], 0)

    def test_el_html_muestra_las_dos_listas(self):
        filas = resumir([registro("ERROR", "StockInsuficiente"), registro("ERROR", "OperationalError")], tasa=1.0)
        pagina = generar(filas, 1.0)
        self.assertIn("Fallas técnicas por tipo", pagina)
        self.assertIn("Rechazos de negocio por tipo", pagina)


class PruebasDelSloConOtrosSpans(unittest.TestCase):
    def test_los_spans_de_la_base_no_cuentan_como_intentos_de_venta(self):
        r = calcular([registro()] * 10 + [registro(nombre="respaldar_base")] * 5, tasa=1.0)
        self.assertEqual(r["intentos_estimados"], 10)


if __name__ == "__main__":
    unittest.main()

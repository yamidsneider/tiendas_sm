"""FPI-30 (ADR-14): los rechazos de negocio no consumen presupuesto de error; las fallas técnicas sí."""
import unittest

from slo_mensual import calcular


def registro(estado="OK", tipo=None, ms=1.2):
    r = {"marca_tiempo": "2026-11-05T10:00:00-05:00", "estado": estado, "duracion_ms": ms}
    if tipo:
        r["error.tipo"] = tipo
    return r


class PruebasSLO(unittest.TestCase):
    def test_rechazo_de_negocio_no_es_falla(self):
        r = calcular([registro()] * 20 + [registro("ERROR", "StockInsuficiente")] * 5, tasa=0.2)
        self.assertEqual(r["fallas_tecnicas"], 0)
        self.assertEqual(r["sli_exito_tecnico"], 100.0)

    def test_falla_tecnica_consume_presupuesto(self):
        r = calcular([registro()] * 199 + [registro("ERROR", "OperationalError", 5015)], tasa=1.0)
        self.assertEqual(r["intentos_estimados"], 200)
        self.assertEqual(r["sli_exito_tecnico"], 99.5)
        self.assertEqual(r["presupuesto_consumido_pct"], 100.0)

    def test_latencia_cuenta_solo_ventas_exitosas_lentas(self):
        r = calcular([registro()] * 99 + [registro(ms=1500)], tasa=1.0)
        self.assertEqual(r["sli_latencia"], 99.0)

    def test_sin_datos(self):
        self.assertEqual(calcular([], tasa=0.2)["sli_exito_tecnico"], 100.0)


if __name__ == "__main__":
    unittest.main()

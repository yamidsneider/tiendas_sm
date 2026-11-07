"""FPI-29 (ADR-13): telemetría ligera — span, métrica y log JSON, muestreo y ausencia de datos personales."""
import json
import unittest

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import StockInsuficiente
from tiendas_sm.telemetria import Telemetria

NOMBRE_FICTICIO = "Cliente Ficticio Telemetría"
CEDULA_FICTICIA = "1090000000"


class PruebasTelemetria(unittest.TestCase):
    def armar(self, tasa):
        self.lineas = []
        self.tel = Telemetria(escribir=self.lineas.append, tasa_muestreo=tasa)
        self.app = Aplicacion(telemetria=self.tel)
        self.p = self.app.productos.registrar_producto("Arroz ficticio", 1000, 1500, 5)
        self.c = self.app.clientes.registrar_cliente(f"{NOMBRE_FICTICIO} {CEDULA_FICTICIA}", True, 100000, 30)

    def test_venta_emite_span_con_ids_y_log_json(self):
        self.armar(tasa=1.0)
        self.app.ventas.registrar_venta_a_credito(self.c.id_cliente, [(self.p.id_producto, 2)])
        registro = json.loads(self.lineas[0])
        self.assertEqual(len(registro["trace_id"]), 32)
        self.assertEqual(len(registro["span_id"]), 16)
        self.assertEqual(registro["estado"], "OK")
        self.assertEqual(registro["atributos"], {"venta.tipo": "CREDITO", "venta.lineas": 1,
                                                 "venta.unidades": 2, "venta.total": 3000})

    def test_error_se_registra_siempre_aunque_no_haya_muestreo(self):
        self.armar(tasa=0.0)
        with self.assertRaises(StockInsuficiente):
            self.app.ventas.registrar_venta_de_contado([(self.p.id_producto, 99)], 1_000_000)
        self.app.ventas.registrar_venta_de_contado([(self.p.id_producto, 1)], 2000)
        self.assertEqual(len(self.lineas), 1)
        self.assertEqual(json.loads(self.lineas[0])["error.tipo"], "StockInsuficiente")

    def test_metricas_cuentan_todo_aunque_no_se_registre(self):
        self.armar(tasa=0.0)
        self.app.ventas.registrar_venta_de_contado([(self.p.id_producto, 1)], 2000)
        self.assertEqual(self.tel.contadores[("registrar_venta", "OK", "")], 1)
        self.assertIn('estado="OK",error=""} 1', self.tel.exportar_prometheus())

    def test_ningun_dato_personal_llega_a_la_telemetria(self):
        self.armar(tasa=1.0)
        self.app.ventas.registrar_venta_a_credito(self.c.id_cliente, [(self.p.id_producto, 1)])
        with self.assertRaises(Exception):
            self.app.ventas.registrar_venta_a_credito(self.c.id_cliente, [(self.p.id_producto, 99)])
        todo = "\n".join(self.lineas) + self.tel.exportar_prometheus()
        for prohibido in (NOMBRE_FICTICIO, CEDULA_FICTICIA, "id_cliente", "nombres"):
            self.assertNotIn(prohibido, todo)

    def test_atributo_no_permitido_se_descarta(self):
        tel = Telemetria(escribir=(lineas := []).append, tasa_muestreo=1.0)
        with tel.span("prueba", **{"cliente.cedula": CEDULA_FICTICIA, "venta.tipo": "CONTADO"}):
            pass
        self.assertNotIn(CEDULA_FICTICIA, lineas[0])

    def test_sin_telemetria_la_aplicacion_no_cambia(self):
        app = Aplicacion()
        self.assertEqual(type(app.ventas).__name__, "ServicioDeVentas")

    def test_tasa_invalida(self):
        with self.assertRaises(ValueError):
            Telemetria(tasa_muestreo=1.5)


class PruebasArchivoDeTelemetria(unittest.TestCase):
    def test_iniciar_tienda_escribe_json_en_la_carpeta_de_datos(self):
        import logging
        import tempfile
        from pathlib import Path
        import iniciar_tienda
        with tempfile.TemporaryDirectory() as carpeta:
            tel = iniciar_tienda.configurar_telemetria(Path(carpeta))
            tel.tasa_muestreo = 1.0
            app, _ = iniciar_tienda.abrir_aplicacion(Path(carpeta) / "t.db", False, tel)
            p = app.productos.registrar_producto("Arroz ficticio", 1000, 1500, 5)
            app.ventas.registrar_venta_de_contado([(p.id_producto, 1)], 2000)
            app.conexion.close()
            registro = logging.getLogger("tiendas_sm.telemetria")
            for manejador in list(registro.handlers):
                manejador.close()
                registro.removeHandler(manejador)
            linea = (Path(carpeta) / "telemetria.jsonl").read_text(encoding="utf-8").splitlines()[0]
            self.assertEqual(json.loads(linea)["atributos"]["venta.tipo"], "CONTADO")


if __name__ == "__main__":
    unittest.main()

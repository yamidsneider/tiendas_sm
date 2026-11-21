"""Reportes de ventas (fase 1 de docs/HOJA_DE_RUTA_APP_COMPLETA.md; aprobada por el desarrollador, noviembre de 2026).

Para un periodo (hoy, últimos 7 días o este mes) el reporte dice: cuántas ventas hubo, cuánto se vendió, cuánto se
devolvió, cuánto entró por cada forma de pago (efectivo, transferencia, fiado), cuánto se recibió en abonos, la
ganancia (precio de venta − precio de compra de lo vendido) y los productos más vendidos.
Para que la ganancia no cambie si después sube el precio de compra, cada línea de la venta guarda el costo con que
se vendió (igual que guarda el precio, HU-02). Las ventas viejas no lo tienen: usan el precio de compra actual y el
reporte avisa que esa ganancia es estimada. *Preliminar:* qué cuenta como ganancia se confirma con el propietario.
Se escribieron antes del código. Datos ficticios.
"""
import unittest
from datetime import datetime, timedelta

from interfaz_web.api import ApiDeLaTienda
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.presentador_reportes import PresentadorDeReportes
from tiendas_sm.servicios import Periodo, rango_del_periodo

MOTIVO = "Cliente se arrepintió (prueba)"


class PruebasDelRango(unittest.TestCase):
    AHORA = datetime(2026, 11, 21, 15, 30)

    def test_hoy_va_desde_la_medianoche_hasta_mañana(self):
        self.assertEqual(rango_del_periodo(Periodo.HOY, self.AHORA),
                         (datetime(2026, 11, 21), datetime(2026, 11, 22)))

    def test_semana_son_los_ultimos_7_dias_contando_hoy(self):
        self.assertEqual(rango_del_periodo(Periodo.SEMANA, self.AHORA),
                         (datetime(2026, 11, 15), datetime(2026, 11, 22)))

    def test_mes_va_desde_el_dia_1(self):
        self.assertEqual(rango_del_periodo(Periodo.MES, self.AHORA),
                         (datetime(2026, 11, 1), datetime(2026, 11, 22)))


class BaseDeReportes(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio", 1000, 1500, 10)
        self.cafe = self.app.productos.registrar_producto("Café ficticio", 2000, 3000, 10)
        self.ana = self.app.clientes.registrar_cliente("Cliente ficticio Ana", True, 100000)

    def vender_el_dia(self):
        """Contado en efectivo 2 arroz (3.000), mixto 1 café (3.000: 1.000 por transferencia) y fiado 1 arroz (1.500)."""
        self.efectivo = self.app.ventas.registrar_venta_de_contado([(self.arroz.id_producto, 2)], 3000)
        self.app.ventas.registrar_venta_de_contado([(self.cafe.id_producto, 1)], 2000, 1000)
        self.app.ventas.registrar_venta_a_credito(self.ana.id_cliente, [(self.arroz.id_producto, 1)])
        cuenta, = self.app.credito.cuentas_del_cliente(self.ana.id_cliente)
        self.app.credito.registrar_abono(cuenta.id_cuenta, 500)

    def resumen(self, periodo=Periodo.HOY, ahora=None):
        return self.app.reportes.reporte(periodo, ahora).resumen


class PruebasDelResumen(BaseDeReportes):
    def test_sin_ventas_todo_queda_en_cero(self):
        reporte = self.app.reportes.reporte(Periodo.HOY)
        self.assertEqual((reporte.resumen.numero_de_ventas, reporte.resumen.vendido, reporte.resumen.ganancia), (0, 0, 0))
        self.assertEqual(reporte.mas_vendidos, [])

    def test_suma_lo_vendido_por_forma_de_pago_y_los_abonos(self):
        self.vender_el_dia()
        resumen = self.resumen()
        self.assertEqual(resumen.numero_de_ventas, 3)
        self.assertEqual(resumen.vendido, 7500)
        self.assertEqual((resumen.efectivo, resumen.transferencia, resumen.credito), (5000, 1000, 1500))
        self.assertEqual(resumen.abonos, 500)

    def test_la_ganancia_es_venta_menos_compra_de_lo_vendido(self):
        self.vender_el_dia()
        self.assertEqual(self.resumen().ganancia, 3 * 500 + 1000)     # 3 arroz a 500 y 1 café a 1.000
        self.assertFalse(self.resumen().ganancia_estimada)

    def test_una_devolucion_resta_de_lo_vendido_y_de_la_ganancia(self):
        self.vender_el_dia()
        self.app.ventas.devolver(self.efectivo.id_venta, [(self.arroz.id_producto, 1)], MOTIVO)
        resumen = self.resumen()
        self.assertEqual((resumen.devuelto, resumen.efectivo_devuelto), (1500, 1500))
        self.assertEqual(resumen.neto, 6000)
        self.assertEqual(resumen.ganancia, 2500 - 500)

    def test_las_ventas_de_otro_dia_no_entran(self):
        self.vender_el_dia()
        pasado_mañana = datetime.now() + timedelta(days=2)
        self.assertEqual(self.resumen(Periodo.HOY, pasado_mañana).vendido, 0)
        self.assertEqual(self.resumen(Periodo.HOY, pasado_mañana).abonos, 0)

    def test_subir_el_precio_de_compra_despues_no_cambia_la_ganancia(self):
        self.vender_el_dia()
        self.app.productos.actualizar_producto(self.arroz.id_producto, "Arroz ficticio", 1400, 1500)
        self.assertEqual(self.resumen().ganancia, 2500)

    def test_la_venta_guarda_el_costo_de_cada_linea(self):
        venta = self.app.ventas.registrar_venta_de_contado([(self.cafe.id_producto, 1)], 3000)
        detalle, = self.app.ventas.obtener(venta.id_venta).detalles
        self.assertEqual(detalle.costo_unitario, 2000)

    def test_una_venta_vieja_sin_costo_usa_el_precio_de_compra_actual_y_avisa(self):
        self.vender_el_dia()
        with self.app.conexion:
            self.app.conexion.execute("UPDATE detalles_venta SET costo_unitario = NULL")    # como una base de antes
        self.app.productos.actualizar_producto(self.arroz.id_producto, "Arroz ficticio", 1200, 1500)
        resumen = self.resumen()
        self.assertEqual(resumen.ganancia, 3 * 300 + 1000)
        self.assertTrue(resumen.ganancia_estimada)


class PruebasDeLosMasVendidos(BaseDeReportes):
    def test_ordena_por_unidades_y_descuenta_las_devueltas(self):
        self.vender_el_dia()
        self.app.ventas.devolver(self.efectivo.id_venta, [(self.arroz.id_producto, 1)], MOTIVO)
        mas_vendidos = self.app.reportes.reporte(Periodo.HOY).mas_vendidos
        self.assertEqual([(p.nombre, p.unidades, p.valor) for p in mas_vendidos],
                         [("Arroz ficticio", 2, 3000), ("Café ficticio", 1, 3000)])

    def test_un_producto_devuelto_completo_no_aparece(self):
        venta = self.app.ventas.registrar_venta_de_contado([(self.cafe.id_producto, 1)], 3000)
        self.app.ventas.anular(venta.id_venta, MOTIVO)
        self.assertEqual(self.app.reportes.reporte(Periodo.HOY).mas_vendidos, [])


class PruebasDelPresentador(BaseDeReportes):
    def test_formatea_el_reporte_para_la_pantalla(self):
        self.vender_el_dia()
        datos = PresentadorDeReportes(self.app).reporte("hoy")
        self.assertEqual(datos["periodo"], "hoy")
        self.assertIn(("Vendido (neto)", "$ 7.500"), datos["tarjetas"])
        self.assertIn(("Ganancia", "$ 2.500"), datos["tarjetas"])
        self.assertIn(("Transferencia", "$ 1.000"), datos["formas"])
        self.assertEqual(datos["mas_vendidos"][0], ("Arroz ficticio", 3, "$ 4.500"))
        self.assertEqual(datos["nota"], "")

    def test_un_periodo_desconocido_muestra_hoy(self):
        self.assertEqual(PresentadorDeReportes(self.app).reporte("año")["periodo"], "hoy")

    def test_avisa_cuando_la_ganancia_es_estimada(self):
        self.vender_el_dia()
        with self.app.conexion:
            self.app.conexion.execute("UPDATE detalles_venta SET costo_unitario = NULL")
        self.assertIn("estimada", PresentadorDeReportes(self.app).reporte("mes")["nota"])

    def test_la_api_entrega_el_reporte_a_la_pagina(self):
        self.vender_el_dia()
        datos = ApiDeLaTienda(self.app).reporte("semana")
        self.assertEqual(datos["periodo"], "semana")
        self.assertEqual(datos["mas_vendidos"][0], ["Arroz ficticio", 3, "$ 4.500"])


if __name__ == "__main__":
    unittest.main()

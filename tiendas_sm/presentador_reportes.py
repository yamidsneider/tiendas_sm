"""Presentador de la sección Reportes (fase 1 de docs/HOJA_DE_RUTA_APP_COMPLETA.md).

No usa ninguna interfaz: arma el texto que la pantalla muestra (pesos con separador de miles) a partir de
ServicioDeReportes. No calcula nada: los totales vienen del servicio.
"""
from datetime import timedelta

from tiendas_sm.presentador import formato_pesos
from tiendas_sm.servicios import Periodo

FORMATO_FECHA = "%d/%m/%Y"
NOTA_ESTIMADA = ("La ganancia es estimada: hay ventas de antes de guardar el costo y para ellas se usó el precio "
                 "de compra actual.")


class PresentadorDeReportes:
    def __init__(self, app):
        self.app = app

    def reporte(self, periodo_texto):
        """Un periodo que no sea hoy, semana o mes muestra hoy."""
        periodo = Periodo(periodo_texto) if periodo_texto in {p.value for p in Periodo} else Periodo.HOY
        reporte = self.app.reportes.reporte(periodo)
        resumen = reporte.resumen
        return {
            "periodo": periodo.value,
            "rango": self._rango(reporte.desde, reporte.hasta),
            "tarjetas": [("Vendido (neto)", formato_pesos(resumen.neto)), ("Ganancia", formato_pesos(resumen.ganancia)),
                         ("Ventas", str(resumen.numero_de_ventas)), ("Abonos recibidos", formato_pesos(resumen.abonos))],
            "formas": [("Efectivo", formato_pesos(resumen.efectivo)), ("Transferencia", formato_pesos(resumen.transferencia)),
                       ("A crédito (fiado)", formato_pesos(resumen.credito)),
                       ("Devoluciones", formato_pesos(resumen.devuelto)),
                       ("Efectivo devuelto", formato_pesos(resumen.efectivo_devuelto)),
                       ("Salidas de mercancía (al costo)", formato_pesos(resumen.salidas_al_costo)),
                       ("Compras de mercancía", formato_pesos(resumen.compras))],
            "mas_vendidos": [(p.nombre, p.unidades, formato_pesos(p.valor)) for p in reporte.mas_vendidos],
            "nota": NOTA_ESTIMADA if resumen.ganancia_estimada else "",
        }

    @staticmethod
    def _rango(desde, hasta):
        """«21/11/2026» o «15/11/2026 al 21/11/2026» (hasta es la medianoche siguiente, se muestra el día anterior)."""
        ultimo_dia = hasta - timedelta(days=1)
        if desde == ultimo_dia:
            return f"{desde:{FORMATO_FECHA}}"
        return f"{desde:{FORMATO_FECHA}} al {ultimo_dia:{FORMATO_FECHA}}"

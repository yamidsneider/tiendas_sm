"""Telemetría ligera de TIENDAS S.M (FPI-29, ADR-13). Solo biblioteca estándar.

Emite los tres pilares con los nombres de OpenTelemetry, para poder cambiar después a su SDK
sin tocar los servicios:
- Traza: un span por operación, con trace_id (32 hex), span_id (16 hex), duración y estado.
- Métricas: contador de operaciones por resultado e histograma de duración (en memoria).
- Log estructurado: una línea JSON por span muestreado.

Privacidad (Ley 1581 de 2012): solo se registran los atributos de la LISTA BLANCA. Nombres,
cédulas, teléfonos, montos por cliente o el id del cliente nunca entran a la telemetría.
Muestreo: los errores se registran siempre; las operaciones exitosas, con la tasa configurada.
"""
import json
import secrets
import time
from contextlib import contextmanager
from datetime import datetime, timezone

ATRIBUTOS_PERMITIDOS = frozenset({"venta.tipo", "venta.lineas", "venta.unidades", "venta.total"})
LIMITES_MS = (1, 2, 5, 10, 25, 50, 100, 250, 500, 1000)
_ESCALA = 10_000


class Telemetria:
    def __init__(self, escribir=None, tasa_muestreo=0.2, servicio="tiendas_sm"):
        if not 0 <= tasa_muestreo <= 1:
            raise ValueError("La tasa de muestreo debe estar entre 0 y 1")
        self.escribir = escribir or (lambda linea: None)
        self.tasa_muestreo = tasa_muestreo
        self.servicio = servicio
        self.contadores = {}
        self.histogramas = {}

    @contextmanager
    def span(self, nombre, **atributos):
        registro = {"trace_id": secrets.token_hex(16), "span_id": secrets.token_hex(8),
                    "nombre": nombre, "atributos": self._filtrar(atributos)}
        inicio = time.perf_counter()
        try:
            yield registro["atributos"]
            registro["estado"] = "OK"
        except Exception as error:
            registro["estado"] = "ERROR"
            registro["error.tipo"] = type(error).__name__
            raise
        finally:
            registro["duracion_ms"] = round((time.perf_counter() - inicio) * 1000, 3)
            registro["atributos"] = self._filtrar(registro["atributos"])
            self._medir(registro)
            if registro["estado"] == "ERROR" or self._muestrear():
                self._registrar(registro)

    def _filtrar(self, atributos):
        return {k: v for k, v in atributos.items() if k in ATRIBUTOS_PERMITIDOS}

    def _muestrear(self):
        return secrets.randbelow(_ESCALA) < self.tasa_muestreo * _ESCALA

    def _medir(self, registro):
        clave = (registro["nombre"], registro["estado"], registro.get("error.tipo", ""))
        self.contadores[clave] = self.contadores.get(clave, 0) + 1
        self.histogramas.setdefault(registro["nombre"], []).append(registro["duracion_ms"])

    def _registrar(self, registro):
        linea = {"marca_tiempo": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                 "servicio": self.servicio, "nivel": "ERROR" if registro["estado"] == "ERROR" else "INFO"}
        linea.update(registro)
        self.escribir(json.dumps(linea, ensure_ascii=False))

    def exportar_prometheus(self):
        """Métricas en el formato de texto de Prometheus (por si algún día se conecta un servidor)."""
        lineas = ["# TYPE tiendas_operaciones_total counter"]
        for (nombre, estado, error), valor in sorted(self.contadores.items()):
            lineas.append(f'tiendas_operaciones_total{{operacion="{nombre}",estado="{estado}",error="{error}"}} {valor}')
        lineas.append("# TYPE tiendas_operacion_duracion_ms histogram")
        for nombre, duraciones in sorted(self.histogramas.items()):
            for limite in LIMITES_MS:
                acumulado = sum(1 for d in duraciones if d <= limite)
                lineas.append(f'tiendas_operacion_duracion_ms_bucket{{operacion="{nombre}",le="{limite}"}} {acumulado}')
            lineas.append(f'tiendas_operacion_duracion_ms_bucket{{operacion="{nombre}",le="+Inf"}} {len(duraciones)}')
            lineas.append(f'tiendas_operacion_duracion_ms_count{{operacion="{nombre}"}} {len(duraciones)}')
        return "\n".join(lineas) + "\n"


class VentasObservadas:
    """Adaptador: envuelve ServicioDeVentas sin cambiarlo y emite un span por venta."""

    def __init__(self, ventas, telemetria):
        self._ventas = ventas
        self._telemetria = telemetria

    def registrar_venta_a_credito(self, id_cliente, lineas):
        lineas = list(lineas)
        with self._telemetria.span("registrar_venta", **_describir("CREDITO", lineas)) as atributos:
            venta = self._ventas.registrar_venta_a_credito(id_cliente, lineas)
            atributos["venta.total"] = venta.calcular_total()
            return venta

    def registrar_venta_de_contado(self, lineas, recibido):
        lineas = list(lineas)
        with self._telemetria.span("registrar_venta", **_describir("CONTADO", lineas)) as atributos:
            venta = self._ventas.registrar_venta_de_contado(lineas, recibido)
            atributos["venta.total"] = venta.calcular_total()
            return venta

    def __getattr__(self, nombre):
        return getattr(self._ventas, nombre)


def _describir(tipo, lineas):
    return {"venta.tipo": tipo, "venta.lineas": len(lineas), "venta.unidades": sum(c for _, c in lineas)}

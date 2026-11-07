"""SLI/SLO y presupuesto de error de TIENDAS S.M (FPI-30, ADR-14). Solo biblioteca estándar.

Lee telemetria.jsonl (FPI-29). Los errores se registran al 100 %; las ventas exitosas con la tasa de
muestreo, así que el total se estima. Un rechazo de negocio (stock, crédito, efectivo, dato inválido)
es el sistema funcionando bien: NO consume presupuesto. Solo cuentan las fallas técnicas.

Uso: python slo_mensual.py telemetria.jsonl [--tasa 0.2] [--mes 2026-11]
"""
import argparse
import json

RECHAZOS_DE_NEGOCIO = {"StockInsuficiente", "CreditoNoPermitido", "EfectivoInsuficiente", "ValueError"}
SLO_EXITO_TECNICO = 99.5      # % de ventas sin falla técnica
SLO_LATENCIA = 99.0           # % de ventas exitosas en menos de 1 s (E-03)
UMBRAL_LATENCIA_MS = 1000
OPERACION_VENTA = "registrar_venta"   # FPI-30: abrir_base y respaldar_base también escriben spans, pero no son ventas


def solo_ventas(registros):
    """Un registro sin nombre se toma como venta (así eran los ejemplos del parche original)."""
    return [r for r in registros if r.get("nombre", OPERACION_VENTA) == OPERACION_VENTA]


def calcular(registros, tasa):
    registros = solo_ventas(registros)
    ok = [r for r in registros if r["estado"] == "OK"]
    negocio = [r for r in registros if r["estado"] == "ERROR" and r.get("error.tipo") in RECHAZOS_DE_NEGOCIO]
    tecnicas = [r for r in registros if r["estado"] == "ERROR" and r.get("error.tipo") not in RECHAZOS_DE_NEGOCIO]
    total = len(ok) / tasa + len(negocio) + len(tecnicas)
    lentas = sum(1 for r in ok if r["duracion_ms"] >= UMBRAL_LATENCIA_MS)
    sli_exito = 100 * (1 - len(tecnicas) / total) if total else 100.0
    sli_latencia = 100 * (1 - lentas / len(ok)) if ok else 100.0
    return {"intentos_estimados": round(total), "fallas_tecnicas": len(tecnicas), "rechazos_de_negocio": len(negocio),
            "sli_exito_tecnico": round(sli_exito, 3), "presupuesto_fallas": round(total * (100 - SLO_EXITO_TECNICO) / 100, 1),
            "presupuesto_consumido_pct": round(100 * len(tecnicas) / (total * (100 - SLO_EXITO_TECNICO) / 100), 1) if total else 0.0,
            "sli_latencia": round(sli_latencia, 3), "tipos_tecnicos": sorted({r.get("error.tipo") for r in tecnicas})}


def main():
    parser = argparse.ArgumentParser(description="SLI/SLO mensual de TIENDAS S.M")
    parser.add_argument("log")
    parser.add_argument("--tasa", type=float, default=0.2)
    parser.add_argument("--mes", default="")
    args = parser.parse_args()
    with open(args.log, encoding="utf-8") as archivo:
        registros = [json.loads(linea) for linea in archivo if linea.strip()]
    registros = [r for r in registros if r["marca_tiempo"].startswith(args.mes)]
    resultado = calcular(registros, args.tasa)
    for clave, valor in resultado.items():
        print(f"{clave}: {valor}")
    congelar = resultado["presupuesto_consumido_pct"] >= 100 or resultado["sli_latencia"] < SLO_LATENCIA
    print("POLÍTICA: " + ("PRESUPUESTO AGOTADO — congelar funciones nuevas y estabilizar (ADR-14)"
                          if congelar else "dentro del presupuesto — se puede seguir entregando"))
    return 1 if congelar else 0


if __name__ == "__main__":
    raise SystemExit(main())

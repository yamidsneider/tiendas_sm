"""Tablero local de observabilidad de TIENDAS S.M (FPI-29, ADR-13). Solo biblioteca estándar.

Lee el log JSON de telemetría y genera un HTML con tres paneles por día: ventas (tasa),
latencia p95 y porcentaje de errores. Los errores se registran al 100 %; las ventas exitosas
con la tasa de muestreo, así que su número se ESTIMA dividiendo por esa tasa.

Uso: python tablero_telemetria.py telemetria.jsonl tablero.html [--tasa 0.2]
"""
import argparse
import html
import json
import math
from collections import Counter, defaultdict

ANCHO, ALTO = 640, 170


def leer(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return [json.loads(linea) for linea in archivo if linea.strip()]


def p95(valores):
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    return ordenados[max(0, math.ceil(0.95 * len(ordenados)) - 1)]


def resumir(registros, tasa):
    por_dia = defaultdict(lambda: {"ok": 0, "error": 0, "duraciones": [], "tipos": Counter()})
    for r in registros:
        dia = por_dia[r["marca_tiempo"][:10]]
        dia["duraciones"].append(r["duracion_ms"])
        if r["estado"] == "ERROR":
            dia["error"] += 1
            dia["tipos"][r.get("error.tipo", "?")] += 1
        else:
            dia["ok"] += 1
    filas = []
    for fecha in sorted(por_dia):
        d = por_dia[fecha]
        ventas = d["ok"] / tasa if tasa else d["ok"]
        total = ventas + d["error"]
        filas.append({"fecha": fecha, "ventas_estimadas": round(ventas), "errores": d["error"],
                      "pct_error": round(100 * d["error"] / total, 1) if total else 0.0,
                      "p95_ms": round(p95(d["duraciones"]), 2), "tipos": dict(d["tipos"])})
    return filas


def barras(filas, campo, titulo, unidad, umbral=None):
    mayor = max([f[campo] for f in filas] + [1])
    dibujar_umbral = umbral is not None and umbral <= 1.5 * mayor
    maximo = max(mayor, umbral) if dibujar_umbral else mayor
    ancho_barra = (ANCHO - 60) / max(len(filas), 1)
    partes = [f'<svg viewBox="0 0 {ANCHO} {ALTO + 30}" role="img" aria-label="{html.escape(titulo)}">']
    for i, f in enumerate(filas):
        alto = (ALTO - 20) * f[campo] / maximo
        x, y = 50 + i * ancho_barra, ALTO - alto
        partes.append(f'<rect x="{x + 6:.1f}" y="{y:.1f}" width="{ancho_barra - 12:.1f}" height="{alto:.1f}" class="b"/>')
        partes.append(f'<text x="{x + ancho_barra / 2:.1f}" y="{y - 4:.1f}" class="v">{f[campo]}</text>')
        partes.append(f'<text x="{x + ancho_barra / 2:.1f}" y="{ALTO + 16}" class="e">{f["fecha"][5:]}</text>')
    if umbral is not None and not dibujar_umbral:
        partes.append(f'<text x="{ANCHO - 12}" y="14" class="ut">umbral {umbral} {unidad}: fuera de escala, muy por encima</text>')
    if dibujar_umbral:
        yu = ALTO - (ALTO - 20) * umbral / maximo
        partes.append(f'<line x1="50" x2="{ANCHO - 10}" y1="{yu:.1f}" y2="{yu:.1f}" class="u"/>'
                      f'<text x="{ANCHO - 12}" y="{yu - 4:.1f}" class="ut">umbral {umbral} {unidad}</text>')
    partes.append("</svg>")
    return f'<section><h2>{html.escape(titulo)}</h2>{"".join(partes)}</section>'


def generar(filas, tasa):
    errores = Counter()
    for f in filas:
        errores.update(f["tipos"])
    detalle = "".join(f"<li>{html.escape(t)}: {n}</li>" for t, n in errores.most_common())
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Tablero TIENDAS S.M</title>
<style>body{{font-family:system-ui,sans-serif;margin:24px;color:#1d2433;background:#fff}}h1{{font-size:20px}}
h2{{font-size:15px;margin:18px 0 4px}}svg{{width:100%;max-width:{ANCHO}px}}.b{{fill:#3b6fd8}}.v,.e{{font-size:11px;text-anchor:middle;fill:#1d2433}}
.u{{stroke:#c0392b;stroke-dasharray:4 3}}.ut{{font-size:10px;fill:#c0392b;text-anchor:end}}p,li{{font-size:13px}}</style></head><body>
<h1>TIENDAS S.M — Observabilidad de registrar_venta</h1>
<p>Fuente: log JSON de telemetría (ADR-13). Errores al 100 %; ventas exitosas muestreadas al {tasa:.0%} y estimadas. Sin datos personales.</p>
{barras(filas, "ventas_estimadas", "Tasa: ventas por día (estimada)", "ventas")}
{barras(filas, "p95_ms", "Latencia p95 por día (ms)", "ms", umbral=1000)}
{barras(filas, "pct_error", "Errores por día (%)", "%", umbral=10)}
<h2>Errores por tipo</h2><ul>{detalle}</ul></body></html>"""


def main():
    parser = argparse.ArgumentParser(description="Tablero local de telemetría")
    parser.add_argument("log")
    parser.add_argument("salida")
    parser.add_argument("--tasa", type=float, default=0.2)
    args = parser.parse_args()
    filas = resumir(leer(args.log), args.tasa)
    with open(args.salida, "w", encoding="utf-8") as archivo:
        archivo.write(generar(filas, args.tasa))
    for f in filas:
        print(f)


if __name__ == "__main__":
    main()

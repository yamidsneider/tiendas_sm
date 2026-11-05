"""Métricas de proceso del repositorio para la retrospectiva cuantitativa (FPI-16).

Solo usa la biblioteca estándar. Se ejecuta DENTRO de tu repositorio clonado.

  python calcular_metricas.py                          # métricas de Git (siempre disponibles)
  python calcular_metricas.py --prs prs.json --issues issues.json   # agrega Pull Requests e issues de GitHub

Para obtener los JSON necesitas la herramienta gh (https://cli.github.com) con sesión iniciada (gh auth login):
  gh pr list    --state all --limit 200 --json number,title,state,createdAt,mergedAt,closedAt,reviews,comments > prs.json
  gh issue list --state all --limit 200 --json number,title,state,createdAt,closedAt,labels > issues.json

El resultado sale en Markdown, listo para copiar a la tabla D de la FPI-16. Los números son reales: si el
diagnóstico no te gusta, el proceso es lo que se corrige, no el cálculo.
"""
import argparse
import json
import re
import statistics
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta


def ejecutar(comando, carpeta):
    resultado = subprocess.run(comando, cwd=carpeta, capture_output=True, text=True, encoding="utf8")
    if resultado.returncode != 0:
        sys.exit(f"Error al ejecutar {' '.join(comando)}:\n{resultado.stderr.strip()}")
    return resultado.stdout


def fecha(texto):
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def minutos(delta):
    return delta.total_seconds() / 60


def formato_duracion(valor_minutos):
    if valor_minutos < 60:
        return f"{valor_minutos:.0f} min"
    if valor_minutos < 60 * 48:
        return f"{valor_minutos / 60:.1f} h"
    return f"{valor_minutos / 1440:.1f} días"


# ------------------------------------------------------------------ Git
def leer_commits(carpeta, rama):
    salida = ejecutar(["git", "log", rama, "--format=%H%x1f%an%x1f%aI%x1f%s"], carpeta)
    commits = []
    for linea in salida.splitlines():
        sha, autor, fecha_iso, asunto = linea.split("\x1f", 3)
        commits.append({"sha": sha, "autor": autor, "fecha": fecha(fecha_iso), "asunto": asunto})
    return sorted(commits, key=lambda c: c["fecha"])


def metricas_git(commits, etiquetas):
    inicio, fin = commits[0]["fecha"], commits[-1]["fecha"]
    dias_periodo = max((fin.date() - inicio.date()).days + 1, 1)
    por_dia = Counter(c["fecha"].date() for c in commits)
    por_semana = Counter(c["fecha"].isocalendar()[:2] for c in commits)
    fin_de_semana = sum(c["fecha"].weekday() >= 5 for c in commits)
    madrugada = sum(c["fecha"].hour < 6 for c in commits)
    umbral_final = inicio + (fin - inicio) * 0.8
    ultimo_tramo = sum(c["fecha"] >= umbral_final for c in commits) if fin > inicio else len(commits)
    rafagas = sum(1 for anterior, actual in zip(commits, commits[1:])
                  if (actual["fecha"] - anterior["fecha"]) < timedelta(seconds=60))
    tipos = Counter((re.match(r"^(\w+)(\(.*?\))?!?:", c["asunto"]) or [None, "otro"])[1] for c in commits)
    prs = [c for c in commits if re.match(r"^Merge pull request #", c["asunto"])]
    return {
        "total": len(commits), "autores": len({c["autor"] for c in commits}), "inicio": inicio, "fin": fin,
        "dias_periodo": dias_periodo, "dias_con_actividad": len(por_dia),
        "dia_pico": max(por_dia.items(), key=lambda x: x[1]), "por_semana": dict(sorted(por_semana.items())),
        "pct_fin_de_semana": 100 * fin_de_semana / len(commits), "pct_madrugada": 100 * madrugada / len(commits),
        "pct_ultimo_tramo": 100 * ultimo_tramo / len(commits), "rafagas": rafagas, "tipos": tipos,
        "merges_pr": len(prs), "etiquetas": etiquetas,
    }


# ------------------------------------------------------------------ GitHub (JSON de gh)
def metricas_prs(prs):
    fusionados = [p for p in prs if p.get("mergedAt")]
    abiertos = [p for p in prs if p["state"] == "OPEN"]
    cerrados = [p for p in prs if p["state"] == "CLOSED" and not p.get("mergedAt")]
    abierto_hasta_fusion = [minutos(fecha(p["mergedAt"]) - fecha(p["createdAt"])) for p in fusionados]
    primera_revision, con_revision, total_revisiones, total_comentarios = [], 0, 0, 0
    for p in prs:
        revisiones = [r for r in p.get("reviews", []) if r.get("submittedAt")]
        total_revisiones += len(revisiones)
        total_comentarios += len(p.get("comments", []))
        if revisiones:
            con_revision += 1
            primera_revision.append(minutos(min(fecha(r["submittedAt"]) for r in revisiones) - fecha(p["createdAt"])))
    return {"total": len(prs), "fusionados": len(fusionados), "abiertos": len(abiertos), "cerrados_sin_fusionar": len(cerrados),
            "tiempo_hasta_fusion": abierto_hasta_fusion, "primera_revision": primera_revision,
            "con_revision": con_revision, "total_revisiones": total_revisiones, "total_comentarios": total_comentarios}


def metricas_issues(issues):
    cerrados = [i for i in issues if i["state"] == "CLOSED" and i.get("closedAt")]
    resolucion = [minutos(fecha(i["closedAt"]) - fecha(i["createdAt"])) for i in cerrados]
    bugs = [i for i in issues if any(e.get("name", "").lower() == "bug" for e in i.get("labels", []))]
    return {"total": len(issues), "cerrados": len(cerrados), "abiertos": len(issues) - len(cerrados),
            "resolucion": resolucion, "bugs": len(bugs), "bugs_cerrados": sum(1 for b in bugs if b["state"] == "CLOSED")}


# ------------------------------------------------------------------ presentación
def resumen_tiempos(valores):
    if not valores:
        return "—"
    return f"promedio {formato_duracion(statistics.mean(valores))}, mediana {formato_duracion(statistics.median(valores))}, " \
           f"mínimo {formato_duracion(min(valores))}, máximo {formato_duracion(max(valores))}"


def barras(por_semana):
    if not por_semana:
        return ""
    mayor = max(por_semana.values())
    return "\n".join(f"  {año}-S{semana:02d} {'█' * max(1, round(20 * n / mayor))} {n}" for (año, semana), n in por_semana.items())


def imprimir(g, p, i):
    print("## Métricas del repositorio (calculadas, no estimadas)\n")
    print("| Métrica | Valor real |\n| --- | --- |")
    print(f"| Commits (rama analizada) | {g['total']} de {g['autores']} {'autor' if g['autores'] == 1 else 'autores'} |")
    print(f"| Período | {g['inicio']:%Y-%m-%d} a {g['fin']:%Y-%m-%d} ({g['dias_periodo']} días; {g['dias_con_actividad']} con commits) |")
    print(f"| Día con más commits | {g['dia_pico'][0]} ({g['dia_pico'][1]} commits, {100 * g['dia_pico'][1] / g['total']:.0f} % del total) |")
    print(f"| Commits en fin de semana / en madrugada (0–6 h) | {g['pct_fin_de_semana']:.0f} % / {g['pct_madrugada']:.0f} % |")
    print(f"| Commits en el último 20 % del período | {g['pct_ultimo_tramo']:.0f} % |")
    print(f"| Commits creados con menos de 60 s de diferencia | {g['rafagas']} |")
    print(f"| Pull Requests fusionados (merge commits «Merge pull request #») | {g['merges_pr']} |")
    print(f"| Releases (etiquetas) | {len(g['etiquetas'])}: {', '.join(g['etiquetas']) or '—'} |")
    print(f"| Tipos de commit | {', '.join(f'{k}: {v}' for k, v in g['tipos'].most_common())} |")
    if p:
        print(f"| Pull Requests (GitHub) | {p['total']} en total: {p['fusionados']} fusionados, {p['abiertos']} abiertos, {p['cerrados_sin_fusionar']} cerrados sin fusionar |")
        print(f"| Tiempo del PR abierto hasta fusionarse | {resumen_tiempos(p['tiempo_hasta_fusion'])} |")
        print(f"| Tiempo hasta la primera revisión | {resumen_tiempos(p['primera_revision'])} |")
        print(f"| PRs con al menos una revisión / revisiones / comentarios | {p['con_revision']} de {p['total']} / {p['total_revisiones']} / {p['total_comentarios']} |")
    if i:
        print(f"| Issues (GitHub) | {i['total']} en total: {i['cerrados']} cerrados, {i['abiertos']} abiertos |")
        print(f"| Tiempo de resolución de issues cerrados | {resumen_tiempos(i['resolucion'])} |")
        print(f"| Defectos (etiqueta bug) | {i['bugs']} ({i['bugs_cerrados']} cerrados) |")
    print("\nCommits por semana:\n" + barras(g["por_semana"]))

    señales = []
    if g["pct_fin_de_semana"] > 60: señales.append(f"{g['pct_fin_de_semana']:.0f} % de los commits son de fin de semana: trabajo poco distribuido.")
    if g["pct_madrugada"] > 30: señales.append(f"{g['pct_madrugada']:.0f} % de los commits son de madrugada: posible desgaste o trabajo a última hora.")
    if g["pct_ultimo_tramo"] > 50: señales.append(f"{g['pct_ultimo_tramo']:.0f} % de los commits están en el último 20 % del período: el trabajo se concentró al final.")
    if 100 * g["dia_pico"][1] / g["total"] > 50: señales.append("Más de la mitad de los commits se hicieron en un solo día.")
    if g["rafagas"] >= 5: señales.append(f"{g['rafagas']} commits se crearon con menos de 60 s de diferencia: suelen venir de scripts o de empaquetar trabajo ya hecho, no de trabajo incremental.")
    if g["dias_con_actividad"] < 4: señales.append("Hay actividad en muy pocos días distintos.")
    if p:
        if p["total"] and p["con_revision"] == 0: señales.append("Ningún PR tiene revisión registrada: el Code Review no quedó en GitHub.")
        if p["tiempo_hasta_fusion"] and statistics.median(p["tiempo_hasta_fusion"]) < 5: señales.append("La mediana entre abrir y fusionar un PR es menor a 5 minutos: revisión probablemente superficial.")
        if p["total_comentarios"] + p["total_revisiones"] == 0 and p["total"]: señales.append("Los PR no tienen comentarios ni revisiones: no hay evidencia de revisión técnica.")
    if i and i["abiertos"] > i["cerrados"]: señales.append("Hay más issues abiertos que cerrados.")
    print("\n## Señales de alerta para el diagnóstico")
    print("\n".join(f"- {s}" for s in señales) if señales else "- Ninguna señal automática. Aun así, léelas con tu propio criterio.")


def principal():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="carpeta del repositorio (por defecto, la actual)")
    parser.add_argument("--rama", default="main", help="rama a analizar (por defecto, main)")
    parser.add_argument("--prs", help="JSON de gh pr list")
    parser.add_argument("--issues", help="JSON de gh issue list")
    argumentos = parser.parse_args()
    commits = leer_commits(argumentos.repo, argumentos.rama)
    if not commits:
        sys.exit("La rama no tiene commits.")
    etiquetas = ejecutar(["git", "tag"], argumentos.repo).split()
    prs = metricas_prs(json.load(open(argumentos.prs, encoding="utf8"))) if argumentos.prs else None
    issues = metricas_issues(json.load(open(argumentos.issues, encoding="utf8"))) if argumentos.issues else None
    imprimir(metricas_git(commits, etiquetas), prs, issues)


if __name__ == "__main__":
    principal()

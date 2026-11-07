"""Respaldo automático verificado y revisión de integridad de la base (FPI-30, ADR-14, INC-SIM-01).

Es infraestructura, como base_de_datos.py: usa sqlite3 y por eso no forma parte del núcleo (ADR-04).
- Al abrir: PRAGMA quick_check (rápido). Si no da "ok", no se vende sobre una base dañada.
- Al cerrar: PRAGMA integrity_check (completo). Solo si da "ok" se copia con la API de respaldo de SQLite
  a respaldo_AAAA-MM-DDTHHMM.db, en la misma carpeta, y se conservan los 7 más recientes.
Un respaldo dañado con nombre de respaldo bueno sería peor que no tener respaldo: por eso se revisa antes.
"""
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from tiendas_sm.telemetria import Telemetria

RESPALDOS_A_CONSERVAR = 7
PATRON_DE_RESPALDOS = "respaldo_*.db"
REVISIONES = {"quick_check": "PRAGMA quick_check", "integrity_check": "PRAGMA integrity_check"}
RESULTADO_SANO = "ok"
MENSAJE_BASE_DANADA = ("La base de datos está dañada. No venda en el sistema: use el cuaderno y "
                       "llame al soporte (Runbook)")


class BaseDeDatosDanada(Exception):
    """Falla técnica: cuenta en el presupuesto de error del SLO (no es un rechazo de negocio)."""


def revisar_integridad(ruta, revision="quick_check"):
    """Devuelve "ok" si la base está sana; si no, el texto que dio SQLite. Abre en solo lectura: no crea archivos."""
    if revision not in REVISIONES:
        raise ValueError("La revisión debe ser quick_check o integrity_check")
    try:
        with closing(sqlite3.connect(Path(ruta).resolve().as_uri() + "?mode=ro", uri=True)) as conexion:
            return conexion.execute(REVISIONES[revision]).fetchone()[0]
    except sqlite3.DatabaseError as error:                    # «database disk image is malformed», etc.
        return str(error)


def revisar_al_abrir(ruta, telemetria=None):
    """Devuelve None si se puede abrir el punto de venta; si la base está dañada, el mensaje para la caja."""
    ruta = Path(ruta)
    if not ruta.exists():                                      # primera vez: la base todavía no existe
        return None
    return None if _esta_sana(ruta, "quick_check", "abrir_base", telemetria) else MENSAJE_BASE_DANADA


def respaldar(ruta, telemetria=None, ahora=None):
    """Respalda la base si está sana y deja solo los 7 respaldos más recientes. Devuelve la ruta o None."""
    ruta = Path(ruta)
    if not ruta.exists() or not _esta_sana(ruta, "integrity_check", "respaldar_base", telemetria):
        return None
    destino = ruta.parent / f"respaldo_{(ahora or datetime.now()):%Y-%m-%dT%H%M}.db"
    with closing(sqlite3.connect(ruta)) as origen, closing(sqlite3.connect(destino)) as copia:
        origen.backup(copia)
    _borrar_respaldos_viejos(ruta.parent)
    return destino


def _esta_sana(ruta, revision, operacion, telemetria):
    """La revisión va dentro de un span: si falla, la telemetría registra BaseDeDatosDanada (solo el tipo)."""
    try:
        with (telemetria or Telemetria()).span(operacion):
            resultado = revisar_integridad(ruta, revision)
            if resultado != RESULTADO_SANO:
                raise BaseDeDatosDanada(resultado)
    except BaseDeDatosDanada:
        return False
    return True


def _borrar_respaldos_viejos(carpeta):
    """El nombre lleva la fecha en formato ISO, así que el orden alfabético es el orden cronológico."""
    respaldos = sorted(carpeta.glob(PATRON_DE_RESPALDOS))
    for viejo in respaldos[:-RESPALDOS_A_CONSERVAR]:
        viejo.unlink()

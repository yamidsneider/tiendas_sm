"""Respaldo automático verificado y revisión de integridad de la base (FPI-30, ADR-14, INC-SIM-01).

Es infraestructura, como base_de_datos.py: usa sqlite3 y por eso no forma parte del núcleo (ADR-04).
- Al abrir: PRAGMA quick_check (rápido). Si no da "ok", no se vende sobre una base dañada.
- Al cerrar: PRAGMA integrity_check (completo). Solo si da "ok" se copia con la API de respaldo de SQLite
  a respaldo_AAAA-MM-DDTHHMM.db, en la misma carpeta, y se conservan los 7 más recientes.
Un respaldo dañado con nombre de respaldo bueno sería peor que no tener respaldo: por eso se revisa antes.

Fase 5 (ServicioDeRespaldos): además, una copia verificada en una carpeta visible del PC (respuesta del desarrollador),
al cerrar la app, al cerrar la caja y con «Respaldar ahora»; y restaurar una de esas copias desde la app.
"""
import sqlite3
from collections import namedtuple
from contextlib import closing
from datetime import datetime
from pathlib import Path

from tiendas_sm.base_de_datos import preparar_esquema
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


def _borrar_respaldos_viejos(carpeta, conservar=RESPALDOS_A_CONSERVAR, patron=PATRON_DE_RESPALDOS):
    """El nombre lleva la fecha en formato ISO, así que el orden alfabético es el orden cronológico."""
    respaldos = sorted(carpeta.glob(patron))
    for viejo in respaldos[:-conservar]:
        viejo.unlink()


# ---------------------------------------------------------------------- fase 5: carpeta del PC y restaurar
RESPALDOS_EN_LA_CARPETA = 30
PREFIJO_RESPALDO = "respaldo"
PREFIJO_SEGURIDAD = "antes_de_restaurar"          # el estado de justo antes de restaurar, por si se eligió mal
PATRONES_RESTAURABLES = (f"{PREFIJO_RESPALDO}_*.db", f"{PREFIJO_SEGURIDAD}_*.db")
CLAVE_DE_LA_CARPETA = "carpeta_respaldos"
SIN_CARPETA = "Elija primero la carpeta de los respaldos"
RESPALDO_INVALIDO = "Ese respaldo está dañado o no es de TIENDAS S.M; elija otro"
RespaldoGuardado = namedtuple("RespaldoGuardado", "nombre fecha tamano")


def copiar_verificado(conexion, carpeta, ahora=None, prefijo=PREFIJO_RESPALDO):
    """Copia la base abierta a carpeta/prefijo_AAAA-MM-DDTHHMMSS.db solo si integrity_check da «ok»."""
    resultado = conexion.execute(REVISIONES["integrity_check"]).fetchone()[0]
    if resultado != RESULTADO_SANO:
        raise BaseDeDatosDanada(resultado)
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / f"{prefijo}_{(ahora or datetime.now()):%Y-%m-%dT%H%M%S}.db"
    with closing(sqlite3.connect(destino)) as copia:
        conexion.backup(copia)
    _borrar_respaldos_viejos(carpeta, RESPALDOS_EN_LA_CARPETA, f"{prefijo}_*.db")
    return destino


def _fecha_del_nombre(archivo):
    """respaldo_2026-11-21T201530.db -> 21/11/2026 20:15:30. Si el nombre no la trae, la fecha del archivo."""
    try:
        return datetime.strptime(archivo.stem.rsplit("_", 1)[-1], "%Y-%m-%dT%H%M%S")
    except ValueError:
        return datetime.fromtimestamp(archivo.stat().st_mtime)


def _es_base_de_la_tienda(archivo):
    if revisar_integridad(archivo, "integrity_check") != RESULTADO_SANO:
        return False
    with closing(sqlite3.connect(Path(archivo).resolve().as_uri() + "?mode=ro", uri=True)) as conexion:
        tablas = {fila[0] for fila in conexion.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    return {"productos", "ventas"} <= tablas


class ServicioDeRespaldos:
    """Infraestructura (usa sqlite3), como el resto de este archivo. carpeta_por_defecto la pone iniciar_tienda.py;
    sin ella (pruebas, base en memoria) no se copia nada hasta que el jefe elija una carpeta."""

    def __init__(self, conexion, configuracion, carpeta_por_defecto=None):
        self.conexion = conexion
        self.configuracion = configuracion
        self.carpeta_por_defecto = Path(carpeta_por_defecto) if carpeta_por_defecto else None

    def carpeta(self):
        guardada = self.configuracion.obtener(CLAVE_DE_LA_CARPETA)
        return Path(guardada) if guardada else self.carpeta_por_defecto

    def cambiar_carpeta(self, texto):
        ruta = Path((texto or "").strip())
        if not (texto or "").strip() or not ruta.is_absolute():
            raise ValueError("Escriba la ruta completa de la carpeta, por ejemplo C:\\Respaldos de la tienda")
        try:
            ruta.mkdir(parents=True, exist_ok=True)
        except OSError:
            raise ValueError("No se pudo usar esa carpeta: revise la ruta o los permisos") from None
        self.configuracion.guardar(CLAVE_DE_LA_CARPETA, str(ruta))
        return ruta

    def respaldar_ahora(self, ahora=None):
        carpeta = self._exigir_carpeta()
        try:
            return copiar_verificado(self.conexion, carpeta, ahora)
        except BaseDeDatosDanada:
            raise ValueError(MENSAJE_BASE_DANADA) from None

    def listar(self):
        """Respaldos y copias de seguridad de la carpeta, del más nuevo al más viejo."""
        carpeta = self.carpeta()
        if carpeta is None or not carpeta.is_dir():
            return []
        guardados = [RespaldoGuardado(a.name, _fecha_del_nombre(a), a.stat().st_size)
                     for patron in PATRONES_RESTAURABLES for a in carpeta.glob(patron)]
        return sorted(guardados, key=lambda r: r.fecha, reverse=True)

    def restaurar(self, nombre, ahora=None):
        """Revisa el archivo, guarda el estado actual («antes_de_restaurar») y copia el respaldo encima de la base
        abierta. Después migra el esquema por si el respaldo es de una versión anterior."""
        if nombre not in {r.nombre for r in self.listar()}:
            raise ValueError("Ese respaldo no está en la carpeta")
        archivo = self._exigir_carpeta() / nombre
        if not _es_base_de_la_tienda(archivo):
            raise ValueError(RESPALDO_INVALIDO)
        copiar_verificado(self.conexion, self._exigir_carpeta(), ahora, PREFIJO_SEGURIDAD)
        with closing(sqlite3.connect(archivo)) as origen:
            origen.backup(self.conexion)
        preparar_esquema(self.conexion)

    def _exigir_carpeta(self):
        carpeta = self.carpeta()
        if carpeta is None:
            raise ValueError(SIN_CARPETA)
        return carpeta

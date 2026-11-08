"""Genera interfaz_web/icono.ico, el ícono de TIENDAS_SM.exe, solo con la biblioteca estándar (sin programas de dibujo).

El dibujo es el logo de la app: un cuadro verde redondeado (la paleta del borrador) con el carrito del menú en blanco.
Cada píxel se calcula con «distancias»: si el punto cae cerca de una línea del carrito se pinta blanco; si cae dentro
del cuadro, verde. Se toman varias muestras por píxel para que los bordes se vean suaves. El .ico guarda 4 tamaños
en formato PNG (16, 32, 48 y 256 píxeles), que Windows elige según dónde muestre el ícono.
Uso: python scripts/generar_icono.py   (solo hace falta volver a correrlo si se cambia el dibujo)
"""
import math
import struct
import zlib
from pathlib import Path

DESTINO = Path(__file__).resolve().parent.parent / "interfaz_web" / "icono.ico"
TAMANOS = (16, 32, 48, 256)
MUESTRAS = 3                                   # 3 x 3 muestras por píxel (bordes suaves)
VERDE_ARRIBA, VERDE_ABAJO = (0x2F, 0xBF, 0x7A), (0x0F, 0x5A, 0x3F)   # --v500 y --v800 del borrador
BLANCO = (255, 255, 255)
RADIO_DE_ESQUINA = 0.22
# El carrito es el mismo ícono del menú (app.js), dibujado en una cuadrícula de 24 x 24
LINEAS_DEL_CARRITO = (((3, 4), (5, 4)), ((5, 4), (7.4, 15)), ((7.4, 15), (18.4, 15)), ((18.4, 15), (21, 7)),
                      ((21, 7), (6.2, 7)))
RUEDAS = ((9, 19), (17, 19))
MARGEN, ESCALA = 0.17, 0.66 / 24               # el carrito ocupa el centro del cuadro
GROSOR, RADIO_RUEDA = 2.3 * ESCALA / 2, 1.9 * ESCALA


def _a_unidad(x, y):
    return MARGEN + x * ESCALA, MARGEN + y * ESCALA


def _distancia_a_segmento(px, py, a, b):
    (ax, ay), (bx, by) = _a_unidad(*a), _a_unidad(*b)
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _dentro_del_cuadro(px, py):
    """Cuadro de 0 a 1 con esquinas redondeadas."""
    r = RADIO_DE_ESQUINA
    cx, cy = min(max(px, r), 1 - r), min(max(py, r), 1 - r)
    return 0 <= px <= 1 and 0 <= py <= 1 and math.hypot(px - cx, py - cy) <= r


def _es_carrito(px, py):
    if any(_distancia_a_segmento(px, py, a, b) <= GROSOR for a, b in LINEAS_DEL_CARRITO):
        return True
    return any(math.hypot(px - x, py - y) <= RADIO_RUEDA for x, y in (_a_unidad(*r) for r in RUEDAS))


def _color_del_pixel(columna, fila, tamano):
    rojo = verde = azul = opaco = 0
    for i in range(MUESTRAS):
        for j in range(MUESTRAS):
            px, py = (columna + (i + 0.5) / MUESTRAS) / tamano, (fila + (j + 0.5) / MUESTRAS) / tamano
            if not _dentro_del_cuadro(px, py):
                continue
            fondo = tuple(round(a + (b - a) * py) for a, b in zip(VERDE_ARRIBA, VERDE_ABAJO))
            r, g, b = BLANCO if _es_carrito(px, py) else fondo
            rojo, verde, azul, opaco = rojo + r, verde + g, azul + b, opaco + 1
    if not opaco:
        return (0, 0, 0, 0)
    return (rojo // opaco, verde // opaco, azul // opaco, 255 * opaco // (MUESTRAS * MUESTRAS))


def crear_png(tamano):
    """Imagen PNG (RGBA) del ícono en el tamaño pedido."""
    filas = b"".join(b"\x00" + bytes(c for x in range(tamano) for c in _color_del_pixel(x, y, tamano))
                     for y in range(tamano))

    def bloque(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos))

    cabecera = struct.pack(">IIBBBBB", tamano, tamano, 8, 6, 0, 0, 0)   # 8 bits por canal, RGBA
    return b"\x89PNG\r\n\x1a\n" + bloque(b"IHDR", cabecera) + bloque(b"IDAT", zlib.compress(filas, 9)) + bloque(b"IEND", b"")


def crear_ico(tamanos=TAMANOS):
    imagenes = [crear_png(t) for t in tamanos]
    encabezado = struct.pack("<HHH", 0, 1, len(imagenes))                # tipo 1 = ícono
    posicion = len(encabezado) + 16 * len(imagenes)
    entradas = b""
    for tamano, imagen in zip(tamanos, imagenes):
        lado = tamano % 256                                              # 256 se escribe como 0 en el formato ICO
        entradas += struct.pack("<BBBBHHII", lado, lado, 0, 0, 1, 32, len(imagen), posicion)
        posicion += len(imagen)
    return encabezado + entradas + b"".join(imagenes)


if __name__ == "__main__":
    DESTINO.write_bytes(crear_ico())
    print(f"Ícono creado: {DESTINO}")

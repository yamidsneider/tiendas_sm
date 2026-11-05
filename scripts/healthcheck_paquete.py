"""TIENDAS S.M — Healthcheck posterior a la publicación (FPI-27, ADR-11).

TIENDAS S.M es una aplicación de escritorio (ADR-03): no tiene un endpoint /health.
El equivalente es comprobar que el paquete PUBLICADO (el mismo .zip que descargará la
tienda) está íntegro y que el sistema arranca y registra una venta.

Uso:
    python healthcheck_paquete.py --paquete tiendas_sm-v1.2.0.zip [--sha256 tiendas_sm-v1.2.0.zip.sha256]

Sale con 0 si todo está bien y con 1 si algo falla (el pipeline queda en rojo).
Solo usa la biblioteca estándar y datos ficticios, en una carpeta temporal.
"""
import argparse
import hashlib
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PRUEBA_DE_HUMO = r"""
import sys
from tiendas_sm.aplicacion import Aplicacion
ruta = sys.argv[1]
app = Aplicacion(ruta)
p = app.productos.registrar_producto("Producto ficticio de humo", 1000, 1500, 10)
c = app.clientes.registrar_cliente("Cliente ficticio de humo", True, 100000, 30)
venta = app.ventas.registrar_venta_a_credito(c.id_cliente, [(p.id_producto, 2)])
assert app.numero_de_ventas() == 1, "la venta no quedó registrada"
assert app.cantidad_en_inventario(p.id_producto) == 8, "no se descontó el inventario"
assert app.credito.saldo_pendiente(c) == venta.calcular_total(), "la cuenta por cobrar no coincide"
salidas = app.conexion.execute(
    "SELECT COALESCE(SUM(cantidad), 0) FROM movimientos_inventario WHERE tipo='SALIDA_VENTA' AND id_producto=?",
    (p.id_producto,)).fetchone()[0]
assert salidas == 2, "la venta no registró su movimiento SALIDA_VENTA (TD-01)"
app.conexion.close()
assert Aplicacion(ruta).numero_de_ventas() == 1, "la venta no persistió en el archivo"
print("venta 1 registrada, inventario 10 -> 8, SALIDA_VENTA 2, saldo", venta.calcular_total(), ", persistencia OK")
"""


def fallar(motivo):
    print(f"HEALTHCHECK FALLÓ: {motivo}")
    sys.exit(1)


def verificar_suma(paquete, archivo_sha):
    esperado = Path(archivo_sha).read_text(encoding="utf-8").split()[0].lower()
    real = hashlib.sha256(Path(paquete).read_bytes()).hexdigest()
    if real != esperado:
        fallar(f"la suma SHA-256 no coincide (esperada {esperado[:12]}…, real {real[:12]}…)")
    print(f"1/3 integridad: SHA-256 {real[:12]}… OK")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--paquete", required=True)
    parser.add_argument("--sha256")
    parser.add_argument("--tiempo-maximo", type=int, default=60)
    args = parser.parse_args()

    if not Path(args.paquete).is_file():
        fallar(f"no existe el paquete {args.paquete}")
    if args.sha256:
        verificar_suma(args.paquete, args.sha256)
    else:
        print("1/3 integridad: sin archivo .sha256 (omitida)")

    with tempfile.TemporaryDirectory() as carpeta:
        try:
            with zipfile.ZipFile(args.paquete) as z:
                z.extractall(carpeta)
        except zipfile.BadZipFile:
            fallar("el paquete no es un .zip válido")
        if not (Path(carpeta) / "tiendas_sm" / "aplicacion.py").is_file():
            fallar("el paquete no contiene tiendas_sm/aplicacion.py")
        print("2/3 contenido: tiendas_sm presente OK")

        try:
            # S603: se ejecuta el mismo Python con la prueba de humo fija de este archivo; no entra nada del usuario.
            r = subprocess.run(  # noqa: S603
                [sys.executable, "-c", PRUEBA_DE_HUMO, str(Path(carpeta) / "humo.db")],
                cwd=carpeta, capture_output=True, text=True, timeout=args.tiempo_maximo,
            )
        except subprocess.TimeoutExpired:
            fallar(f"el sistema no respondió en {args.tiempo_maximo} s")
        if r.returncode != 0:
            ultima = (r.stderr.strip().splitlines() or ["(sin detalle)"])[-1]
            fallar(f"la prueba de humo terminó con código {r.returncode}: {ultima}")
        print(f"3/3 humo: {r.stdout.strip()}")

    print("HEALTHCHECK OK")


if __name__ == "__main__":
    main()

"""Demostración en vivo de TIENDAS S.M (Demo Day, FPI-16).

Ejecuta el flujo crítico del negocio —vender a crédito, controlar el inventario y cobrar abonos— sobre datos
FICTICIOS que simulan una tienda de barrio, narrando cada paso. No usa archivos ni internet: la base de datos
SQLite vive en memoria.

Uso:
    python demo_en_vivo.py                 # se detiene en cada paso; presiona Enter para continuar
    python demo_en_vivo.py --sin-pausas    # corre de una vez (para probar)
"""
import sqlite3
import sys

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import CreditoNoPermitido, StockInsuficiente

PAUSAS = "--sin-pausas" not in sys.argv


def pesos(valor):
    return "$ " + f"{valor:,}".replace(",", ".")


def paso(numero, titulo, explicacion=""):
    print(f"\n{'=' * 72}\nPASO {numero}: {titulo}\n{'=' * 72}")
    if explicacion:
        print(explicacion)
    if PAUSAS:
        input("   [Enter para ejecutar] ")


def inventario(app, productos):
    for producto in productos:
        print(f"   {producto.nombre:<14} quedan {app.cantidad_en_inventario(producto.id_producto):>3} unidades")


def main():
    app = Aplicacion()                                     # base de datos nueva, en memoria
    print("TIENDAS S.M — demostración del flujo crítico (datos ficticios)")

    paso(1, "Registrar productos y recibir mercancía",
         "HU-01 y HU-03: el propietario registra productos con precio de compra y de venta y anota la entrada.")
    arroz = app.productos.registrar_producto("Arroz 500 g", 2000, 2500, cantidad_inicial=10)
    aceite = app.productos.registrar_producto("Aceite 1 L", 7500, 9800, cantidad_inicial=4)
    productos = [arroz, aceite]
    inventario(app, productos)

    paso(2, "Registrar un cliente con crédito",
         "HU-05 y regla de crédito: el cliente puede comprar fiado hasta un límite de $ 50.000, con plazo de 15 días.")
    cliente = app.clientes.registrar_cliente("Cliente de ejemplo", True, 50000, plazo_credito_dias=15)
    print(f"   {cliente.nombres}: límite {pesos(cliente.limite_credito)}, plazo {cliente.plazo_credito_dias} días")

    paso(3, "Vender a crédito (CU-01, el flujo crítico)",
         "Vende 3 de arroz y 1 de aceite. El sistema calcula el total, descuenta el inventario y crea la deuda en una "
         "sola operación.")
    venta = app.ventas.registrar_venta_a_credito(cliente.id_cliente, [(arroz.id_producto, 3), (aceite.id_producto, 1)])
    cuenta = app.credito.cuentas_del_cliente(cliente.id_cliente)[0]
    print(f"   Total de la venta: {pesos(venta.total)}  (3 × {pesos(2500)} + 1 × {pesos(9800)})")
    print(f"   Deuda creada: {pesos(cuenta.monto_original)}, vence el {str(cuenta.fecha_vencimiento)[:10]}")
    inventario(app, productos)

    paso(4, "Intentar vender más de lo que hay",
         "Regla de inventario: no se puede vender lo que no existe. El sistema debe decir cuánto queda.")
    try:
        app.ventas.registrar_venta_a_credito(cliente.id_cliente, [(aceite.id_producto, 10)])
    except StockInsuficiente as error:
        print(f"   Venta rechazada: {error}")
    inventario(app, productos)

    paso(5, "Respetar el límite de crédito",
         "El cliente ya debe $ 17.300 de $ 50.000. Primero hace una compra que cabe dentro del límite y luego otra "
         "que lo superaría.")
    app.ventas.registrar_venta_a_credito(cliente.id_cliente, [(aceite.id_producto, 3)])
    print(f"   Compra de 3 aceites aceptada. Deuda total: {pesos(app.credito.saldo_pendiente(cliente))} de {pesos(cliente.limite_credito)}")
    try:
        app.ventas.registrar_venta_a_credito(cliente.id_cliente, [(arroz.id_producto, 2)])
    except CreditoNoPermitido as error:
        print(f"   Compra de 2 arroces rechazada ({pesos(5000)} llevaría la deuda a {pesos(app.credito.saldo_pendiente(cliente) + 5000)}): {error}")
    print(f"   Deuda total sin cambios: {pesos(app.credito.saldo_pendiente(cliente))}")

    paso(6, "Una falla a mitad de la operación no deja nada a medias (RNF-04)",
         "Simulamos un error de la base de datos justo al crear la deuda. La venta, el descuento y la deuda deben "
         "guardarse juntos o ninguno.")
    antes = app.cantidad_en_inventario(arroz.id_producto), app.numero_de_ventas()
    app.conexion.execute("CREATE TRIGGER falla_simulada BEFORE INSERT ON cuentas_por_cobrar "
                         "BEGIN SELECT RAISE(ABORT, 'falla simulada'); END")
    try:
        app.ventas.registrar_venta_a_credito(cliente.id_cliente, [(arroz.id_producto, 1)])
    except sqlite3.Error as error:
        print(f"   La base de datos falló: {error}")
    despues = app.cantidad_en_inventario(arroz.id_producto), app.numero_de_ventas()
    print(f"   Inventario de arroz y ventas antes: {antes}  después: {despues}  -> {'sin cambios' if antes == despues else 'ERROR'}")
    app.conexion.execute("DROP TRIGGER falla_simulada")

    paso(7, "Cobrar un abono",
         "HU-06: el cliente paga una parte y el saldo baja. Un abono mayor al saldo se rechaza mostrando cuánto debe.")
    cuenta = app.credito.cuentas_del_cliente(cliente.id_cliente)[0]
    app.credito.registrar_abono(cuenta.id_cuenta, 10000)
    print(f"   Abono de {pesos(10000)} registrado. Saldo de esa cuenta: "
          f"{pesos(app.credito.cuentas_del_cliente(cliente.id_cliente)[0].calcular_saldo())}")
    try:
        app.credito.registrar_abono(cuenta.id_cuenta, 1000000)
    except ValueError as error:
        print(f"   Abono rechazado: {error}")

    paso(8, "Qué quedó pendiente (honestidad del cierre)",
         "Lo que esta demostración NO muestra todavía:")
    for pendiente in ("Interfaz de escritorio con Tkinter (la demo es por consola)",
                      "Venta de contado (RF-05 está parcial: hoy solo se programó la venta a crédito)",
                      "Lotes, vencimientos y alertas (Should/Could Have)",
                      "Validación de las reglas con el propietario real (stock, plazo y límite del crédito son propuestas)"):
        print("   -", pendiente)
    print("\nFin de la demostración.")


if __name__ == "__main__":
    main()

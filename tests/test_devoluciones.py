"""Anular una venta y devolver productos (respuesta 1.5 del propietario; cambia DT-08 con aprobación).

La venta no se borra: queda con su devolución registrada (motivo, fecha, productos y valor) o «Anulada» si
ya no le queda nada por devolver. Lo devuelto vuelve al inventario con un movimiento DEVOLUCION.
En contado se devuelve el dinero; en crédito se descuenta de la deuda y, si lo devuelto pasa del saldo, la
cuenta queda pagada y el resto se devuelve en efectivo (no hay saldo a favor, respuesta 2.5).
Por ahora cualquiera puede hacerlo, con motivo obligatorio (la clave del jefe llegará con CR-01).
Todo se guarda en una transacción (RNF-04). Se escribieron antes del código. Datos ficticios.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from interfaz_web.api import ApiDeLaTienda
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import EstadoCuenta, EstadoVenta
from tiendas_sm.presentador_existencias import PresentadorDeExistencias
from tiendas_sm.presentador_ventas import PresentadorDeVentas

MOTIVO = "Producto en mal estado (prueba)"


class BaseDeDevoluciones(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio", 2000, 2500, 20)
        self.panela = self.app.productos.registrar_producto("Panela ficticia", 2000, 2500, 20)
        self.ana = self.app.clientes.registrar_cliente("Cliente ficticio Ana", True, 100000)
        self.contado = self.app.ventas.registrar_venta_de_contado(
            [(self.arroz.id_producto, 2), (self.panela.id_producto, 2)], 10000)       # total 10.000

    def vender_a_credito(self):
        venta = self.app.ventas.registrar_venta_a_credito(self.ana.id_cliente,
                                                          [(self.arroz.id_producto, 2), (self.panela.id_producto, 2)])
        cuenta, = self.app.credito.cuentas_del_cliente(self.ana.id_cliente)
        return venta, cuenta

    def stock(self, producto):
        return self.app.cantidad_en_inventario(producto.id_producto)


class PruebasDeContado(BaseDeDevoluciones):
    def test_devolver_una_parte_regresa_el_stock_y_el_dinero(self):
        devolucion = self.app.ventas.devolver(self.contado.id_venta, [(self.arroz.id_producto, 1)], MOTIVO)
        self.assertEqual((devolucion.valor(), devolucion.efectivo_devuelto, devolucion.descontado_de_la_deuda),
                         (2500, 2500, 0))
        self.assertEqual(self.stock(self.arroz), 19)
        self.assertEqual(self.app.ventas.obtener(self.contado.id_venta).estado, EstadoVenta.CONFIRMADA)

    def test_no_se_devuelve_mas_de_lo_que_queda(self):
        self.app.ventas.devolver(self.contado.id_venta, [(self.arroz.id_producto, 1)], MOTIVO)
        with self.assertRaises(ValueError) as error:
            self.app.ventas.devolver(self.contado.id_venta, [(self.arroz.id_producto, 2)], MOTIVO)
        self.assertEqual(str(error.exception), "De Arroz ficticio solo se pueden devolver 1")
        self.assertEqual(self.stock(self.arroz), 19)

    def test_el_motivo_es_obligatorio(self):
        with self.assertRaises(ValueError) as error:
            self.app.ventas.devolver(self.contado.id_venta, [(self.arroz.id_producto, 1)], "  ")
        self.assertEqual(str(error.exception), "Escribe el motivo de la devolución")

    def test_un_producto_que_no_esta_en_la_venta(self):
        sal = self.app.productos.registrar_producto("Sal ficticia", 800, 1200, 5)
        with self.assertRaises(ValueError) as error:
            self.app.ventas.devolver(self.contado.id_venta, [(sal.id_producto, 1)], MOTIVO)
        self.assertEqual(str(error.exception), f"Ese producto no está en la venta #{self.contado.id_venta}")

    def test_sin_productos_no_hay_devolucion(self):
        with self.assertRaises(ValueError) as error:
            self.app.ventas.devolver(self.contado.id_venta, [], MOTIVO)
        self.assertEqual(str(error.exception), "Elige al menos un producto para devolver")

    def test_anular_devuelve_todo_y_queda_anulada(self):
        devolucion = self.app.ventas.anular(self.contado.id_venta, MOTIVO)
        self.assertEqual(devolucion.efectivo_devuelto, 10000)
        self.assertEqual((self.stock(self.arroz), self.stock(self.panela)), (20, 20))
        self.assertEqual(self.app.ventas.obtener(self.contado.id_venta).estado, EstadoVenta.ANULADA)
        with self.assertRaises(ValueError) as error:
            self.app.ventas.anular(self.contado.id_venta, MOTIVO)
        self.assertEqual(str(error.exception), f"La venta #{self.contado.id_venta} ya está anulada")

    def test_devolver_todo_por_partes_tambien_la_anula(self):
        self.app.ventas.devolver(self.contado.id_venta, [(self.arroz.id_producto, 2)], MOTIVO)
        self.app.ventas.devolver(self.contado.id_venta, [(self.panela.id_producto, 2)], MOTIVO)
        self.assertEqual(self.app.ventas.obtener(self.contado.id_venta).estado, EstadoVenta.ANULADA)

    def test_queda_el_movimiento_de_devolucion_en_existencias(self):
        self.app.ventas.devolver(self.contado.id_venta, [(self.arroz.id_producto, 1)], MOTIVO)
        _, (_, producto, movimiento, cantidad) = PresentadorDeExistencias(self.app).movimientos()[0]
        self.assertEqual((producto, movimiento, cantidad), ("Arroz ficticio", "Devolución", "+1"))


class PruebasDeCredito(BaseDeDevoluciones):
    def test_sin_abonos_se_descuenta_de_la_deuda(self):
        venta, cuenta = self.vender_a_credito()
        devolucion = self.app.ventas.devolver(venta.id_venta, [(self.arroz.id_producto, 1)], MOTIVO)
        self.assertEqual((devolucion.descontado_de_la_deuda, devolucion.efectivo_devuelto), (2500, 0))
        self.assertEqual(self.app.credito.obtener_cuenta(cuenta.id_cuenta).calcular_saldo(), 7500)
        self.assertEqual(self.app.credito.saldo_pendiente(self.ana), 7500)              # TD-13: la consulta coincide

    def test_ejemplo_aprobado_deuda_a_cero_y_el_resto_en_efectivo(self):
        """Debía 10.000, abonó 8.000 (le falta 2.000) y devuelve 5.000: deuda a 0 y se le dan 3.000."""
        venta, cuenta = self.vender_a_credito()
        self.app.credito.registrar_abono(cuenta.id_cuenta, 8000)
        devolucion = self.app.ventas.devolver(venta.id_venta, [(self.arroz.id_producto, 2)], MOTIVO)
        self.assertEqual((devolucion.descontado_de_la_deuda, devolucion.efectivo_devuelto), (2000, 3000))
        guardada = self.app.credito.obtener_cuenta(cuenta.id_cuenta)
        self.assertEqual((guardada.calcular_saldo(), guardada.estado), (0, EstadoCuenta.PAGADA))
        self.assertEqual(self.app.credito.saldo_pendiente(self.ana), 0)

    def test_anular_un_fiado_sin_abonos_deja_la_deuda_en_cero(self):
        venta, cuenta = self.vender_a_credito()
        devolucion = self.app.ventas.anular(venta.id_venta, MOTIVO)
        self.assertEqual((devolucion.descontado_de_la_deuda, devolucion.efectivo_devuelto), (10000, 0))
        self.assertEqual(self.app.credito.obtener_cuenta(cuenta.id_cuenta).estado, EstadoCuenta.PAGADA)


class PruebasDeLaSeccionVentas(BaseDeDevoluciones):
    def setUp(self):
        super().setUp()
        self.pve = PresentadorDeVentas(self.app)

    def test_lista_lo_que_se_puede_devolver(self):
        self.app.ventas.devolver(self.contado.id_venta, [(self.arroz.id_producto, 1)], MOTIVO)
        self.assertEqual(self.pve.para_devolver(self.contado.id_venta),
                         [(self.arroz.id_producto, ("Arroz ficticio", 2, 1, 1, "$ 2.500")),
                          (self.panela.id_producto, ("Panela ficticia", 2, 0, 2, "$ 2.500"))])

    def test_devolver_desde_el_formulario(self):
        resultado = self.pve.devolver(self.contado.id_venta, {self.arroz.id_producto: "2", self.panela.id_producto: ""},
                                      MOTIVO)
        self.assertEqual((resultado.exito, resultado.mensaje),
                         (True, f"Devolución registrada en la venta #{self.contado.id_venta}. Devolver en efectivo: $ 5.000"))
        self.assertIn("DEVOLUCIÓN", resultado.ticket)

    def test_una_cantidad_que_no_es_numero(self):
        resultado = self.pve.devolver(self.contado.id_venta, {self.arroz.id_producto: "dos"}, MOTIVO)
        self.assertEqual((resultado.exito, resultado.mensaje), (False, "La cantidad debe ser un número entero"))

    def test_anular_desde_la_seccion_y_el_ticket_lo_dice(self):
        resultado = self.pve.anular(self.contado.id_venta, MOTIVO)
        self.assertEqual(resultado.mensaje, f"Venta #{self.contado.id_venta} anulada. Devolver en efectivo: $ 10.000")
        ticket = self.pve.ticket(self.contado.id_venta)
        self.assertIn("VENTA ANULADA", ticket)
        self.assertIn(f"Motivo: {MOTIVO}", ticket)

    def test_mensaje_de_un_fiado_con_abonos(self):
        venta, cuenta = self.vender_a_credito()
        self.app.credito.registrar_abono(cuenta.id_cuenta, 8000)
        resultado = self.pve.devolver(venta.id_venta, {self.arroz.id_producto: "2"}, MOTIVO)
        self.assertEqual(resultado.mensaje, f"Devolución registrada en la venta #{venta.id_venta}. "
                                            "Se descontó de la deuda: $ 2.000. Devolver en efectivo: $ 3.000")

    def test_estado_de_cada_venta(self):
        venta, _ = self.vender_a_credito()
        self.app.ventas.devolver(venta.id_venta, [(self.arroz.id_producto, 1)], MOTIVO)
        self.app.ventas.anular(self.contado.id_venta, MOTIVO)
        self.assertEqual(self.pve.estados(), {venta.id_venta: "Con devolución", self.contado.id_venta: "Anulada"})


class PruebasDeLaApi(BaseDeDevoluciones):
    def test_para_devolver_devolver_y_anular(self):
        api = ApiDeLaTienda(self.app)
        filas = api.para_devolver(self.contado.id_venta)
        self.assertEqual(filas[0]["valores"][0], "Arroz ficticio")
        respuesta = api.devolver(self.contado.id_venta, {str(self.arroz.id_producto): "1"}, MOTIVO)
        self.assertTrue(respuesta["exito"], respuesta["mensaje"])
        self.assertEqual({f["id"]: f["estado"] for f in api.ventas()}, {self.contado.id_venta: "Con devolución"})
        self.assertTrue(api.anular(self.contado.id_venta, MOTIVO)["exito"])


class PruebasDeLaMigracion(unittest.TestCase):
    def test_una_base_vieja_abre_y_su_cuenta_conserva_el_saldo(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as carpeta:
            ruta = str(Path(carpeta) / "vieja.db")
            conexion = sqlite3.connect(ruta)
            conexion.executescript("""
                CREATE TABLE cuentas_por_cobrar (id_cuenta INTEGER PRIMARY KEY AUTOINCREMENT, id_venta INTEGER NOT NULL,
                    id_cliente INTEGER NOT NULL, fecha_apertura TEXT NOT NULL, fecha_vencimiento TEXT NOT NULL,
                    monto_credito_original INTEGER NOT NULL, estado TEXT NOT NULL);
                INSERT INTO cuentas_por_cobrar VALUES (1, 1, 1, '2026-10-01T09:00:00', '2026-10-31T09:00:00', 7000, 'ABIERTA');""")
            conexion.close()
            app = Aplicacion(ruta)
            self.assertEqual(app.credito.obtener_cuenta(1).calcular_saldo(), 7000)
            app.conexion.close()


if __name__ == "__main__":
    unittest.main()

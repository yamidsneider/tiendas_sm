"""Estado de cuenta del cliente para imprimir (fase 7 de docs/HOJA_DE_RUTA_APP_COMPLETA.md; ayuda a cobrar el fiado).

Lista, en orden de fecha, cada compra fiada, cada abono y cada devolución que bajó la deuda, con el saldo después de
cada una. Al final los totales, el saldo actual y si tiene cuentas vencidas. Arriba los datos de la tienda (fase 6).
Sale a 42 caracteres por renglón, como el ticket de 80 mm, para imprimirlo en la misma impresora.
Solo lee: no cambia deudas. Lo pueden ver jefe y empleado (Permiso.CONSULTAR). Se escribieron antes del código.
Datos ficticios.
"""
import unittest
from datetime import datetime, timedelta

from interfaz_web.api import ApiDeLaTienda
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.presentador_clientes import PresentadorDeClientes

CLAVE = "clave-ficticia-1"
MOTIVO = "Prueba"


class BaseDelEstadoDeCuenta(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio", 1000, 2000, 50)
        self.ana = self.app.clientes.registrar_cliente("Cliente ficticia Ana", True, 100000, telefono="300 111 2222")

    def fiar_abonar_y_devolver(self):
        """Fía 5 arroz (10.000), abona 4.000 y devuelve 1 arroz (2.000 que bajan la deuda)."""
        self.venta = self.app.ventas.registrar_venta_a_credito(self.ana.id_cliente, [(self.arroz.id_producto, 5)])
        cuenta, = self.app.credito.cuentas_del_cliente(self.ana.id_cliente)
        self.app.credito.registrar_abono(cuenta.id_cuenta, 4000)
        self.app.ventas.devolver(self.venta.id_venta, [(self.arroz.id_producto, 1)], MOTIVO)

    def texto(self):
        return PresentadorDeClientes(self.app).estado_de_cuenta(self.ana.id_cliente)


class PruebasDelServicio(BaseDelEstadoDeCuenta):
    def test_movimientos_en_orden_con_el_saldo_despues_de_cada_uno(self):
        self.fiar_abonar_y_devolver()
        movimientos = self.app.credito.estado_de_cuenta(self.ana.id_cliente)
        self.assertEqual([(m.tipo, m.valor, m.saldo) for m in movimientos],
                         [("Compra", 10000, 10000), ("Abono", 4000, 6000), ("Devolución", 2000, 4000)])
        self.assertTrue(all(m.id_venta == self.venta.id_venta for m in movimientos))

    def test_sin_fiado_no_hay_movimientos(self):
        self.app.ventas.registrar_venta_de_contado([(self.arroz.id_producto, 1)], 2000)
        self.assertEqual(self.app.credito.estado_de_cuenta(self.ana.id_cliente), [])

    def test_una_devolucion_de_contado_no_aparece(self):
        contado = self.app.ventas.registrar_venta_de_contado([(self.arroz.id_producto, 1)], 2000)
        self.app.ventas.devolver(contado.id_venta, [(self.arroz.id_producto, 1)], MOTIVO)
        self.assertEqual(self.app.credito.estado_de_cuenta(self.ana.id_cliente), [])


class PruebasDelTexto(BaseDelEstadoDeCuenta):
    def test_encabezado_con_la_tienda_y_el_cliente(self):
        self.app.tienda.guardar("Tienda ficticia", "", "", "", "")
        lineas = self.texto().split("\n")
        self.assertEqual(lineas[0], "Tienda ficticia")
        self.assertIn("ESTADO DE CUENTA", lineas)
        self.assertIn("Cliente: Cliente ficticia Ana", lineas)
        self.assertIn("Tel: 300 111 2222", lineas)

    def test_cada_movimiento_con_su_saldo(self):
        self.fiar_abonar_y_devolver()
        texto = self.texto()
        hoy = f"{datetime.now():%d/%m/%y}"
        self.assertIn(f"{hoy} Compra #{self.venta.id_venta}".ljust(26) + "+10.000".rjust(8) + "10.000".rjust(8), texto)
        self.assertIn(f"{hoy} Abono".ljust(26) + "-4.000".rjust(8) + "6.000".rjust(8), texto)
        self.assertIn(f"{hoy} Devolución".ljust(26) + "-2.000".rjust(8) + "4.000".rjust(8), texto)

    def test_totales_y_saldo_actual(self):
        self.fiar_abonar_y_devolver()
        texto = self.texto()
        for linea in ("Total fiado: $ 10.000", "Total abonado: $ 4.000", "Devoluciones: $ 2.000",
                      "SALDO ACTUAL: $ 4.000", "Al día: no tiene cuentas vencidas"):
            self.assertIn(linea, texto)

    def test_avisa_las_cuentas_vencidas(self):
        self.fiar_abonar_y_devolver()
        hace_un_mes = (datetime.now() - timedelta(days=30)).isoformat()
        with self.app.conexion:
            self.app.conexion.execute("UPDATE cuentas_por_cobrar SET fecha_vencimiento = ?", (hace_un_mes,))
        self.assertIn("Cuentas vencidas: 1 (saldo $ 4.000)", self.texto())

    def test_sin_fiado(self):
        self.assertIn("No tiene compras fiadas", self.texto())
        self.assertIn("SALDO ACTUAL: $ 0", self.texto())

    def test_cabe_en_la_impresora_de_80_mm(self):
        self.app.tienda.guardar("Tienda ficticia con un nombre largo para probar el ancho", "", "", "", "Gracias")
        self.fiar_abonar_y_devolver()
        self.assertTrue(all(len(linea) <= 42 for linea in self.texto().split("\n")))

    def test_cliente_que_no_existe(self):
        self.assertEqual(PresentadorDeClientes(self.app).estado_de_cuenta(999), "")


class PruebasDeLaApi(BaseDelEstadoDeCuenta):
    def test_el_empleado_tambien_lo_ve(self):
        self.app.usuarios.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE)
        api = ApiDeLaTienda(self.app)
        self.assertEqual(api.estado_de_cuenta(self.ana.id_cliente)["mensaje"], "Primero ingrese con su usuario y clave")
        api.iniciar_sesion("jefe", CLAVE)
        self.assertIn("ESTADO DE CUENTA", api.estado_de_cuenta(self.ana.id_cliente))


if __name__ == "__main__":
    unittest.main()

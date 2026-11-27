"""Proveedores y compras (fase 8 de docs/HOJA_DE_RUTA_APP_COMPLETA.md; CR-02, respuesta 5.3).

*Preliminar (decisión del desarrollador; el propietario no ha respondido si quiere cuentas por pagar):*
- Proveedor: nombre (obligatorio), teléfono y NIT (opcionales).
- Compra: proveedor, número de factura (opcional) y líneas (producto, cantidad, costo unitario). En una transacción
  (RNF-04) suben las existencias, queda un movimiento ENTRADA con el motivo «Compra #n a <proveedor>» y el precio de compra
  del producto pasa a ser el último costo. Se asume pagada de una vez: no hay cuentas por pagar.
- Solo el jefe (Permiso.GESTIONAR_COMPRAS). Un producto desactivado no se compra. Reportes suma lo comprado.
Se escribieron antes del código. Datos ficticios.
"""
import unittest

from interfaz_web.api import ApiDeLaTienda
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import Permiso, Rol
from tiendas_sm.presentador_compras import PresentadorDeCompras
from tiendas_sm.presentador_reportes import PresentadorDeReportes

CLAVE = "clave-ficticia-1"


class BaseDeCompras(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.jefe = self.app.usuarios.crear_primer_jefe("Jefe ficticio", "jefe", CLAVE)
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio", 1000, 2000, 5)
        self.panela = self.app.productos.registrar_producto("Panela ficticia", 800, 1500, 2)
        self.proveedor = self.app.compras.registrar_proveedor("Distribuidora ficticia", "300 123 4567", "900111222-3")

    def stock(self, producto):
        return self.app.cantidad_en_inventario(producto.id_producto)

    def comprar(self, lineas=None, factura="F-001"):
        lineas = lineas or [(self.arroz.id_producto, 10, 1100), (self.panela.id_producto, 4, 900)]
        return self.app.compras.registrar_compra(self.proveedor.id_proveedor, lineas, self.jefe.id_usuario, factura)


class PruebasDeProveedores(BaseDeCompras):
    def test_registrar_y_listar_por_nombre(self):
        self.app.compras.registrar_proveedor("Abarrotes ficticios", "", "")
        self.assertEqual([p.nombre for p in self.app.compras.listar_proveedores()],
                         ["Abarrotes ficticios", "Distribuidora ficticia"])

    def test_el_nombre_es_obligatorio(self):
        with self.assertRaises(ValueError) as error:
            self.app.compras.registrar_proveedor("  ", "", "")
        self.assertEqual(str(error.exception), "Escribe el nombre del proveedor")

    def test_el_telefono_solo_lleva_numeros(self):
        with self.assertRaises(ValueError):
            self.app.compras.registrar_proveedor("Otro ficticio", "llamar al vecino", "")


class PruebasDeRegistrarCompra(BaseDeCompras):
    def test_suben_las_existencias_y_el_total(self):
        compra = self.comprar()
        self.assertEqual((self.stock(self.arroz), self.stock(self.panela)), (15, 6))
        self.assertEqual(compra.total(), 10 * 1100 + 4 * 900)

    def test_el_precio_de_compra_pasa_a_ser_el_ultimo_costo(self):
        self.comprar()
        self.assertEqual(self.app.productos.obtener(self.arroz.id_producto).precio_compra, 1100)
        self.assertEqual(self.app.productos.obtener(self.arroz.id_producto).precio_venta, 2000)    # no se toca

    def test_deja_el_movimiento_de_entrada_con_la_compra(self):
        compra = self.comprar()
        movimiento = next(m for m in self.app.productos.movimientos() if m.id_producto == self.arroz.id_producto)
        self.assertEqual((movimiento.tipo, movimiento.cantidad), ("ENTRADA", 10))
        self.assertEqual(movimiento.motivo, f"Compra #{compra.id_compra} a Distribuidora ficticia")

    def test_se_guarda_y_se_puede_consultar(self):
        compra = self.comprar()
        guardada = self.app.compras.obtener_compra(compra.id_compra)
        self.assertEqual((guardada.id_proveedor, guardada.factura, guardada.total()),
                         (self.proveedor.id_proveedor, "F-001", 14600))
        self.assertEqual([c.id_compra for c in self.app.compras.listar_compras()], [compra.id_compra])

    def test_sin_productos_no_se_registra(self):
        with self.assertRaises(ValueError) as error:
            self.comprar(lineas=[])
        self.assertEqual(str(error.exception), "Agregue al menos un producto a la compra")

    def test_cantidad_y_costo_validos(self):
        for linea in ((self.arroz.id_producto, 0, 1000), (self.arroz.id_producto, 2, -5)):
            with self.subTest(linea=linea), self.assertRaises(ValueError):
                self.comprar(lineas=[linea])
        self.assertEqual(self.stock(self.arroz), 5)

    def test_todo_o_nada_si_un_producto_no_existe(self):
        with self.assertRaises(ValueError):
            self.comprar(lineas=[(self.arroz.id_producto, 3, 1000), (999, 1, 100)])
        self.assertEqual(self.stock(self.arroz), 5)
        self.assertEqual(self.app.compras.listar_compras(), [])

    def test_proveedor_que_no_existe(self):
        with self.assertRaises(ValueError) as error:
            self.app.compras.registrar_compra(999, [(self.arroz.id_producto, 1, 1000)], self.jefe.id_usuario)
        self.assertEqual(str(error.exception), "Elige un proveedor de la lista")

    def test_un_producto_desactivado_no_se_compra(self):
        self.app.productos.cambiar_estado(self.panela.id_producto, False)
        with self.assertRaises(ValueError) as error:
            self.comprar(lineas=[(self.panela.id_producto, 1, 900)])
        self.assertEqual(str(error.exception), "Panela ficticia está desactivado: actívelo antes de comprarlo")

    def test_el_reporte_suma_lo_comprado(self):
        self.comprar()
        self.assertIn(("Compras de mercancía", "$ 14.600"), PresentadorDeReportes(self.app).reporte("hoy")["formas"])


class PruebasDelPresentador(BaseDeCompras):
    def test_registrar_desde_la_pantalla(self):
        presentador = PresentadorDeCompras(self.app)
        lineas = [{"producto": str(self.arroz.id_producto), "cantidad": "10", "costo": "1100"},
                  {"producto": "", "cantidad": "", "costo": ""}]                     # renglón vacío: se ignora
        resultado = presentador.registrar(str(self.proveedor.id_proveedor), "F-9", lineas, self.jefe)
        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertEqual(resultado.mensaje, "Compra #1 a Distribuidora ficticia registrada por $ 11.000")

    def test_texto_mal_escrito(self):
        presentador = PresentadorDeCompras(self.app)
        lineas = [{"producto": str(self.arroz.id_producto), "cantidad": "diez", "costo": "1100"}]
        self.assertEqual(presentador.registrar(str(self.proveedor.id_proveedor), "", lineas, self.jefe).mensaje,
                         "La cantidad debe ser un número entero")

    def test_tablas_de_proveedores_y_compras(self):
        self.comprar()
        presentador = PresentadorDeCompras(self.app)
        self.assertEqual(presentador.proveedores()[0][1], ("Distribuidora ficticia", "300 123 4567", "900111222-3"))
        _, fila = presentador.compras()[0]
        self.assertEqual(fila[1:], ("Distribuidora ficticia", "F-001", "2 productos", "$ 14.600"))

    def test_detalle_de_una_compra(self):
        compra = self.comprar()
        detalle = PresentadorDeCompras(self.app).detalle(compra.id_compra)
        self.assertIn("Compra #1 · Distribuidora ficticia", detalle)
        self.assertIn("10 x Arroz ficticio a $ 1.100 = $ 11.000", detalle)
        self.assertIn("TOTAL: $ 14.600", detalle)


class PruebasDeLaApi(BaseDeCompras):
    def test_solo_el_jefe_compra(self):
        self.assertFalse(Rol.EMPLEADO.puede(Permiso.GESTIONAR_COMPRAS))
        self.app.usuarios.crear_usuario("Empleado ficticio", "pedro", Rol.EMPLEADO, CLAVE)
        api = ApiDeLaTienda(self.app)
        api.iniciar_sesion("pedro", CLAVE)
        self.assertEqual(api.proveedores()["mensaje"], "Solo el jefe puede hacer esto")

    def test_el_jefe_registra_proveedor_y_compra(self):
        api = ApiDeLaTienda(self.app)
        api.iniciar_sesion("jefe", CLAVE)
        self.assertTrue(api.registrar_proveedor("Otro proveedor ficticio", "", "")["exito"])
        respuesta = api.registrar_compra(str(self.proveedor.id_proveedor), "",
                                         [{"producto": str(self.panela.id_producto), "cantidad": "3", "costo": "850"}])
        self.assertTrue(respuesta["exito"], respuesta["mensaje"])
        self.assertEqual(self.stock(self.panela), 5)
        self.assertEqual(len(api.compras()), 1)
        self.assertIn("TOTAL: $ 2.550", api.detalle_compra(api.compras()[0]["id"]))


if __name__ == "__main__":
    unittest.main()

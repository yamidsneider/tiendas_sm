"""Pruebas de CAJA NEGRA de TIENDAS S.M (FPI-14).

Se diseñan SOLO desde los criterios de aceptación Gherkin de la FPI-06 (qué entra y qué debe salir),
sin mirar cómo está escrito el código. Solo se usa la fachada pública `Aplicacion`.
Técnicas: partición en clases de equivalencia y análisis de valores límite.

ID    Criterio de origen (FPI-06)
CN-01 HU-04 escenario 1: venta de dos productos, total e inventario
CN-02 HU-04 escenario 2: stock insuficiente, el sistema informa cuántas unidades hay
CN-03 HU-06 escenario 2: abono mayor al saldo, el sistema muestra el saldo
CN-04 HU-03 escenario 2: entrada de cantidad 0 o negativa
CN-05 HU-01 escenario 2: producto sin nombre o con precio negativo
CN-06 CU-01 / RN-03: límite de crédito (valores límite 50.000 y 50.001)
CN-07 HU-04: valores límite del stock (cantidad = stock - 1, stock y stock + 1)
CN-08 HU-02 escenario 1: ventas anteriores no cambian al subir el precio
CN-09 RN-14 / TD-04: stock mínimo del producto (valores límite -1 y 0) y que se pueda registrar
"""
import unittest

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import CreditoNoPermitido, StockInsuficiente


class PruebasDeCajaNegra(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.cliente = self.app.clientes.registrar_cliente("Cliente de prueba", True, 50000)

    def producto(self, nombre, precio_venta, stock):
        return self.app.productos.registrar_producto(nombre, precio_venta // 2, precio_venta, stock)

    def vender(self, lineas):
        return self.app.ventas.registrar_venta_a_credito(self.cliente.id_cliente, lineas)

    def test_cn01_total_e_inventario_de_la_venta_de_dos_productos(self):
        a = self.producto("A", 2500, 10)
        b = self.producto("B", 3000, 4)
        venta = self.vender([(a.id_producto, 2), (b.id_producto, 1)])
        self.assertEqual(venta.total, 8000)
        self.assertEqual(self.app.cantidad_en_inventario(a.id_producto), 8)
        self.assertEqual(self.app.cantidad_en_inventario(b.id_producto), 3)

    def test_cn02_stock_insuficiente_informa_cuantas_unidades_hay(self):
        a = self.producto("A", 2500, 1)
        with self.assertRaises(StockInsuficiente) as contexto:
            self.vender([(a.id_producto, 3)])
        self.assertRegex(str(contexto.exception), r"\b1\b")     # "solo hay 1 disponible"
        self.assertEqual(self.app.cantidad_en_inventario(a.id_producto), 1)

    def test_cn03_abono_mayor_al_saldo_muestra_el_saldo(self):
        a = self.producto("A", 5000, 10)
        self.vender([(a.id_producto, 10)])                      # deuda de 50.000
        cuenta = self.app.credito.cuentas_del_cliente(self.cliente.id_cliente)[0]
        self.app.credito.registrar_abono(cuenta.id_cuenta, 20000)   # saldo 30.000
        with self.assertRaises(ValueError) as contexto:
            self.app.credito.registrar_abono(cuenta.id_cuenta, 60000)
        self.assertRegex(str(contexto.exception), r"\b30000\b")  # "muestra que el saldo es 30.000"

    def test_cn04_entrada_de_cantidad_cero_o_negativa(self):
        a = self.producto("A", 2500, 5)
        for cantidad in (0, -1, -100):                          # clase de equivalencia inválida
            with self.assertRaises(ValueError):
                self.app.productos.registrar_entrada(a.id_producto, cantidad)
        self.assertEqual(self.app.cantidad_en_inventario(a.id_producto), 5)

    def test_cn05_producto_sin_nombre_o_con_precio_negativo(self):
        with self.assertRaises(ValueError) as sin_nombre:
            self.app.productos.registrar_producto("", 1000, 2000)
        self.assertIn("nombre", str(sin_nombre.exception).lower())
        with self.assertRaises(ValueError) as precio_negativo:
            self.app.productos.registrar_producto("Arroz", 1000, -1)
        self.assertIn("precio", str(precio_negativo.exception).lower())
        self.assertEqual(self.app.productos.listar(), [])

    def test_cn06_valores_limite_del_credito(self):
        a = self.producto("A", 5000, 20)
        self.vender([(a.id_producto, 10)])                      # exactamente 50.000 = límite: se permite
        otro = self.app.clientes.registrar_cliente("Otro cliente", True, 50000)
        with self.assertRaises(CreditoNoPermitido):             # 50.001 > 50.000: se rechaza
            caro = self.producto("Caro", 50001, 1)
            self.app.ventas.registrar_venta_a_credito(otro.id_cliente, [(caro.id_producto, 1)])

    def test_cn07_valores_limite_del_stock(self):
        a = self.producto("A", 1000, 4)
        self.vender([(a.id_producto, 3)])                       # stock - 1: válido
        self.assertEqual(self.app.cantidad_en_inventario(a.id_producto), 1)
        self.vender([(a.id_producto, 1)])                       # justo lo que queda: válido
        self.assertEqual(self.app.cantidad_en_inventario(a.id_producto), 0)
        with self.assertRaises(StockInsuficiente):              # stock + 1: se rechaza
            self.vender([(a.id_producto, 1)])

    def test_cn08_las_ventas_anteriores_no_cambian_al_subir_el_precio(self):
        a = self.producto("A", 2500, 10)
        self.vender([(a.id_producto, 2)])
        self.app.productos.actualizar_precio(a.id_producto, 2700)
        vendido = self.app.conexion.execute("SELECT precio_unitario_venta FROM detalles_venta").fetchone()[0]
        self.assertEqual(vendido, 2500)
        self.assertEqual(self.app.productos.obtener(a.id_producto).precio_venta, 2700)

    def test_cn09_valores_limite_del_stock_minimo(self):
        with self.assertRaises(ValueError) as negativo:                # -1: se rechaza
            self.app.productos.registrar_producto("Arroz", 1000, 2000, stock_minimo=-1)
        self.assertIn("stock mínimo", str(negativo.exception).lower())
        self.assertEqual(self.app.productos.listar(), [])
        cero = self.app.productos.registrar_producto("Arroz", 1000, 2000, stock_minimo=0)   # 0: se acepta
        self.assertEqual(self.app.productos.obtener(cero.id_producto).stock_minimo, 0)

    def test_cn09_el_stock_minimo_registrado_se_conserva(self):
        p = self.app.productos.registrar_producto("Frijol", 3000, 4000, 8, stock_minimo=5)
        guardado = self.app.productos.obtener(p.id_producto)
        self.assertEqual(guardado.stock_minimo, 5)
        self.assertEqual(self.app.cantidad_en_inventario(p.id_producto), 8)


if __name__ == "__main__":
    unittest.main(verbosity=2)

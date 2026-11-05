"""Pruebas del presentador del punto de venta (tarea 8, TD-03, DAD §10.2).

El presentador es la parte de la pantalla que NO usa Tkinter: recibe lo que escribe el vendedor,
llama a los servicios de Aplicacion y devuelve filas y mensajes listos para mostrar. Por eso se
prueba aquí sin abrir ventanas. Se escribieron antes del código. Datos ficticios.
"""
import unittest
from unittest.mock import Mock

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.presentador import PresentadorPuntoDeVenta, formato_pesos


class BaseDelPresentador(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz 500 g", 2000, 2500, 10)
        self.panela = self.app.productos.registrar_producto("Panela", 2000, 3000, 1)
        self.arroz_integral = self.app.productos.registrar_producto("Arroz integral", 2500, 3200, 4)
        self.cliente = self.app.clientes.registrar_cliente("Cliente de prueba", True, 100000, plazo_credito_dias=15)
        self.pv = PresentadorPuntoDeVenta(self.app)


class PruebasDeBusquedaYCarrito(BaseDelPresentador):
    def test_formato_de_pesos_con_separador_de_miles(self):
        self.assertEqual(formato_pesos(17300), "$ 17.300")
        self.assertEqual(formato_pesos(0), "$ 0")
        self.assertEqual(formato_pesos(1250000), "$ 1.250.000")

    def test_busca_solo_por_nombre_sin_importar_mayusculas(self):
        filas = self.pv.buscar("ARROZ")
        self.assertEqual([f.nombre for f in filas], ["Arroz 500 g", "Arroz integral"])
        self.assertEqual((filas[0].precio, filas[0].disponibles), (2500, 10))

    def test_buscar_texto_vacio_no_devuelve_nada(self):
        self.assertEqual(self.pv.buscar("   "), [])

    def test_agregar_el_mismo_producto_suma_la_cantidad(self):
        self.pv.agregar(self.arroz.id_producto, "2")
        self.pv.agregar(self.arroz.id_producto, "3")
        linea, = self.pv.lineas()
        self.assertEqual((linea.nombre, linea.cantidad, linea.importe, linea.disponibles), ("Arroz 500 g", 5, 12500, 10))

    def test_cantidad_que_no_es_numero_da_un_mensaje_claro_y_no_agrega(self):
        resultado = self.pv.agregar(self.arroz.id_producto, "dos")
        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.mensaje, "La cantidad debe ser un número entero")
        self.assertEqual(self.pv.lineas(), [])

    def test_cantidad_cero_usa_el_mensaje_del_dominio(self):
        resultado = self.pv.agregar(self.arroz.id_producto, "0")
        self.assertEqual(resultado.mensaje, "La cantidad debe ser mayor a cero")

    def test_no_valida_el_stock_al_agregar_solo_al_confirmar(self):
        resultado = self.pv.agregar(self.panela.id_producto, "3")   # solo hay 1
        self.assertTrue(resultado.exito)
        self.assertEqual(self.pv.lineas()[0].disponibles, 1)

    def test_total_y_resumen_del_carrito(self):
        self.pv.agregar(self.arroz.id_producto, "2")
        self.pv.agregar(self.panela.id_producto, "1")
        self.assertEqual(self.pv.total(), 8000)
        self.assertEqual(self.pv.resumen(), "2 productos · 3 unidades")

    def test_quitar_y_limpiar(self):
        self.pv.agregar(self.arroz.id_producto, "2")
        self.pv.agregar(self.panela.id_producto, "1")
        self.pv.quitar(self.arroz.id_producto)
        self.assertEqual([l.nombre for l in self.pv.lineas()], ["Panela"])
        self.pv.limpiar()
        self.assertEqual((self.pv.lineas(), self.pv.total(), self.pv.resumen()), ([], 0, "Sin productos"))


class PruebasDelCobroDeContado(BaseDelPresentador):
    def test_venta_de_contado_devuelve_ticket_con_cambio_y_vacia_el_carrito(self):
        self.pv.agregar(self.arroz.id_producto, "2")
        self.pv.agregar(self.panela.id_producto, "1")
        resultado = self.pv.cobrar_de_contado("10000")
        self.assertTrue(resultado.exito)
        self.assertIn("Cambio: $ 2.000", resultado.mensaje)
        for texto in ("Comprobante interno (no es factura)", "2 x Arroz 500 g", "TOTAL: $ 8.000",
                      "Forma de pago: EFECTIVO", "Recibido: $ 10.000", "Cambio: $ 2.000"):
            self.assertIn(texto, resultado.ticket)
        self.assertEqual(self.pv.lineas(), [])
        self.assertEqual(self.app.cantidad_en_inventario(self.arroz.id_producto), 8)

    def test_el_total_mostrado_es_el_mismo_que_se_guarda(self):
        self.pv.agregar(self.arroz.id_producto, "3")
        mostrado = self.pv.total()
        self.pv.cobrar_de_contado(str(mostrado))
        guardado = self.app.conexion.execute("SELECT total FROM ventas").fetchone()[0]
        self.assertEqual(guardado, mostrado)

    def test_stock_insuficiente_muestra_el_mensaje_del_dominio_y_conserva_el_carrito(self):
        self.pv.agregar(self.panela.id_producto, "3")
        resultado = self.pv.cobrar_de_contado("20000")
        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.mensaje, "Solo hay 1 disponibles de Panela")
        self.assertEqual(len(self.pv.lineas()), 1)
        self.assertEqual(self.app.numero_de_ventas(), 0)

    def test_efectivo_insuficiente_muestra_el_mensaje_del_dominio(self):
        self.pv.agregar(self.arroz.id_producto, "2")
        resultado = self.pv.cobrar_de_contado("4999")
        self.assertEqual(resultado.mensaje, "El efectivo recibido (4999) no alcanza para el total, que es 5000")

    def test_recibido_que_no_es_numero(self):
        self.pv.agregar(self.arroz.id_producto, "1")
        self.assertEqual(self.pv.cobrar_de_contado("diez mil").mensaje, "El valor recibido debe ser un número entero")

    def test_carrito_vacio_usa_el_mensaje_del_dominio(self):
        self.assertEqual(self.pv.cobrar_de_contado("1000").mensaje, "La venta no tiene productos")

    def test_falla_al_guardar_da_un_mensaje_para_reintentar(self):
        self.app.conexion.execute("CREATE TRIGGER falla_simulada BEFORE INSERT ON detalles_venta "
                                  "BEGIN SELECT RAISE(ABORT, 'falla simulada'); END")
        self.pv.agregar(self.arroz.id_producto, "1")
        resultado = self.pv.cobrar_de_contado("2500")
        self.assertEqual(resultado.mensaje, "No se pudo guardar la venta; no quedó nada a medias. Intente de nuevo.")
        self.assertEqual(len(self.pv.lineas()), 1)


class PruebasDeLaVentaACredito(BaseDelPresentador):
    def test_datos_del_cliente_muestran_limite_deuda_y_credito_disponible(self):
        self.pv.agregar(self.arroz.id_producto, "2")
        self.pv.vender_a_credito(self.cliente.id_cliente)
        datos = self.pv.datos_del_cliente(self.cliente.id_cliente)
        self.assertEqual((datos.limite, datos.deuda, datos.disponible), (100000, 5000, 95000))
        self.assertIn("Crédito disponible: $ 95.000", datos.texto)

    def test_lista_de_clientes_para_elegir(self):
        self.assertEqual([(c.id_cliente, c.nombres) for c in self.pv.clientes()],
                         [(self.cliente.id_cliente, "Cliente de prueba")])

    def test_venta_a_credito_devuelve_ticket_con_cliente_y_vencimiento(self):
        self.pv.agregar(self.arroz.id_producto, "2")
        resultado = self.pv.vender_a_credito(self.cliente.id_cliente)
        self.assertTrue(resultado.exito)
        cuenta, = self.app.credito.cuentas_del_cliente(self.cliente.id_cliente)
        for texto in ("Forma de pago: CRÉDITO", "Cliente: Cliente de prueba",
                      f"Vence: {cuenta.fecha_vencimiento:%Y-%m-%d}", "TOTAL: $ 5.000"):
            self.assertIn(texto, resultado.ticket)
        self.assertEqual(self.pv.lineas(), [])

    def test_credito_no_permitido_muestra_el_mensaje_del_dominio(self):
        sin_credito = self.app.clientes.registrar_cliente("Sin crédito", False, 0)
        self.pv.agregar(self.arroz.id_producto, "1")
        resultado = self.pv.vender_a_credito(sin_credito.id_cliente)
        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.mensaje, "El cliente no puede comprar a crédito por 2500")

    def test_sin_cliente_elegido_usa_el_mensaje_del_dominio(self):
        self.pv.agregar(self.arroz.id_producto, "1")
        self.assertEqual(self.pv.vender_a_credito(None).mensaje, "El cliente no existe")


class PruebasDeQueSoloLlamaAlServicio(unittest.TestCase):
    """Con un mock de Aplicacion: el presentador delega la venta, no la hace por su cuenta."""

    def test_cobrar_de_contado_llama_una_sola_vez_al_servicio_con_las_lineas(self):
        app = Mock()
        app.productos.obtener.return_value = Mock(id_producto=1, nombre="Producto A", precio_venta=2500)
        app.ventas.registrar_venta_de_contado.side_effect = ValueError("detenido en la prueba")
        pv = PresentadorPuntoDeVenta(app)
        pv.agregar(1, "2")
        pv.cobrar_de_contado("5000")
        app.ventas.registrar_venta_de_contado.assert_called_once_with([(1, 2)], 5000)


if __name__ == "__main__":
    unittest.main()

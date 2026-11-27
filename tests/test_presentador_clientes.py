"""Pruebas del presentador de la sección Clientes (HU-05, RF-07; etapa 2 de la interfaz).

Igual que el del punto de venta: no usa Tkinter, recibe texto y devuelve filas y mensajes listos.
Solo usa los datos del cliente que ya tiene el dominio (nombre, crédito, límite, plazo): los demás datos
están por confirmar con el propietario. No bloquea nombres repetidos (regla «por definir», HU-05).
Se escribieron antes del código. Datos ficticios.
"""
import unittest

from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.presentador_clientes import PresentadorDeClientes


class BaseDeClientes(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz 500 g", 2000, 2500, 10)
        self.ana = self.app.clientes.registrar_cliente("Cliente ficticio Ana", True, 100000, plazo_credito_dias=15)
        self.beto = self.app.clientes.registrar_cliente("Cliente ficticio Beto", False, 0, plazo_credito_dias=30)
        self.pc = PresentadorDeClientes(self.app)


class PruebasDeLaLista(BaseDeClientes):
    def test_lista_con_limite_deuda_y_disponible_en_pesos(self):
        self.app.ventas.registrar_venta_a_credito(self.ana.id_cliente, [(self.arroz.id_producto, 2)])
        filas = dict(self.pc.tabla())
        self.assertEqual(filas[self.ana.id_cliente], ("Cliente ficticio Ana", "$ 100.000", "$ 5.000", "$ 95.000"))

    def test_cliente_sin_credito_lo_dice_en_disponible(self):
        self.assertEqual(dict(self.pc.tabla())[self.beto.id_cliente][3], "Sin crédito")

    def test_busca_por_nombre_sin_importar_mayusculas(self):
        self.assertEqual([iid for iid, _ in self.pc.tabla("  beto ")], [self.beto.id_cliente])
        self.assertEqual(len(self.pc.tabla("")), 2)


class PruebasDelRegistro(BaseDeClientes):
    def test_registra_con_los_cuatro_datos_del_dominio(self):
        resultado = self.pc.registrar("  Cliente ficticio Carla ", True, "80000", "20")
        self.assertTrue(resultado.exito)
        self.assertEqual(resultado.mensaje, "Cliente registrado: Cliente ficticio Carla")
        carla = next(c for c in self.app.clientes.listar() if c.nombres == "Cliente ficticio Carla")
        self.assertEqual((carla.credito_habilitado, carla.limite_credito, carla.plazo_credito_dias), (True, 80000, 20))

    def test_el_mensaje_del_dominio_llega_tal_cual(self):
        casos = (("", "80000", "20", "El nombre es obligatorio"),
                 ("Cliente ficticio", "-1", "20", "El límite de crédito no puede ser negativo"),
                 ("Cliente ficticio", "80000", "0", "El plazo de crédito debe ser de al menos 1 día"))
        for nombre, limite, plazo, mensaje in casos:
            with self.subTest(mensaje=mensaje):
                resultado = self.pc.registrar(nombre, True, limite, plazo)
                self.assertFalse(resultado.exito)
                self.assertEqual(resultado.mensaje, mensaje)
        self.assertEqual(len(self.app.clientes.listar()), 2)          # no se guardó ninguno

    def test_texto_que_no_es_numero_se_explica(self):
        resultado = self.pc.registrar("Cliente ficticio", True, "cien mil", "20")
        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.mensaje, "El límite debe ser un número entero")

    def test_el_plazo_por_defecto_es_el_del_dominio(self):
        self.assertEqual(self.pc.plazo_por_defecto(), "30")


class PruebasDelDetalle(BaseDeClientes):
    def test_sin_deudas(self):
        texto = self.pc.detalle(self.ana.id_cliente)
        self.assertIn("Cliente ficticio Ana", texto)
        self.assertIn("Crédito habilitado · plazo 15 días", texto)
        self.assertIn("Límite $ 100.000 · Debe $ 0 · Disponible $ 100.000", texto)
        self.assertIn("No tiene cuentas pendientes", texto)

    def test_muestra_solo_las_cuentas_con_saldo(self):
        self.app.ventas.registrar_venta_a_credito(self.ana.id_cliente, [(self.arroz.id_producto, 2)])
        venta_pagada = self.app.ventas.registrar_venta_a_credito(self.ana.id_cliente, [(self.arroz.id_producto, 1)])
        cuenta_pagada = self.app.credito.cuentas_del_cliente(self.ana.id_cliente)[1]
        self.app.credito.registrar_abono(cuenta_pagada.id_cuenta, 2500)
        texto = self.pc.detalle(self.ana.id_cliente)
        self.assertIn("Cuentas pendientes: 1", texto)
        self.assertIn("saldo $ 5.000", texto)
        self.assertNotIn(f"Venta #{venta_pagada.id_venta} ", texto)

    def test_cliente_sin_credito(self):
        self.assertIn("Sin crédito habilitado", self.pc.detalle(self.beto.id_cliente))

    def test_cliente_que_no_existe(self):
        self.assertEqual(self.pc.detalle(999), "")


if __name__ == "__main__":
    unittest.main()

"""Editar cliente (recomendación aprobada por el desarrollador, noviembre de 2026).

Se pueden cambiar los mismos 4 datos con que se registra: nombre, crédito habilitado, límite y plazo. Las reglas
son las del registro (las valida el dominio). Las cuentas que ya existen NO cambian: su vencimiento se calculó
con el plazo de cuando se vendió. Bajar el límite por debajo de la deuda se permite (solo impide fiar más);
eso queda por confirmar con el propietario. Se escribieron antes del código. Datos ficticios.
"""
import unittest

from interfaz_web.api import ApiDeLaTienda
from tiendas_sm.aplicacion import Aplicacion
from tiendas_sm.dominio import CreditoNoPermitido
from tiendas_sm.presentador_clientes import PresentadorDeClientes


class BaseDeEdicion(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacion()
        self.arroz = self.app.productos.registrar_producto("Arroz ficticio", 2000, 2500, 50)
        self.ana = self.app.clientes.registrar_cliente("Cliente ficticia Ana", True, 100000, plazo_credito_dias=15)

    def guardado(self):
        return self.app.clientes.obtener(self.ana.id_cliente)


class PruebasDelServicio(BaseDeEdicion):
    def test_actualiza_los_4_datos_y_quedan_guardados(self):
        self.app.clientes.actualizar_cliente(self.ana.id_cliente, "Cliente ficticia Ana María", False, 80000, 30)
        cliente = self.guardado()
        self.assertEqual((cliente.nombres, cliente.credito_habilitado, cliente.limite_credito, cliente.plazo_credito_dias),
                         ("Cliente ficticia Ana María", False, 80000, 30))
        self.assertEqual(len(self.app.clientes.listar()), 1)           # no crea otro cliente

    def test_aplica_las_mismas_reglas_del_registro_y_no_guarda_nada_si_falla(self):
        for datos in (("", True, 1000, 15), ("Ana", True, -1, 15), ("Ana", True, 1000, 0)):
            with self.subTest(datos=datos), self.assertRaises(ValueError):
                self.app.clientes.actualizar_cliente(self.ana.id_cliente, *datos)
        self.assertEqual(self.guardado().nombres, "Cliente ficticia Ana")

    def test_cliente_que_no_existe(self):
        with self.assertRaisesRegex(ValueError, "El cliente no existe"):
            self.app.clientes.actualizar_cliente(999, "Nadie", True, 1000, 15)

    def test_las_cuentas_que_ya_existen_conservan_su_vencimiento(self):
        self.app.ventas.registrar_venta_a_credito(self.ana.id_cliente, [(self.arroz.id_producto, 2)])
        antes = self.app.credito.cuentas_del_cliente(self.ana.id_cliente)[0].fecha_vencimiento
        self.app.clientes.actualizar_cliente(self.ana.id_cliente, "Cliente ficticia Ana", True, 100000, 60)
        self.assertEqual(self.app.credito.cuentas_del_cliente(self.ana.id_cliente)[0].fecha_vencimiento, antes)

    def test_bajar_el_limite_bajo_la_deuda_impide_fiar_mas(self):
        self.app.ventas.registrar_venta_a_credito(self.ana.id_cliente, [(self.arroz.id_producto, 4)])   # debe 10.000
        self.app.clientes.actualizar_cliente(self.ana.id_cliente, "Cliente ficticia Ana", True, 5000, 15)
        with self.assertRaises(CreditoNoPermitido):
            self.app.ventas.registrar_venta_a_credito(self.ana.id_cliente, [(self.arroz.id_producto, 1)])


class PruebasDelPresentador(BaseDeEdicion):
    def setUp(self):
        super().setUp()
        self.pc = PresentadorDeClientes(self.app)

    def test_datos_para_editar_trae_lo_guardado_como_texto(self):
        datos = self.pc.datos_para_editar(self.ana.id_cliente)
        self.assertEqual((datos.nombres, datos.credito_habilitado, datos.limite, datos.plazo),
                         ("Cliente ficticia Ana", True, "100000", "15"))
        self.assertIsNone(self.pc.datos_para_editar(999))

    def test_editar_convierte_el_texto_y_muestra_el_mensaje(self):
        resultado = self.pc.editar(self.ana.id_cliente, "  Cliente ficticia Ana  ", True, "120000", "20")
        self.assertEqual((resultado.exito, resultado.mensaje), (True, "Cliente actualizado: Cliente ficticia Ana"))
        self.assertEqual(self.guardado().limite_credito, 120000)

    def test_editar_con_datos_invalidos_muestra_el_mensaje_del_dominio(self):
        self.assertEqual(self.pc.editar(self.ana.id_cliente, "Ana", True, "mucho", "15").mensaje,
                         "El límite debe ser un número entero")
        self.assertEqual(self.pc.editar(self.ana.id_cliente, " ", True, "1000", "15").mensaje, "El nombre es obligatorio")
        self.assertFalse(self.pc.editar(None, "Ana", True, "1000", "15").exito)


class PruebasDeLaApi(BaseDeEdicion):
    def test_datos_y_editar_desde_la_pagina(self):
        api = ApiDeLaTienda(self.app)
        self.assertEqual(api.datos_cliente(self.ana.id_cliente),
                         {"nombres": "Cliente ficticia Ana", "credito": True, "limite": "100000", "plazo": "15",
                          "telefono": "", "direccion": ""})
        self.assertIsNone(api.datos_cliente(999))
        self.assertTrue(api.editar_cliente(self.ana.id_cliente, "Cliente ficticia Ana", False, "0", "15")["exito"])
        self.assertFalse(self.guardado().credito_habilitado)


if __name__ == "__main__":
    unittest.main()

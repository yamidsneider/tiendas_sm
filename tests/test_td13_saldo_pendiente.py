"""TD-13 (FPI-31): el saldo pendiente se calcula en la base con una sola consulta, sin cambiar el resultado.

Prueba de equivalencia: en escenarios aleatorios (semilla fija) con varios clientes, ventas a crédito y abonos
parciales y totales, el saldo nuevo debe ser idéntico a la regla de siempre: suma de calcular_saldo() de cada cuenta.
"""
import random
import unittest

from tiendas_sm.aplicacion import Aplicacion


def saldo_por_la_regla_original(app, cliente):
    return sum(cuenta.calcular_saldo() for cuenta in app.credito.cuentas_del_cliente(cliente.id_cliente))


class PruebasEquivalenciaSaldo(unittest.TestCase):
    def test_el_repositorio_calcula_el_saldo_en_una_consulta(self):
        app = Aplicacion()
        cliente = app.clientes.registrar_cliente("Cliente ficticio", True, 10**9, 30)
        self.assertEqual(app.repo_ventas.saldo_pendiente_del_cliente(cliente.id_cliente), 0)

    def test_equivalencia_en_200_escenarios_aleatorios(self):
        azar = random.Random(31)  # noqa: S311 — datos de prueba reproducibles, no criptografía
        for escenario in range(200):
            with self.subTest(escenario=escenario):
                app = Aplicacion()
                productos = [app.productos.registrar_producto(f"P{i}", 100, azar.randint(150, 9000), 10**6) for i in range(4)]
                clientes = [app.clientes.registrar_cliente(f"Cliente ficticio {i}", True, 10**9, 30) for i in range(3)]
                for _ in range(azar.randint(0, 12)):
                    lineas = [(azar.choice(productos).id_producto, azar.randint(1, 4)) for _ in range(azar.randint(1, 3))]
                    app.ventas.registrar_venta_a_credito(azar.choice(clientes).id_cliente, lineas)
                for cliente in clientes:
                    for cuenta in app.credito.cuentas_del_cliente(cliente.id_cliente):
                        if azar.random() < 0.6 and cuenta.calcular_saldo() > 0:
                            abono = cuenta.calcular_saldo() if azar.random() < 0.3 else azar.randint(1, cuenta.calcular_saldo())
                            app.credito.registrar_abono(cuenta.id_cuenta, abono)
                for cliente in clientes:
                    esperado = saldo_por_la_regla_original(app, cliente)
                    self.assertEqual(app.credito.saldo_pendiente(cliente), esperado)
                    self.assertEqual(app.repo_ventas.saldo_pendiente_del_cliente(cliente.id_cliente), esperado)

    def test_cliente_sin_cuentas_tiene_saldo_cero(self):
        app = Aplicacion()
        cliente = app.clientes.registrar_cliente("Cliente ficticio", True, 1000, 30)
        self.assertEqual(app.credito.saldo_pendiente(cliente), 0)


if __name__ == "__main__":
    unittest.main()

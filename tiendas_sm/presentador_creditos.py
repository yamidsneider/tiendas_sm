"""Presentador de la sección Créditos y abonos (HU-06, RF-09; etapa 3 de la interfaz).

No usa Tkinter. Reúne las cuentas por cobrar de todos los clientes con ControlCredito, convierte el monto
escrito a número y registra el abono. Las reglas (abono mayor a cero y no mayor al saldo, cuenta PAGADA al
llegar a 0) las aplica el dominio; su mensaje se muestra tal cual. No se calcula mora ni se marca
«vencida»: esas reglas están por confirmar con el propietario.
"""
from collections import namedtuple

from tiendas_sm.dominio import EstadoCuenta
from tiendas_sm.presentador import Resultado, a_entero, formato_pesos

FORMATO_FECHA = "%d/%m/%Y"
NOMBRE_DEL_ESTADO = {EstadoCuenta.ABIERTA: "Abierta", EstadoCuenta.PAGADA: "Pagada"}
MENSAJE_SIN_CUENTA = "Elige una cuenta de la lista"

CuentaConCliente = namedtuple("CuentaConCliente", "cuenta nombres")


def _contar(cantidad, singular, plural):
    return f"{cantidad} {singular if cantidad == 1 else plural}"


class PresentadorDeCreditos:
    def __init__(self, app):
        self.app = app

    def tabla(self, ver_pagadas=False):
        """Filas (id_cuenta, (cliente, saldo, vence, estado)): primero las abiertas, por fecha de vencimiento."""
        cuentas = [c for c in self._cuentas() if ver_pagadas or c.cuenta.estado == EstadoCuenta.ABIERTA]
        cuentas.sort(key=lambda c: (c.cuenta.estado != EstadoCuenta.ABIERTA, c.cuenta.fecha_vencimiento))
        return [(c.cuenta.id_cuenta, (c.nombres, formato_pesos(c.cuenta.calcular_saldo()),
                                      f"{c.cuenta.fecha_vencimiento:{FORMATO_FECHA}}",
                                      NOMBRE_DEL_ESTADO[c.cuenta.estado])) for c in cuentas]

    def resumen(self):
        abiertas = [c.cuenta for c in self._cuentas() if c.cuenta.estado == EstadoCuenta.ABIERTA]
        total = sum(cuenta.calcular_saldo() for cuenta in abiertas)
        return f"Por cobrar: {formato_pesos(total)} en {_contar(len(abiertas), 'cuenta', 'cuentas')}"

    def detalle(self, id_cuenta):
        elegida = self._buscar(id_cuenta)
        if elegida is None:
            return ""
        cuenta = elegida.cuenta
        abonado = sum(cuenta.abonos)
        return "\n".join((
            elegida.nombres,
            f"Venta #{cuenta.id_venta} · {NOMBRE_DEL_ESTADO[cuenta.estado]}",
            f"Total {formato_pesos(cuenta.monto_original)} · Abonado {formato_pesos(abonado)} · "
            f"Saldo {formato_pesos(cuenta.calcular_saldo())}",
            f"Abierta el {cuenta.fecha_apertura:{FORMATO_FECHA}} · vence {cuenta.fecha_vencimiento:{FORMATO_FECHA}}",
            _contar(len(cuenta.abonos), "abono registrado", "abonos registrados")))

    def abonar(self, id_cuenta, monto_texto):
        if id_cuenta is None:
            return Resultado(False, MENSAJE_SIN_CUENTA)
        try:
            monto = a_entero(monto_texto, "El abono")
            cuenta = self.app.credito.registrar_abono(id_cuenta, monto)
        except ValueError as error:
            return Resultado(False, str(error))
        final = ("La cuenta quedó PAGADA" if cuenta.estado == EstadoCuenta.PAGADA
                 else f"Saldo: {formato_pesos(cuenta.calcular_saldo())}")
        return Resultado(True, f"Abono de {formato_pesos(monto)} registrado. {final}")

    def _cuentas(self):
        """Las cuentas de todos los clientes, con el nombre del cliente al lado."""
        return [CuentaConCliente(cuenta, cliente.nombres) for cliente in self.app.clientes.listar()
                for cuenta in self.app.credito.cuentas_del_cliente(cliente.id_cliente)]

    def _buscar(self, id_cuenta):
        return next((c for c in self._cuentas() if c.cuenta.id_cuenta == id_cuenta), None)

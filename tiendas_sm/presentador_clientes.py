"""Presentador de la sección Clientes (HU-05, RF-07; etapa 2 de la interfaz).

Como el del punto de venta: no usa Tkinter, así se prueba sin ventanas. Convierte el texto del formulario
a números, llama a ServicioDeClientes y ControlCredito, y devuelve filas y mensajes listos para mostrar.
Las reglas (nombre obligatorio, límite no negativo, plazo mínimo) las valida el dominio; su mensaje se
muestra tal cual. Teléfono y dirección son opcionales (respuesta 3.1) y son datos personales.
"""
from collections import namedtuple

from tiendas_sm.dominio import PLAZO_POR_DEFECTO_DIAS, EstadoCuenta
from tiendas_sm.presentador import Resultado, a_entero, formato_pesos

SIN_CREDITO = "Sin crédito"
MENSAJE_SIN_CLIENTE = "Elige un cliente de la lista"

DatosParaEditar = namedtuple("DatosParaEditar", "nombres credito_habilitado limite plazo telefono direccion")
FORMATO_FECHA = "%d/%m/%Y"


class PresentadorDeClientes:
    def __init__(self, app):
        self.app = app

    def plazo_por_defecto(self):
        return str(PLAZO_POR_DEFECTO_DIAS)

    def tabla(self, texto=""):
        """Filas (id, (cliente, límite, debe, disponible)) de los clientes cuyo nombre contiene el texto."""
        buscado = texto.strip().lower()
        filas = []
        for cliente in self.app.clientes.listar():
            if buscado in cliente.nombres.lower():
                deuda = self.app.credito.saldo_pendiente(cliente)
                disponible = (formato_pesos(cliente.credito_disponible(deuda)) if cliente.credito_habilitado
                              else SIN_CREDITO)
                filas.append((cliente.id_cliente, (cliente.nombres, formato_pesos(cliente.limite_credito),
                                                   formato_pesos(deuda), disponible)))
        return filas

    def registrar(self, nombres, credito_habilitado, limite_texto, plazo_texto, telefono="", direccion=""):
        try:
            limite = a_entero(limite_texto, "El límite")
            plazo = a_entero(plazo_texto, "El plazo")
            cliente = self.app.clientes.registrar_cliente(nombres.strip(), credito_habilitado, limite,
                                                          plazo_credito_dias=plazo, telefono=telefono,
                                                          direccion=direccion)
        except ValueError as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Cliente registrado: {cliente.nombres}")

    def datos_para_editar(self, id_cliente):
        """Los datos guardados, como texto para llenar el formulario de Editar cliente; None si no existe."""
        cliente = self.app.clientes.obtener(id_cliente)
        if cliente is None:
            return None
        return DatosParaEditar(cliente.nombres, cliente.credito_habilitado, str(cliente.limite_credito),
                               str(cliente.plazo_credito_dias), cliente.telefono, cliente.direccion)

    def editar(self, id_cliente, nombres, credito_habilitado, limite_texto, plazo_texto, telefono=None, direccion=None):
        """Sin teléfono ni dirección (la versión Tkinter no los pide) se conservan los guardados."""
        if id_cliente is None:
            return Resultado(False, MENSAJE_SIN_CLIENTE)
        try:
            limite = a_entero(limite_texto, "El límite")
            plazo = a_entero(plazo_texto, "El plazo")
            cliente = self.app.clientes.actualizar_cliente(id_cliente, nombres.strip(), credito_habilitado, limite,
                                                           plazo, telefono, direccion)
        except ValueError as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Cliente actualizado: {cliente.nombres}")

    def detalle(self, id_cliente):
        """Texto con el crédito del cliente y sus cuentas que todavía tienen saldo (solo lectura)."""
        cliente = next((c for c in self.app.clientes.listar() if c.id_cliente == id_cliente), None)
        if cliente is None:
            return ""
        deuda = self.app.credito.saldo_pendiente(cliente)
        credito = (f"Crédito habilitado · plazo {cliente.plazo_credito_dias} días" if cliente.credito_habilitado
                   else "Sin crédito habilitado")
        contacto = [f"{rotulo}: {valor}" for rotulo, valor in (("Teléfono", cliente.telefono),
                                                              ("Dirección", cliente.direccion)) if valor]
        lineas = [cliente.nombres, *contacto, credito,
                  f"Límite {formato_pesos(cliente.limite_credito)} · Debe {formato_pesos(deuda)} · "
                  f"Disponible {formato_pesos(cliente.credito_disponible(deuda))}"]
        return "\n".join(lineas + self._cuentas_pendientes(id_cliente))

    def _cuentas_pendientes(self, id_cliente):
        cuentas = [c for c in self.app.credito.cuentas_del_cliente(id_cliente) if c.estado == EstadoCuenta.ABIERTA]
        if not cuentas:
            return ["No tiene cuentas pendientes"]
        return [f"Cuentas pendientes: {len(cuentas)}"] + [
            f"Venta #{c.id_venta} · saldo {formato_pesos(c.calcular_saldo())} · "
            f"vence {c.fecha_vencimiento:{FORMATO_FECHA}}" for c in cuentas]

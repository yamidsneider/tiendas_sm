from collections import namedtuple
from datetime import datetime
from enum import Enum

from tiendas_sm.validaciones import (exigir_mayor_a_cero, exigir_no_negativo, exigir_solo_caracteres,
                                     exigir_texto_obligatorio)

PLAZO_POR_DEFECTO_DIAS = 30
PLAZO_MINIMO_DIAS = 1   # UC-05 del DDS: el plazo de crédito es de al menos un día
CARACTERES_DEL_TELEFONO = set("0123456789 +-")   # respuesta 3.1: el teléfono es opcional


class StockInsuficiente(Exception):
    pass


class CreditoNoPermitido(Exception):
    pass


class EfectivoInsuficiente(Exception):
    pass


class TipoVenta(str, Enum):
    CONTADO = "CONTADO"
    CREDITO = "CREDITO"


class FormaDePago(str, Enum):
    EFECTIVO = "EFECTIVO"
    TRANSFERENCIA = "TRANSFERENCIA"   # Nequi, Daviplata: se confirma mirando el celular (respuesta 1.2)
    MIXTO = "MIXTO"                   # parte por transferencia y parte en efectivo


class EstadoVenta(str, Enum):
    ABIERTA = "ABIERTA"
    CONFIRMADA = "CONFIRMADA"
    ANULADA = "ANULADA"


class EstadoCuenta(str, Enum):
    ABIERTA = "ABIERTA"
    PAGADA = "PAGADA"


# RF-04: una entrada o una salida por venta ya guardada. Solo se lee (no tiene reglas); la fecha es datetime.
MovimientoDeInventario = namedtuple("MovimientoDeInventario", "id_movimiento id_producto tipo cantidad fecha")


class Producto:
    def __init__(self, id_producto, nombre, precio_compra, precio_venta, stock_minimo=0, codigo="", dias_aviso=0):
        """codigo: código de barras opcional (respuesta 1.4); vacío si el producto no tiene.
        dias_aviso: con cuántos días de anticipación avisar que un lote de este producto va a vencer (RF-13)."""
        exigir_texto_obligatorio(nombre, "El nombre es obligatorio")
        if precio_compra < 0 or precio_venta < 0:
            raise ValueError("Los precios no pueden ser negativos")
        exigir_no_negativo(stock_minimo, "El stock mínimo no puede ser negativo")
        exigir_no_negativo(dias_aviso, "Los días de aviso no pueden ser negativos")
        self.dias_aviso = dias_aviso
        self.id_producto = id_producto
        self.nombre = nombre
        self.precio_compra = precio_compra
        self.precio_venta = precio_venta
        self.stock_minimo = stock_minimo
        self.codigo = (codigo or "").strip()

    def actualizar_precio(self, nuevo_precio):
        if nuevo_precio < 0:
            raise ValueError("El precio no puede ser negativo")
        self.precio_venta = nuevo_precio

    def necesita_reponer(self, disponibles):
        """RF-12: avisa cuando quedan el stock mínimo o menos. Un mínimo de 0 quiere decir «sin aviso»."""
        return self.stock_minimo > 0 and disponibles <= self.stock_minimo


class Lote:
    """RF-10 y RF-13: un lote que llegó con su fecha de vencimiento. Es solo un registro para avisar: NO está
    ligado a las existencias (decisión del grupo B). La cantidad es informativa (lo que traía el lote)."""
    VENCIDO, POR_VENCER, AL_DIA = "Vencido", "Por vencer", "Al día"

    def __init__(self, id_lote, id_producto, numero, fecha_vencimiento, cantidad, activo=True):
        exigir_mayor_a_cero(cantidad)
        self.id_lote = id_lote
        self.id_producto = id_producto
        self.numero = (numero or "").strip()
        self.fecha_vencimiento = fecha_vencimiento      # date (sin hora)
        self.cantidad = cantidad
        self.activo = activo

    def dias_para_vencer(self, hoy):
        """Negativo si ya venció."""
        return (self.fecha_vencimiento - hoy).days

    def estado(self, hoy, dias_aviso):
        dias = self.dias_para_vencer(hoy)
        if dias < 0:
            return self.VENCIDO
        return self.POR_VENCER if dias <= dias_aviso else self.AL_DIA

    def retirar(self):
        """«Ya no está»: se vendió, se botó o se devolvió al proveedor. Sale de la lista de alertas."""
        if not self.activo:
            raise ValueError("Ese lote ya no está en la lista")
        self.activo = False


class Existencia:
    def __init__(self, id_producto, cantidad_actual=0, cantidad_reservada=0):
        self.id_producto = id_producto
        self.cantidad_actual = cantidad_actual
        self.cantidad_reservada = cantidad_reservada

    def cantidad_disponible(self):
        return self.cantidad_actual - self.cantidad_reservada

    def descontar(self, cantidad):
        exigir_mayor_a_cero(cantidad)
        if cantidad > self.cantidad_actual:
            raise StockInsuficiente(f"Solo hay {self.cantidad_actual} disponibles")
        self.cantidad_actual -= cantidad

    def aumentar(self, cantidad):
        exigir_mayor_a_cero(cantidad)
        self.cantidad_actual += cantidad


class Cliente:
    def __init__(self, id_cliente, nombres, credito_habilitado, limite_credito, plazo_credito_dias,
                 telefono="", direccion=""):
        """telefono y direccion (respuesta 3.1) son opcionales y son datos personales."""
        exigir_texto_obligatorio(nombres, "El nombre es obligatorio")
        telefono, direccion = (telefono or "").strip(), (direccion or "").strip()
        exigir_solo_caracteres(telefono, CARACTERES_DEL_TELEFONO, "El teléfono solo puede tener números, espacios, + y -")
        exigir_no_negativo(limite_credito, "El límite de crédito no puede ser negativo")
        if plazo_credito_dias < PLAZO_MINIMO_DIAS:
            raise ValueError(f"El plazo de crédito debe ser de al menos {PLAZO_MINIMO_DIAS} día")
        self.id_cliente = id_cliente
        self.nombres = nombres
        self.credito_habilitado = credito_habilitado
        self.limite_credito = limite_credito
        self.plazo_credito_dias = plazo_credito_dias
        self.telefono = telefono
        self.direccion = direccion

    def credito_disponible(self, saldo_pendiente):
        return self.limite_credito - saldo_pendiente

    def puede_endeudarse(self, monto, saldo_pendiente):
        return self.credito_habilitado and monto <= self.credito_disponible(saldo_pendiente)


class DetalleVenta:
    def __init__(self, numero_linea, id_producto, cantidad, precio_unitario):
        self.numero_linea = numero_linea
        self.id_producto = id_producto
        self.cantidad = cantidad
        self.precio_unitario = precio_unitario

    def subtotal(self):
        return self.cantidad * self.precio_unitario


class Venta:
    def __init__(self, id_cliente=None, tipo=TipoVenta.CREDITO):
        self.id_venta = None
        self.id_cliente = id_cliente
        self.tipo = tipo
        self.forma_pago = None       # solo se llena en las ventas de contado
        self.valor_recibido = None   # efectivo recibido
        self.valor_transferencia = None
        self.fecha = datetime.now()
        self.estado = EstadoVenta.ABIERTA
        self.detalles = []
        self.total = 0

    def agregar_detalle(self, producto, cantidad):
        exigir_mayor_a_cero(cantidad)
        numero_linea = len(self.detalles) + 1
        self.detalles.append(DetalleVenta(numero_linea, producto.id_producto, cantidad, producto.precio_venta))

    def calcular_total(self):
        self.total = sum(detalle.subtotal() for detalle in self.detalles)
        return self.total

    def registrar_pago_en_efectivo(self, recibido):
        self.registrar_pago(recibido, 0)

    def registrar_pago(self, efectivo, transferencia=0):
        """Respuesta 1.2: efectivo, transferencia o las dos (mixto). La transferencia no puede pasar del total
        (no se da cambio por transferencia); el efectivo cubre lo que falta y de él sale el cambio."""
        total = self.calcular_total()
        exigir_no_negativo(transferencia, "La transferencia no puede ser negativa")
        if transferencia > total:
            raise ValueError(f"La transferencia ({transferencia}) no puede ser mayor al total, que es {total}")
        if efectivo + transferencia < total:
            if not transferencia:
                raise EfectivoInsuficiente(f"El efectivo recibido ({efectivo}) no alcanza para el total, que es {total}")
            raise EfectivoInsuficiente(f"El pago ({efectivo + transferencia}) no alcanza para el total, que es {total}")
        self.forma_pago = (FormaDePago.EFECTIVO if not transferencia else
                           FormaDePago.TRANSFERENCIA if not efectivo else FormaDePago.MIXTO)
        self.valor_recibido = efectivo
        self.valor_transferencia = transferencia

    def calcular_cambio(self):
        return self.valor_recibido + (self.valor_transferencia or 0) - self.total

    def confirmar(self):
        if not self.detalles:
            raise ValueError("La venta no tiene productos")
        self.estado = EstadoVenta.CONFIRMADA

    def anular(self):
        self.estado = EstadoVenta.ANULADA

    def unidades_por_producto(self):
        """Unidades vendidas de cada producto (suma sus líneas), en el orden en que se vendieron."""
        vendidas = {}
        for detalle in self.detalles:
            vendidas[detalle.id_producto] = vendidas.get(detalle.id_producto, 0) + detalle.cantidad
        return vendidas

    def precio_de(self, id_producto):
        """El precio con que se vendió ese producto (HU-02): es el que se devuelve."""
        return next(d.precio_unitario for d in self.detalles if d.id_producto == id_producto)


# Respuesta 1.5: una línea de una devolución (producto, unidades y el precio con que se vendió).
DetalleDevolucion = namedtuple("DetalleDevolucion", "id_producto cantidad precio_unitario")


class Devolucion:
    """Respuesta 1.5: productos que regresan de una venta ya cobrada. La venta no se borra (cambia DT-08)."""

    def __init__(self, id_venta, motivo, fecha=None):
        exigir_texto_obligatorio(motivo, "Escribe el motivo de la devolución")
        self.id_devolucion = None
        self.id_venta = id_venta
        self.motivo = motivo.strip()
        self.fecha = fecha or datetime.now()
        self.lineas = []
        self.descontado_de_la_deuda = 0
        self.efectivo_devuelto = 0

    def agregar(self, id_producto, cantidad, precio_unitario):
        exigir_mayor_a_cero(cantidad)
        self.lineas.append(DetalleDevolucion(id_producto, cantidad, precio_unitario))

    def valor(self):
        return sum(linea.cantidad * linea.precio_unitario for linea in self.lineas)

    def repartir(self, cuenta):
        """En un fiado se descuenta de la deuda hasta dejarla en 0; lo que sobre se devuelve en efectivo
        (no hay saldo a favor, respuesta 2.5). En contado todo se devuelve en dinero."""
        self.descontado_de_la_deuda = cuenta.aplicar_devolucion(self.valor()) if cuenta else 0
        self.efectivo_devuelto = self.valor() - self.descontado_de_la_deuda


class CuentaPorCobrar:
    def __init__(self, id_cuenta, id_venta, id_cliente, monto_original, fecha_apertura, fecha_vencimiento):
        self.id_cuenta = id_cuenta
        self.id_venta = id_venta
        self.id_cliente = id_cliente
        self.monto_original = monto_original
        self.fecha_apertura = fecha_apertura
        self.fecha_vencimiento = fecha_vencimiento
        self.abonos = []
        self.valor_devuelto = 0          # lo que se descontó por devoluciones (respuesta 1.5)
        self.estado = EstadoCuenta.ABIERTA

    def calcular_saldo(self):
        return self.monto_original - sum(self.abonos) - self.valor_devuelto

    def aplicar_devolucion(self, valor):
        """Descuenta lo devuelto hasta dejar el saldo en 0 y dice cuánto descontó; el resto va en efectivo."""
        descontado = min(valor, self.calcular_saldo())
        self.valor_devuelto += descontado
        if self.calcular_saldo() == 0:
            self.estado = EstadoCuenta.PAGADA
        return descontado

    def aplicar_pago(self, monto):
        exigir_mayor_a_cero(monto)
        saldo = self.calcular_saldo()
        if monto > saldo:
            raise ValueError(f"El abono ({monto}) no puede ser mayor al saldo pendiente, que es {saldo}")
        self.abonos.append(monto)
        if self.calcular_saldo() == 0:
            self.estado = EstadoCuenta.PAGADA

    def esta_vencida(self, ahora):
        """Respuesta 2.3: una cuenta ABIERTA cuya fecha de vencimiento ya pasó. Una pagada nunca está vencida."""
        return self.estado == EstadoCuenta.ABIERTA and ahora > self.fecha_vencimiento

    def dias_de_atraso(self, ahora):
        """Días de calendario desde el vencimiento (0 si todavía no vence). Solo informa: no hay intereses."""
        return max(0, (ahora.date() - self.fecha_vencimiento.date()).days)

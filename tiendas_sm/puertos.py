"""Puertos del núcleo (ADR-04, FPI-20, "hexagonal ligero").

Son los contratos que el núcleo (servicios y dominio) espera de la persistencia. El núcleo es
dueño de estos contratos; repositorios.py los implementa con SQLite. Este archivo solo importa
abc: no sabe nada de la base de datos (lo vigila tests/test_arquitectura.py).
"""
from abc import ABC, abstractmethod


class RepositorioDeVentas(ABC):
    """Abstracción de la FPI-11: los servicios dependen de esta interfaz, no de SQLite."""

    @abstractmethod
    def guardar_transaccion(self, venta, cuenta, existencias):
        """Guarda venta, detalles, cuenta y existencias: todo o nada (RNF-04).
        En una venta de contado, 'cuenta' es None (no hay deuda)."""

    @abstractmethod
    def cuentas_del_cliente(self, id_cliente):
        ...

    @abstractmethod
    def obtener_cuenta(self, id_cuenta):
        ...

    @abstractmethod
    def guardar_abono(self, cuenta, valor):
        ...

    @abstractmethod
    def contar_ventas(self):
        """Número de ventas guardadas (lo usa Aplicacion.numero_de_ventas)."""

    @abstractmethod
    def obtener(self, id_venta):
        """Una venta guardada con sus detalles, o None si no existe (sección Ventas)."""

    @abstractmethod
    def listar(self, limite):
        """Las últimas ventas, de la más reciente a la más vieja, con sus detalles (sección Ventas)."""

    @abstractmethod
    def unidades_devueltas(self, id_venta):
        """Respuesta 1.5: {id_producto: unidades ya devueltas} de esa venta."""

    @abstractmethod
    def devoluciones_de_la_venta(self, id_venta):
        """Las devoluciones (Devolucion) de esa venta, de la más vieja a la más nueva."""

    @abstractmethod
    def guardar_devolucion(self, devolucion, venta, cuenta, existencias):
        """Guarda la devolución, el estado de la venta, la cuenta (si es fiado) y las existencias: todo o nada."""

    @abstractmethod
    def saldo_pendiente_del_cliente(self, id_cliente):
        """TD-13: suma de (monto original − abonos) de todas las cuentas del cliente (regla de calcular_saldo)."""


class PuertoDeProductos(ABC):
    """Lo que el núcleo necesita para productos y existencias."""

    @abstractmethod
    def obtener(self, id_producto):
        ...

    @abstractmethod
    def listar(self):
        ...

    @abstractmethod
    def guardar(self, producto):
        ...

    @abstractmethod
    def obtener_por_codigo(self, codigo):
        """Respuesta 1.4: el producto con ese código de barras, o None."""

    @abstractmethod
    def obtener_existencia(self, id_producto):
        ...

    @abstractmethod
    def guardar_existencia(self, existencia, tipo_movimiento, cantidad):
        ...

    @abstractmethod
    def guardar_salida_manual(self, existencia, cantidad, motivo, id_usuario, id_autorizo, costo_unitario):
        """Fase 3: existencias y movimiento SALIDA_MANUAL (con motivo, quién, quién autorizó y costo), todo o nada."""

    @abstractmethod
    def listar_movimientos(self, limite):
        """RF-04: los últimos movimientos de inventario (MovimientoDeInventario), del más reciente al más viejo."""

    @abstractmethod
    def guardar_lote(self, lote):
        """RF-10: guarda un lote nuevo o su estado (activo). No toca las existencias."""

    @abstractmethod
    def obtener_lote(self, id_lote):
        ...

    @abstractmethod
    def lotes_activos(self):
        """Los lotes que siguen en la lista, del que vence primero al último (FEFO manual)."""


class PuertoDeReportes(ABC):
    """Fase 1 (reportes): totales de ventas de un rango de fechas [desde, hasta). Solo consulta, no guarda nada."""

    @abstractmethod
    def resumen_de_ventas(self, desde, hasta):
        """ResumenDeVentas del rango: ventas por fecha de la venta, devoluciones y abonos por su propia fecha."""

    @abstractmethod
    def mas_vendidos(self, desde, hasta, limite):
        """ProductoMasVendido con unidades netas (vendidas − devueltas) mayores a 0, de más a menos unidades."""


class PuertoDeUsuarios(ABC):
    """Fase 2 (CR-01): usuarios que pueden ingresar. Guarda la huella de la clave, nunca la clave."""

    @abstractmethod
    def guardar(self, usuario):
        """Inserta (sin id) o actualiza nombre, rol, clave y activo. Un usuario repetido lanza ValueError."""

    @abstractmethod
    def obtener(self, id_usuario):
        ...

    @abstractmethod
    def obtener_por_usuario(self, usuario):
        """El usuario con ese nombre de ingreso (ya normalizado), o None."""

    @abstractmethod
    def listar(self):
        """Todos, ordenados por nombre."""


class PuertoDeClientes(ABC):
    """Lo que el núcleo necesita para clientes."""

    @abstractmethod
    def obtener(self, id_cliente):
        ...

    @abstractmethod
    def guardar(self, cliente):
        ...

    @abstractmethod
    def listar(self):
        """Todos los clientes, ordenados por nombre (HU-05: elegir a quién se le fía)."""

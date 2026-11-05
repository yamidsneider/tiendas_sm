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
    def obtener_existencia(self, id_producto):
        ...

    @abstractmethod
    def guardar_existencia(self, existencia, tipo_movimiento, cantidad):
        ...


class PuertoDeClientes(ABC):
    """Lo que el núcleo necesita para clientes."""

    @abstractmethod
    def obtener(self, id_cliente):
        ...

    @abstractmethod
    def guardar(self, cliente):
        ...

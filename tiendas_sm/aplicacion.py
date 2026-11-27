from tiendas_sm.base_de_datos import BaseDeDatos
from tiendas_sm.repositorios import (RepositorioDeCaja, RepositorioDeCompras, RepositorioDeConfiguracion, RepositorioDeProductos,
                                     RepositorioDeClientes, RepositorioDeReportesSqlite, RepositorioDeUsuarios,
                                     RepositorioDeVentasSqlite)
from tiendas_sm.respaldo import ServicioDeRespaldos
from tiendas_sm.telemetria import VentasObservadas
from tiendas_sm.servicios import (ServicioDeProductos, ServicioDeClientes, ControlInventario, ControlCredito,
                                  ServicioDeCaja, ServicioDeCompras, ServicioDeLaTienda, ServicioDeReportes, ServicioDeUsuarios,
                                  ServicioDeVentas)


class Aplicacion:
    """Punto único donde se arma el sistema (se crean los objetos y se conectan)."""

    def __init__(self, ruta=":memory:", telemetria=None, carpeta_de_respaldos=None):
        base = BaseDeDatos(ruta)
        self.conexion = base.conexion
        self.repo_productos = RepositorioDeProductos(self.conexion)
        repo_clientes = RepositorioDeClientes(self.conexion)
        self.repo_ventas = RepositorioDeVentasSqlite(self.conexion)
        control_inventario = ControlInventario(self.repo_productos)
        self.credito = ControlCredito(self.repo_ventas)
        self.productos = ServicioDeProductos(self.repo_productos)
        self.clientes = ServicioDeClientes(repo_clientes)
        self.ventas = ServicioDeVentas(self.repo_productos, repo_clientes, self.repo_ventas,
                                       control_inventario, self.credito)
        repo_reportes = RepositorioDeReportesSqlite(self.conexion)
        self.reportes = ServicioDeReportes(repo_reportes)                               # fase 1: solo consulta
        self.caja = ServicioDeCaja(RepositorioDeCaja(self.conexion), repo_reportes)    # fase 4
        configuracion = RepositorioDeConfiguracion(self.conexion)
        self.respaldos = ServicioDeRespaldos(self.conexion, configuracion, carpeta_de_respaldos)   # fase 5
        self.compras = ServicioDeCompras(RepositorioDeCompras(self.conexion), self.repo_productos)   # fase 8
        self.tienda = ServicioDeLaTienda(configuracion)                                       # fase 6
        self.usuarios = ServicioDeUsuarios(RepositorioDeUsuarios(self.conexion))         # fase 2: CR-01
        if telemetria is not None:                            # FPI-29: observabilidad opcional (ADR-13)
            self.ventas = VentasObservadas(self.ventas, telemetria)

    def cantidad_en_inventario(self, id_producto):
        return self.repo_productos.obtener_existencia(id_producto).cantidad_actual

    def numero_de_ventas(self):
        return self.repo_ventas.contar_ventas()

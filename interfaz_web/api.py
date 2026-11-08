"""API de la app de escritorio: lo único que la página (JavaScript) puede pedirle a Python (opción B en DECISIONES).

pywebview publica los métodos de ApiDeLaTienda en la página como window.pywebview.api.<método>. Cada método
llama al presentador de su sección (los mismos que usaba Tkinter) y devuelve datos simples: listas,
diccionarios y texto, que pywebview convierte a JSON. Aquí no hay reglas de negocio: las valida el dominio
y su mensaje llega tal cual a la pantalla.

Dos cuidados:
- Los atributos empiezan con «_» para que pywebview no los publique (la página no ve la app ni la base).
- pywebview atiende cada llamada en un hilo distinto, pero la conexión de SQLite solo acepta el hilo que la
  abrió. Por eso todo pasa por HiloDeLaBase: un único hilo que abre la base y hace todas las consultas,
  una a la vez (así tampoco se cruzan dos operaciones).
"""
from concurrent.futures import ThreadPoolExecutor

from tiendas_sm.presentador import PresentadorPuntoDeVenta, formato_pesos
from tiendas_sm.presentador_clientes import PresentadorDeClientes
from tiendas_sm.presentador_creditos import PresentadorDeCreditos
from tiendas_sm.presentador_existencias import PresentadorDeExistencias
from tiendas_sm.presentador_productos import PresentadorDeProductos
from tiendas_sm.presentador_ventas import PresentadorDeVentas


class HiloDeLaBase:
    """Un solo hilo de trabajo: ejecutar(funcion) la corre allí y devuelve su resultado (o lanza su error)."""

    def __init__(self):
        self._trabajador = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tiendas_sm_base")

    def ejecutar(self, funcion):
        return self._trabajador.submit(funcion).result()

    def cerrar(self):
        self._trabajador.shutdown(wait=True)


def _ejecutar_aqui(funcion):
    """Sin ventana (pruebas): se ejecuta en el mismo hilo."""
    return funcion()


def _id(valor):
    """La página manda los id como número o texto; si no es un número, None (el presentador pide elegir)."""
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _filas(filas):
    return [{"id": id_fila, "valores": list(valores)} for id_fila, valores in filas]


def _resultado(resultado):
    return {"exito": resultado.exito, "mensaje": resultado.mensaje, "ticket": resultado.ticket}


class ApiDeLaTienda:
    def __init__(self, app, ejecutar=_ejecutar_aqui):
        self._ejecutar = ejecutar
        self._venta = PresentadorPuntoDeVenta(app)
        self._ventas = PresentadorDeVentas(app)
        self._productos = PresentadorDeProductos(app)
        self._existencias = PresentadorDeExistencias(app)
        self._clientes = PresentadorDeClientes(app)
        self._creditos = PresentadorDeCreditos(app)

    # ------------------------------------------------------------------ punto de venta (HU-04, CU-01, CU-02)
    def buscar(self, texto):
        return self._ejecutar(lambda: [{"id": p.id_producto, "nombre": p.nombre, "precio": formato_pesos(p.precio),
                                        "disponibles": p.disponibles} for p in self._venta.buscar(str(texto))])

    def carrito(self):
        return self._ejecutar(self._carrito)

    def agregar(self, id_producto, cantidad):
        return self._ejecutar(lambda: self._con_carrito(self._venta.agregar(_id(id_producto), cantidad)))

    def quitar(self, id_producto):
        return self._ejecutar(lambda: self._despues_de(self._venta.quitar, _id(id_producto)))

    def limpiar(self):
        return self._ejecutar(lambda: self._despues_de(self._venta.limpiar))

    def clientes_para_credito(self):
        return self._ejecutar(lambda: [{"id": c.id_cliente, "nombres": c.nombres, "texto": c.texto}
                                       for c in self._venta.clientes()])

    def cambio(self, recibido):
        return self._ejecutar(lambda: _resultado(self._venta.cambio_previo(recibido)))

    def cobrar_de_contado(self, recibido):
        return self._ejecutar(lambda: self._con_carrito(self._venta.cobrar_de_contado(recibido)))

    def vender_a_credito(self, id_cliente):
        return self._ejecutar(lambda: self._con_carrito(self._venta.vender_a_credito(_id(id_cliente))))

    def _carrito(self):
        lineas = [{"id": l.id_producto, "nombre": l.nombre, "precio": formato_pesos(l.precio), "cantidad": l.cantidad,
                   "importe": formato_pesos(l.importe), "disponibles": l.disponibles} for l in self._venta.lineas()]
        total = self._venta.total()
        return {"lineas": lineas, "total": formato_pesos(total), "total_numero": total, "resumen": self._venta.resumen(),
                "vacio": not lineas}

    def _despues_de(self, accion, *argumentos):
        """Hace la acción sobre el carrito y devuelve cómo quedó."""
        accion(*argumentos)
        return self._carrito()

    def _con_carrito(self, resultado):
        return {**_resultado(resultado), "carrito": self._carrito()}

    # ------------------------------------------------------------------ ventas (RF-05)
    def ventas(self):
        return self._ejecutar(lambda: _filas(self._ventas.tabla()))

    def ticket(self, id_venta):
        return self._ejecutar(lambda: self._ventas.ticket(_id(id_venta)))

    # ------------------------------------------------------------------ productos (HU-01, HU-02)
    def productos(self, texto=""):
        return self._ejecutar(lambda: _filas(self._productos.tabla(str(texto))))

    def registrar_producto(self, nombre, compra, venta, cantidad):
        return self._ejecutar(lambda: _resultado(self._productos.registrar(str(nombre), compra, venta, cantidad)))

    def precio_actual(self, id_producto):
        return self._ejecutar(lambda: self._productos.precio_actual(_id(id_producto)))

    def cambiar_precio(self, id_producto, nuevo):
        return self._ejecutar(lambda: _resultado(self._productos.cambiar_precio(_id(id_producto), nuevo)))

    # ------------------------------------------------------------------ existencias (HU-03, RF-04)
    def existencias(self, texto=""):
        return self._ejecutar(lambda: _filas(self._existencias.tabla(str(texto))))

    def movimientos(self):
        return self._ejecutar(lambda: _filas(self._existencias.movimientos()))

    def registrar_entrada(self, id_producto, cantidad):
        return self._ejecutar(lambda: _resultado(self._existencias.registrar_entrada(_id(id_producto), cantidad)))

    # ------------------------------------------------------------------ clientes (HU-05, RF-07)
    def clientes(self, texto=""):
        return self._ejecutar(lambda: _filas(self._clientes.tabla(str(texto))))

    def plazo_por_defecto(self):
        return self._clientes.plazo_por_defecto()

    def registrar_cliente(self, nombres, credito, limite, plazo):
        return self._ejecutar(lambda: _resultado(self._clientes.registrar(str(nombres), bool(credito), limite, plazo)))

    def detalle_cliente(self, id_cliente):
        return self._ejecutar(lambda: self._clientes.detalle(_id(id_cliente)))

    def datos_cliente(self, id_cliente):
        """Lo guardado, para llenar el formulario de Editar cliente; None si no existe."""
        datos = self._ejecutar(lambda: self._clientes.datos_para_editar(_id(id_cliente)))
        if datos is None:
            return None
        return {"nombres": datos.nombres, "credito": datos.credito_habilitado, "limite": datos.limite, "plazo": datos.plazo}

    def editar_cliente(self, id_cliente, nombres, credito, limite, plazo):
        return self._ejecutar(lambda: _resultado(self._clientes.editar(_id(id_cliente), str(nombres), bool(credito),
                                                                       limite, plazo)))

    # ------------------------------------------------------------------ créditos y abonos (HU-06, RF-09)
    def creditos(self, ver_pagadas=False):
        return self._ejecutar(lambda: {"filas": _filas(self._creditos.tabla(bool(ver_pagadas))),
                                       "resumen": self._creditos.resumen()})

    def detalle_credito(self, id_cuenta):
        return self._ejecutar(lambda: self._creditos.detalle(_id(id_cuenta)))

    def abonar(self, id_cuenta, monto):
        return self._ejecutar(lambda: _resultado(self._creditos.abonar(_id(id_cuenta), monto)))

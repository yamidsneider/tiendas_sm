"""API de la app de escritorio: lo único que la página (JavaScript) puede pedirle a Python (opción B en DECISIONES).

pywebview publica los métodos de ApiDeLaTienda en la página como window.pywebview.api.<método>. Cada método
llama al presentador de su sección (los mismos que usaba Tkinter) y devuelve datos simples: listas,
diccionarios y texto, que pywebview convierte a JSON. Aquí no hay reglas de negocio: las valida el dominio
y su mensaje llega tal cual a la pantalla.

Tres cuidados:
- Los atributos empiezan con «_» para que pywebview no los publique (la página no ve la app ni la base).
- pywebview atiende cada llamada en un hilo distinto, pero la conexión de SQLite solo acepta el hilo que la
  abrió. Por eso todo pasa por HiloDeLaBase: un único hilo que abre la base y hace todas las consultas,
  una a la vez (así tampoco se cruzan dos operaciones).
- Fase 2 (CR-01): cada método lleva @requiere(permiso). Si nadie ingresó o el rol no tiene ese permiso, no se
  hace nada y se devuelve el motivo. Esconder un botón en la página no basta: la barrera está aquí
  (test_usuarios revisa que ningún método quede sin permiso).
"""
import functools
from concurrent.futures import ThreadPoolExecutor

from tiendas_sm.dominio import Permiso
from tiendas_sm.presentador import PresentadorPuntoDeVenta, formato_pesos
from tiendas_sm.presentador_caja import PresentadorDeCaja
from tiendas_sm.presentador_clientes import PresentadorDeClientes
from tiendas_sm.presentador_creditos import PresentadorDeCreditos
from tiendas_sm.presentador_existencias import PresentadorDeExistencias
from tiendas_sm.presentador_productos import PresentadorDeProductos
from tiendas_sm.presentador_reportes import PresentadorDeReportes
from tiendas_sm.presentador_respaldos import PresentadorDeRespaldos
from tiendas_sm.presentador_tienda import PresentadorDeLaTienda
from tiendas_sm.presentador_usuarios import PresentadorDeUsuarios
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


def requiere(permiso):
    """Antes de hacer la acción, la sesión dice si se puede; si no, se devuelve el motivo y no se toca nada."""
    def decorar(metodo):
        @functools.wraps(metodo)
        def con_permiso(self, *argumentos, **opciones):
            motivo = self._usuarios.sesion.negar(permiso)
            if motivo:
                return {"exito": False, "mensaje": motivo, "ticket": None}
            return metodo(self, *argumentos, **opciones)
        con_permiso.permiso = permiso
        return con_permiso
    return decorar


class ApiDeLaTienda:
    def __init__(self, app, ejecutar=_ejecutar_aqui):
        self._ejecutar = ejecutar
        self._usuarios = PresentadorDeUsuarios(app)          # guarda la sesión de esta ventana
        self._venta = PresentadorPuntoDeVenta(app)
        self._ventas = PresentadorDeVentas(app)
        self._productos = PresentadorDeProductos(app)
        self._existencias = PresentadorDeExistencias(app)
        self._clientes = PresentadorDeClientes(app)
        self._creditos = PresentadorDeCreditos(app)
        self._reportes = PresentadorDeReportes(app)
        self._caja = PresentadorDeCaja(app)
        self._respaldos = PresentadorDeRespaldos(app)
        self._tienda = PresentadorDeLaTienda(app)

    # ------------------------------------------------------------------ ingreso (fase 2): libres, sin permiso
    def estado_sesion(self):
        return self._ejecutar(self._usuarios.estado)

    def crear_primer_jefe(self, nombre, usuario, clave, confirmacion):
        return self._ejecutar(lambda: self._con_estado(self._usuarios.crear_primer_jefe(
            str(nombre), str(usuario), str(clave), str(confirmacion))))

    def iniciar_sesion(self, usuario, clave):
        return self._ejecutar(lambda: self._con_estado(self._usuarios.iniciar_sesion(str(usuario), str(clave))))

    def cerrar_sesion(self):
        """Quien llegue después no ve el carrito a medias del anterior."""
        def cerrar():
            self._venta.limpiar()
            self._usuarios.cerrar_sesion()
            return self._usuarios.estado()
        return self._ejecutar(cerrar)

    def _con_estado(self, resultado):
        return {**_resultado(resultado), "estado": self._usuarios.estado()}

    # ------------------------------------------------------------------ caja (fase 4)
    @requiere(Permiso.VENDER)
    def estado_caja(self):
        return self._ejecutar(self._caja.estado)

    @requiere(Permiso.MANEJAR_CAJA)
    def abrir_caja(self, base):
        quien = self._usuarios.sesion.usuario
        return self._ejecutar(lambda: _resultado(self._caja.abrir(base, quien)))

    @requiere(Permiso.MANEJAR_CAJA)
    def revisar_cierre(self, contado):
        return self._ejecutar(lambda: self._caja.revisar(contado))

    @requiere(Permiso.MANEJAR_CAJA)
    def cerrar_caja(self, contado):
        """Fase 5 (respuesta 5.2): al cerrar la caja se hace también un respaldo en la carpeta."""
        quien = self._usuarios.sesion.usuario

        def cerrar():
            resultado = _resultado(self._caja.cerrar(contado, quien))
            if resultado["exito"]:
                resultado["mensaje"] += self._respaldos.respaldar_si_hay_carpeta()
            return resultado
        return self._ejecutar(cerrar)

    # ------------------------------------------------------------------ datos de la tienda y productos (fase 6)
    @requiere(Permiso.CONFIGURAR_TIENDA)
    def datos_tienda(self):
        return self._ejecutar(self._tienda.datos)

    @requiere(Permiso.CONFIGURAR_TIENDA)
    def guardar_datos_tienda(self, nombre, nit, direccion, telefono, mensaje):
        return self._ejecutar(lambda: _resultado(self._tienda.guardar(str(nombre), str(nit), str(direccion),
                                                                      str(telefono), str(mensaje))))

    @requiere(Permiso.CONFIGURAR_TIENDA)
    def activar_producto(self, id_producto, activo):
        return self._ejecutar(lambda: _resultado(self._productos.activar(_id(id_producto), bool(activo))))

    # ------------------------------------------------------------------ respaldos (fase 5): solo el jefe
    @requiere(Permiso.GESTIONAR_RESPALDOS)
    def respaldos(self):
        def consultar():
            datos = self._respaldos.datos()
            return {"carpeta": datos["carpeta"], "filas": _filas(datos["filas"])}
        return self._ejecutar(consultar)

    @requiere(Permiso.GESTIONAR_RESPALDOS)
    def cambiar_carpeta_respaldos(self, carpeta):
        return self._ejecutar(lambda: _resultado(self._respaldos.cambiar_carpeta(str(carpeta))))

    @requiere(Permiso.GESTIONAR_RESPALDOS)
    def respaldar_ahora(self):
        return self._ejecutar(lambda: _resultado(self._respaldos.respaldar_ahora()))

    @requiere(Permiso.GESTIONAR_RESPALDOS)
    def restaurar_respaldo(self, nombre):
        """Los usuarios pueden ser otros en el respaldo: se cierra la sesión y se vacía el carrito."""
        def restaurar():
            resultado = self._respaldos.restaurar(str(nombre))
            if resultado.exito:
                self._venta.limpiar()
                self._usuarios.cerrar_sesion()
            return self._con_estado(resultado)
        return self._ejecutar(restaurar)

    @requiere(Permiso.VER_REPORTES)
    def historial_caja(self):
        return self._ejecutar(lambda: _filas(self._caja.historial()))

    # ------------------------------------------------------------------ usuarios (fase 2): solo el jefe
    @requiere(Permiso.GESTIONAR_USUARIOS)
    def usuarios(self):
        return self._ejecutar(lambda: _filas(self._usuarios.tabla()))

    @requiere(Permiso.GESTIONAR_USUARIOS)
    def crear_usuario(self, nombre, usuario, rol, clave, confirmacion):
        return self._ejecutar(lambda: _resultado(self._usuarios.crear(str(nombre), str(usuario), str(rol), str(clave),
                                                                      str(confirmacion))))

    @requiere(Permiso.GESTIONAR_USUARIOS)
    def cambiar_clave_usuario(self, id_usuario, clave, confirmacion):
        return self._ejecutar(lambda: _resultado(self._usuarios.cambiar_clave(_id(id_usuario), str(clave),
                                                                              str(confirmacion))))

    @requiere(Permiso.GESTIONAR_USUARIOS)
    def activar_usuario(self, id_usuario, activo):
        return self._ejecutar(lambda: _resultado(self._usuarios.activar(_id(id_usuario), bool(activo))))

    # ------------------------------------------------------------------ punto de venta (HU-04, CU-01, CU-02)
    @requiere(Permiso.VENDER)
    def buscar(self, texto):
        return self._ejecutar(lambda: [{"id": p.id_producto, "nombre": p.nombre, "precio": formato_pesos(p.precio),
                                        "disponibles": p.disponibles} for p in self._venta.buscar(str(texto))])

    @requiere(Permiso.VENDER)
    def carrito(self):
        return self._ejecutar(self._carrito)

    @requiere(Permiso.VENDER)
    def agregar(self, id_producto, cantidad):
        return self._ejecutar(lambda: self._con_carrito(self._venta.agregar(_id(id_producto), cantidad)))

    @requiere(Permiso.VENDER)
    def quitar(self, id_producto):
        return self._ejecutar(lambda: self._despues_de(self._venta.quitar, _id(id_producto)))

    @requiere(Permiso.VENDER)
    def quitar_uno(self, id_producto):
        return self._ejecutar(lambda: self._despues_de(self._venta.quitar_uno, _id(id_producto)))

    @requiere(Permiso.VENDER)
    def limpiar(self):
        return self._ejecutar(lambda: self._despues_de(self._venta.limpiar))

    @requiere(Permiso.VENDER)
    def clientes_para_credito(self):
        return self._ejecutar(lambda: [{"id": c.id_cliente, "nombres": c.nombres, "texto": c.texto}
                                       for c in self._venta.clientes()])

    @requiere(Permiso.VENDER)
    def cambio(self, recibido, transferencia="0"):
        return self._ejecutar(lambda: _resultado(self._venta.cambio_previo(recibido, transferencia)))

    @requiere(Permiso.VENDER)
    def cobrar_de_contado(self, recibido, transferencia="0"):
        return self._ejecutar(lambda: self._con_carrito(self._venta.cobrar_de_contado(recibido, transferencia)))

    @requiere(Permiso.VENDER)
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
    @requiere(Permiso.CONSULTAR)
    def ventas(self):
        """Filas de ventas; «estado» dice si está Anulada o Con devolución (respuesta 1.5)."""
        def consultar():
            estados = self._ventas.estados()
            return [{**fila, "estado": estados.get(fila["id"], "")} for fila in _filas(self._ventas.tabla())]
        return self._ejecutar(consultar)

    @requiere(Permiso.DEVOLVER)
    def para_devolver(self, id_venta):
        return self._ejecutar(lambda: _filas(self._ventas.para_devolver(_id(id_venta))))

    @requiere(Permiso.DEVOLVER)
    def devolver(self, id_venta, cantidades, motivo):
        """cantidades llega de JavaScript como {"id_producto": "texto"}."""
        por_producto = {_id(id_producto): texto for id_producto, texto in dict(cantidades or {}).items()}
        return self._ejecutar(lambda: _resultado(self._ventas.devolver(_id(id_venta), por_producto, str(motivo))))

    @requiere(Permiso.DEVOLVER)
    def anular(self, id_venta, motivo):
        return self._ejecutar(lambda: _resultado(self._ventas.anular(_id(id_venta), str(motivo))))

    @requiere(Permiso.CONSULTAR)
    def ticket(self, id_venta):
        return self._ejecutar(lambda: self._ventas.ticket(_id(id_venta)))

    # ------------------------------------------------------------------ productos (HU-01, HU-02)
    @requiere(Permiso.CONSULTAR)
    def productos(self, texto=""):
        """Filas de productos; «activo» es False en los desactivados (fase 6)."""
        def consultar():
            inactivos = self._productos.inactivos()
            return [{**fila, "activo": fila["id"] not in inactivos} for fila in _filas(self._productos.tabla(str(texto)))]
        return self._ejecutar(consultar)

    @requiere(Permiso.GESTIONAR_PRODUCTOS)
    def registrar_producto(self, nombre, compra, venta, cantidad, minimo="0", codigo="", aviso="0"):
        return self._ejecutar(lambda: _resultado(self._productos.registrar(str(nombre), compra, venta, cantidad, minimo,
                                                                           str(codigo), aviso)))

    @requiere(Permiso.CONSULTAR)
    def precio_actual(self, id_producto):
        return self._ejecutar(lambda: self._productos.precio_actual(_id(id_producto)))

    @requiere(Permiso.GESTIONAR_PRODUCTOS)
    def cambiar_precio(self, id_producto, nuevo):
        return self._ejecutar(lambda: _resultado(self._productos.cambiar_precio(_id(id_producto), nuevo)))

    @requiere(Permiso.GESTIONAR_PRODUCTOS)
    def datos_producto(self, id_producto):
        """Lo guardado, para llenar el formulario de Editar producto; None si no existe."""
        datos = self._ejecutar(lambda: self._productos.datos_para_editar(_id(id_producto)))
        if datos is None:
            return None
        return {"nombre": datos.nombre, "compra": datos.compra, "venta": datos.venta, "minimo": datos.minimo,
                "codigo": datos.codigo, "aviso": datos.aviso}

    @requiere(Permiso.GESTIONAR_PRODUCTOS)
    def editar_producto(self, id_producto, nombre, compra, venta, minimo=None, codigo=None, aviso=None):
        return self._ejecutar(lambda: _resultado(self._productos.editar(_id(id_producto), str(nombre), compra, venta,
                                                                        minimo, codigo, aviso)))

    # ------------------------------------------------------------------ existencias (HU-03, RF-04)
    @requiere(Permiso.CONSULTAR)
    def existencias(self, texto=""):
        """Filas de existencias; «reponer» marca las que llegaron a su stock mínimo (RF-12)."""
        def consultar():
            reponer = {id_producto for id_producto, _ in self._existencias.por_reponer()}
            inactivos = self._productos.inactivos()                      # fase 6: se marcan «Inactivo»
            return [{**fila, "reponer": fila["id"] in reponer, "activo": fila["id"] not in inactivos}
                    for fila in _filas(self._existencias.tabla(str(texto)))]
        return self._ejecutar(consultar)

    @requiere(Permiso.CONSULTAR)
    def por_reponer(self):
        return self._ejecutar(lambda: _filas(self._existencias.por_reponer()))

    @requiere(Permiso.CONSULTAR)
    def movimientos(self):
        return self._ejecutar(lambda: _filas(self._existencias.movimientos()))

    @requiere(Permiso.REGISTRAR_ENTRADA)
    def motivos_de_salida(self):
        return self._existencias.motivos_de_salida()

    @requiere(Permiso.REGISTRAR_ENTRADA)
    def registrar_salida(self, id_producto, cantidad, motivo, detalle="", jefe="", clave_jefe=""):
        """Fase 3: quien mueve inventario puede pedirla; si no es jefe, jefe y clave_jefe la autorizan (respuesta 4.4)."""
        quien = self._usuarios.sesion.usuario
        return self._ejecutar(lambda: _resultado(self._existencias.registrar_salida(
            _id(id_producto), cantidad, str(motivo), str(detalle), quien, str(jefe), str(clave_jefe))))

    @requiere(Permiso.REGISTRAR_ENTRADA)
    def registrar_entrada(self, id_producto, cantidad):
        return self._ejecutar(lambda: _resultado(self._existencias.registrar_entrada(_id(id_producto), cantidad)))

    # ------------------------------------------------------------------ lotes por vencer (RF-10, RF-13)
    @requiere(Permiso.CONSULTAR)
    def lotes(self):
        """Lotes activos y cuántos están vencidos o por vencer (para el número del panel)."""
        return self._ejecutar(lambda: {"filas": _filas(self._existencias.lotes()),
                                       "alerta": self._existencias.cuantos_en_alerta()})

    @requiere(Permiso.REGISTRAR_ENTRADA)
    def registrar_lote(self, id_producto, numero, fecha, cantidad):
        return self._ejecutar(lambda: _resultado(self._existencias.registrar_lote(_id(id_producto), str(numero),
                                                                                   str(fecha), cantidad)))

    @requiere(Permiso.REGISTRAR_ENTRADA)
    def retirar_lote(self, id_lote):
        return self._ejecutar(lambda: _resultado(self._existencias.retirar_lote(_id(id_lote))))

    # ------------------------------------------------------------------ clientes (HU-05, RF-07)
    @requiere(Permiso.CONSULTAR)
    def clientes(self, texto=""):
        return self._ejecutar(lambda: _filas(self._clientes.tabla(str(texto))))

    @requiere(Permiso.CONSULTAR)
    def plazo_por_defecto(self):
        return self._clientes.plazo_por_defecto()

    @requiere(Permiso.GESTIONAR_CLIENTES)
    def registrar_cliente(self, nombres, credito, limite, plazo, telefono="", direccion=""):
        return self._ejecutar(lambda: _resultado(self._clientes.registrar(str(nombres), bool(credito), limite, plazo,
                                                                          str(telefono), str(direccion))))

    @requiere(Permiso.CONSULTAR)
    def detalle_cliente(self, id_cliente):
        return self._ejecutar(lambda: self._clientes.detalle(_id(id_cliente)))

    @requiere(Permiso.GESTIONAR_CLIENTES)
    def datos_cliente(self, id_cliente):
        """Lo guardado, para llenar el formulario de Editar cliente; None si no existe."""
        datos = self._ejecutar(lambda: self._clientes.datos_para_editar(_id(id_cliente)))
        if datos is None:
            return None
        return {"nombres": datos.nombres, "credito": datos.credito_habilitado, "limite": datos.limite, "plazo": datos.plazo,
                "telefono": datos.telefono, "direccion": datos.direccion}

    @requiere(Permiso.GESTIONAR_CLIENTES)
    def editar_cliente(self, id_cliente, nombres, credito, limite, plazo, telefono=None, direccion=None):
        return self._ejecutar(lambda: _resultado(self._clientes.editar(_id(id_cliente), str(nombres), bool(credito),
                                                                       limite, plazo, telefono, direccion)))

    # ------------------------------------------------------------------ créditos y abonos (HU-06, RF-09)
    @requiere(Permiso.CONSULTAR)
    def creditos(self, ver_pagadas=False):
        return self._ejecutar(lambda: {"filas": _filas(self._creditos.tabla(bool(ver_pagadas))),
                                       "resumen": self._creditos.resumen()})

    @requiere(Permiso.CONSULTAR)
    def atrasados(self):
        return self._ejecutar(lambda: _filas(self._creditos.atrasados()))

    @requiere(Permiso.CONSULTAR)
    def detalle_credito(self, id_cuenta):
        return self._ejecutar(lambda: self._creditos.detalle(_id(id_cuenta)))

    @requiere(Permiso.REGISTRAR_ABONO)
    def abonar(self, id_cuenta, monto):
        return self._ejecutar(lambda: _resultado(self._creditos.abonar(_id(id_cuenta), monto)))

    # ------------------------------------------------------------------ reportes (fase 1 de la hoja de ruta)
    @requiere(Permiso.VER_REPORTES)
    def reporte(self, periodo="hoy"):
        """periodo: «hoy», «semana» o «mes». Las parejas y filas van como listas (así llegan igual a JavaScript)."""
        def consultar():
            datos = self._reportes.reporte(str(periodo))
            return {**datos, **{clave: [list(fila) for fila in datos[clave]]
                                for clave in ("tarjetas", "formas", "mas_vendidos")}}
        return self._ejecutar(consultar)

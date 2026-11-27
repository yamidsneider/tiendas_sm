import textwrap
from collections import namedtuple
from datetime import datetime, timedelta
from enum import Enum

from tiendas_sm.dominio import (Producto, Cliente, Venta, CuentaPorCobrar, StockInsuficiente, Devolucion, Lote,
                                CreditoNoPermitido, TipoVenta, EstadoVenta, PLAZO_POR_DEFECTO_DIAS, Rol, TurnoDeCaja,
                                Usuario, DatosDeLaTienda, SIGNO_DEL_MOVIMIENTO_DE_CUENTA, normalizar_usuario)
from tiendas_sm.validaciones import exigir_mayor_a_cero, exigir_no_negativo

LineaDeVenta = namedtuple("LineaDeVenta", "id_producto cantidad")
MOVIMIENTOS_A_MOSTRAR = 50          # RF-04: el historial muestra los últimos, no toda la historia
VENTAS_A_MOSTRAR = 50               # sección Ventas: las últimas (no es un reporte)


class ServicioDeProductos:
    def __init__(self, repo_productos):
        self.repo_productos = repo_productos

    def registrar_producto(self, nombre, precio_compra, precio_venta, cantidad_inicial=0, stock_minimo=0, codigo="",
                           dias_aviso=0):
        producto = Producto(None, nombre, precio_compra, precio_venta, stock_minimo, codigo, dias_aviso)
        self._exigir_codigo_libre(producto)
        self.repo_productos.guardar(producto)
        if cantidad_inicial > 0:
            self.registrar_entrada(producto.id_producto, cantidad_inicial)
        return producto

    def obtener(self, id_producto):
        return self.repo_productos.obtener(id_producto)

    def buscar_por_codigo(self, codigo):
        """Respuesta 1.4: lo que manda el lector de código de barras (sin espacios ni Enter); None si no hay."""
        codigo = codigo.strip()
        return self.repo_productos.obtener_por_codigo(codigo) if codigo else None

    def _exigir_codigo_libre(self, producto):
        """Dos productos no pueden tener el mismo código: el lector no sabría cuál agregar."""
        otro = self.buscar_por_codigo(producto.codigo)
        if otro is not None and otro.id_producto != producto.id_producto:
            raise ValueError(f"El código {producto.codigo} ya es del producto {otro.nombre}")

    def listar(self):
        return self.repo_productos.listar()

    def actualizar_precio(self, id_producto, nuevo_precio):
        producto = self.repo_productos.obtener(id_producto)
        if producto is None:
            raise ValueError("El producto no existe")
        producto.actualizar_precio(nuevo_precio)
        self.repo_productos.guardar(producto)
        return producto

    def actualizar_producto(self, id_producto, nombre, precio_compra, precio_venta, stock_minimo=None, codigo=None,
                            dias_aviso=None):
        """Editar producto: se arma un Producto con el mismo id para que el dominio valide igual que al registrar.
        Las existencias no se tocan (cambian con entradas y ventas). Lo que llegue en None (stock mínimo, código,
        días de aviso) conserva lo guardado."""
        actual = self._exigir_producto(id_producto)
        minimo = actual.stock_minimo if stock_minimo is None else stock_minimo
        codigo = actual.codigo if codigo is None else codigo
        aviso = actual.dias_aviso if dias_aviso is None else dias_aviso
        producto = Producto(id_producto, nombre, precio_compra, precio_venta, minimo, codigo, aviso, actual.activo)
        self._exigir_codigo_libre(producto)
        self.repo_productos.guardar(producto)
        return producto

    def cambiar_estado(self, id_producto, activo):
        """Fase 6: desactivar (no se vende más) o volver a activar. Nunca se borra: conserva su historia (DT-08)."""
        producto = self._exigir_producto(id_producto)
        producto.activo = bool(activo)
        self.repo_productos.guardar(producto)
        return producto

    def registrar_entrada(self, id_producto, cantidad):
        existencia = self.repo_productos.obtener_existencia(id_producto)
        if existencia is None:
            raise ValueError("El producto no existe")
        existencia.aumentar(cantidad)
        self.repo_productos.guardar_existencia(existencia, "ENTRADA", cantidad)
        return existencia

    def registrar_salida(self, id_producto, cantidad, motivo, id_usuario, id_autorizo):
        """Fase 3 (respuesta 4.4): mercancía que sale sin venderse. motivo ya viene armado (texto_del_motivo).
        Guarda el precio de compra de hoy para saber cuánto se perdió; quién autoriza lo decide el presentador."""
        producto = self._exigir_producto(id_producto)
        existencia = self.repo_productos.obtener_existencia(id_producto)
        exigir_mayor_a_cero(cantidad)
        if cantidad > existencia.cantidad_disponible():
            raise ValueError(f"Solo hay {existencia.cantidad_disponible()} disponibles de {producto.nombre}")
        existencia.descontar(cantidad)
        self.repo_productos.guardar_salida_manual(existencia, cantidad, motivo, id_usuario, id_autorizo,
                                                  producto.precio_compra)
        return existencia

    def movimientos(self, limite=MOVIMIENTOS_A_MOSTRAR):
        return self.repo_productos.listar_movimientos(limite)

    def _exigir_producto(self, id_producto):
        producto = self.repo_productos.obtener(id_producto)
        if producto is None:
            raise ValueError("El producto no existe")
        return producto

    # Lotes (RF-10, RF-13): solo un registro para avisar del vencimiento. No cambian las existencias.
    def registrar_lote(self, id_producto, numero, fecha_vencimiento, cantidad):
        self._exigir_producto(id_producto)
        lote = Lote(None, id_producto, numero, fecha_vencimiento, cantidad)
        self.repo_productos.guardar_lote(lote)
        return lote

    def retirar_lote(self, id_lote):
        lote = self.repo_productos.obtener_lote(id_lote)
        if lote is None:
            raise ValueError("Ese lote ya no está en la lista")
        lote.retirar()
        self.repo_productos.guardar_lote(lote)
        return lote

    def lotes_activos(self):
        return self.repo_productos.lotes_activos()


class ServicioDeClientes:
    def __init__(self, repo_clientes):
        self.repo_clientes = repo_clientes

    def registrar_cliente(self, nombres, credito_habilitado, limite_credito,
                          plazo_credito_dias=PLAZO_POR_DEFECTO_DIAS, telefono="", direccion=""):
        cliente = Cliente(None, nombres, credito_habilitado, limite_credito, plazo_credito_dias, telefono, direccion)
        self.repo_clientes.guardar(cliente)
        return cliente

    def obtener(self, id_cliente):
        return self.repo_clientes.obtener(id_cliente)

    def actualizar_cliente(self, id_cliente, nombres, credito_habilitado, limite_credito, plazo_credito_dias,
                           telefono=None, direccion=None):
        """Editar cliente: se arma un Cliente nuevo con el mismo id para que el dominio valide igual que al registrar.
        Las cuentas ya abiertas no cambian (su vencimiento se calculó al vender). Si no llegan teléfono o
        dirección (None), se conserva lo guardado."""
        actual = self.repo_clientes.obtener(id_cliente)
        if actual is None:
            raise ValueError("El cliente no existe")
        telefono = actual.telefono if telefono is None else telefono
        direccion = actual.direccion if direccion is None else direccion
        cliente = Cliente(id_cliente, nombres, credito_habilitado, limite_credito, plazo_credito_dias, telefono, direccion)
        self.repo_clientes.guardar(cliente)
        return cliente

    def listar(self):
        return self.repo_clientes.listar()


class ControlInventario:
    def __init__(self, repo_productos):
        self.repo_productos = repo_productos

    def hay_disponible(self, producto, cantidad):
        existencia = self.repo_productos.obtener_existencia(producto.id_producto)
        return existencia.cantidad_disponible() >= cantidad

    def cantidad_disponible(self, producto):
        return self.repo_productos.obtener_existencia(producto.id_producto).cantidad_disponible()

    def descontar(self, producto, cantidad):
        existencia = self.repo_productos.obtener_existencia(producto.id_producto)
        existencia.descontar(cantidad)
        return existencia


class ControlCredito:
    def __init__(self, repo_ventas):
        self.repo_ventas = repo_ventas

    def saldo_pendiente(self, cliente):
        return self.repo_ventas.saldo_pendiente_del_cliente(cliente.id_cliente)   # TD-13: una consulta, no N cuentas

    def puede_comprar_a_credito(self, cliente, monto):
        return cliente.puede_endeudarse(monto, self.saldo_pendiente(cliente))

    def tiene_cuentas_vencidas(self, cliente, ahora=None):
        """Respuesta 2.3: a quien tiene una cuenta vencida sin pagar no se le fía más."""
        ahora = ahora or datetime.now()
        return any(cuenta.esta_vencida(ahora) for cuenta in self.cuentas_del_cliente(cliente.id_cliente))

    def crear_cuenta(self, venta, plazo_dias=PLAZO_POR_DEFECTO_DIAS):
        apertura = datetime.now()
        vencimiento = apertura + timedelta(days=plazo_dias)
        return CuentaPorCobrar(None, venta.id_venta, venta.id_cliente, venta.total, apertura, vencimiento)

    def registrar_abono(self, id_cuenta, monto):
        cuenta = self.repo_ventas.obtener_cuenta(id_cuenta)
        if cuenta is None:
            raise ValueError("La cuenta por cobrar no existe")
        cuenta.aplicar_pago(monto)
        self.repo_ventas.guardar_abono(cuenta, monto)
        return cuenta

    def cuentas_del_cliente(self, id_cliente):
        return self.repo_ventas.cuentas_del_cliente(id_cliente)

    def obtener_cuenta(self, id_cuenta):
        return self.repo_ventas.obtener_cuenta(id_cuenta)

    def estado_de_cuenta(self, id_cliente):
        """Fase 7: los movimientos del fiado en orden, cada uno con el saldo que quedó (compra suma, abono y
        devolución restan). Solo lee."""
        saldo, movimientos = 0, []
        for movimiento in self.repo_ventas.movimientos_de_cuenta(id_cliente):
            saldo += SIGNO_DEL_MOVIMIENTO_DE_CUENTA[movimiento.tipo] * movimiento.valor
            movimientos.append(movimiento._replace(saldo=saldo))
        return movimientos


class ServicioDeVentas:
    def __init__(self, repo_productos, repo_clientes, repo_ventas, control_inventario, control_credito):
        self.repo_productos = repo_productos
        self.repo_clientes = repo_clientes
        self.repo_ventas = repo_ventas
        self.control_inventario = control_inventario
        self.control_credito = control_credito

    def registrar_venta_a_credito(self, id_cliente, lineas):
        cliente = self._obtener_cliente(id_cliente)
        venta, pedido = self._armar_venta(Venta(cliente.id_cliente, TipoVenta.CREDITO), lineas)
        self._validar_credito(cliente, venta.calcular_total())
        existencias = self._descontar_existencias(pedido)
        venta.confirmar()
        cuenta = self.control_credito.crear_cuenta(venta, cliente.plazo_credito_dias)
        self.repo_ventas.guardar_transaccion(venta, cuenta, existencias)
        return venta

    def registrar_venta_de_contado(self, lineas, recibido, transferencia=0):
        """UC-02: mismas validaciones de existencias que CU-01, pero sin cliente ni cuenta por cobrar.
        recibido es el efectivo; transferencia, lo pagado por Nequi o Daviplata (respuesta 1.2)."""
        venta, pedido = self._armar_venta(Venta(tipo=TipoVenta.CONTADO), lineas)
        venta.registrar_pago(recibido, transferencia)
        existencias = self._descontar_existencias(pedido)
        venta.confirmar()
        self.repo_ventas.guardar_transaccion(venta, None, existencias)
        return venta

    def obtener(self, id_venta):
        return self.repo_ventas.obtener(id_venta)

    # ------------------------------------------------------------------ devoluciones (respuesta 1.5, cambia DT-08)
    def devolver(self, id_venta, lineas, motivo):
        """Devuelve productos de una venta ya cobrada: vuelven al inventario y se devuelve el dinero o se
        descuenta de la deuda. Si ya no queda nada por devolver, la venta queda ANULADA. Todo o nada (RNF-04)."""
        venta = self._venta_que_se_puede_devolver(id_venta)
        devolucion = Devolucion(venta.id_venta, motivo)
        pendientes = self.pendientes_por_devolver(venta)
        for id_producto, cantidad in lineas:
            self._agregar_a_la_devolucion(devolucion, venta, pendientes, id_producto, cantidad)
        if not devolucion.lineas:
            raise ValueError("Elige al menos un producto para devolver")
        cuenta = self._cuenta_de(venta)
        devolucion.repartir(cuenta)
        if not any(pendientes.values()):
            venta.anular()
        self.repo_ventas.guardar_devolucion(devolucion, venta, cuenta, self._existencias_que_regresan(devolucion))
        return devolucion

    def anular(self, id_venta, motivo):
        """Anular = devolver todo lo que queda de la venta."""
        venta = self._venta_que_se_puede_devolver(id_venta)
        return self.devolver(id_venta, list(self.pendientes_por_devolver(venta).items()), motivo)

    def pendientes_por_devolver(self, venta):
        """{id_producto: unidades vendidas que todavía no se han devuelto}."""
        devueltas = self.repo_ventas.unidades_devueltas(venta.id_venta)
        return {id_producto: vendidas - devueltas.get(id_producto, 0)
                for id_producto, vendidas in venta.unidades_por_producto().items()}

    def unidades_devueltas(self, id_venta):
        return self.repo_ventas.unidades_devueltas(id_venta)

    def devoluciones_de_la_venta(self, id_venta):
        return self.repo_ventas.devoluciones_de_la_venta(id_venta)

    def _venta_que_se_puede_devolver(self, id_venta):
        venta = self.repo_ventas.obtener(id_venta)
        if venta is None:
            raise ValueError("La venta no existe")
        if venta.estado == EstadoVenta.ANULADA:
            raise ValueError(f"La venta #{venta.id_venta} ya está anulada")
        return venta

    def _agregar_a_la_devolucion(self, devolucion, venta, pendientes, id_producto, cantidad):
        if id_producto not in pendientes:
            raise ValueError(f"Ese producto no está en la venta #{venta.id_venta}")
        exigir_mayor_a_cero(cantidad)
        if cantidad > pendientes[id_producto]:
            nombre = self._obtener_producto(id_producto).nombre
            raise ValueError(f"De {nombre} solo se pueden devolver {pendientes[id_producto]}")
        devolucion.agregar(id_producto, cantidad, venta.precio_de(id_producto))
        pendientes[id_producto] -= cantidad

    def _cuenta_de(self, venta):
        if venta.tipo != TipoVenta.CREDITO:
            return None
        return next(c for c in self.repo_ventas.cuentas_del_cliente(venta.id_cliente) if c.id_venta == venta.id_venta)

    def _existencias_que_regresan(self, devolucion):
        existencias = {}
        for linea in devolucion.lineas:
            existencia = existencias.get(linea.id_producto) or self.repo_productos.obtener_existencia(linea.id_producto)
            existencia.aumentar(linea.cantidad)
            existencias[linea.id_producto] = existencia
        return list(existencias.values())

    def listar(self, limite=VENTAS_A_MOSTRAR):
        return self.repo_ventas.listar(limite)

    def _obtener_cliente(self, id_cliente):
        cliente = self.repo_clientes.obtener(id_cliente)
        if cliente is None:
            raise ValueError("El cliente no existe")
        return cliente

    def _obtener_producto(self, id_producto):
        producto = self.repo_productos.obtener(id_producto)
        if producto is None:
            raise ValueError("El producto no existe")
        return producto

    def _armar_venta(self, venta, lineas):
        """Llena la venta y valida el stock. 'pedido' guarda, por producto, el total pedido."""
        pedido = {}
        for linea in map(LineaDeVenta._make, lineas):
            producto = self._obtener_producto(linea.id_producto)
            producto.exigir_activo()                          # fase 6: aunque ya estuviera en el carrito
            cantidad_total = pedido.get(producto.id_producto, (producto, 0))[1] + linea.cantidad
            pedido[producto.id_producto] = (producto, cantidad_total)
            if not self.control_inventario.hay_disponible(producto, cantidad_total):
                disponible = self.control_inventario.cantidad_disponible(producto)
                raise StockInsuficiente(f"Solo hay {disponible} disponibles de {producto.nombre}")
            venta.agregar_detalle(producto, linea.cantidad)
        return venta, pedido

    def _validar_credito(self, cliente, total):
        if self.control_credito.tiene_cuentas_vencidas(cliente):
            raise CreditoNoPermitido(f"No se le puede fiar a {cliente.nombres}: tiene cuentas vencidas sin pagar")
        if not self.control_credito.puede_comprar_a_credito(cliente, total):
            raise CreditoNoPermitido(f"El cliente no puede comprar a crédito por {total}")

    def _descontar_existencias(self, pedido):
        return [self.control_inventario.descontar(producto, cantidad)
                for producto, cantidad in pedido.values()]


# ---------------------------------------------------------------------- reportes (fase 1 de la hoja de ruta)
class Periodo(str, Enum):
    HOY = "hoy"
    SEMANA = "semana"      # los últimos 7 días, contando hoy
    MES = "mes"            # desde el día 1 del mes


DIAS_DE_LA_SEMANA = 7
MAS_VENDIDOS_A_MOSTRAR = 10
ReporteDeVentas = namedtuple("ReporteDeVentas", "desde hasta resumen mas_vendidos")


def rango_del_periodo(periodo, ahora):
    """[desde, hasta): hasta es la medianoche de mañana, así entra todo lo de hoy."""
    hoy = datetime(ahora.year, ahora.month, ahora.day)
    desde = {Periodo.HOY: hoy, Periodo.SEMANA: hoy - timedelta(days=DIAS_DE_LA_SEMANA - 1),
             Periodo.MES: hoy.replace(day=1)}[periodo]
    return desde, hoy + timedelta(days=1)


class ServicioDeReportes:
    """Solo consulta: no cambia ventas, inventario ni deudas. Los totales los suma el repositorio (PuertoDeReportes)."""

    def __init__(self, repo_reportes):
        self.repo_reportes = repo_reportes

    def reporte(self, periodo, ahora=None):
        desde, hasta = rango_del_periodo(Periodo(periodo), ahora or datetime.now())
        return ReporteDeVentas(desde, hasta, self.repo_reportes.resumen_de_ventas(desde, hasta),
                               self.repo_reportes.mas_vendidos(desde, hasta, MAS_VENDIDOS_A_MOSTRAR))


# ---------------------------------------------------------------------- datos de la tienda (fase 6)
ANCHO_DEL_TICKET = 42                     # impresora térmica de 80 mm (respuesta 1.3)
CAMPOS_DE_LA_TIENDA = DatosDeLaTienda._fields


class ServicioDeLaTienda:
    """Nombre, NIT, dirección, teléfono y mensaje del ticket, guardados en la configuración (*preliminar*)."""

    def __init__(self, repo_configuracion):
        self.repo_configuracion = repo_configuracion

    def datos(self):
        por_defecto = DatosDeLaTienda()
        return DatosDeLaTienda(*(self.repo_configuracion.obtener(f"tienda_{campo}", getattr(por_defecto, campo))
                                 for campo in CAMPOS_DE_LA_TIENDA))

    def guardar(self, nombre, nit, direccion, telefono, mensaje):
        datos = DatosDeLaTienda.validados(nombre, nit, direccion, telefono, mensaje)
        for campo in CAMPOS_DE_LA_TIENDA:
            self.repo_configuracion.guardar(f"tienda_{campo}", getattr(datos, campo))
        return datos

    def encabezado_del_ticket(self):
        """Solo lo que esté lleno, partido a 42 caracteres por renglón."""
        datos = self.datos()
        partes = [datos.nombre, f"NIT: {datos.nit}" if datos.nit else "", datos.direccion,
                  f"Tel: {datos.telefono}" if datos.telefono else ""]
        return [renglon for parte in partes if parte for renglon in textwrap.wrap(parte, ANCHO_DEL_TICKET)]

    def mensaje_del_ticket(self):
        return textwrap.wrap(self.datos().mensaje, ANCHO_DEL_TICKET)


# ---------------------------------------------------------------------- caja (fase 4)
TURNOS_EN_EL_HISTORIAL = 30
UN_INSTANTE = timedelta(seconds=1)      # para que entre lo registrado en el mismo segundo de la consulta
DetalleDeCaja = namedtuple("DetalleDeCaja", "base ventas_en_efectivo abonos efectivo_devuelto esperado")
RevisionDeCierre = namedtuple("RevisionDeCierre", "esperado contado diferencia")


class ServicioDeCaja:
    """Abrir el turno con la base del día y cerrarlo con lo contado. El turno abierto queda en la base de datos,
    así se puede cerrar la app sin cerrar la caja. Los totales salen del mismo PuertoDeReportes (fase 1)."""

    def __init__(self, repo_caja, repo_reportes):
        self.repo_caja = repo_caja
        self.repo_reportes = repo_reportes

    def turno_abierto(self):
        return self.repo_caja.turno_abierto()

    def abrir(self, base, id_usuario, ahora=None):
        abierto = self.turno_abierto()
        if abierto is not None:
            raise ValueError(f"Ya hay una caja abierta desde el {abierto.abierto_en:%d/%m/%Y %H:%M}")
        return self.repo_caja.guardar(TurnoDeCaja(None, base, ahora or datetime.now(), id_usuario))

    def esperado(self, ahora=None):
        """*Preliminar:* base + ventas de contado en efectivo + abonos − efectivo devuelto, desde que se abrió."""
        turno = self._exigir_turno_abierto()
        resumen = self.repo_reportes.resumen_de_ventas(turno.abierto_en, (ahora or datetime.now()) + UN_INSTANTE)
        esperado = turno.base + resumen.efectivo + resumen.abonos - resumen.efectivo_devuelto
        return DetalleDeCaja(turno.base, resumen.efectivo, resumen.abonos, resumen.efectivo_devuelto, esperado)

    def revisar_cierre(self, contado, ahora=None):
        """Dice cuánto falta o sobra sin cerrar: si no cuadra, se puede cancelar y contar de nuevo."""
        exigir_no_negativo(contado, "Lo contado no puede ser negativo")
        esperado = self.esperado(ahora).esperado
        return RevisionDeCierre(esperado, contado, contado - esperado)

    def cerrar(self, contado, id_usuario, ahora=None):
        ahora = ahora or datetime.now()
        esperado = self.revisar_cierre(contado, ahora).esperado
        turno = self._exigir_turno_abierto()
        turno.cerrar(contado, esperado, id_usuario, ahora)
        return self.repo_caja.guardar(turno)

    def historial(self, limite=TURNOS_EN_EL_HISTORIAL):
        return self.repo_caja.listar_cerrados(limite)

    def _exigir_turno_abierto(self):
        turno = self.turno_abierto()
        if turno is None:
            raise ValueError("No hay una caja abierta")
        return turno


# ---------------------------------------------------------------------- usuarios y sesión (fase 2, CR-01, RNF-03)
ACCESO_INCORRECTO = "Usuario o clave incorrectos"     # el mismo mensaje siempre: no revela qué usuarios existen
SIN_INGRESAR = "Primero ingrese con su usuario y clave"
SOLO_EL_JEFE = "Solo el jefe puede hacer esto"
AUTORIZACION_INCORRECTA = "Usuario o clave del jefe incorrectos"


class ServicioDeUsuarios:
    def __init__(self, repo_usuarios):
        self.repo_usuarios = repo_usuarios

    def hay_usuarios(self):
        return bool(self.repo_usuarios.listar())

    def crear_primer_jefe(self, nombre, usuario, clave):
        """La primera vez que se abre la tienda no hay nadie: se crea el jefe. Después, solo el jefe crea usuarios."""
        if self.hay_usuarios():
            raise ValueError("Ya hay usuarios: el jefe crea los demás en la sección Usuarios")
        return self.crear_usuario(nombre, usuario, Rol.JEFE, clave)

    def crear_usuario(self, nombre, usuario, rol, clave):
        return self.repo_usuarios.guardar(Usuario.nuevo(nombre, usuario, rol, clave))

    def obtener(self, id_usuario):
        usuario = self.repo_usuarios.obtener(id_usuario)
        if usuario is None:
            raise ValueError("El usuario no existe")
        return usuario

    def listar(self):
        return self.repo_usuarios.listar()

    def iniciar_sesion(self, usuario, clave):
        try:
            encontrado = self.repo_usuarios.obtener_por_usuario(normalizar_usuario(usuario))
        except ValueError:
            encontrado = None
        if encontrado is None or not encontrado.activo or not encontrado.clave_correcta(clave):
            raise ValueError(ACCESO_INCORRECTO)
        return encontrado

    def autorizar(self, usuario, clave, permiso):
        """Fase 3: alguien con ese permiso (el jefe) escribe su usuario y su clave para autorizar una acción."""
        try:
            quien = self.iniciar_sesion(usuario, clave)
        except ValueError:
            quien = None
        if quien is None or not quien.rol.puede(permiso):
            raise ValueError(AUTORIZACION_INCORRECTA)
        return quien

    def cambiar_clave(self, id_usuario, clave):
        usuario = self.obtener(id_usuario)
        usuario.cambiar_clave(clave)
        return self.repo_usuarios.guardar(usuario)

    def activar(self, id_usuario, activo, quien):
        """quien: el usuario que hace el cambio. Nadie se bloquea a sí mismo y siempre queda un jefe activo."""
        usuario = self.obtener(id_usuario)
        if not activo and usuario.id_usuario == quien.id_usuario:
            raise ValueError("No puede desactivar su propio usuario")
        if not activo and usuario.rol == Rol.JEFE and self._jefes_activos() <= 1:
            raise ValueError("Debe quedar al menos un jefe activo")
        usuario.activo = activo
        return self.repo_usuarios.guardar(usuario)

    def _jefes_activos(self):
        return sum(1 for u in self.repo_usuarios.listar() if u.rol == Rol.JEFE and u.activo)


class Sesion:
    """Quién está usando la tienda en esta ventana. No sabe de pantallas: solo dice si algo se puede hacer."""

    def __init__(self):
        self.usuario = None

    def iniciar(self, usuario):
        self.usuario = usuario

    def cerrar(self):
        self.usuario = None

    def negar(self, permiso):
        """None si se puede; si no, el mensaje que se muestra."""
        if self.usuario is None:
            return SIN_INGRESAR
        if not self.usuario.rol.puede(permiso):
            return SOLO_EL_JEFE
        return None

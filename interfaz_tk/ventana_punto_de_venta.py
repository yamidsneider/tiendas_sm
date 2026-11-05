"""Ventana del punto de venta (tarea 8, TD-03, DAD §10.2, DDS §9.1).

Solo dibuja y reenvía: cada botón o tecla llama a un método del presentador y muestra lo que devuelve.
Atajos: F2 buscar, Enter agregar, F9 cobrar de contado, F4 vender a crédito, Supr quitar, Esc cerrar diálogo.
"""
import tkinter as tk
from tkinter import ttk

from tiendas_sm.presentador import formato_pesos

TITULO = "TIENDAS S.M — Punto de venta"
ANCHO_MINIMO, ALTO_MINIMO = 1024, 600          # DDS §9.2
FUENTE_TOTAL = ("Segoe UI", 28, "bold")
FUENTE_NORMAL = ("Segoe UI", 11)
COLOR_ERROR, COLOR_OK = "#b00020", "#1b5e20"
CANTIDAD_INICIAL = "1"


class VentanaPuntoDeVenta:
    def __init__(self, raiz, presentador):
        self.raiz = raiz
        self.pv = presentador
        self.dialogo = None          # diálogo de cobro abierto (contado o crédito), si hay uno
        self.ventana_ticket = None
        raiz.title(TITULO)
        raiz.minsize(ANCHO_MINIMO, ALTO_MINIMO)
        self._construir()
        self._atajos()
        self.refrescar()
        self.enfocar_busqueda()

    # ------------------------------------------------------------------ construcción
    def _construir(self):
        izquierda = ttk.Frame(self.raiz, padding=12)
        derecha = ttk.Frame(self.raiz, padding=12)
        izquierda.pack(side="left", fill="both", expand=True)
        derecha.pack(side="right", fill="y")
        self._construir_busqueda(izquierda)
        self._construir_carrito(izquierda)
        self._construir_panel_de_cobro(derecha)

    def _construir_busqueda(self, padre):
        fila = ttk.Frame(padre)
        fila.pack(fill="x")
        ttk.Label(fila, text="Buscar producto (F2):", font=FUENTE_NORMAL).pack(side="left")
        self.texto_busqueda = tk.StringVar()
        self.campo_busqueda = ttk.Entry(fila, textvariable=self.texto_busqueda, width=34, font=FUENTE_NORMAL)
        self.campo_busqueda.pack(side="left", padx=6)
        ttk.Label(fila, text="Cantidad:", font=FUENTE_NORMAL).pack(side="left")
        self.cantidad = tk.StringVar(value=CANTIDAD_INICIAL)
        self.campo_cantidad = ttk.Entry(fila, textvariable=self.cantidad, width=5, font=FUENTE_NORMAL)
        self.campo_cantidad.pack(side="left", padx=6)
        ttk.Button(fila, text="Agregar (Enter)", command=self.agregar_seleccionado).pack(side="left")
        self.resultados = self._tabla(padre, "Resultados", ("Producto", "Precio", "Disponibles"), alto=5)
        self.texto_busqueda.trace_add("write", lambda *_: self.actualizar_resultados())

    def _construir_carrito(self, padre):
        self.carrito = self._tabla(padre, "Venta en curso", ("Producto", "Precio", "Cantidad", "Importe", "Disponibles"),
                                   alto=10)
        self.mensaje = ttk.Label(padre, text="", font=FUENTE_NORMAL)
        self.mensaje.pack(fill="x", pady=(8, 0))

    def _tabla(self, padre, titulo, columnas, alto):
        marco = ttk.LabelFrame(padre, text=titulo, padding=6)
        marco.pack(fill="both", expand=True, pady=(10, 0))
        tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=alto, selectmode="browse")
        for columna in columnas:
            tabla.heading(columna, text=columna)
            tabla.column(columna, anchor="w" if columna == "Producto" else "e", width=260 if columna == "Producto" else 110)
        tabla.pack(fill="both", expand=True)
        return tabla

    def _construir_panel_de_cobro(self, padre):
        caja = ttk.LabelFrame(padre, text="TOTAL A COBRAR", padding=12)
        caja.pack(fill="x")
        self.etiqueta_total = ttk.Label(caja, text=formato_pesos(0), font=FUENTE_TOTAL)
        self.etiqueta_total.pack()
        self.etiqueta_resumen = ttk.Label(caja, text="", font=FUENTE_NORMAL)
        self.etiqueta_resumen.pack()
        self.boton_contado = ttk.Button(padre, text="Cobrar de contado (F9)", command=self.abrir_cobro_de_contado)
        self.boton_credito = ttk.Button(padre, text="Vender a crédito (F4)", command=self.abrir_venta_a_credito)
        self.boton_quitar = ttk.Button(padre, text="Quitar producto (Supr)", command=self.quitar_seleccionado)
        self.boton_limpiar = ttk.Button(padre, text="Limpiar venta", command=self.limpiar)
        for boton in (self.boton_contado, self.boton_credito, self.boton_quitar, self.boton_limpiar):
            boton.pack(fill="x", pady=(10, 0), ipady=6)

    def _atajos(self):
        self.raiz.bind("<F2>", lambda _: self.enfocar_busqueda())
        self.raiz.bind("<F9>", lambda _: self.abrir_cobro_de_contado())
        self.raiz.bind("<F4>", lambda _: self.abrir_venta_a_credito())
        self.raiz.bind("<Delete>", lambda _: self.quitar_seleccionado())
        for campo in (self.campo_busqueda, self.campo_cantidad):
            campo.bind("<Return>", lambda _: self.agregar_seleccionado())
        self.resultados.bind("<Double-1>", lambda _: self.agregar_seleccionado())

    # ------------------------------------------------------------------ acciones del carrito
    def enfocar_busqueda(self):
        self.campo_busqueda.focus_set()
        self.campo_busqueda.select_range(0, "end")

    def actualizar_resultados(self):
        self.resultados.delete(*self.resultados.get_children())
        for fila in self.pv.buscar(self.texto_busqueda.get()):
            self.resultados.insert("", "end", iid=str(fila.id_producto),
                                   values=(fila.nombre, formato_pesos(fila.precio), f"Disponibles: {fila.disponibles}"))

    def agregar_seleccionado(self):
        """Agrega el resultado elegido o, si no hay uno elegido, el primero de la lista."""
        elegido = self.resultados.selection() or self.resultados.get_children()[:1]
        if not elegido:
            self.mostrar_mensaje("Escribe el nombre de un producto y elígelo de la lista", error=True)
            return
        resultado = self.pv.agregar(int(elegido[0]), self.cantidad.get())
        self.mostrar_mensaje(resultado.mensaje, error=not resultado.exito)
        if resultado.exito:
            self.texto_busqueda.set("")
            self.cantidad.set(CANTIDAD_INICIAL)
            self.enfocar_busqueda()
        self.refrescar()

    def quitar_seleccionado(self):
        for iid in self.carrito.selection():
            self.pv.quitar(int(iid))
        self.refrescar()

    def limpiar(self):
        self.pv.limpiar()
        self.mostrar_mensaje("")
        self.refrescar()

    def refrescar(self):
        self.carrito.delete(*self.carrito.get_children())
        for linea in self.pv.lineas():
            self.carrito.insert("", "end", iid=str(linea.id_producto),
                                values=(linea.nombre, formato_pesos(linea.precio), linea.cantidad,
                                        formato_pesos(linea.importe), f"Disponibles: {linea.disponibles}"))
        self.etiqueta_total.config(text=formato_pesos(self.pv.total()))
        self.etiqueta_resumen.config(text=self.pv.resumen())
        estado = "normal" if self.pv.carrito else "disabled"     # DAD §10.2: no se cobra una venta vacía
        for boton in (self.boton_contado, self.boton_credito, self.boton_quitar, self.boton_limpiar):
            boton.config(state=estado)

    def mostrar_mensaje(self, texto, error=False):
        self.mensaje.config(text=texto, foreground=COLOR_ERROR if error else COLOR_OK)

    # ------------------------------------------------------------------ cobro
    def abrir_cobro_de_contado(self):
        if self._se_puede_abrir_dialogo():
            self.dialogo = DialogoDeContado(self)

    def abrir_venta_a_credito(self):
        if self._se_puede_abrir_dialogo():
            self.dialogo = DialogoDeCredito(self)

    def _se_puede_abrir_dialogo(self):
        if not self.pv.carrito:
            self.mostrar_mensaje("Agrega al menos un producto antes de cobrar", error=True)
            return False
        return self.dialogo is None

    def terminar_cobro(self, resultado):
        """Lo llama el diálogo después de confirmar: si salió bien, cierra y muestra el ticket."""
        self.mostrar_mensaje(resultado.mensaje, error=not resultado.exito)
        if resultado.exito:
            self.cerrar_dialogo()
            self.mostrar_ticket(resultado.ticket)
            self.refrescar()

    def cerrar_dialogo(self):
        if self.dialogo is not None:
            self.dialogo.ventana.destroy()
            self.dialogo = None
        self.enfocar_busqueda()

    def mostrar_ticket(self, ticket):
        self.ventana_ticket = tk.Toplevel(self.raiz)
        self.ventana_ticket.title("Ticket de la venta")
        texto = tk.Text(self.ventana_ticket, width=56, height=16, font=("Consolas", 11))
        texto.insert("1.0", ticket)
        texto.config(state="disabled")
        texto.pack(padx=12, pady=12)
        ttk.Button(self.ventana_ticket, text="Cerrar (Esc)", command=self.ventana_ticket.destroy).pack(pady=(0, 12))
        self.ventana_ticket.bind("<Escape>", lambda _: self.ventana_ticket.destroy())


class _DialogoDeCobro:
    """Parte común de los dos diálogos: ventana modal, Esc para cancelar y Confirmar que se desactiva al primer clic."""

    def __init__(self, ventana_principal, titulo):
        self.principal = ventana_principal
        self.ventana = tk.Toplevel(ventana_principal.raiz)
        self.ventana.title(titulo)
        self.ventana.transient(ventana_principal.raiz)
        self.ventana.protocol("WM_DELETE_WINDOW", ventana_principal.cerrar_dialogo)
        self.ventana.bind("<Escape>", lambda _: ventana_principal.cerrar_dialogo())
        self.cuerpo = ttk.Frame(self.ventana, padding=16)
        self.cuerpo.pack(fill="both", expand=True)
        ttk.Label(self.cuerpo, text=f"Total: {formato_pesos(ventana_principal.pv.total())}", font=FUENTE_NORMAL).pack(
            anchor="w")

    def _botones(self):
        self.etiqueta_error = ttk.Label(self.cuerpo, text="", foreground=COLOR_ERROR, font=FUENTE_NORMAL,
                                        wraplength=420, justify="left")
        self.etiqueta_error.pack(anchor="w", pady=(10, 0))
        fila = ttk.Frame(self.cuerpo)
        fila.pack(fill="x", pady=(14, 0))
        self.boton_confirmar = ttk.Button(fila, text="Confirmar venta", command=self.confirmar)
        self.boton_confirmar.pack(side="left")
        ttk.Button(fila, text="Cancelar (Esc)", command=self.principal.cerrar_dialogo).pack(side="left", padx=8)
        self.ventana.bind("<Return>", lambda _: self.confirmar())

    def confirmar(self):
        if str(self.boton_confirmar.cget("state")) == "disabled":
            return                                                  # DDS §13.1: un doble clic no duplica la venta
        self.boton_confirmar.config(state="disabled")
        resultado = self.registrar()
        if not resultado.exito:
            self.etiqueta_error.config(text=resultado.mensaje)      # el mensaje del dominio, tal como llega
            self.boton_confirmar.config(state="normal")             # se puede corregir y reintentar
        self.principal.terminar_cobro(resultado)

    def registrar(self):
        raise NotImplementedError


class DialogoDeContado(_DialogoDeCobro):
    def __init__(self, ventana_principal):
        super().__init__(ventana_principal, "Cobrar de contado")
        ttk.Label(self.cuerpo, text="Recibido en efectivo:", font=FUENTE_NORMAL).pack(anchor="w", pady=(10, 0))
        self.recibido = tk.StringVar()
        self.campo_recibido = ttk.Entry(self.cuerpo, textvariable=self.recibido, font=FUENTE_NORMAL)
        self.campo_recibido.pack(fill="x")
        self.etiqueta_cambio = ttk.Label(self.cuerpo, text="", font=FUENTE_NORMAL)
        self.etiqueta_cambio.pack(anchor="w", pady=(6, 0))
        self.recibido.trace_add("write", lambda *_: self.actualizar_cambio())
        self._botones()
        self.campo_recibido.focus_set()

    def actualizar_cambio(self):
        self.etiqueta_cambio.config(text=self.principal.pv.cambio_previo(self.recibido.get()).mensaje)

    def registrar(self):
        return self.principal.pv.cobrar_de_contado(self.recibido.get())


class DialogoDeCredito(_DialogoDeCobro):
    def __init__(self, ventana_principal):
        super().__init__(ventana_principal, "Vender a crédito")
        self.clientes = ventana_principal.pv.clientes()
        ttk.Label(self.cuerpo, text="Cliente:", font=FUENTE_NORMAL).pack(anchor="w", pady=(10, 0))
        self.selector = ttk.Combobox(self.cuerpo, state="readonly", font=FUENTE_NORMAL, width=36,
                                     values=[cliente.nombres for cliente in self.clientes])
        self.selector.pack(fill="x")
        self.etiqueta_cliente = ttk.Label(self.cuerpo, text="Elige el cliente que se lleva la venta",
                                          font=FUENTE_NORMAL, justify="left")
        self.etiqueta_cliente.pack(anchor="w", pady=(6, 0))
        self.selector.bind("<<ComboboxSelected>>", lambda _: self.mostrar_cliente())
        self._botones()
        self.selector.focus_set()

    def cliente_elegido(self):
        indice = self.selector.current()
        return self.clientes[indice].id_cliente if indice >= 0 else None

    def mostrar_cliente(self):
        self.etiqueta_cliente.config(text=self.principal.pv.datos_del_cliente(self.cliente_elegido()).texto)

    def registrar(self):
        return self.principal.pv.vender_a_credito(self.cliente_elegido())

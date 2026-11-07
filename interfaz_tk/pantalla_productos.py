"""Sección Productos (HU-01, HU-02, RF-01, RF-02; etapa 4 de la interfaz). Solo dibuja y reenvía.

A la izquierda el catálogo con búsqueda; a la derecha «Nuevo producto» y «Cambiar precio de venta» del
producto elegido. Las entradas de mercancía se registran en la sección Existencias.
"""
import tkinter as tk
from tkinter import ttk

from interfaz_tk.pantalla import Pantalla
from interfaz_tk.tema import COLOR_ERROR, COLOR_OK, FUENTE_NORMAL, crear_tabla, llenar_tabla

ANCHO_PANEL_DERECHO = 280
ANCHO_DEL_TEXTO = ANCHO_PANEL_DERECHO - 30
ANCHO_MINIMO_DE_CAMPO = 8
COLUMNAS = ("Producto", "Compra", "Venta", "Disponibles")
SIN_ELEGIR = "Elige un producto de la lista"


class PantallaProductos(Pantalla):
    def __init__(self, contenedor, presentador):
        super().__init__(contenedor)
        self.pp = presentador
        izquierda = ttk.Frame(self.marco, padding=(0, 6, 12, 0))
        derecha = ttk.Frame(self.marco, padding=(6, 6, 0, 0), width=ANCHO_PANEL_DERECHO)
        derecha.pack(side="right", fill="y")
        derecha.pack_propagate(False)
        izquierda.pack(side="left", fill="both", expand=True)
        self._construir_lista(izquierda)
        self._construir_formulario(derecha)
        self._construir_cambio_de_precio(derecha)

    def al_mostrar(self):
        self.refrescar()                 # las ventas y las entradas cambian los disponibles

    # ------------------------------------------------------------------ construcción
    def _construir_lista(self, padre):
        fila = ttk.Frame(padre)
        fila.pack(fill="x")
        ttk.Label(fila, text="Buscar producto:").pack(side="left")
        self.busqueda = tk.StringVar()
        ttk.Entry(fila, textvariable=self.busqueda, width=24, font=FUENTE_NORMAL).pack(side="left", padx=6)
        self.busqueda.trace_add("write", lambda *_: self.refrescar())
        self.tabla = crear_tabla(padre, "Catálogo", COLUMNAS, alto=12)
        self.tabla.bind("<<TreeviewSelect>>", lambda _: self.mostrar_precio_actual())

    def _construir_formulario(self, padre):
        caja = ttk.LabelFrame(padre, text="Nuevo producto", padding=10)
        caja.pack(fill="x")
        self.nombre, self.precio_compra = tk.StringVar(), tk.StringVar()
        self.precio_venta, self.cantidad_inicial = tk.StringVar(), tk.StringVar(value="0")
        self._campo(caja, "Nombre", self.nombre, self.guardar)
        self._fila_de_dos(caja, ("Compra (pesos)", self.precio_compra), ("Venta (pesos)", self.precio_venta))
        self._campo(caja, "Cantidad inicial", self.cantidad_inicial, self.guardar)
        ttk.Button(caja, text="Guardar producto", style="Primario.TButton",
                   command=self.guardar).pack(fill="x", pady=(10, 0))
        self.mensaje = ttk.Label(caja, text="", wraplength=ANCHO_DEL_TEXTO, justify="left")
        self.mensaje.pack(anchor="w", pady=(4, 0))

    def _fila_de_dos(self, padre, primero, segundo):
        fila = ttk.Frame(padre)
        fila.pack(fill="x")
        for posicion, (titulo, variable) in enumerate((primero, segundo)):
            columna = ttk.Frame(fila)
            columna.pack(side="left", fill="x", expand=True, padx=(0, 6) if posicion == 0 else 0)
            self._campo(columna, titulo, variable, self.guardar)

    def _campo(self, padre, titulo, variable, al_presionar_enter):
        ttk.Label(padre, text=titulo).pack(anchor="w", pady=(4, 0))
        campo = ttk.Entry(padre, textvariable=variable, font=FUENTE_NORMAL, width=ANCHO_MINIMO_DE_CAMPO)
        campo.pack(fill="x")
        campo.bind("<Return>", lambda _: al_presionar_enter())
        return campo

    def _construir_cambio_de_precio(self, padre):
        caja = ttk.LabelFrame(padre, text="Cambiar precio de venta", padding=10)
        caja.pack(fill="both", expand=True, pady=(8, 0))
        self.precio_elegido = ttk.Label(caja, text=SIN_ELEGIR, style="Tenue.TLabel", wraplength=ANCHO_DEL_TEXTO,
                                        justify="left")
        self.precio_elegido.pack(anchor="w")
        fila = ttk.Frame(caja)
        fila.pack(fill="x", pady=(6, 0))
        self.nuevo_precio = tk.StringVar()
        campo = ttk.Entry(fila, textvariable=self.nuevo_precio, font=FUENTE_NORMAL, width=ANCHO_MINIMO_DE_CAMPO)
        campo.pack(side="left", fill="x", expand=True)
        campo.bind("<Return>", lambda _: self.cambiar_precio())
        ttk.Button(fila, text="Cambiar", command=self.cambiar_precio).pack(side="left", padx=(6, 0))
        self.mensaje_precio = ttk.Label(caja, text="", wraplength=ANCHO_DEL_TEXTO, justify="left")
        self.mensaje_precio.pack(anchor="w", pady=(4, 0))

    # ------------------------------------------------------------------ acciones
    def producto_elegido(self):
        elegido = self.tabla.selection()
        return int(elegido[0]) if elegido else None

    def refrescar(self):
        elegido = self.tabla.selection()
        llenar_tabla(self.tabla, self.pp.tabla(self.busqueda.get()))
        if elegido and self.tabla.exists(elegido[0]):
            self.tabla.selection_set(elegido[0])         # se conserva el producto que estaba elegido
        self.mostrar_precio_actual()

    def mostrar_precio_actual(self):
        producto = self.producto_elegido()
        texto = self.pp.precio_actual(producto) if producto is not None else ""
        self.precio_elegido.config(text=texto or SIN_ELEGIR, style="TLabel" if texto else "Tenue.TLabel")

    def guardar(self):
        resultado = self.pp.registrar(self.nombre.get(), self.precio_compra.get(), self.precio_venta.get(),
                                      self.cantidad_inicial.get())
        self.mensaje.config(text=resultado.mensaje, foreground=COLOR_OK if resultado.exito else COLOR_ERROR)
        if resultado.exito:
            for variable in (self.nombre, self.precio_compra, self.precio_venta):
                variable.set("")
            self.cantidad_inicial.set("0")
            self.refrescar()

    def cambiar_precio(self):
        resultado = self.pp.cambiar_precio(self.producto_elegido(), self.nuevo_precio.get())
        self.mensaje_precio.config(text=resultado.mensaje, foreground=COLOR_OK if resultado.exito else COLOR_ERROR)
        if resultado.exito:
            self.nuevo_precio.set("")
            self.refrescar()

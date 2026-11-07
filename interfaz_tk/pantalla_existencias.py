"""Sección Existencias (HU-03, RF-03, RF-04; etapa 5 de la interfaz). Solo dibuja y reenvía.

A la izquierda cuántas unidades hay de cada producto y el historial de los últimos movimientos; a la
derecha el formulario para registrar una entrada de mercancía. Las salidas se registran solas al vender.
"""
import tkinter as tk
from tkinter import ttk

from interfaz_tk.pantalla import Pantalla
from interfaz_tk.tema import COLOR_ERROR, COLOR_OK, FUENTE_NORMAL, crear_tabla, llenar_tabla

ANCHO_PANEL_DERECHO = 270
ANCHO_DEL_TEXTO = ANCHO_PANEL_DERECHO - 30
ANCHOS_DEL_HISTORIAL = {"Fecha": 140, "Movimiento": 135, "Cantidad": 80}
SIN_ELEGIR = "Elige un producto de la lista"


class PantallaExistencias(Pantalla):
    def __init__(self, contenedor, presentador):
        super().__init__(contenedor)
        self.pe = presentador
        izquierda = ttk.Frame(self.marco, padding=(0, 6, 12, 0))
        derecha = ttk.Frame(self.marco, padding=(6, 6, 0, 0), width=ANCHO_PANEL_DERECHO)
        derecha.pack(side="right", fill="y")
        derecha.pack_propagate(False)
        izquierda.pack(side="left", fill="both", expand=True)
        self._construir_tablas(izquierda)
        self._construir_entrada(derecha)

    def al_mostrar(self):
        self.refrescar()                 # las ventas descuentan unidades y dejan movimientos

    # ------------------------------------------------------------------ construcción
    def _construir_tablas(self, padre):
        fila = ttk.Frame(padre)
        fila.pack(fill="x")
        ttk.Label(fila, text="Buscar producto:").pack(side="left")
        self.busqueda = tk.StringVar()
        ttk.Entry(fila, textvariable=self.busqueda, width=24, font=FUENTE_NORMAL).pack(side="left", padx=6)
        self.busqueda.trace_add("write", lambda *_: self.refrescar())
        self.tabla = crear_tabla(padre, "Inventario", ("Producto", "Disponibles"), alto=5)
        self.tabla.bind("<<TreeviewSelect>>", lambda _: self.mostrar_elegido())
        self.historial = crear_tabla(padre, "Últimos movimientos", ("Fecha", "Producto", "Movimiento", "Cantidad"),
                                     alto=5, columna_principal="Producto", anchos=ANCHOS_DEL_HISTORIAL)
        for columna in ("Fecha", "Movimiento"):          # son texto: a la izquierda
            self.historial.column(columna, anchor="w")

    def _construir_entrada(self, padre):
        caja = ttk.LabelFrame(padre, text="Registrar entrada", padding=10)
        caja.pack(fill="both", expand=True)
        self.elegido = ttk.Label(caja, text=SIN_ELEGIR, style="Tenue.TLabel", wraplength=ANCHO_DEL_TEXTO,
                                 justify="left")
        self.elegido.pack(anchor="w")
        ttk.Label(caja, text="Unidades que llegaron").pack(anchor="w", pady=(14, 0))
        self.cantidad = tk.StringVar()
        campo = ttk.Entry(caja, textvariable=self.cantidad, font=FUENTE_NORMAL)
        campo.pack(fill="x")
        campo.bind("<Return>", lambda _: self.registrar_entrada())
        ttk.Button(caja, text="Registrar entrada", style="Primario.TButton",
                   command=self.registrar_entrada).pack(fill="x", pady=(12, 0))
        self.mensaje = ttk.Label(caja, text="", wraplength=ANCHO_DEL_TEXTO, justify="left")
        self.mensaje.pack(anchor="w", pady=(8, 0))
        ttk.Label(caja, text="Las salidas se registran solas al vender.", style="Tenue.TLabel",
                  wraplength=ANCHO_DEL_TEXTO, justify="left").pack(side="bottom", anchor="w")

    # ------------------------------------------------------------------ acciones
    def producto_elegido(self):
        elegido = self.tabla.selection()
        return int(elegido[0]) if elegido else None

    def refrescar(self):
        elegido = self.tabla.selection()
        llenar_tabla(self.tabla, self.pe.tabla(self.busqueda.get()))
        if elegido and self.tabla.exists(elegido[0]):
            self.tabla.selection_set(elegido[0])         # se conserva el producto que estaba elegido
        llenar_tabla(self.historial, self.pe.movimientos())
        self.mostrar_elegido()

    def mostrar_elegido(self):
        producto = self.producto_elegido()
        nombre = self.pe.nombre(producto) if producto is not None else ""
        self.elegido.config(text=nombre or SIN_ELEGIR, style="TLabel" if nombre else "Tenue.TLabel")

    def registrar_entrada(self):
        resultado = self.pe.registrar_entrada(self.producto_elegido(), self.cantidad.get())
        self.mensaje.config(text=resultado.mensaje, foreground=COLOR_OK if resultado.exito else COLOR_ERROR)
        if resultado.exito:
            self.cantidad.set("")                       # si falla, la cantidad queda para corregirla
            self.refrescar()

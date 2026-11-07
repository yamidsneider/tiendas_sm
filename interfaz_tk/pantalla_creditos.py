"""Sección Créditos y abonos (HU-06, RF-09; etapa 3 de la interfaz). Solo dibuja y reenvía al presentador.

A la izquierda el total por cobrar y las cuentas (las pagadas solo si se marca la casilla); a la derecha
el detalle de la cuenta elegida y el formulario para registrar un abono.
"""
import tkinter as tk
from tkinter import ttk

from interfaz_tk.pantalla import Pantalla
from interfaz_tk.tema import COLOR_ERROR, COLOR_OK, FUENTE_NORMAL, FUENTE_TITULO, crear_tabla, llenar_tabla

ANCHO_PANEL_DERECHO = 270
ANCHO_DEL_TEXTO = ANCHO_PANEL_DERECHO - 30
COLUMNAS = ("Cliente", "Saldo", "Vence", "Estado")
SIN_ELEGIR = "Elige una cuenta de la lista"


class PantallaCreditos(Pantalla):
    def __init__(self, contenedor, presentador):
        super().__init__(contenedor)
        self.pc = presentador
        izquierda = ttk.Frame(self.marco, padding=(0, 6, 12, 0))
        derecha = ttk.Frame(self.marco, padding=(6, 6, 0, 0), width=ANCHO_PANEL_DERECHO)
        derecha.pack(side="right", fill="y")
        derecha.pack_propagate(False)
        izquierda.pack(side="left", fill="both", expand=True)
        self._construir_lista(izquierda)
        self._construir_abono(derecha)

    def al_mostrar(self):
        self.refrescar()                 # una venta a crédito en el punto de venta crea una cuenta nueva

    # ------------------------------------------------------------------ construcción
    def _construir_lista(self, padre):
        fila = ttk.Frame(padre)
        fila.pack(fill="x")
        self.etiqueta_resumen = ttk.Label(fila, text="", font=(FUENTE_TITULO[0], 13, "bold"))
        self.etiqueta_resumen.pack(side="left")
        self.ver_pagadas = tk.BooleanVar(value=False)
        ttk.Checkbutton(fila, text="Ver también las pagadas", variable=self.ver_pagadas,
                        command=self.refrescar).pack(side="right")
        self.tabla = crear_tabla(padre, "Cuentas por cobrar", COLUMNAS, alto=12)
        self.tabla.bind("<<TreeviewSelect>>", lambda _: self.mostrar_detalle())

    def _construir_abono(self, padre):
        caja = ttk.LabelFrame(padre, text="Registrar abono", padding=10)
        caja.pack(fill="both", expand=True)
        self.detalle = ttk.Label(caja, text=SIN_ELEGIR, style="Tenue.TLabel", wraplength=ANCHO_DEL_TEXTO,
                                 justify="left")
        self.detalle.pack(anchor="w")
        ttk.Label(caja, text="Monto del abono (pesos)").pack(anchor="w", pady=(14, 0))
        self.monto = tk.StringVar()
        campo = ttk.Entry(caja, textvariable=self.monto, font=FUENTE_NORMAL)
        campo.pack(fill="x")
        campo.bind("<Return>", lambda _: self.abonar())
        ttk.Button(caja, text="Registrar abono", style="Primario.TButton",
                   command=self.abonar).pack(fill="x", pady=(12, 0))
        self.mensaje = ttk.Label(caja, text="", wraplength=ANCHO_DEL_TEXTO, justify="left")
        self.mensaje.pack(anchor="w", pady=(8, 0))

    # ------------------------------------------------------------------ acciones
    def cuenta_elegida(self):
        elegida = self.tabla.selection()
        return int(elegida[0]) if elegida else None

    def refrescar(self):
        elegida = self.tabla.selection()
        llenar_tabla(self.tabla, self.pc.tabla(self.ver_pagadas.get()))
        if elegida and self.tabla.exists(elegida[0]):
            self.tabla.selection_set(elegida[0])        # se conserva la cuenta que estaba elegida
        self.etiqueta_resumen.config(text=self.pc.resumen())
        self.mostrar_detalle()

    def mostrar_detalle(self):
        cuenta = self.cuenta_elegida()
        texto = self.pc.detalle(cuenta) if cuenta is not None else ""
        self.detalle.config(text=texto or SIN_ELEGIR, style="TLabel" if texto else "Tenue.TLabel")

    def abonar(self):
        cuenta = self.cuenta_elegida()
        resultado = self.pc.abonar(cuenta, self.monto.get())
        if resultado.exito:
            self.monto.set("")                          # si falla, el monto queda para corregirlo
            self.refrescar()
            self.detalle.config(text=self.pc.detalle(cuenta), style="TLabel")   # aunque ya esté pagada
        self.mensaje.config(text=resultado.mensaje, foreground=COLOR_OK if resultado.exito else COLOR_ERROR)

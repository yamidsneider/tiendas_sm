"""Sección Ventas (RF-05; etapa 6 de la interfaz). Solo dibuja y reenvía al presentador.

A la izquierda las últimas ventas; a la derecha el ticket de la venta elegida, solo para leer.
No se anulan ventas (DT-08) ni hay totales o reportes (no aprobados).
"""
import tkinter as tk
from tkinter import ttk

from interfaz_tk.pantalla import Pantalla
from interfaz_tk.tema import PALETA, crear_tabla, llenar_tabla
from tiendas_sm.servicios import VENTAS_A_MOSTRAR

ANCHO_PANEL_DERECHO = 285
COLUMNAS = ("N.º", "Fecha", "Tipo", "Cliente", "Total")
ANCHOS = {"N.º": 45, "Fecha": 132, "Tipo": 70, "Total": 90}
FUENTE_DEL_TICKET = ("Consolas", 10)
SIN_ELEGIR = "Elige una venta de la lista para ver su ticket."


class PantallaVentas(Pantalla):
    def __init__(self, contenedor, presentador):
        super().__init__(contenedor)
        self.pv = presentador
        izquierda = ttk.Frame(self.marco, padding=(0, 6, 12, 0))
        derecha = ttk.Frame(self.marco, padding=(6, 6, 0, 0), width=ANCHO_PANEL_DERECHO)
        derecha.pack(side="right", fill="y")
        derecha.pack_propagate(False)
        izquierda.pack(side="left", fill="both", expand=True)
        self._construir_lista(izquierda)
        self._construir_ticket(derecha)

    def al_mostrar(self):
        self.refrescar()                 # las ventas nuevas del punto de venta aparecen al volver

    def _construir_lista(self, padre):
        ttk.Label(padre, text=f"Se muestran las últimas {VENTAS_A_MOSTRAR} ventas.", style="Tenue.TLabel").pack(
            anchor="w")
        self.tabla = crear_tabla(padre, "Ventas", COLUMNAS, alto=12, columna_principal="Cliente", anchos=ANCHOS)
        for columna in ("Fecha", "Tipo"):                   # son texto: a la izquierda
            self.tabla.column(columna, anchor="w")
        self.tabla.bind("<<TreeviewSelect>>", lambda _: self.mostrar_ticket())

    def _construir_ticket(self, padre):
        caja = ttk.LabelFrame(padre, text="Ticket", padding=6)
        caja.pack(fill="both", expand=True)
        self.ticket = tk.Text(caja, font=FUENTE_DEL_TICKET, width=1, height=1, wrap="word", relief="flat",
                              bg=PALETA["blanco"], fg=PALETA["tinta"], padx=8, pady=8)
        self.ticket.pack(fill="both", expand=True)
        self._escribir_ticket(SIN_ELEGIR)

    def refrescar(self):
        elegida = self.tabla.selection()
        llenar_tabla(self.tabla, self.pv.tabla())
        if elegida and self.tabla.exists(elegida[0]):
            self.tabla.selection_set(elegida[0])        # se conserva la venta que estaba elegida
        self.mostrar_ticket()

    def mostrar_ticket(self):
        elegida = self.tabla.selection()
        texto = self.pv.ticket(int(elegida[0])) if elegida else ""
        self._escribir_ticket(texto or SIN_ELEGIR)

    def _escribir_ticket(self, texto):
        """El cuadro queda en solo lectura: se habilita un momento para cambiar el texto."""
        self.ticket.config(state="normal")
        self.ticket.delete("1.0", "end")
        self.ticket.insert("1.0", texto)
        self.ticket.config(state="disabled")

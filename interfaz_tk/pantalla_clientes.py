"""Sección Clientes (HU-05, RF-07; etapa 2 de la interfaz). Solo dibuja y reenvía al presentador.

A la izquierda la lista con búsqueda; a la derecha el formulario «Nuevo cliente» y el detalle del cliente
elegido (crédito y cuentas pendientes). Los abonos se registran en la sección Créditos y abonos.
"""
import tkinter as tk
from tkinter import ttk

from interfaz_tk.pantalla import Pantalla
from interfaz_tk.tema import COLOR_ERROR, COLOR_OK, FUENTE_NORMAL, crear_tabla, llenar_tabla

ANCHO_PANEL_DERECHO = 280
ANCHO_DEL_TEXTO = ANCHO_PANEL_DERECHO - 30       # para que el texto largo baje de renglón dentro del panel
LIMITE_SIN_CREDITO = "0"
ANCHO_MINIMO_DE_CAMPO = 8                        # letras; el campo se estira hasta llenar el panel
COLUMNAS = ("Cliente", "Límite", "Debe", "Disponible")


class PantallaClientes(Pantalla):
    def __init__(self, contenedor, presentador):
        super().__init__(contenedor)
        self.pc = presentador
        izquierda = ttk.Frame(self.marco, padding=(0, 6, 12, 0))
        derecha = ttk.Frame(self.marco, padding=(6, 6, 0, 0), width=ANCHO_PANEL_DERECHO)
        derecha.pack(side="right", fill="y")
        derecha.pack_propagate(False)
        izquierda.pack(side="left", fill="both", expand=True)
        self._construir_lista(izquierda)
        self._construir_formulario(derecha)
        self._construir_detalle(derecha)

    def al_mostrar(self):
        self.refrescar()                 # una venta a crédito en el punto de venta cambia la deuda

    # ------------------------------------------------------------------ construcción
    def _construir_lista(self, padre):
        fila = ttk.Frame(padre)
        fila.pack(fill="x")
        ttk.Label(fila, text="Buscar cliente:").pack(side="left")
        self.busqueda = tk.StringVar()
        ttk.Entry(fila, textvariable=self.busqueda, width=24, font=FUENTE_NORMAL).pack(side="left", padx=6)
        self.busqueda.trace_add("write", lambda *_: self.refrescar())
        self.tabla = crear_tabla(padre, "Clientes", COLUMNAS, alto=12)
        self.tabla.bind("<<TreeviewSelect>>", lambda _: self.mostrar_detalle())

    def _construir_formulario(self, padre):
        caja = ttk.LabelFrame(padre, text="Nuevo cliente", padding=10)
        caja.pack(fill="x")
        self.nombres, self.limite = tk.StringVar(), tk.StringVar()
        self.plazo = tk.StringVar(value=self.pc.plazo_por_defecto())
        self.credito = tk.BooleanVar(value=True)
        self._campo(caja, "Nombre", self.nombres)
        ttk.Checkbutton(caja, text="Crédito habilitado", variable=self.credito,
                        command=self.cambiar_credito).pack(anchor="w", pady=(8, 0))
        fila = ttk.Frame(caja)                              # límite y plazo lado a lado: cabe en 600 px de alto
        fila.pack(fill="x")
        izquierda, derecha = ttk.Frame(fila), ttk.Frame(fila)
        izquierda.pack(side="left", fill="x", expand=True, padx=(0, 6))
        derecha.pack(side="left", fill="x", expand=True)
        self.campo_limite = self._campo(izquierda, "Límite (pesos)", self.limite)
        self._campo(derecha, "Plazo (días)", self.plazo)
        ttk.Button(caja, text="Guardar cliente", style="Primario.TButton",
                   command=self.guardar).pack(fill="x", pady=(12, 0))
        self.mensaje = ttk.Label(caja, text="", wraplength=ANCHO_DEL_TEXTO, justify="left")
        self.mensaje.pack(anchor="w", pady=(6, 0))

    def _campo(self, padre, titulo, variable):
        ttk.Label(padre, text=titulo).pack(anchor="w", pady=(6, 0))
        campo = ttk.Entry(padre, textvariable=variable, font=FUENTE_NORMAL, width=ANCHO_MINIMO_DE_CAMPO)
        campo.pack(fill="x")
        campo.bind("<Return>", lambda _: self.guardar())
        return campo

    def _construir_detalle(self, padre):
        caja = ttk.LabelFrame(padre, text="Detalle del cliente", padding=10)
        caja.pack(fill="both", expand=True, pady=(10, 0))
        self.detalle = ttk.Label(caja, text="Elige un cliente de la lista", style="Tenue.TLabel",
                                 wraplength=ANCHO_DEL_TEXTO, justify="left")
        self.detalle.pack(anchor="nw")

    # ------------------------------------------------------------------ acciones
    def refrescar(self):
        elegido = self.tabla.selection()
        llenar_tabla(self.tabla, self.pc.tabla(self.busqueda.get()))
        if elegido and self.tabla.exists(elegido[0]):
            self.tabla.selection_set(elegido[0])         # se conserva el cliente que estaba elegido
        self.mostrar_detalle()

    def mostrar_detalle(self):
        elegido = self.tabla.selection()
        texto = self.pc.detalle(int(elegido[0])) if elegido else ""
        self.detalle.config(text=texto or "Elige un cliente de la lista",
                            style="TLabel" if texto else "Tenue.TLabel")

    def cambiar_credito(self):
        """Sin crédito no hay límite que escribir: queda en 0, como en los datos de ejemplo."""
        if self.credito.get():
            self.campo_limite.config(state="normal")
            self.limite.set("")
        else:
            self.limite.set(LIMITE_SIN_CREDITO)
            self.campo_limite.config(state="disabled")

    def guardar(self):
        resultado = self.pc.registrar(self.nombres.get(), self.credito.get(), self.limite.get(), self.plazo.get())
        self.mensaje.config(text=resultado.mensaje, foreground=COLOR_OK if resultado.exito else COLOR_ERROR)
        if resultado.exito:
            self.nombres.set("")
            self.credito.set(True)
            self.cambiar_credito()
            self.plazo.set(self.pc.plazo_por_defecto())
            self.refrescar()

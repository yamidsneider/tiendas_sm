"""Ventana principal de TIENDAS S.M: menú lateral verde y una sección a la vez (opción A, borrador HTML).

Solo tiene las 6 secciones aprobadas. Lotes, alertas, configuración y tablero esperan al propietario;
proveedores, pedidos y caja son CR-02 (Won't Have) y no aparecen. Cada sección se crea la primera vez que
se abre y después solo se oculta: así la venta en curso no se pierde al cambiar de sección.
"""
import tkinter as tk
from tkinter import ttk

from interfaz_tk.pantalla import Pantalla
from interfaz_tk.pantalla_clientes import PantallaClientes
from interfaz_tk.tema import FUENTE_MENU, LETRA, PALETA, aplicar_tema
from interfaz_tk.ventana_punto_de_venta import VentanaPuntoDeVenta
from tiendas_sm.presentador import PresentadorPuntoDeVenta
from tiendas_sm.presentador_clientes import PresentadorDeClientes

TITULO = "TIENDAS S.M"
ANCHO_MINIMO, ALTO_MINIMO = 1024, 600          # DDS §9.2
ANCHO_DEL_MENU = 210
SECCIONES = ("Punto de venta", "Ventas", "Productos", "Existencias", "Clientes", "Créditos y abonos")


class VentanaPrincipal:
    def __init__(self, raiz, app):
        self.raiz = raiz
        self.app = app
        self.pantallas = {}
        self.seccion_actual = None
        raiz.title(TITULO)
        raiz.minsize(ANCHO_MINIMO, ALTO_MINIMO)
        aplicar_tema(raiz)
        self._construir_menu()
        self._construir_contenido()
        self.mostrar(SECCIONES[0])

    def _construir_menu(self):
        p = PALETA
        menu = tk.Frame(self.raiz, bg=p["v900"], width=ANCHO_DEL_MENU)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)                  # el menú conserva su ancho aunque los textos sean cortos
        tk.Label(menu, text=TITULO, bg=p["v900"], fg=p["blanco"], font=(LETRA, 16, "bold"),
                 anchor="w").pack(fill="x", padx=18, pady=(18, 0))
        tk.Label(menu, text="Inventario, ventas y créditos", bg=p["v900"], fg=p["v300"], font=(LETRA, 9),
                 anchor="w").pack(fill="x", padx=18, pady=(0, 16))
        self.botones = {}
        for seccion in SECCIONES:
            boton = tk.Button(menu, text=seccion, anchor="w", relief="flat", bd=0, cursor="hand2", padx=18, pady=9,
                              font=FUENTE_MENU, bg=p["v900"], fg=p["blanco"], activebackground=p["v700"],
                              activeforeground=p["blanco"], command=lambda s=seccion: self.mostrar(s))
            boton.pack(fill="x")
            self.botones[seccion] = boton

    def _construir_contenido(self):
        contenido = ttk.Frame(self.raiz, padding=(20, 14))
        contenido.pack(side="left", fill="both", expand=True)
        self.titulo = ttk.Label(contenido, text="", style="Titulo.TLabel")
        self.titulo.pack(anchor="w")
        self.area = ttk.Frame(contenido)
        self.area.pack(fill="both", expand=True, pady=(6, 0))

    def mostrar(self, seccion):
        """Oculta la sección actual, muestra la elegida y marca su botón en el menú."""
        if self.seccion_actual is not None:
            self.pantallas[self.seccion_actual].ocultar()
            self.botones[self.seccion_actual].config(bg=PALETA["v900"])
        if seccion not in self.pantallas:
            self.pantallas[seccion] = self._crear_pantalla(seccion)
        self.pantallas[seccion].mostrar()
        self.botones[seccion].config(bg=PALETA["v600"])
        self.titulo.config(text=seccion)
        self.seccion_actual = seccion

    def _crear_pantalla(self, seccion):
        if seccion == "Punto de venta":
            return VentanaPuntoDeVenta(self.raiz, PresentadorPuntoDeVenta(self.app), contenedor=self.area)
        if seccion == "Clientes":
            return PantallaClientes(self.area, PresentadorDeClientes(self.app))
        return PantallaPendiente(self.area, seccion)


class PantallaPendiente(Pantalla):
    """Lugar reservado para las secciones de las etapas 2 a 6 mientras se construyen."""

    def __init__(self, contenedor, seccion):
        super().__init__(contenedor)
        self.aviso = ttk.Label(self.marco, text=f"Próximamente: la sección {seccion} se construye en la "
                                                "siguiente etapa.", style="Tenue.TLabel")
        self.aviso.pack(anchor="w", pady=20)

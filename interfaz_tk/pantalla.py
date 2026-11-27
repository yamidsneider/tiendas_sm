"""Lo común a cada sección del menú: un marco que se muestra u oculta y si está activa (en pantalla).

Las teclas rápidas se enlazan a la ventana entera; con _si_activa una tecla solo actúa cuando su sección
está a la vista. Así F9 no cobra una venta mientras el usuario está en Clientes.
"""
from tkinter import ttk


class Pantalla:
    def __init__(self, contenedor):
        self.marco = ttk.Frame(contenedor)
        self.activa = False

    def mostrar(self):
        self.marco.pack(fill="both", expand=True)
        self.activa = True
        self.al_mostrar()

    def ocultar(self):
        self.marco.pack_forget()
        self.activa = False

    def al_mostrar(self):
        """Cada sección la redefine si necesita refrescar datos al volver a ella."""

    def _si_activa(self, accion):
        def solo_si_esta_a_la_vista(*_evento):
            if self.activa:
                return accion()
            return None
        return solo_si_esta_a_la_vista

"""Tema visual de TIENDAS S.M: la paleta y la letra del borrador HTML del desarrollador (opción A).

Solo define colores, letras y estilos de ttk; no tiene lógica del negocio. Se usa el tema base «clam»
porque el tema nativo de Windows ignora los colores de fondo de botones y tablas.
También trae dos ayudantes para las tablas, que comparten todas las pantallas.
"""
from tkinter import font as tkfont
from tkinter import ttk

PALETA = {
    "v900": "#0a3b2a", "v800": "#0f5a3f", "v700": "#157a50", "v600": "#1f9d63", "v500": "#2fbf7a",
    "v300": "#9af0c4", "v100": "#e3f6ec", "v50": "#f2f9f5",
    "fondo": "#eef5f1", "tinta": "#12332a", "tenue": "#5d786d", "linea": "#dbe8e1", "blanco": "#ffffff",
    "ambar": "#e08a00", "ambar_f": "#fff3d9", "rojo": "#d64545", "rojo_f": "#fde7e7",
    "azul": "#1f78a8", "azul_f": "#e2f2fa",
}
LETRA = "Segoe UI"
FUENTE_NORMAL = (LETRA, 11)
FUENTE_PEQUENA = (LETRA, 9)
FUENTE_NEGRITA = (LETRA, 11, "bold")
FUENTE_MENU = (LETRA, 12)
FUENTE_TITULO = (LETRA, 18, "bold")
FUENTE_TOTAL = (LETRA, 28, "bold")
FUENTE_TICKET = ("Consolas", 11)
COLOR_ERROR, COLOR_OK = PALETA["rojo"], PALETA["v700"]
ESPACIO_EXTRA_DE_FILA = 10                      # píxeles sobre el alto de la letra: no se cortan la g ni la p
ANCHO_COLUMNA_PRINCIPAL, ANCHO_COLUMNA = 110, 104   # caben 5 columnas a 1024 px; si sobra espacio, se estiran
COLOR_DESACTIVADO = "#a9cbb9"


def aplicar_tema(raiz):
    """Configura los estilos una sola vez para toda la aplicación y devuelve el objeto Style."""
    p = PALETA
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    raiz.configure(bg=p["fondo"])
    estilo.configure(".", font=FUENTE_NORMAL, background=p["fondo"], foreground=p["tinta"],
                     bordercolor=p["linea"], lightcolor=p["blanco"], darkcolor=p["linea"])
    _estilos_de_texto(estilo, p)
    _estilos_de_botones(estilo, p)
    _estilos_de_campos(estilo, p)
    _estilos_de_tablas(estilo, p)
    return estilo


def _estilos_de_texto(estilo, p):
    estilo.configure("Tarjeta.TFrame", background=p["blanco"], relief="solid", borderwidth=1)
    estilo.configure("Tarjeta.TLabel", background=p["blanco"])
    estilo.configure("Titulo.TLabel", font=FUENTE_TITULO, foreground=p["v900"])
    estilo.configure("Tenue.TLabel", foreground=p["tenue"])
    estilo.configure("TarjetaTenue.TLabel", background=p["blanco"], foreground=p["tenue"])
    estilo.configure("Total.TLabel", background=p["blanco"], foreground=p["v800"], font=FUENTE_TOTAL)
    estilo.configure("TLabelframe", background=p["fondo"], relief="solid", borderwidth=1)
    estilo.configure("TLabelframe.Label", background=p["fondo"], foreground=p["v800"], font=FUENTE_NEGRITA)


def _estilos_de_botones(estilo, p):
    estilo.configure("TButton", padding=(12, 6), background=p["blanco"])
    estilo.map("TButton", background=[("disabled", p["fondo"]), ("active", p["v100"])],
               foreground=[("disabled", p["tenue"])])
    for nombre, color, color_activo in (("Primario", p["v600"], p["v700"]), ("Credito", p["azul"], p["v900"])):
        estilo.configure(f"{nombre}.TButton", background=color, foreground=p["blanco"], font=(LETRA, 12, "bold"),
                         bordercolor=color)
        estilo.map(f"{nombre}.TButton", background=[("disabled", COLOR_DESACTIVADO), ("active", color_activo)],
                   foreground=[("disabled", p["fondo"])])


def _estilos_de_campos(estilo, p):
    for campo in ("TEntry", "TCombobox", "TSpinbox"):
        estilo.configure(campo, fieldbackground=p["blanco"], padding=4)
        estilo.map(campo, bordercolor=[("focus", p["v500"])], lightcolor=[("focus", p["v500"])])
    estilo.configure("TCheckbutton", background=p["fondo"])


def _estilos_de_tablas(estilo, p):
    alto_de_letra = tkfont.Font(font=FUENTE_NORMAL).metrics("linespace")
    estilo.configure("Treeview", background=p["blanco"], fieldbackground=p["blanco"], foreground=p["tinta"],
                     rowheight=alto_de_letra + ESPACIO_EXTRA_DE_FILA, borderwidth=0)
    estilo.map("Treeview", background=[("selected", p["v500"])], foreground=[("selected", p["blanco"])])
    estilo.configure("Treeview.Heading", background=p["v800"], foreground=p["blanco"], font=FUENTE_NEGRITA,
                     relief="flat", padding=(6, 6))
    estilo.map("Treeview.Heading", background=[("active", p["v700"])])


def crear_tabla(padre, titulo, columnas, alto, columna_principal=None):
    """Tabla con encabezado verde y filas alternadas, dentro de un marco con título.

    La columna principal (por defecto la primera) va alineada a la izquierda y más ancha; las demás, a la
    derecha, porque casi siempre son números o pesos.
    """
    principal = columna_principal or columnas[0]
    marco = ttk.LabelFrame(padre, text=titulo, padding=6)
    marco.pack(fill="both", expand=True, pady=(10, 0))
    tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=alto, selectmode="browse")
    for columna in columnas:
        es_principal = columna == principal
        tabla.heading(columna, text=columna)
        tabla.column(columna, anchor="w" if es_principal else "e", stretch=es_principal,   # el espacio que sobra
                     width=ANCHO_COLUMNA_PRINCIPAL if es_principal else ANCHO_COLUMNA)   # va al nombre
    tabla.tag_configure("par", background=PALETA["v50"])
    tabla.pack(fill="both", expand=True)
    return tabla


def llenar_tabla(tabla, filas):
    """Reemplaza el contenido: cada fila es (iid, valores). Las filas pares se colorean para leer mejor."""
    tabla.delete(*tabla.get_children())
    for numero, (iid, valores) in enumerate(filas):
        tabla.insert("", "end", iid=str(iid), values=valores, tags=("par",) if numero % 2 else ())

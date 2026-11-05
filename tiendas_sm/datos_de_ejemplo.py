"""Datos de ejemplo FICTICIOS para probar la interfaz y medir el escenario E-01 (tarea 8).

Solo se cargan si la base está vacía (sin productos ni clientes), así nunca se mezclan con datos reales.
Usan los servicios de Aplicacion, por lo que pasan por las mismas validaciones del dominio.
"""
PRODUCTOS_DE_EJEMPLO = (            # nombre, precio de compra, precio de venta, cantidad inicial
    ("Arroz 500 g", 2000, 2500, 30),
    ("Aceite 1 L", 7500, 9800, 12),
    ("Panela 500 g", 2200, 3000, 20),
    ("Huevos x 12", 9000, 11500, 10),
    ("Leche 1 L", 3200, 4200, 24),
    ("Pan tajado", 4000, 5500, 8),
    ("Café 250 g", 8500, 11000, 6),
    ("Azúcar 1 kg", 3800, 4900, 15),
)
CLIENTES_DE_EJEMPLO = (             # nombre, crédito habilitado, límite, plazo en días
    ("Cliente de ejemplo 1", True, 100000, 15),
    ("Cliente de ejemplo 2", True, 50000, 30),
    ("Cliente de ejemplo 3 (sin crédito)", False, 0, 30),
)


def cargar_datos_de_ejemplo(app):
    """Devuelve True si cargó los datos; False si la base ya tenía productos o clientes."""
    if app.productos.listar() or app.clientes.listar():
        return False
    for nombre, compra, venta, cantidad in PRODUCTOS_DE_EJEMPLO:
        app.productos.registrar_producto(nombre, compra, venta, cantidad)
    for nombre, credito, limite, plazo in CLIENTES_DE_EJEMPLO:
        app.clientes.registrar_cliente(nombre, credito, limite, plazo_credito_dias=plazo)
    return True

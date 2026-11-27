"""Presentador de la sección Compras (fase 8 de docs/HOJA_DE_RUTA_APP_COMPLETA.md; solo el jefe).

No usa ninguna interfaz. Convierte lo que se escribe en el formulario (texto) en números y llama a ServicioDeCompras.
Un renglón de la compra totalmente vacío se ignora (la pantalla deja renglones de sobra). Las reglas las valida el
dominio y su mensaje se muestra tal cual.
"""
from tiendas_sm.presentador import Resultado, a_entero, formato_pesos

FORMATO_FECHA_Y_HORA = "%d/%m/%Y %H:%M"
SIN_FACTURA = "—"


def _plural(cantidad, singular, plural):
    return f"{cantidad} {singular if cantidad == 1 else plural}"


def _id(texto):
    try:
        return int(str(texto).strip())
    except ValueError:
        return None


class PresentadorDeCompras:
    def __init__(self, app):
        self.app = app

    # ------------------------------------------------------------------ proveedores
    def proveedores(self):
        """Filas (id, (nombre, teléfono, NIT))."""
        return [(p.id_proveedor, (p.nombre, p.telefono, p.nit)) for p in self.app.compras.listar_proveedores()]

    def registrar_proveedor(self, nombre, telefono, nit):
        try:
            proveedor = self.app.compras.registrar_proveedor(nombre, telefono, nit)
        except ValueError as error:
            return Resultado(False, str(error))
        return Resultado(True, f"Proveedor registrado: {proveedor.nombre}")

    # ------------------------------------------------------------------ compras
    def registrar(self, id_proveedor_texto, factura, renglones, quien):
        """renglones: [{producto, cantidad, costo}] como texto. Los totalmente vacíos no cuentan."""
        try:
            lineas = [(_id(r.get("producto")), a_entero(r.get("cantidad", ""), "La cantidad"),
                       a_entero(r.get("costo", ""), "El costo"))
                      for r in renglones if any(str(r.get(campo, "")).strip() for campo in ("producto", "cantidad", "costo"))]
            compra = self.app.compras.registrar_compra(_id(id_proveedor_texto), lineas, quien.id_usuario, factura)
        except ValueError as error:
            return Resultado(False, str(error))
        proveedor = self.app.compras.obtener_proveedor(compra.id_proveedor)
        return Resultado(True, f"Compra #{compra.id_compra} a {proveedor.nombre} registrada por "
                               f"{formato_pesos(compra.total())}")

    def compras(self):
        """Filas (id, (fecha, proveedor, factura, cuántos productos, total)), de la más reciente a la más vieja."""
        nombres = {p.id_proveedor: p.nombre for p in self.app.compras.listar_proveedores()}
        return [(c.id_compra, (f"{c.fecha:{FORMATO_FECHA_Y_HORA}}", nombres.get(c.id_proveedor, ""),
                               c.factura or SIN_FACTURA, _plural(len(c.lineas), "producto", "productos"),
                               formato_pesos(c.total())))
                for c in self.app.compras.listar_compras()]

    def detalle(self, id_compra):
        compra = self.app.compras.obtener_compra(id_compra)
        if compra is None:
            return ""
        proveedor = self.app.compras.obtener_proveedor(compra.id_proveedor)
        lineas = [f"Compra #{compra.id_compra} · {proveedor.nombre}", f"Fecha: {compra.fecha:{FORMATO_FECHA_Y_HORA}}",
                  f"Factura del proveedor: {compra.factura or SIN_FACTURA}", ""]
        for linea in compra.lineas:
            nombre = self.app.productos.obtener(linea.id_producto).nombre
            lineas.append(f"{linea.cantidad} x {nombre} a {formato_pesos(linea.costo_unitario)} = "
                          f"{formato_pesos(linea.cantidad * linea.costo_unitario)}")
        return "\n".join(lineas + ["", f"TOTAL: {formato_pesos(compra.total())}"])

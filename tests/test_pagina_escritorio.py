"""Pruebas de la página de la app de escritorio (opción B en DECISIONES).

La página se arma juntando index.html, app.css y app.js en un solo texto que pywebview muestra; así no hace
falta ningún servidor ni puerto. Aquí se revisa lo que se puede revisar sin abrir la ventana: que se arme
completa, que no cargue nada de internet, que no tenga emojis y que la API que llama exista en Python.
"""
import re
import unittest

from interfaz_web.api import ApiDeLaTienda
from interfaz_web.pagina import CARPETA_ESTATICA, armar_pagina
from tiendas_sm.aplicacion import Aplicacion

# Reportes, Usuarios y Caja: fases 1, 2 y 4 de docs/HOJA_DE_RUTA_APP_COMPLETA.md (aprobadas por el desarrollador, nov. 2026).
SECCIONES_APROBADAS = ("Punto de venta", "Ventas", "Caja", "Productos", "Existencias", "Clientes", "Créditos y abonos",
                       "Reportes", "Respaldos", "Tienda", "Usuarios")


class PruebasDeLaPagina(unittest.TestCase):
    def setUp(self):
        self.pagina = armar_pagina()
        self.codigo = (CARPETA_ESTATICA / "app.js").read_text(encoding="utf-8")

    def test_la_pagina_lleva_dentro_los_estilos_y_el_codigo(self):
        self.assertIn(".lateral{", self.pagina)
        self.assertIn("window.pywebview.api", self.pagina)
        self.assertNotIn("/*ESTILOS*/", self.pagina)
        self.assertNotIn("/*CODIGO*/", self.pagina)

    def test_no_carga_nada_de_internet(self):
        self.assertIsNone(re.search(r"(src|href)\s*=\s*[\"']?https?:", self.pagina))
        self.assertNotIn("@import", self.pagina)

    def test_el_codigo_no_cierra_la_etiqueta_script_antes_de_tiempo(self):
        self.assertNotIn("</script", self.codigo)

    def test_sin_emojis(self):
        self.assertEqual([c for c in self.pagina if ord(c) >= 0x1F000], [])

    def test_el_menu_tiene_solo_las_secciones_aprobadas(self):
        titulos = re.findall(r"titulo: '([^']+)'", self.codigo)
        self.assertEqual(tuple(titulos), SECCIONES_APROBADAS)

    def test_el_ticket_se_puede_imprimir_solo(self):
        """Botón «Imprimir» en la ventana del ticket; al imprimir se ocultan el menú y la sección: sale solo el ticket."""
        self.assertIn("imprimir: () => window.print()", self.codigo)
        self.assertIn("texto: 'Imprimir'", self.codigo)
        impresion = self.pagina[self.pagina.index("@media print"):]
        for oculto in (".lateral", ".principal", ".modal-pie"):
            self.assertIn(oculto, impresion[:impresion.index("}")])

    def test_cada_metodo_que_llama_la_pagina_existe_en_la_api(self):
        llamados = set(re.findall(r"llamar\('(\w+)'", self.codigo))
        self.assertGreaterEqual(len(llamados), 20)
        api = ApiDeLaTienda(Aplicacion())
        self.assertEqual([m for m in sorted(llamados) if not callable(getattr(api, m, None))], [])


if __name__ == "__main__":
    unittest.main()

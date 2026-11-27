"""Ícono de TIENDAS_SM.exe: generado con la biblioteca estándar (scripts/generar_icono.py). Sin ventanas."""
import struct
import unittest

from construir_exe import ICONO, OPCIONES, _texto_para_powershell
from scripts.generar_icono import DESTINO, TAMANOS, crear_png

FIRMA_PNG = b"\x89PNG\r\n\x1a\n"


class PruebasDelIcono(unittest.TestCase):
    def test_el_png_tiene_la_firma_y_el_tamano_pedido(self):
        imagen = crear_png(16)
        self.assertTrue(imagen.startswith(FIRMA_PNG))
        self.assertEqual(struct.unpack(">II", imagen[16:24]), (16, 16))

    def test_el_ico_guardado_trae_los_4_tamanos_en_png(self):
        datos = DESTINO.read_bytes()
        reservado, tipo, cantidad = struct.unpack("<HHH", datos[:6])
        self.assertEqual((reservado, tipo, cantidad), (0, 1, len(TAMANOS)))
        lados = []
        for i in range(cantidad):
            ancho, _, _, _, _, _, largo, posicion = struct.unpack("<BBBBHHII", datos[6 + 16 * i: 22 + 16 * i])
            lados.append(ancho or 256)
            self.assertTrue(datos[posicion:posicion + largo].startswith(FIRMA_PNG))
        self.assertEqual(tuple(lados), TAMANOS)

    def test_el_exe_usa_el_icono(self):
        self.assertIn(f"--icon={ICONO}", OPCIONES)
        self.assertEqual(DESTINO.name, ICONO.name)

    def test_las_comillas_de_la_ruta_no_rompen_la_orden_de_powershell(self):
        self.assertEqual(_texto_para_powershell(r"C:\Tienda de D'Ana\TIENDAS_SM.exe"), r"C:\Tienda de D''Ana\TIENDAS_SM.exe")


if __name__ == "__main__":
    unittest.main()

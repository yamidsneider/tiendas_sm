"""Pruebas del healthcheck de la entrega continua (tarea 10, FPI-27, ADR-11).

scripts/healthcheck_paquete.py revisa el .zip publicado: integridad (SHA-256), que traiga tiendas_sm y que el
sistema arranque y registre una venta de humo, incluido su movimiento SALIDA_VENTA (TD-01). Aquí se arma el
paquete con zipfile (igual que git archive, solo la carpeta tiendas_sm) en una carpeta temporal. No abre Tkinter.
"""
import hashlib
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "scripts" / "healthcheck_paquete.py"
CODIGO_OK, CODIGO_FALLA = 0, 1


def armar_paquete(destino):
    with zipfile.ZipFile(destino, "w") as paquete:
        for archivo in (RAIZ / "tiendas_sm").glob("*.py"):
            paquete.write(archivo, f"tiendas_sm/{archivo.name}")


class PruebasDelHealthcheck(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.paquete = Path(self.carpeta.name) / "tiendas_sm-v0.0.0.zip"
        armar_paquete(self.paquete)

    def tearDown(self):
        self.carpeta.cleanup()

    def ejecutar(self, *argumentos):
        # S603: se ejecuta el mismo Python con un script del repositorio y rutas de esta prueba.
        return subprocess.run([sys.executable, str(SCRIPT), *argumentos],  # noqa: S603
                              capture_output=True, text=True, timeout=120)

    def guardar_suma(self, contenido_suma):
        ruta = Path(self.carpeta.name) / "paquete.sha256"
        ruta.write_text(f"{contenido_suma}  {self.paquete.name}\n", encoding="utf-8")
        return ruta

    def test_paquete_sano_con_su_suma_sale_ok_y_revisa_el_movimiento_de_venta(self):
        suma = self.guardar_suma(hashlib.sha256(self.paquete.read_bytes()).hexdigest())
        resultado = self.ejecutar("--paquete", str(self.paquete), "--sha256", str(suma))
        self.assertEqual(resultado.returncode, CODIGO_OK, resultado.stdout + resultado.stderr)
        self.assertIn("HEALTHCHECK OK", resultado.stdout)
        self.assertIn("SALIDA_VENTA", resultado.stdout)

    def test_suma_que_no_coincide_falla(self):
        suma = self.guardar_suma("0" * 64)
        resultado = self.ejecutar("--paquete", str(self.paquete), "--sha256", str(suma))
        self.assertEqual(resultado.returncode, CODIGO_FALLA)
        self.assertIn("la suma SHA-256 no coincide", resultado.stdout)

    def test_paquete_danado_falla(self):
        self.paquete.write_bytes(self.paquete.read_bytes()[:100])          # .zip cortado: ya no es válido
        resultado = self.ejecutar("--paquete", str(self.paquete))
        self.assertEqual(resultado.returncode, CODIGO_FALLA)
        self.assertIn("HEALTHCHECK FALLÓ", resultado.stdout)

    def test_paquete_sin_tiendas_sm_falla(self):
        with zipfile.ZipFile(self.paquete, "w") as vacio:
            vacio.writestr("LEEME.txt", "sin código")
        resultado = self.ejecutar("--paquete", str(self.paquete))
        self.assertEqual(resultado.returncode, CODIGO_FALLA)
        self.assertIn("no contiene tiendas_sm/aplicacion.py", resultado.stdout)


if __name__ == "__main__":
    unittest.main()

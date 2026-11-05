# BUG-01 — Ids que no existen provocan un error confuso (antes DT-06)

| Campo | Valor |
| --- | --- |
| Severidad / prioridad | Media / media |
| Detectado en | Revisión de código del PR 1 (FPI-13) |
| Historias afectadas | HU-02, HU-03, HU-06 |
| Estado | Cerrado cuando el PR se fusione con el pipeline en verde |

## Pasos para reproducir
1. Crear la aplicación: `from tiendas_sm.aplicacion import Aplicacion; app = Aplicacion()`
2. Sin registrar ningún producto, ejecutar `app.productos.registrar_entrada(999, 5)`.
3. Repetir con `app.productos.actualizar_precio(999, 100)` y con `app.credito.registrar_abono(999, 100)`.

## Resultado esperado
Un error claro de negocio (`ValueError`) que diga qué no existe, sin guardar nada.

## Resultado obtenido
`AttributeError: 'NoneType' object has no attribute 'aumentar'` (y `'actualizar_precio'`, `'aplicar_pago'`):
el programa falla por un detalle interno y el mensaje no le sirve al usuario.

## Entorno
Python 3.12.3, Linux, SQLite 3.45.1, rama `main` después de la FPI-14.

## Causa y corrección
`obtener_existencia`, `obtener` y `obtener_cuenta` devuelven `None` cuando el id no existe y el servicio no lo comprobaba.
Se agrega la comprobación en `ServicioDeProductos.registrar_entrada`, `ServicioDeProductos.actualizar_precio` y
`ControlCredito.registrar_abono`.

## Pruebas de regresión
`tests/test_defectos_corregidos.py::PruebasBug01IdsInexistentes` (6 pruebas). Antes de la corrección: 6 errores; después: 6 OK.

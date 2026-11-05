# BUG-02 — El vencimiento del crédito ignora el plazo del cliente (antes DT-02)

| Campo | Valor |
| --- | --- |
| Severidad / prioridad | Alta / alta (se cobra en una fecha equivocada) |
| Detectado en | Auditoría de código de la FPI-12 |
| Historias afectadas | CU-01, RF-08 |
| Estado | Cerrado cuando el PR se fusione con el pipeline en verde |

## Pasos para reproducir
1. Registrar un cliente con crédito y plazo propio: `registrar_cliente("Cliente de prueba", True, 100000, plazo_credito_dias=15)`.
2. Registrar un producto con existencias y venderle uno a crédito.
3. Consultar la cuenta: `app.credito.cuentas_del_cliente(id)[0]` y restar `fecha_vencimiento - fecha_apertura`.

## Resultado esperado
15 días (el plazo del cliente).

## Resultado obtenido
30 días, siempre, sin importar el plazo del cliente.

## Entorno
Python 3.12.3, Linux, SQLite 3.45.1, rama `main` después de la FPI-14.

## Causa y corrección
`ControlCredito.crear_cuenta` usaba la constante `PLAZO_POR_DEFECTO_DIAS`. Ahora recibe el plazo (por defecto 30) y
`ServicioDeVentas` le pasa `cliente.plazo_credito_dias`.

## Pruebas de regresión
`tests/test_defectos_corregidos.py::PruebasBug02PlazoDelCredito` (3 pruebas) y `test_bug02_el_vencimiento_usa_el_plazo_del_cliente`.
Antes de la corrección: 2 fallas (30 ≠ 15 y 30 ≠ 45); después: todas OK. La prueba que estaba marcada como falla esperada se
convirtió en una prueba normal.

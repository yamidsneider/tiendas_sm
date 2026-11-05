# Decisiones por fase (FPI-01 a FPI-16)

| Ficha | Decisión clave | Estado |
| --- | --- | --- |
| FPI-01 | Definir TIENDAS S.M como MVP de inventario, ventas y créditos con 14 funcionalidades iniciales | Vigente |
| FPI-02 | Modelo de ciclo de vida **Incremental** con 4 incrementos | Incrementos 1 a 3 en código; el 4 pendiente |
| FPI-03 | Kanban con límites de WIP, Sprints de 1 semana, Definition of Done y backlog inicial; tablero en GitHub Projects (`github.com/users/yamidsneider/projects/1`) | Vigente |
| FPI-04 | Stakeholders con las 5 categorías de Pressman; el cliente de la tienda es actor indirecto; entrevista y observación en tienda | **Trabajo de campo pendiente** |
| FPI-05 | Catálogo de 13 RF, 5 RNF y 5 restricciones, con métricas propuestas | Vigente, sin validar |
| FPI-06 | 9 historias con criterios Gherkin y el caso de uso CU-01 | Vigente |
| FPI-07 | MoSCoW: Must HU-01..06 y CU-01; Should HU-07 y HU-08; Could HU-09; Won't ideas no aprobadas | Vigente |
| FPI-08 | Revisión técnica: 5 hallazgos; CR-01 aplazada; matriz de trazabilidad | Vigente |
| FPI-09 | Modelo de dominio de 29 entidades; CR-02 sin aprobar | Adoptado |
| FPI-10 | UML selectivo: solo CU-01 (8 clases + secuencia). Tipos genéricos | Implementado |
| FPI-11 | SOLID donde hay riesgo: `ControlInventario`, `ControlCredito` y la interfaz `RepositorioDeVentas` | Implementado |
| FPI-12 | **Python + SQLite + Tkinter**, dinero entero, refactor de 8 code smells, deuda DT-01..DT-05 | Tkinter pendiente |
| FPI-13 | GitHub Flow, `main` protegida, commits atómicos, conflicto simulado, release v0.1.0 | Evidencia en GitHub por confirmar |
| FPI-14 | Pruebas unitarias con stubs/mocks, caja negra, integración ascendente, cobertura | Implementado |
| FPI-15 | CI con GitHub Actions, regresión, BUG-01 y BUG-02 corregidos | Pipeline verde por confirmar |
| FPI-16 | Demo, retrospectiva cuantitativa, bitácora de IA y hoja de ruta hacia IS II | En cierre |

## Decisiones técnicas que no deben revertirse sin explicar por qué
- Solo biblioteca estándar (sin dependencias externas) en el MVP. Única herramienta externa: `ruff`, solo en el CI.
- Dinero como enteros en pesos. Fechas como texto ISO en SQLite.
- Existencias sin `Lote` en el MVP (DT-01): `Existencia` se liga directamente al producto.
- Los abonos son una tabla simple (DT-03), no el modelo Pago/AplicacionPago del modelo de 29 entidades.
- `guardar_transaccion` recibe también las existencias para que descontar el inventario sea parte de la misma transacción.
- Los repositorios de productos y clientes son clases concretas; solo `RepositorioDeVentas` es una abstracción.
- **Venta de contado (UC-02, noviembre de 2026).** Firma `registrar_venta_de_contado(lineas, recibido)`, sin el parámetro
  `forma_de_pago` que propone el DDS: hoy la única forma de pago aprobada es efectivo (transferencia y pago mixto son CR-02),
  y el DAD aclara que esos nombres son contratos de referencia. Si se aprueba CR-02, se agrega el parámetro.
  *Causa:* no programar opciones sin aprobar. *Impacto:* solo `servicios.py`; las pruebas fijan la firma.
- `guardar_transaccion(venta, cuenta, existencias)` acepta `cuenta=None` en la venta de contado, en vez de agregar un método a
  `RepositorioDeVentas`. *Causa:* mantener pequeña la única interfaz (ISP). *Impacto:* `repositorios.py`.
- La tabla `ventas` guarda `tipo` (CONTADO o CREDITO), `forma_pago` y `valor_recibido` (ERS 7.1 y ticket del DDS 10.3).
  En la venta a crédito `forma_pago` y `valor_recibido` quedan vacíos. No había bases de datos reales, así que no hubo migración.
- El efectivo insuficiente es una excepción propia (`EfectivoInsuficiente`), como `StockInsuficiente` y `CreditoNoPermitido`.
  Orden de validación de UC-02: existencias, después efectivo; ninguna de las dos cambia datos.

## Deuda técnica
DT-01 existencias sin lotes (abierta) · DT-03 abonos simples (abierta) · DT-04 cobertura medida, faltan pruebas de interfaz (parcial) · DT-05 constructores con muchos parámetros (aceptada) ·
DT-08 `Venta.anular()` sin historia (abierta) · **pagadas:** DT-02 → BUG-02, DT-06 → BUG-01, DT-07 (mensajes con cantidades),
DT-09 (cliente sin validar).

**DT-09 (noviembre de 2026).** *Hallazgo:* `Cliente` se guardaba con nombre vacío, límite negativo o plazo menor a 1 día; con nombre `None`
SQLite lanzaba `IntegrityError` en vez de un mensaje claro. *Regla:* UC-05 del DDS (nombre obligatorio, límite no negativo, plazo de al menos
un día). *Corrección:* en el dominio (`Cliente.__init__`), no en la pantalla; prueba primero en `test_defectos_corregidos.py`.
*Impacto:* `dominio.py` y `validaciones.py` (`exigir_texto_obligatorio`, que ahora también usa `Producto`). Los datos adicionales del
cliente y el control de duplicados siguen pendientes con el propietario.

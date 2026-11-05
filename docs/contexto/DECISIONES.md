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
- ~~Los repositorios de productos y clientes son clases concretas; solo `RepositorioDeVentas` es una abstracción.~~
  **Reemplazada (noviembre de 2026) por ADR-04, «hexagonal ligero», pedida por la Guía 4 de IS II (FPI-20).** El documento ADR-04 no está
  en este repositorio; se siguió el texto de la tarea entregado por el desarrollador. *Cambio:* `tiendas_sm/puertos.py` (solo importa `abc`)
  tiene `RepositorioDeVentas` (movido sin cambios, más `contar_ventas()`), `PuertoDeProductos` y `PuertoDeClientes`; los repositorios SQLite
  heredan de ellos y `repositorios.py` reexporta `RepositorioDeVentas`. *Causa:* que el núcleo sea dueño de sus contratos y no dependa de
  SQLite, vigilado por `tests/test_arquitectura.py`. *Impacto:* `puertos.py` (nuevo), `repositorios.py`, `aplicacion.py`
  (`numero_de_ventas()` ya no tiene SQL). No cambió ninguna firma pública ni comportamiento; las pruebas anteriores pasan sin modificarse.
  Se mantiene la idea de no crear una interfaz por cada clase: solo hay puertos para la persistencia.
  *Orden:* la Guía 4 la ponía como primera tarea; aquí se hizo después de la venta de contado y de DT-09.
- **`PuertoDeClientes.listar()` (noviembre de 2026).** Se amplía el contrato de clientes con `listar()`, ordenado por nombre como el de
  productos. *Causa:* la interfaz debe dejar elegir al cliente en la venta a crédito (HU-05, RF-07, tarea 8). *Impacto:* `puertos.py`,
  `repositorios.py` (más `_a_cliente`, que reutiliza `obtener()`) y `servicios.py`. Solo consulta: sin búsqueda, filtros ni datos nuevos.
- **Venta de contado (UC-02, noviembre de 2026).** Firma `registrar_venta_de_contado(lineas, recibido)`, sin el parámetro
  `forma_de_pago` que propone el DDS: hoy la única forma de pago aprobada es efectivo (transferencia y pago mixto son CR-02),
  y el DAD aclara que esos nombres son contratos de referencia. Si se aprueba CR-02, se agrega el parámetro.
  *Causa:* no programar opciones sin aprobar. *Impacto:* solo `servicios.py`; las pruebas fijan la firma.
- `guardar_transaccion(venta, cuenta, existencias)` acepta `cuenta=None` en la venta de contado, en vez de agregar un método a
  `RepositorioDeVentas`. *Causa:* mantener pequeña la única interfaz (ISP). *Impacto:* `repositorios.py`.
- La tabla `ventas` guarda `tipo` (CONTADO o CREDITO), `forma_pago` y `valor_recibido` (ERS 7.1 y ticket del DDS 10.3).
  En la venta a crédito `forma_pago` y `valor_recibido` quedan vacíos. **Migración (DIF-06, tarea 7):** `BaseDeDatos._migrar_ventas`
  agrega con `ALTER TABLE` las columnas que falten en una base vieja; las ventas viejas quedan como `CREDITO`.
  *Desviación de E-04:* la venta de contado cambió 4 archivos de `tiendas_sm/` (dominio, servicios, repositorios y base_de_datos);
  el criterio pedía como máximo 3. Se hizo así para guardar tipo y forma de pago (ERS 7.1); se declara en lugar de ocultarlo.
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

**TD-01 (noviembre de 2026, pagada).** *Hallazgo:* `guardar_transaccion` descontaba existencias sin insertar nada en `movimientos_inventario`
(incumplía RF-04, RN-07 y RNF-10). *Corrección:* `RepositorioDeVentasSqlite._insertar_salidas` agrega un movimiento `SALIDA_VENTA` por producto
(suma de sus líneas) con la fecha de la venta, dentro de la misma transacción (RNF-04), en el repositorio y no con un trigger (FPI-19).
Aplica a la venta a crédito y a la de contado. *Prueba:* escenario E-05 (entradas − salidas = cantidad actual) en `test_defectos_corregidos.py`.
*Impacto:* solo `repositorios.py`; sin cambios de firmas.

**TD-04 (noviembre de 2026, pagada).** *Hallazgo:* `Producto` aceptaba un `stock_minimo` negativo y `registrar_producto` no permitía
fijarlo (ERS RN-14, DDS §11.2). La parte del cliente ya se había corregido como DT-09. *Corrección:* `exigir_no_negativo` en
`validaciones.py`, usada por `Producto` (stock mínimo) y por `Cliente` (límite, mismo mensaje); `registrar_producto` recibe
`stock_minimo=0` al final. *Prueba:* CN-09 en `test_caja_negra.py` (−1 rechazado, 0 aceptado, el valor se conserva).
*Pendiente con el propietario:* si el stock mínimo es general o por producto y su valor; aquí solo se guarda, no genera alertas (RF-12).

**TD-14 (noviembre de 2026, pagada).** *Hallazgo:* al leer una cuenta desde SQLite, `_a_cuenta` dejaba `fecha_apertura` y
`fecha_vencimiento` como texto; al crearla son `datetime`. No fallaba aún, pero el futuro estado «cuenta vencida» sí fallaría.
*Corrección:* `_a_cuenta` convierte con `datetime.fromisoformat`; se siguen guardando como texto ISO (DEC-05 del DDS). Se revisaron las
demás fechas: ninguna otra se lee de la base como objeto. *Prueba:* `test_defectos_corregidos.py`, por `cuentas_del_cliente` y `obtener_cuenta`.
*Impacto:* solo `repositorios.py`.

**Interfaz Tkinter, primera versión (tarea 8, TD-03, noviembre de 2026).** Solo el punto de venta, como pide la tarea 8 (el plan inicial
de 4 pestañas queda para después). *Diseño:* `tiendas_sm/presentador.py` (sin Tkinter, cuenta para la cobertura) recibe texto, llama a
`Aplicacion` y devuelve filas y mensajes; `interfaz_tk/ventana_punto_de_venta.py` solo dibuja (no cuenta para la cobertura). El total y el
cambio previo usan `Venta` del dominio; el stock se valida solo al confirmar (se muestra «Disponibles: N»); los mensajes del dominio se
muestran tal como llegan. *Base de datos:* `%LOCALAPPDATA%\TIENDAS_SM\tiendas_sm.db` (DDS §14), decisión del desarrollador; antes se
había dicho «junto a `iniciar_tienda.py`». *Datos de ejemplo:* `--datos-de-ejemplo` carga datos ficticios solo si la base está vacía.
*Desviación declarada:* las pruebas de `iniciar_tienda.py` y `datos_de_ejemplo.py` se escribieron después del código.
*Pendiente:* medir E-01 (venta de 5 productos en menos de 60 s) con personas reales; pantallas de productos, clientes y abonos.

**Escenarios de calidad E-02, E-03 y E-05 (tarea 6, ADR-02, noviembre de 2026).** `tests/test_escenarios_calidad.py`:
E-02, 20 procesos que mueren con `os._exit(3)` a mitad de la transacción sin dejar nada a medias (`integrity_check = ok`);
E-03, con 1.000 productos `listar()` y una venta de 5 líneas (medido en el equipo de desarrollo: unos 5 ms y 1 ms; límites 2 s y 1 s);
E-05, entradas − salidas = cantidad actual y toda unidad vendida con su `SALIDA_VENTA`. El archivo tarda unos 2 s.

**Hallazgo pendiente de numerar (deuda técnica):** `movimientos_inventario` no guarda el número de la venta, y en Windows dos ventas
seguidas pueden quedar con la misma fecha y hora. Por eso no se puede probar venta por venta qué movimiento le corresponde; E-05 se
comprueba por producto. *Recomendación (no aprobada):* agregar `id_venta` al movimiento de venta. Se registrará con el número TD que
corresponda en las fichas.

**TD-05 y TD-07 (noviembre de 2026).** *TD-05 (pagada):* `medir_cobertura.py` descarta los números de línea `None` que entrega
`trace` en Python 3.13 (`lineas_validas`); prueba en `test_medir_cobertura.py` que simula esa entrada. En 3.12 el resultado no cambió
(606 de 617 líneas). *TD-07 (pagada con la FPI-25):* matriz 3.12 y 3.13, Dependabot semanal, `ruff==0.16.9` y `coverage==7.13.4`
comprobadas en PyPI y actions fijadas por el SHA real de su etiqueta (`git ls-remote`, con autorización del desarrollador).

**Pipeline de la Guía 9 (FPI-25, ADR-09, noviembre de 2026).** `ci.yml` pasa de un job a tres encadenados: `linter` (ruff con
seguridad `S` y complejidad `C901` ≤ 10), `test` en 3.12 y 3.13, y `analysis` (cobertura ≥ 90 %, SonarCloud si hay `SONAR_TOKEN`,
artefacto `.zip` en `main`). Se partió de `salidas/ci_propuesto.yml`, agregando `interfaz_tk` e `iniciar_tienda.py` al lint y al build.
*Hallazgos al ejecutar ruff por primera vez:* un `import os` sin usar en `test_escenarios_calidad.py` (el CI anterior habría quedado
en rojo) y dos consultas SQL con f-string en pruebas (S608), corregidas con consultas fijas; el `subprocess` de E-02 (S603) queda con
una excepción justificada. *No verificado en local:* Python 3.13 y SonarCloud (sin token). Los checks de `main` cambian a `linter`,
`test (Python 3.12)`, `test (Python 3.13)` y `analysis` (ver `docs/CI.md`).

**Entrega continua (tarea 10, FPI-27, ADR-11, noviembre de 2026).** `.github/workflows/deploy.yml` y `scripts/healthcheck_paquete.py`
de la propuesta, sin cambiar su lógica. *Ajustes:* el healthcheck comprueba también el movimiento `SALIDA_VENTA` (TD-01); las actions
quedan fijadas por SHA (TD-07); el CI revisa y compila `scripts/`. *Verificado en local:* el healthcheck da `HEALTHCHECK OK` sobre un
paquete real de `git archive` y sale con código 1 con un `.zip` dañado o cortado (`tests/test_healthcheck_paquete.py`). *No verificado:*
el workflow en GitHub (no hay `gh` ni push); `--prerelease=false` no aparece escrito así en el manual de `gh release edit`.
*Excepciones de ruff:* S603 en los `subprocess` del healthcheck y de sus pruebas, con la razón al lado (el mismo Python con un script
fijo). Es una excepción por línea, no se desactivó la regla.

### Equivalencia de numeraciones (DT-xx del repositorio y TD-xx de las fichas FPI-17 en adelante)
Desde noviembre de 2026 la deuda nueva usa la numeración **TD-xx** de las fichas. Lo ya registrado como DT-xx no se renumera.
Solo se anotan equivalencias comprobadas con el texto de las tareas; el catálogo completo de TD-xx no está en el repositorio.

| Repositorio | Fichas | Relación |
| --- | --- | --- |
| DT-09 (cliente sin validar) | TD-04 | DT-09 cubrió la parte del cliente; el resto de TD-04 (stock mínimo) se hizo como TD-04 |
| Hallazgo de la venta de contado (sin movimiento al vender) | TD-01 | Es el mismo problema; quedó registrado como TD-01 |

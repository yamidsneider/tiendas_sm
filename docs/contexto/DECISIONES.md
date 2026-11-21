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
| FPI-12 | **Python + SQLite + Tkinter**, dinero entero, refactor de 8 code smells, deuda DT-01..DT-05 | Tkinter: las 6 pantallas del MVP; en curso la app de escritorio con la visual del borrador (pywebview, opción B) |
| FPI-13 | GitHub Flow, `main` protegida, commits atómicos, conflicto simulado, release v0.1.0 | Evidencia en GitHub por confirmar |
| FPI-14 | Pruebas unitarias con stubs/mocks, caja negra, integración ascendente, cobertura | Implementado |
| FPI-15 | CI con GitHub Actions, regresión, BUG-01 y BUG-02 corregidos | Pipeline verde por confirmar |
| FPI-16 | Demo, retrospectiva cuantitativa, bitácora de IA y hoja de ruta hacia IS II | En cierre |

## Decisiones técnicas que no deben revertirse sin explicar por qué
- Solo biblioteca estándar (sin dependencias externas) en el MVP. Única herramienta externa: `ruff`, solo en el CI. Excepción aprobada: `pywebview` y `PyInstaller` para la app de escritorio (opción B).
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
- **Lecturas nuevas en los puertos para las pantallas (noviembre de 2026).** Solo consultas; no cambian el esquema ni las reglas.
  `PuertoDeProductos.listar_movimientos(limite)` devuelve `MovimientoDeInventario` (registro de datos en `dominio.py`, sin reglas) y
  `ServicioDeProductos.movimientos()` trae los últimos 50 (RF-04, sección Existencias). `RepositorioDeVentas.obtener(id_venta)` y
  `listar(limite)` rearman la venta con el precio guardado en cada línea, y `ServicioDeVentas.obtener/listar` traen las últimas 50
  (RF-05, sección Ventas). *Causa:* los movimientos y las ventas ya se guardaban, pero ningún contrato permitía leerlos; se siguió la
  convención `obtener`/`listar` de ADR-04. *Impacto:* `dominio.py`, `puertos.py`, `repositorios.py` y `servicios.py`; cada método
  abstracto tiene su prueba en ROJO primero en `test_arquitectura`. Ninguna prueba anterior cambió.

## Deuda técnica
DT-01 existencias sin lotes (abierta) · DT-03 abonos simples (abierta) · DT-04 cobertura medida; las 37 pruebas de pantallas se saltan en el CI sin pantalla (parcial) · DT-05 constructores con muchos parámetros (aceptada) ·
DT-08 `Venta.anular()` sin historia (abierta) · **pagadas:** DT-02 → BUG-02, DT-06 → BUG-01, DT-07 (mensajes con cantidades),
DT-09 (cliente sin validar), TD-13 (saldo en una consulta, FPI-31).

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

**DevSecOps (tarea 12, FPI-28, ADR-12, noviembre de 2026).** `.github/workflows/ci-security.yml` (Semgrep y Trivy), `.trivyignore`
(sin exclusiones) y `ruff.toml` con las excepciones justificadas. Versiones comprobadas: `semgrep==1.183.0` (PyPI), `trivy-action`
v0.36.0 por SHA y Trivy v0.76.2 (publicada, Latest; lejos de v0.69.4–v0.69.6, CVE-2026-33634). *Hallazgo:* en la prueba del gate,
Semgrep (`p/python`, `p/security-audit`) **no detecta** una consulta `sqlite3` armada con f-string; la detecta ruff S608.
*Recomendación (no aprobada):* agregar una regla propia de Semgrep para ese patrón, o dejar constancia de que la barrera es ruff.
*No verificado en local:* Trivy (requiere descargar su ejecutable).

**Observabilidad (tarea 13, FPI-29, ADR-13, noviembre de 2026).** Parche `cambios_fpi29.patch` aplicado sin cambiar su lógica:
`tiendas_sm/telemetria.py` (span con `trace_id`/`span_id`, contador e histograma en memoria y log JSON por línea), `tests/test_telemetria.py`
(8 pruebas) y `tablero_telemetria.py` (HTML local). *Reglas revisadas:* solo biblioteca estándar; el dominio y `ServicioDeVentas` no
cambian, se instrumenta con el adaptador `VentasObservadas` que arma `Aplicacion` solo si recibe una telemetría (sin ella todo sigue
igual); lista blanca de atributos (`venta.tipo`, `venta.lineas`, `venta.unidades`, `venta.total`): nada del cliente, y de un error solo su
tipo; muestreo 0,2 para ventas exitosas y 100 % para errores; `telemetria.jsonl` junto a la base con rotación de 1 MB y 3 respaldos.
`*.jsonl` y `tablero*.html` no se suben (`.gitignore`). *Verificado en local:* 172 pruebas OK, cobertura 98,3 %, ruff con las reglas del
CI (ahora también sobre `tablero_telemetria.py`) y 5 ventas por el mismo arranque de `iniciar_tienda` (sin abrir la ventana, en una
carpeta temporal): 4 OK y 1 `StockInsuficiente`; con muestreo 0,2 solo quedó la línea del error, con muestreo 1,0 las 5 líneas, y
ninguna contiene el nombre del cliente ni el texto del error. *Observaciones:* la guía esperaba 168 pruebas, pero su parche se probó
con un `main` anterior (aquí 164 + 8 = 172); `marca_tiempo` está en UTC, así que el tablero agrupa por día UTC (una venta después de
las 7 p. m. de Colombia cae en el día siguiente), lo que queda como recomendación sin aplicar; `tablero_telemetria.py` no tiene pruebas
propias (herramienta del desarrollador, como `medir_*.py`). *No verificado:* Python 3.13 (lo corre el CI) y el uso real durante varios días.

**Confiabilidad (tarea 14, FPI-30, ADR-14, INC-SIM-01, noviembre de 2026).** Parche `cambios_fpi30.patch` sin cambios (`slo_mensual.py`
y 4 pruebas: SLO 99,5 % de ventas sin falla técnica y 99 % en menos de 1 s; los rechazos de negocio no consumen presupuesto). Runbook en
`docs/Runbook_base_de_datos.md` y Postmortem en `docs/incidentes/`. *Causa raíz del simulacro, corregida con TDD (ROJO, VERDE y
REFACTOR):* `tiendas_sm/respaldo.py`. **Al cerrar** (en el `finally` de `iniciar_tienda.py`): `PRAGMA integrity_check`; si da `ok`,
copia con `sqlite3 .backup()` a `respaldo_AAAA-MM-DDTHHMM.db` en la misma carpeta y conserva los 7 más recientes; si la base está
dañada no respalda y la telemetría registra `BaseDeDatosDanada` (solo el tipo). **Al abrir:** `PRAGMA quick_check` en solo lectura (no
crea el archivo si no existe); si no da `ok`, muestra «La base de datos está dañada. No venda en el sistema: use el cuaderno y llame al
soporte (Runbook)» y no abre el punto de venta. Las pruebas usan una base dañada a propósito (basura en la página 2): `quick_check` y
`integrity_check` la detectan. `respaldo.py` es infraestructura (usa `sqlite3`), no núcleo: `test_arquitectura` no cambia.
*Tablero:* el porcentaje cuenta solo fallas técnicas (umbral 0,5 % = 100 − SLO) y los rechazos se listan aparte, con la misma lista
`RECHAZOS_DE_NEGOCIO` de `slo_mensual.py`. *Ajuste no pedido, con prueba en ROJO primero:* los spans nuevos `abrir_base` y
`respaldar_base` se habrían contado como ventas en el tablero y en el SLO; `slo_mensual.solo_ventas` los deja fuera (un registro sin
nombre sigue contando como venta, para no romper las pruebas del parche). *Verificado en local:* 193 pruebas OK, cobertura 98,4 %
(`respaldo.py` 100 %), ruff con las reglas del CI (ahora también sobre `slo_mensual.py`) y todos los comandos del Runbook (3.1, 3.2,
3.3, 4.B y el respaldo de la sección 6) ejecutados en `cmd` con `verificar_runbook.py` sobre una carpeta temporal: detecta el daño,
se niega a restaurar un respaldo inexistente, restaura el bueno y vuelve a dar `ok` con las 5 ventas. *No verificado:* la ventana del
mensaje de base dañada (no se abrió a mano), Python 3.13, el computador real de la tienda y el simulacro con tiempo medido por Yamid.

**TD-13 pagada (tarea 15, FPI-31, ADR-15, noviembre de 2026).** Refactorización preventiva: `ControlCredito.saldo_pendiente` cargaba
todas las cuentas y sus abonos y sumaba en Python; ahora `RepositorioDeVentasSqlite.saldo_pendiente_del_cliente` lo calcula en una sola
consulta. Tres commits de los parches de la guía, con su mensaje y su autor originales («Ensayo»): ROJO (prueba de equivalencia en 200
escenarios aleatorios con semilla fija), VERDE (consulta SQL) y REFACTOR (misma regla por cuenta e índices `idx_cuentas_por_cliente` e
`idx_abonos_por_cuenta`, con `IF NOT EXISTS`, así que también llegan a las bases que ya existen). *Revisado:* la regla es la de
`CuentaPorCobrar.calcular_saldo` (monto original − abonos de cada cuenta, todas las cuentas del cliente, sin filtrar por estado); el stub
de `test_unitarias_dobles` solo ganó un método, sin cambiar aserciones. *Desviación:* `git am --keep-cr` no aplicó los commits 2 y 3
(finales de línea, en `repositorios.py`, `servicios.py` y `base_de_datos.py`); se aplicaron con `git apply --ignore-whitespace`, el diff
es idéntico al del parche y los archivos siguen en CRLF. *Ajuste no pedido:* `RepositorioDeVentas` (puertos.py, ADR-04) no declaraba el
método nuevo que usa el servicio; se agregó como método abstracto, con su prueba en ROJO primero en `test_arquitectura`.
*Medido en el equipo del desarrollador* (`medir_saldo.py`, mediana de 30): 100 cuentas 0,751 → 0,058 ms; 500 cuentas 7,893 → 0,263 ms;
2.000 cuentas 81,360 → 1,071 ms (unas 76 veces menos; el ensayo de la guía daba 39 → 0,6 ms en otro equipo). Los saldos son idénticos
antes y después. *Verificado:* 197 pruebas OK, cobertura 98,4 %, ruff con las reglas del CI. *No verificado:* Python 3.13 (lo corre el CI).

**Interfaz con el diseño del borrador HTML (opción A, noviembre de 2026).** El desarrollador mostró su borrador
`tiendas_sm_dashboard.html` y eligió la **opción A**: seguir en Tkinter y copiar solo el diseño (paleta verde, letra Segoe UI, menú
lateral), sin emojis y **sin cambiar la arquitectura**; la lógica del borrador (JavaScript y `localStorage`) no se usó. *Alternativa
descartada:* la opción B (interfaz HTML) cambiaba el stack de FPI-12. *Cómo quedó:* `interfaz_tk/tema.py` (paleta y estilos sobre el tema
`clam`, porque el tema nativo de Windows ignora los colores; tablas con filas alternadas), `interfaz_tk/pantalla.py` (mostrar, ocultar y
`_si_activa`: F2/F9/F4/Supr solo actúan con el punto de venta a la vista), `interfaz_tk/ventana_principal.py` (menú con las **6 secciones
aprobadas**: Punto de venta, Ventas, Productos, Existencias, Clientes, Créditos y abonos; cada una se crea la primera vez y después solo se
oculta, así la venta en curso no se pierde). Cada sección tiene su presentador sin Tkinter en `tiendas_sm/presentador_*.py`, probado sin
ventanas, y su pantalla en `interfaz_tk/pantalla_*.py`, que solo dibuja; los mensajes del dominio se muestran tal como llegan.
*Fuera a propósito:* lotes, alertas, configuración y tablero (esperan al propietario); proveedores, pedidos y caja (CR-02); stock mínimo
en el formulario (TD-04: ¿general o por producto?); mora o cuentas «vencidas» (reglas del crédito por confirmar); salida manual (H-1);
nombres de cliente repetidos (HU-05, por definir); anular ventas y borrar productos (DT-08); totales, reportes y ganancias (no aprobados).
*Único control nuevo:* una cantidad inicial negativa en «Nuevo producto» se rechaza antes de guardar (antes `registrar_producto` la
ignoraba en silencio). *Proceso:* una rama por etapa con ROJO y VERDE (y un REFACTOR aparte para reutilizar el ticket), fusionadas con
`--no-ff` en la rama de integración `app/pantallas`. *Verificado en local:* 275 pruebas OK (las 37 de pantallas se ejecutaron con
pantalla real), cobertura 98,8 %, V(G) máximo 6, ruff con las reglas del CI, y cada pantalla revisada a 1024×600 con datos ficticios.
*No verificado:* Python 3.13 (lo corre el CI, donde las 37 pruebas de pantallas se saltan), el uso por personas (E-01, RNF-01) y el PR a `main`.
*Recomendación sin aprobar:* «Editar cliente» (ver `ESTADO_Y_PENDIENTES.md`).

**Interfaz de escritorio con la visual del borrador HTML (opción B, noviembre de 2026; cambia FPI-12).** Después de terminar la opción A,
el desarrollador pidió una app **de escritorio, con su `.exe`**, que no se vea como un navegador y que siga la estructura y la visual de su
borrador `tiendas_sm_dashboard.html`. *Causa:* el borrador se ve y se usa mejor que Tkinter (tarjetas, ventanas emergentes, insignias) y
el desarrollador quiere que la app final se parezca a él. *Qué cambia:* solo la capa que dibuja. **pywebview** abre una ventana nativa de
Windows (motor WebView2, que trae Windows 11) con la página de `interfaz_web/estatico/`; el JavaScript de la página llama a
`interfaz_web/api.py`, que usa los **mismos presentadores** de `tiendas_sm/presentador*.py`. El dominio, los servicios, los puertos y la
base no cambian. **PyInstaller** arma `TIENDAS_SM.exe`, que no necesita Python instalado. *Excepción a «solo biblioteca estándar»:*
`pywebview` (en la app) y `PyInstaller` (solo para armar el `.exe`), con versiones fijas en `requirements-escritorio.txt`; el núcleo y
las pruebas siguen sin dependencias, así el CI no cambia. *Cuidados:* no hay servidor ni puerto abierto (nada queda expuesto en la red);
la página no carga nada de internet; todas las llamadas a la base pasan por **un solo hilo**, porque pywebview atiende cada llamada en un
hilo distinto y la conexión de SQLite es una sola. *Qué se toma del borrador:* estructura y CSS; **no** su JavaScript de negocio ni
`localStorage`. Solo las **6 secciones aprobadas**, sin emojis. *Impacto:* `iniciar_tienda.py` abre la ventana nueva; al cerrarla se hace
el respaldo verificado (FPI-30). `interfaz_tk/` se conserva hasta que el desarrollador decida retirarla (copia en
`../TIENDAS-SM_version_tkinter`). *Alternativas descartadas:* seguir con Tkinter (no se parece lo suficiente al borrador); un servidor
local abierto en el navegador o en modo app de Edge (se ve como navegador y exige cuidar un puerto local); abrir el borrador tal cual
(sus reglas en JavaScript duplicarían el dominio y no guardan en SQLite).

**Editar cliente y editar producto (aprobado por el desarrollador, noviembre de 2026).** *Cliente:* los mismos 4 datos del registro (nombre, crédito, límite y plazo), con las mismas reglas del dominio; las cuentas ya abiertas conservan su vencimiento. *Producto:* nombre, precio de compra y precio de venta; las existencias solo cambian con entradas y ventas, el stock mínimo se conserva (TD-04) y las ventas anteriores guardan su precio (HU-02). `RepositorioDeClientes.guardar` ahora actualiza si el cliente ya tiene id (el puerto no cambia). *Preliminar, por confirmar con el propietario:* se permite dejar el límite por debajo de la deuda; solo impide fiar más hasta que abone (el «disponible» se ve negativo).

**Respuestas del propietario y grupo A (*validado*: el desarrollador confirmó el 8 de noviembre de 2026 que respondió el propietario real de una tienda).**
Fuente: `docs/contexto/PREGUNTAS_PROPIETARIO.docx`. La fecha de la entrevista no se anotó («irrelevante»); se registra la de la confirmación.
E-01 sigue sin medir. Programado, cada uno con su prueba:
- 1.3 Ticket para impresora térmica de 80 mm (42 caracteres por renglón, `@page` de 80 mm). El cambio solo sale en contado.
- 3.1 Teléfono y dirección del cliente, opcionales (datos personales; columnas nuevas con migración).
- 4.1 Stock mínimo por producto al crearlo y lista «Por reponer» (RF-12; cierra TD-04 como mínimo *por producto*). Avisa con el mínimo o menos; 0 = sin aviso.
- 2.2/2.3 Plazo máximo por cliente (ya existía), cuenta «Vencida», lista de atrasados y **no fiar a quien tiene una cuenta vencida**. Sin intereses.
- 1.4 Código de barras opcional y único; el lector escribe el código y Enter lo agrega. La búsqueda por nombre sigue.
Sin cambio (la app ya lo hace): 1.1 stock insuficiente, 2.1 límite por cliente, 2.5 abono ≤ saldo, 3.2 apodo entre paréntesis.
*Recomendación (no pedida):* el teléfono solo acepta números, espacios, + y -. *Ambigua:* 2.4 se interpreta como «solo fiar en lo disponible» (como hoy).
**Pendiente de aprobación (grupo C):** salida manual con clave del jefe y roles jefe/empleado (4.4, 5.1, CR-01), respaldo al cerrar turno (5.2),
proveedores y pedidos (5.3, CR-02).

**Grupo B (*aprobado* por el desarrollador el 8 de noviembre de 2026).** Programado, cada uno con su prueba:
- 1.2 Pago por transferencia (Nequi, Daviplata; se confirma mirando el celular) y mixto. La transferencia no puede pasar del total; el cambio sale solo del efectivo.
- 1.5 Anular una venta o devolver parte, con motivo obligatorio. **Cambia DT-08** (antes no se anulaba): la venta no se borra; queda la devolución
  con su motivo y un movimiento «Devolución» que regresa las unidades. Si fue fiada, primero baja la deuda hasta 0 y el resto se devuelve en
  efectivo (no hay saldo a favor). Todo en una transacción (RNF-04). Por ahora cualquiera puede hacerlo; la clave del jefe llega con CR-01.
- 4.2/4.3 Lotes con vencimiento (RF-10, RF-13) como **registro de aviso, no ligado al inventario**: registrar o quitar un lote no cambia las
  existencias. Días de aviso **por producto** (0 = solo avisa el día que vence). FEFO manual: el panel «Lotes por vencer» los ordena por fecha;
  «Ya no está» lo quita de la lista. *Decisión del desarrollador:* el número de lote es opcional y se permite registrar un lote ya vencido.

**Deuda nueva TD-15, TD-16 y TD-17 (FPI-31).** El texto completo de la FPI-31 **no está** en el repositorio ni en las carpetas del
proyecto; lo que sigue sale de `Dossier_Final.md` (secciones 3 y 6) y debe confirmarse con la ficha:
- **TD-15 — movimiento de inventario sin `id_venta`** (bajo impacto con una caja; H2/H3). Es el hallazgo de E-05 (tarea 8): no se puede
  ligar cada `SALIDA_VENTA` con su venta. *Por confirmar:* la relación TD-15 ↔ «movimiento sin id_venta» se deduce del orden de una fila
  del dossier («TD-10, TD-15, TD-12, TD-08: abonos simples, movimiento sin id_venta, plazo fijo, fechas sin zona»).
- **TD-16 — operación: respaldo manual y sin revisión al abrir** (no aceptable para un piloto). **Atendida en el código por la tarea 14**
  (`tiendas_sm/respaldo.py`); falta usarla en la tienda real y el simulacro medido.
- **TD-17 — Semgrep no detecta SQL armado con f-string** (hallazgo de la prueba del gate, tarea 12). Abierta: hoy la barrera es ruff S608;
  la regla propia de Semgrep sigue como recomendación sin aprobar.

### Equivalencia de numeraciones (DT-xx del repositorio y TD-xx de las fichas FPI-17 en adelante)
Desde noviembre de 2026 la deuda nueva usa la numeración **TD-xx** de las fichas. Lo ya registrado como DT-xx no se renumera.
Solo se anotan equivalencias comprobadas con el texto de las tareas; el catálogo completo de TD-xx no está en el repositorio.

| Repositorio | Fichas | Relación |
| --- | --- | --- |
| DT-09 (cliente sin validar) | TD-04 | DT-09 cubrió la parte del cliente; el resto de TD-04 (stock mínimo) se hizo como TD-04 |
| Hallazgo de la venta de contado (sin movimiento al vender) | TD-01 | Es el mismo problema; quedó registrado como TD-01 |
| Hallazgo E-05 (movimientos sin `id_venta`) | TD-15 | Por confirmar con la FPI-31 (deducido del orden de una fila del dossier) |
| Causa raíz de INC-SIM-01 (respaldo manual, sin revisión al abrir) | TD-16 | Comprobada con el dossier; atendida por la tarea 14 |
| Prueba del gate: Semgrep no detecta SQL con f-string | TD-17 | Comprobada con el dossier (fila de la FPI-28) |

**Hoja de ruta hacia la app completa y fase 1: Reportes (*aprobado* por el desarrollador, 21 de noviembre de 2026).**
*Causa:* el desarrollador pidió llevar el MVP a una app completa. El orden de las 9 fases está en `docs/HOJA_DE_RUTA_APP_COMPLETA.md`.
*Cambia:* «reportes» deja de ser *Won't Have* (regla 3 de `CLAUDE.md`). *Qué hace:* sección **Reportes** (séptima del menú, grupo
Administración) con hoy, últimos 7 días y este mes: vendido neto (vendido − devuelto), ganancia, número de ventas, abonos recibidos,
totales por forma de pago (efectivo, transferencia, fiado, devoluciones) y los 10 productos más vendidos (unidades netas).
Solo consulta; no cambia ventas, inventario ni deudas. *Diseño:* `PuertoDeReportes` en `puertos.py` y las consultas SQL en
`RepositorioDeReportesSqlite` (con parámetros, sin f-string); el núcleo sigue sin SQL (`test_arquitectura`).
*Costo de cada línea:* `detalles_venta.costo_unitario` guarda el precio de compra al vender (como el precio de venta, HU-02), con
migración; las líneas viejas quedan en NULL y usan el precio de compra actual, y el reporte avisa que la ganancia es *estimada*.
*Preliminar, por confirmar con el propietario:* la ganancia es precio de venta − precio de compra, sin gastos; las ventas cuentan
por su fecha y las devoluciones y abonos por la suya; en una devolución de una venta pagada por transferencia el dinero aparece
como «efectivo devuelto» (así lo registra la respuesta 1.5).

**Fase 2: usuarios y roles (CR-01, RNF-03; *aprobado* por el desarrollador, 21 de noviembre de 2026).**
*Respuestas del desarrollador:* la tienda tiene 2 empleados; la clave se pide **al abrir la app**; cada usuario solo hace lo que
su rol permite. *Roles:* jefe y empleado (`Rol`, `Permiso` y `PERMISOS_POR_ROL` en `dominio.py`).
*Preliminar (propuesta, por confirmar con el propietario):* el empleado vende (contado y fiado), consulta, registra entradas
y lotes, y recibe abonos; solo el jefe devuelve o anula ventas, crea o edita productos y precios, crea o edita clientes (cupo y
plazo), ve los reportes y administra los usuarios.
*Seguridad:* la clave se guarda como huella PBKDF2-SHA256 (200.000 vueltas) con sal propia por usuario, solo con la biblioteca
estándar; se compara en tiempo constante; mínimo 4 caracteres (como un PIN). Usuario o clave malos dan el mismo mensaje. No hay
usuarios ni claves en el código ni en los datos de ejemplo: la primera vez la ventana pide crear la cuenta del jefe. Nadie se
desactiva a sí mismo y siempre queda un jefe activo. *Barrera:* cada método de `ApiDeLaTienda` lleva `@requiere(permiso)` y
`test_usuarios` falla si alguno queda sin permiso; esconder botones en la página es solo comodidad. Al cerrar sesión se vacía el
carrito. *Impacto:* `--tkinter` ya no abre la versión Tkinter (no pide clave y se saltaría los permisos); se abre la ventana
normal. Las pruebas de la API ingresan como jefe con `tests/sesion_de_prueba.py`.
*Pendiente:* clave del jefe para la salida manual (fase 3); registrar qué usuario hizo cada venta (fase 4, caja); bloqueo
tras varios intentos fallidos (recomendación, no pedida).

**Fase 3: salida manual de mercancía (respuesta 4.4 del propietario; *aprobada* por el desarrollador, 21 de noviembre de 2026).**
*Qué hace:* en Existencias, «− Salida» baja las unidades de un producto sin venderlo, con un movimiento `SALIDA_MANUAL` que
guarda el motivo, quién la registró (`id_usuario`), quién la autorizó (`id_autorizo`) y el precio de compra de ese momento
(`costo_unitario`); columnas nuevas de `movimientos_inventario` con migración. No deja sacar más de lo que hay. El historial
muestra «Salida manual (motivo)» y Reportes suma «Salidas de mercancía (al costo)».
*Autorización (respuesta 4.4, «con clave del jefe»):* el jefe la registra directo (`Permiso.REGISTRAR_SALIDA`); el empleado solo
si el jefe escribe ahí mismo su usuario y su clave (`ServicioDeUsuarios.autorizar`). Clave de otro empleado o clave mala:
«Usuario o clave del jefe incorrectos».
*Preliminar (decisión del desarrollador sin respuesta del propietario):* motivos Dañado, Vencido, Consumo propio y Otro;
en «Otro» el detalle es obligatorio. Los lotes siguen siendo solo aviso: una salida por «Vencido» no quita el lote de la lista
(eso llega con la fase 9).

**Fase 4: caja con apertura y cierre (arqueo) (CR-02 caja; *aprobada* por el desarrollador, 21 de noviembre de 2026).**
*Respuestas del desarrollador:* la caja se abre al empezar el día escribiendo la base (cambia cada día); se cierra cuando
haga falta o al final del día; se puede cerrar la app y dejar el turno abierto; al cerrar se escribe lo contado, se muestra
cuánto falta o sobra y se puede confirmar el cierre o cancelar para contar de nuevo.
*Qué hace:* tabla `turnos_caja` (base, quién abre y cuándo, quién cierra y cuándo, esperado y contado); `ServicioDeCaja`
(un solo turno abierto a la vez) y sección **Caja** en el grupo Operación. El turno abierto vive en la base de datos, por eso
sobrevive a cerrar la app. «Revisar» no cierra nada; «Cerrar caja» guarda el arqueo. El jefe ve los cierres anteriores.
*Preliminar (decisión del desarrollador):* esperado en efectivo = base + ventas de contado en efectivo (sin la parte por
transferencia) + abonos − efectivo devuelto, desde la hora de apertura (usa el mismo `PuertoDeReportes` de la fase 1); los
abonos se cuentan como efectivo porque no se registra cómo se pagaron. Jefe y empleado abren y cierran (`Permiso.MANEJAR_CAJA`).
Con la caja cerrada **se puede vender**, pero el punto de venta avisa que esa venta no entra en ningún cierre.
*Pendiente:* forma de pago del abono (efectivo o transferencia); si se debe impedir vender con la caja cerrada.

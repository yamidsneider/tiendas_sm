# TIENDAS S.M — Contexto completo del proyecto

Documento de traspaso. Describe **solo el proyecto** (qué es, qué se decidió, qué se construyó, qué falta), no los ejercicios de taller ni los foros de las guías. Está escrito para que una persona, o una IA en un chat nuevo, pueda retomar el trabajo sin haber visto lo anterior.

Estado descrito: noviembre de 2026, después de las 16 guías de aprendizaje de Ingeniería de Software I.

---

## 0. Cómo leer este archivo

- Las secciones 1 a 7 explican **qué es el proyecto y qué se decidió** (negocio, requisitos, diseño).
- Las secciones 8 a 13 explican **qué se construyó** (código, pruebas, calidad, Git, CI, prototipos).
- Las secciones 14 a 17 son las **más importantes para no equivocarse**: uso de IA, estado real, pendientes y qué es real frente a qué es ejemplo.
- La sección **19** describe los documentos formales (ERS, DAD, DDS), el diseño de la base de datos, el póster y el paquete para Claude Code, que también forman parte del proyecto.
- Cuando algo dice **por confirmar**, es una propuesta del desarrollador que el propietario de la tienda todavía no aprobó.

---

## 1. Identidad del proyecto

| Dato | Valor |
| --- | --- |
| Nombre | **TIENDAS S.M** |
| Descripción | Sistema de gestión de inventario, ventas y créditos para tiendas de barrio |
| Desarrollador | Yamid Sneider Merchan Castro (proyecto individual: asume todos los roles) |
| Asignatura | Ingeniería de Software I, Universidad de Pamplona |
| Tipo de entrega | MVP académico (producto mínimo viable), no un sistema en producción |
| Repositorio | `yamidsneider/TIENDAS-SM` (GitHub, público) |
| Tablero Kanban | `https://github.com/users/yamidsneider/projects/1` |
| Idioma de trabajo | Español (código, mensajes, documentos) |
| Profesor (según el póster) | Miguel Eduardo Posada Haddad |

---

## 2. El problema y para quién es

Una tienda de barrio lleva sus productos, su caja y sus deudas de clientes a mano o en cuadernos. Eso produce tres problemas: no se sabe cuánto hay de cada producto, se pierde el rastro de lo que los clientes deben ("fiado") y se pasa la fecha de vencimiento de productos perecederos.

TIENDAS S.M ayuda a:

1. Saber **cuánto hay** de cada producto y cuándo hay que reponer.
2. **Vender** (de contado y a crédito) y que el inventario se descuente solo.
3. Controlar **a quién se le fía**, cuánto debe y cuánto ha abonado.
4. (Cuando haya tiempo) controlar **lotes y vencimientos** y avisar con anticipación.

Usuario principal: el propietario o vendedor de una tienda de barrio, sin formación técnica, que atiende clientes con prisa. De ahí el requisito de usabilidad (una venta de 5 productos en menos de 1 minuto).

Hasta hoy **no se ha hablado con un propietario real**: no hubo entrevista ni observación en una tienda. Todas las reglas de negocio son propuestas.

---

## 3. Alcance del MVP (priorización MoSCoW)

**Must Have (entra al MVP):** HU-01 a HU-06 y CU-01: productos, entradas de inventario, ventas de contado y a crédito, clientes y abonos. Trazan a RF-01 a RF-09.

**Should Have:** HU-08 (alerta de stock bajo) y HU-07 (lotes y vencimiento).

**Could Have:** HU-09 (alerta de lotes próximos a vencer).

**Won't Have (en esta versión):** facturación, proveedores, categorías, código de barras, reportes formales, devoluciones, descuentos, impuestos, roles avanzados, copias de seguridad y modo sin conexión.

**Requisitos no funcionales** RNF-01 a RNF-05 se mantienen en el MVP.

Nota: el código de barras, las categorías, los proveedores, los pedidos y el corte de caja aparecen en el prototipo de interfaz (sección 13) marcados como **recomendados** o **ampliación CR-02**; no son requisitos aprobados.

---

## 4. Ciclo de vida, trabajo ágil y tablero

- **Modelo de ciclo de vida:** Incremental, con 4 incrementos:
  1. Productos e inventario (entradas).
  2. Ventas.
  3. Clientes y créditos (abonos).
  4. Lotes, vencimientos y alertas.
- **Trabajo ágil:** Kanban con límites de trabajo en curso (WIP) y Sprints de una semana. Definition of Done de 9 puntos (después se le sumaron pruebas automáticas y CI).
- **Tablero (GitHub Projects):** columnas `Backlog | Por hacer (Sprint 1) | En programación | En pruebas y revisión | Terminado`.
  - Límites WIP: En programación = 2, En pruebas y revisión = 1, Por hacer = 10.
  - Sprint 1 (10 tarjetas, issues #1 a #10): T1–T4 (HU-01), T5–T7 (HU-02), T8–T10 (HU-03).
  - Backlog (3 tarjetas): Incremento 2 (ventas), Incremento 3 (clientes y créditos), Incremento 4 (lotes y alertas).
- Para defectos se mapeó el ciclo de vida a las columnas: Abierto = Por hacer, En progreso = En programación, En revisión = En pruebas y revisión, Cerrado = Terminado. "Reabierto" vuelve a En programación con la etiqueta `reabierto`.

---

## 5. Requisitos

### 5.1 Requisitos funcionales (RF-01 a RF-13)

| ID | Requisito | Prioridad | Historia |
| --- | --- | --- | --- |
| RF-01 | Registrar, consultar y actualizar productos | Must | HU-01, HU-02 |
| RF-02 | Precio de compra y de venta | Must | HU-01 |
| RF-03 | Cantidad disponible por producto | Must | HU-03 |
| RF-04 | Entradas y salidas de inventario | Must | HU-03 |
| RF-05 | Registrar ventas | Must | HU-04 |
| RF-06 | Descontar del inventario lo vendido | Must | HU-04 |
| RF-07 | Registrar clientes | Must | HU-05 |
| RF-08 | Venta a crédito asociada a un cliente | Must | CU-01 |
| RF-09 | Abonos y saldo pendiente | Must | HU-06 |
| RF-10 | Registrar lotes | Should | HU-07 |
| RF-11 | Fecha de vencimiento del lote | Should | HU-07 |
| RF-12 | Alerta de stock bajo | Should | HU-08 |
| RF-13 | Alerta de lotes próximos a vencer | Could | HU-09 |

### 5.2 Requisitos no funcionales

| ID | Requisito (métrica propuesta, por validar) |
| --- | --- |
| RNF-01 | Usabilidad: una venta de 5 productos se registra en menos de 1 minuto |
| RNF-02 | Desempeño: consultas en menos de 2 segundos con 1.000 productos |
| RNF-03 | Seguridad: los datos de clientes solo se ven con credenciales |
| RNF-04 | Consistencia: la venta se guarda toda o no se guarda |
| RNF-05 | Mantenibilidad: los cambios no rompen lo que ya funcionaba (pruebas de regresión) |

Además hay 5 restricciones (R-01 a R-05) en el catálogo de la FPI-05; no se detallan aquí.

### 5.3 Historias de usuario y caso de uso (FPI-06)

Nueve historias con criterios de aceptación en formato Gherkin y un caso de uso formal:

- HU-01 registrar producto · HU-02 actualizar precio · HU-03 registrar entrada de mercancía.
- HU-04 registrar venta (de contado o a crédito) · HU-05 registrar cliente · HU-06 registrar abono y consultar saldo.
- HU-07 lotes y vencimiento · HU-08 alerta de stock bajo · HU-09 alerta de lotes por vencer.
- **CU-01: venta a crédito**, el flujo crítico del sistema (buscar productos, validar stock, validar límite de crédito, descontar inventario, crear la deuda, todo en una sola operación).

### 5.4 Hallazgos de la revisión técnica de requisitos (FPI-08)

| ID | Hallazgo |
| --- | --- |
| H-1 | RF-04 solo tenía entrada (HU-03); la salida manual (merma, daño) está por confirmar |
| H-2 | No estaba definido qué pasa con stock insuficiente (propuesta: rechazar y decir cuántas hay) |
| H-3 | RNF-03 no tenía historia que lo implemente → dio origen a CR-01 |
| H-4 | "Consultas" (FPI-04) frente a "reportes" (FPI-07): saldo y abonos en pantalla son parte de RF-09; los reportes formales siguen Won't Have |
| H-5 | Nivel mínimo de stock y días de aviso sin valor definido |

### 5.5 Solicitudes de cambio

- **CR-01:** acceso con usuario y contraseña. **Aplazada**: depende de que el propietario confirme si habrá usuarios y roles. RNF-03 se mantiene como requisito sin pantalla ni código.
- **CR-02:** ampliar el modelo a 29 entidades (proveedores, pedidos, caja, devoluciones, roles, etc.) según la descripción del negocio que el desarrollador obtuvo de una IA. **No aprobada**: no cambia el alcance del MVP.

### 5.6 Glosario (lenguaje ubicuo)

- **Existencias:** cantidad disponible de un producto (no usar "stock" ni "inventario" a secas en el dominio).
- **Venta:** operación de contado o a crédito.
- **Crédito / fiado:** deuda del cliente con la tienda.
- **Límite de crédito:** tope que un cliente puede deber.
- **Pago mixto:** un pago con parte en efectivo y parte por transferencia (CR-02).
- **Lote:** grupo de unidades con la misma fecha de vencimiento.
- **Corte de caja:** cierre de turno (CR-02).

---

## 6. Modelo de dominio (FPI-09)

Se modelaron **29 entidades** y se clasificaron para no mezclar lo aprobado con lo propuesto:

- **Núcleo (respaldadas por requisitos validados):** Producto, Ubicacion, Lote, Existencia, MovimientoInventario, Venta, DetalleVenta, Cliente, CuentaPorCobrar, Pago, AplicacionPago, Alerta.
- **Ampliación (de la descripción del negocio, CR-02):** Categoria, Empleado, Proveedor, ProductoProveedor, PedidoCompra, DetallePedido, RecepcionCompra, DetalleRecepcion, Caja, SesionCaja, DetallePago.
- **Sugerencia de la IA (no respaldada por la descripción):** Devolucion, DetalleDevolucion, MovimientoCaja, Usuario, Rol, ConfiguracionAlerta.

Hay un modelo entidad-relación en notación pata de gallo (imágenes `MER_TIENDAS_SM_general.png` y `MER_TIENDAS_SM_completo_con_atributos.png`, generadas con Graphviz). **El código Python implementa solo 8 de esas entidades** (las del flujo crítico), sin Lote.

---

## 7. Diseño: UML selectivo y SOLID (FPI-10 y FPI-11)

**Criterio:** modelar solo donde hay riesgo, no todo el sistema. Se modeló únicamente **CU-01** (venta a crédito): diagrama de casos de uso, diagrama de clases de dominio y de diseño, y diagrama de secuencia.

**Clases del flujo crítico antes del refactor SOLID:** Producto, Lote, Existencia, Venta, DetalleVenta, Cliente, CuentaPorCobrar.

**Violaciones SOLID encontradas y resueltas (11 elementos al final):**

1. `ServicioDeVentas` hacía demasiado (S) → se separó en `ControlInventario` y `ControlCredito`.
2. `Cliente` tenía una regla de crédito y dependía de `CuentaPorCobrar` (S y acoplamiento) → la regla se movió a `ControlCredito`; no queda ciclo.
3. `ServicioDeVentas` dependía de la persistencia concreta (D) → interfaz `RepositorioDeVentas`.

No se aplicó O (no se aprobó variar tipos de pago, CR-02), ni I ni L (no hay herencia ni interfaces grandes).

**Ajuste posterior (FPI-12):** `Cliente` recuperó el cálculo puro `puede_endeudarse(monto, saldo_pendiente)`, recibiendo el saldo como parámetro. No reintroduce la dependencia de `CuentaPorCobrar`.

**Ajustes al implementar (registrados en la FPI-12):** `Existencia` va ligada directo al `Producto` (sin `Lote`, deuda DT-01); `guardar_transaccion` también recibe las existencias; los repositorios de productos y clientes son clases concretas (solo `RepositorioDeVentas` es abstracción); los abonos son una tabla simple (DT-03); se agregaron `ServicioDeProductos` y `ServicioDeClientes` para los flujos simples (HU-01 a HU-03, HU-05).

---

## 8. Tecnología y código del MVP

### 8.1 Decisiones tecnológicas

- **Lenguaje:** Python 3 (solo biblioteca estándar, sin dependencias externas).
- **Base de datos:** SQLite (un archivo, sin servidor).
- **Interfaz:** aplicación de escritorio con **Tkinter** → **todavía no está construida**.
- **Pruebas:** `unittest`.
- **Dinero:** números enteros en pesos colombianos (sin centavos).
- **Estilo:** `snake_case`, nombres en español.

### 8.2 Estructura del paquete `tiendas_sm/`

| Archivo | Contenido |
| --- | --- |
| `dominio.py` | `Producto`, `Existencia`, `Cliente`, `Venta`, `DetalleVenta`, `CuentaPorCobrar`, enums `EstadoVenta` y `EstadoCuenta`, excepciones `StockInsuficiente` y `CreditoNoPermitido`, constante `PLAZO_POR_DEFECTO_DIAS = 30` |
| `servicios.py` | `ServicioDeProductos`, `ServicioDeClientes`, `ControlInventario`, `ControlCredito`, `ServicioDeVentas`, y `LineaDeVenta` (namedtuple) |
| `repositorios.py` | `RepositorioDeVentas` (abstracta), `RepositorioDeVentasSqlite`, `RepositorioDeProductos`, `RepositorioDeClientes` |
| `base_de_datos.py` | Conexión SQLite y esquema |
| `validaciones.py` | `exigir_mayor_a_cero` |
| `aplicacion.py` | `Aplicacion`: arma todos los objetos y los conecta (punto único de composición) |

Tamaño aproximado: 537 líneas del sistema y 717 de pruebas.

### 8.3 Esquema de la base de datos (8 tablas)

`productos`, `existencias`, `movimientos_inventario`, `clientes`, `ventas`, `detalles_venta`, `cuentas_por_cobrar`, `abonos`. Claves foráneas activas. Cada línea de venta guarda el **precio del momento**.

### 8.4 Reglas de negocio implementadas (y con qué mensaje)

- **Producto:** nombre obligatorio, precios no negativos.
- **Existencias:** descontar o aumentar exige cantidad mayor a cero. Si se pide más de lo que hay: `Solo hay N disponibles de <producto>`.
- **Venta a crédito (CU-01):** el mismo producto en varias líneas suma las cantidades; el cliente debe tener crédito habilitado; el total no puede superar `límite − deuda`; el vencimiento usa el **plazo del cliente**; venta, detalles, deuda y existencias se guardan en **una sola transacción** (todo o nada, RNF-04).
- **Abonos:** mayor a cero y no mayor al saldo. Mensaje: `El abono (X) no puede ser mayor al saldo pendiente, que es Y`. Al llegar el saldo a cero, la cuenta queda `PAGADA`.
- **Ids inexistentes:** `El producto no existe`, `La cuenta por cobrar no existe`.

### 8.5 Lo que el código Python **no** tiene

Interfaz gráfica, **venta de contado** (solo existe `registrar_venta_a_credito`; RF-05 está parcial), lotes y vencimientos, alertas, salida manual de inventario, control de clientes duplicados, usuarios y contraseñas, `Venta.anular` sin uso (DT-08).

---

## 9. Calidad: refactoring, deuda técnica y defectos

### 9.1 Auditoría y refactoring (FPI-12)

El primer borrador del código pasaba todas sus pruebas pero tenía **8 code smells**: método largo (`registrar_venta_a_credito`, 32 líneas), Feature Envy (regla de crédito usando datos de `Cliente`), código duplicado (la misma validación 5 veces), números y cadenas mágicas, clase grande (un repositorio único con 14 métodos), dependencia oculta, código muerto y nombres poco claros.

Técnicas aplicadas: Extract Method, Move Method, Extract Class, enums, constantes, `namedtuple`, inyección de dependencias. Las mismas pruebas pasaron antes y después.

| Medida | Antes | Después |
| --- | --- | --- |
| Funciones de más de 15 líneas | 3 | 0 |
| Líneas de `registrar_venta_a_credito` | 32 | 9 |
| Validación copiada | 5 | 1 |
| Números mágicos | 17 | 1 |
| Código muerto | 3 | 0 |

Lo que **no mejoró**: funciones con más de 3 parámetros (6 → 7) y el tamaño del código (436 → 526 líneas).

### 9.2 Deuda técnica registrada

| ID | Descripción | Estado |
| --- | --- | --- |
| DT-01 | Existencias sin lote ni vencimiento | Abierta |
| DT-02 | El vencimiento ignoraba el plazo del cliente | **Pagada** (BUG-02) |
| DT-03 | Abonos en tabla simple, sin modelo de pagos | Abierta |
| DT-04 | Cobertura sin medir y sin pruebas de interfaz | Parcial (cobertura medida y en CI; faltan pruebas de interfaz) |
| DT-05 | Constructores con muchos parámetros | Aceptada |
| DT-06 | Ids inexistentes daban `AttributeError` | **Pagada** (BUG-01) |
| DT-07 | Mensajes de stock y de abono sin las cantidades | **Pagada** |
| DT-08 | `Venta.anular()` sin historia ni pruebas | Abierta |

### 9.3 Defectos gestionados formalmente (FPI-15)

- **BUG-01:** registrar entrada, actualizar precio o abonar con un id inexistente daba `AttributeError`. Ahora lanza `ValueError` claro y no guarda nada. 6 pruebas de regresión.
- **BUG-02:** el vencimiento del crédito era siempre a 30 días. Ahora usa el plazo del cliente. 3 pruebas nuevas más una existente.
- Ambos tienen informe en `docs/defectos/` (pasos, resultado esperado y obtenido, entorno, causa, corrección) y plantilla de issue.
- **DT-07** salió de las pruebas de caja negra derivadas de los criterios Gherkin (stock y abono).

---

## 10. Pruebas

**77 pruebas, todas en verde** (`python -m unittest discover -s tests`). Cobertura de líneas **99,0 %** (377 de 381), medida con el módulo `trace`.

| Archivo | Tipo | Pruebas |
| --- | --- | --- |
| `test_comportamiento.py` | Flujo completo con SQLite real (escenarios de la FPI-06) | 23 |
| `test_unitarias_dobles.py` | Unitarias aisladas con stubs y mocks (mock solo donde la interacción es el comportamiento) | 31 |
| `test_caja_negra.py` | Caja negra CN-01 a CN-08, derivadas de los criterios Gherkin y valores límite | 8 |
| `test_integracion_incremental.py` | Integración ascendente (Bottom-Up) por niveles | 6 |
| `test_defectos_corregidos.py` | Regresión de BUG-01 y BUG-02 | 9 |

- **Integración ascendente:** nivel 1 dominio → 2 dominio + SQLite → 3 + controles → 4 + `ServicioDeVentas` → 5 + interfaz (pendiente).
- **Complejidad ciclomática:** máximo V(G) = 5 en `Producto.__init__`; `_armar_venta` = 3. Promedio de 1,39 en 76 funciones.
- La prueba de falla simulada usa un *trigger* de SQLite que lanza error al crear la deuda; comprueba que no queda nada a medias.

**Importante:** son pruebas de **verificación** (el código cumple lo escrito). No hay **validación** con el propietario ni pruebas de interfaz.

---

## 11. Git, integración continua y releases

### 11.1 Flujo de trabajo

- **GitHub Flow:** `main` protegida, ramas de corta vida (`feature/`, `fix/`, `refactor/`, `docs/`, `test/`, `ci/`), Pull Request con revisión de código, fusión con **merge commit** (no squash) para conservar commits atómicos.
- Mensajes de commit: `tipo(alcance): qué se hizo`, con el porqué en el cuerpo.
- Documentado en `docs/FLUJO_GIT.md` del repositorio, con plantilla de Pull Request.
- Versionamiento SemVer. Etiquetas previstas: `v0.1.0` (primer release del MVP sin interfaz) y `v0.1.1` (correcciones BUG-01/BUG-02 y cierre).

### 11.2 Plan de Pull Requests (preparados con scripts, ver sección 12)

| PR | Rama | Contenido |
| --- | --- | --- |
| 1 | `feature/dominio-servicios-persistencia` | Primer código, 23 pruebas y script de calidad (5 commits) |
| 2 | `refactor/auditoria-calidad-fpi12` | Refactoring de los 8 smells y evidencia (5 commits) |
| 3 | `test/suite-unitaria-caja-negra` | Unitarias, caja negra, integración, medidores (6 commits) |
| 4 | `ci/pipeline-github-actions` | Pipeline de CI |
| 5 | `fix/bug-01-ids-inexistentes` | Corrección de BUG-01 |
| 6 | `fix/bug-02-plazo-credito` | Corrección de BUG-02 y regresión (5 commits) |
| 7 | `docs/cierre-semestre` | Demo, métricas, bitácora de IA y hoja de ruta (4 commits) |

Además, un **conflicto de mezcla simulado**: dos ramas cambian la misma línea (`PLAZO_POR_DEFECTO_DIAS`, 15 contra 45) y se resuelve conservando 30 por criterio de negocio.

### 11.3 Integración continua

`.github/workflows/ci.yml` (GitHub Actions), job `pruebas`, se ejecuta en cada Pull Request hacia `main` y en cada push a `main`:

1. **Build:** `compileall` y arma la `Aplicacion`.
2. **Lint:** `ruff` con reglas de errores reales (`E9, F63, F7, F82, F401, F841`).
3. **Test:** toda la suite.
4. **Cobertura:** falla si baja del 90 %.

Sin secretos, `permissions: contents: read`. Para que bloquee la fusión hay que exigir el chequeo `pruebas` en las reglas de `main` (se hace en la interfaz de GitHub).

---

## 12. Herramientas y scripts del proyecto

Dentro del paquete del proyecto (raíz):

| Archivo | Para qué sirve |
| --- | --- |
| `medir_calidad.py` | Funciones largas, números mágicos, clases grandes y código muerto |
| `medir_complejidad.py` | Complejidad ciclomática V(G) por función |
| `medir_cobertura.py` | Cobertura de líneas; con `--minimo 90` falla si baja |
| `correr_regresion.py` | Elige las pruebas de regresión según los archivos que cambiaron |
| `demo_en_vivo.py` | Demostración narrada del flujo crítico en 8 pasos (datos ficticios, en memoria) |
| `calcular_metricas.py` | Métricas reales de Git y de GitHub (con JSON de `gh`) para la retrospectiva |
| `docs/CI.md`, `docs/FLUJO_GIT.md`, `docs/PRUEBAS.md`, `docs/defectos/`, `docs/BITACORA_IA.md`, `docs/HOJA_DE_RUTA_IS2.md` | Documentación del repositorio |
| `evidencia_fpi12/`, `evidencia_fpi14/`, `evidencia_fpi15/` | Resultados guardados de pruebas, métricas y simulación del pipeline |

**Kits de Git** (cada uno con un script `.sh`, contenido por commit, textos de los PR y un `LEEME_PRIMERO.md`): Guías 13, 14, 15 y 16. Crean ramas y commits atómicos **en el repositorio del propio desarrollador**; no hacen `push` ni fusionan. Se probaron de punta a punta en un repositorio de prueba local.

---

## 13. Prototipos de interfaz

### 13.1 Panel HTML (`tiendas_sm_dashboard.html`)

Un solo archivo autónomo (sin internet) inspirado en un punto de venta de escritorio. Paleta verde, 14 pantallas y 12 ventanas emergentes:

- **Operación:** Dashboard, Punto de venta (búsqueda por código, ticket, cobro de contado y a crédito, atajos F2/F9/F4), Ventas.
- **Inventario:** Productos, Existencias (entradas, salida manual), Lotes y vencimientos, Alertas.
- **Clientes y crédito:** Clientes, Créditos y abonos.
- **Ampliación CR-02 (etiquetada, se puede ocultar):** Proveedores, Pedidos, Corte de caja.
- **Sistema:** Configuración (días de aviso, plazo, lista "por confirmar"), Estado del proyecto.

Reglas fieles al código Python (stock, límite, abonos, todo o nada). Lleva su propia lógica con **21 pruebas** y **24 casos de interfaz** con un navegador simulado. No se abrió en un navegador real. Datos ficticios guardados en el navegador (localStorage).

En el panel ya funcionan cosas que **no existen en el código Python**: venta de contado, lotes con venta del que vence primero, alertas, proveedores, pedidos, corte de caja.

### 13.2 Wireframes (`Wireframes_TIENDAS_SM.pdf`)

22 páginas en horizontal, escala de grises, con el mismo formato del documento de wireframes de un compañero (UP TIME): portada, convenciones, mapa de navegación, P1 a P14, M1 a M12 y tabla de trazabilidad pantalla–requisito. Los números de ejemplo coinciden con los del panel HTML.

---

## 14. Uso de inteligencia artificial (declaración honesta)

- **La IA generó casi todo el contenido técnico:** los documentos, el código del MVP, las pruebas, los diagramas, los scripts de Git y de CI, el panel HTML y los wireframes. El desarrollador definió el contexto y las decisiones y debe poder explicar y defender todo.
- Proporción del código generada con IA: **prácticamente el 100 %**. Cuánto leyó, ejecutó y modificó el desarrollador: **por confirmar por él**.
- **Bitácora (`docs/BITACORA_IA.md`):** 20 hallazgos **reales** en lo generado por IA (8 smells, 2 defectos de lógica, 2 incumplimientos de criterios encontrados por caja negra, errores en pruebas/herramientas/medición, 1 inconsistencia entre documento y código y 3 en el modelo entidad-relación de una IA real).
- **14 ejemplos de taller son simulados:** el prompt y la respuesta de la IA en el ejercicio de auditoría de las guías 3 a 15 se redactaron como ejemplo y se declararon así. **No cuentan como hallazgos reales.**
- No se usaron datos reales de clientes, contraseñas ni información confidencial.
- Única herramienta externa: `ruff` (solo en el CI); su licencia debe verificarse antes de IS II.

---

## 15. Estado real del proyecto

### 15.1 Hecho y verificado en el entorno de trabajo

- Análisis, requisitos, historias, priorización, revisión técnica, modelo de dominio, diseño y SOLID (documentos).
- Código del MVP: productos, entradas, **venta a crédito**, clientes, abonos; 77 pruebas en verde; cobertura 99,0 %.
- Refactoring de 8 smells, 2 defectos corregidos, deuda registrada.
- Scripts, kits de Git, pipeline de CI escrito, panel HTML y wireframes.

### 15.2 Parcial

- **RF-05 (ventas):** solo venta a crédito en el código Python.
- **RF-04:** solo entradas; la salida manual está por confirmar.
- **RF-07:** clientes sin control de duplicados (datos por definir).
- **RNF-05:** hay pruebas de regresión; falta comprobar el pipeline real.
- **FPI-04:** clasificación de stakeholders hecha; falta el trabajo de campo (entrevista y observación).

### 15.3 No hecho

- Interfaz de escritorio con Tkinter (no se pudo construir ni probar: el entorno de trabajo no tenía Tkinter).
- Venta de contado en el código; lotes, vencimientos y alertas en el código.
- Validación con el propietario.
- RNF-01 y RNF-02 sin medir (necesitan la interfaz). RNF-03 sin implementar (CR-01 aplazada).
- Abonos con modelo de pagos completo (DT-03) y todo CR-02.

### 15.4 Desconocido (lo sabe solo el desarrollador)

**No se sabe si el desarrollador ejecutó los kits en su repositorio real.** Por tanto, no hay confirmación de: main protegida, Pull Requests abiertos y fusionados, número de PR e issues, revisión de código humana, pipeline en verde en GitHub, conflicto resuelto con capturas, releases `v0.1.0` y `v0.1.1`, ni las métricas reales del repositorio. En las fichas esos campos quedaron **en amarillo** para completarlos con datos reales.

---

## 16. Decisiones por confirmar con el propietario

1. ¿Qué hacer cuando se vende más de lo que hay? (propuesta: rechazar e informar cuántas hay).
2. ¿Qué lote se descuenta primero? (propuesta: el que vence antes).
3. Reglas del crédito: tope, plazo y mora/intereses (hoy el plazo es 30 días por defecto y cada cliente tiene el suyo).
4. Datos que se piden para registrar un cliente y cómo evitar duplicados.
5. Nivel mínimo de stock: ¿uno general o uno por producto?
6. Días de anticipación para avisar un vencimiento (ejemplo: 7).
7. ¿Se necesita la salida manual de mercancía (mermas, daños, consumo propio)?
8. ¿Habrá usuarios y contraseñas? (CR-01).
9. ¿Se aprueba ampliar el sistema (CR-02: proveedores, pedidos, caja, pagos mixtos, devoluciones)?
10. Forma de calcular ganancias (hoy no se calculan).

---

## 17. Qué es real, qué es ejemplo y qué es propuesta

| Cosa | Naturaleza |
| --- | --- |
| Código Python, pruebas, scripts, kits, panel HTML y wireframes | **Reales**: existen y se ejecutaron en el entorno de trabajo |
| Resultados "77 pruebas OK", "99,0 % cobertura", métricas antes/después | **Reales**: medidos en el entorno de trabajo |
| Ejecución del pipeline en GitHub, PR, revisiones, releases, métricas del repositorio | **No verificadas**: dependen de que el desarrollador ejecute los kits |
| Nombres de clientes, proveedores, productos, montos y teléfonos | **Ficticios** (ejemplos) |
| Reglas de negocio (stock, lote, plazo, límite, mínimo, días de aviso) | **Propuestas** sin validar |
| Ejercicio de IA de las guías 3 a 15 | **Simulado** (redactado como ejemplo) |
| Módulos de proveedores, pedidos y caja | **Ampliación CR-02** sin aprobar |

**Reglas de trabajo acordadas para seguir:** no inventar evidencia (números de PR, enlaces, revisiones, métricas); declarar qué es simulado; no usar datos reales; dejar lo pendiente en las fichas como pendiente y no como hecho.

---

## 18. Lista de entregables que se generaron

**Documentos Word (uno por guía, ya rellenados):** guías 3 a 16, con nombre `Guia_N_<tema>_yamid_sneider_merchan_castro.docx`. Las guías 1 y 2 las hizo el desarrollador antes de este trabajo.

**Código y paquetes:** `tiendas_sm_proyecto_g16.zip` (versión final del proyecto; contiene el código, las pruebas, los scripts y la documentación). Los zips de las guías 12, 14 y 15 son versiones anteriores del mismo proyecto.

**Kits de Git:** `kit_git_guia13.zip`, `kit_git_guia14.zip`, `kit_git_guia15.zip`, `kit_git_guia16.zip`.

**Prototipos:** `tiendas_sm_dashboard.html` y `Wireframes_TIENDAS_SM.pdf`.

**Diagramas:** `MER_TIENDAS_SM_general.png` y `MER_TIENDAS_SM_completo_con_atributos.png` (los diagramas UML de casos de uso, clases y secuencia están dentro de los Word de las guías 9 y 10).

**Insumo original del desarrollador:** `bd_tienda_sm.txt` (descripción del negocio de la que salió el modelo de 29 entidades) y las guías en blanco de cada tema.

**Nota:** el historial completo de la conversación original se guardó en una transcripción interna que el desarrollador **no puede abrir**; por eso este archivo debe bastar como contexto.

---

## 19. Documentos formales, base de datos, póster y paquete para Claude Code

Además de las 16 fichas, la carpeta de entregas contiene estos archivos del proyecto. Se revisaron por dentro (portada y títulos de sección) para describirlos; **este archivo no resume su contenido detallado**: si hace falta un dato exacto, hay que abrir el documento.

| Archivo | Qué es |
| --- | --- |
| `ERS_TIENDAS_SM.docx` | **Especificación de Requisitos de Software.** Control y aprobación del documento; alcance y fuera de alcance; actores; flujo funcional; estados del negocio; requisitos funcionales por módulo (productos y precios, inventario y bodega, ventas, clientes y créditos, lotes y alertas); reglas de negocio obligatorias; datos de venta, ticket y consultas; requisitos no funcionales; arquitectura de referencia y SOLID; auditoría; criterios de aceptación; supuestos y decisiones pendientes; matriz de trazabilidad (Anexo A). |
| `DAD_TIENDAS_SM.docx` | **Documento de Análisis y Diseño.** Principios y SOLID; proceso y estados; actores y permisos; casos de uso (catálogo y críticos); arquitectura de software y reglas de dependencia; diseño de datos e integridad; interfaces y contratos de servicios; seguridad y auditoría; experiencia de usuario (sección 10). |
| `DDS_TIENDAS_SM.docx` | **Documento de Diseño Detallado del Software.** Objetivos verificables; componentes y reglas de dependencia; modelo de dominio y agregados; estados y evaluación determinista del crédito; **contratos de casos de uso**: UC-01 venta a crédito (CU-01), **UC-02 venta de contado (CU-02, por construir)**, UC-03 productos, UC-04 entrada de mercancía, UC-05 clientes, UC-06 abono, **UC-07 lote (por construir)**, **UC-08 alertas (por construir)**; diseño de datos. |
| `Diseno_Base_de_Datos_TIENDAS_SM_yamid_sneider_merchan_castro.docx` | **Diseño de la base de datos** (autor: Yamid, v1.0, octubre de 2026). Motor de referencia SQLite 3 (portable a PostgreSQL y MySQL). |
| `base_de_datos_tiendas_sm.zip` | Paquete de la base de datos: `01_esquema.sql` (esquema de **29 tablas**), `02_datos_ejemplo.sql` (datos ficticios), `03_consultas.sql` (6 consultas), `probar_bd.py` (crea la base en memoria, carga los datos, ejecuta las consultas y prueba 17 inserciones inválidas que deben rechazarse) y `diagramas/` (MER general, `mer_d1` a `mer_d9` y `mr_d1` a `mr_d9`). **Ojo:** este esquema de 29 tablas corresponde al modelo ampliado (CR-02); el código Python del MVP usa solo 8 tablas. |
| `Poster_TIENDAS_SM_YamidMerchan_A2.pdf` | Póster A2 del proyecto (planteamiento del problema, solución desarrollada con el prototipo HTML y datos de ejemplo, entre otros). |
| `TIENDAS-SM_listo_para_claude_code.zip` | El proyecto final listo para abrirlo con Claude Code: código y pruebas idénticos a la versión `g16` (77 pruebas OK) más `CLAUDE.md` (reglas de trabajo, stack, estructura, comandos, estado y pendientes) y `docs/contexto/` (contexto, requisitos, decisiones, estado y pendientes, prompt inicial). Su copia del panel HTML en `docs/referencia/` es **una versión anterior** (Marta R. con límite de $ 50.000); la vigente es `tiendas_sm_dashboard.html`. |
| `contexto_claude_code.zip` | Solo el contexto de ese paquete (`CLAUDE.md`, `docs/contexto/`, `LEEME_COMO_USARLO.md`); es un subconjunto del zip anterior. |
| `completar_guia13.zip` | `COMPLETAR_GUIA13.md` y `reunir_evidencia_guia13.sh`: ayuda para reunir la evidencia real de la Guía 13 en el repositorio. |
| `dashboard_tiendas_sm.html` | **Versión antigua** del panel (pestañas "La tienda" y "El proyecto"). Quedó reemplazada por `tiendas_sm_dashboard.html`. |
| `tiendas_sm_proyecto.zip`, `_g14.zip`, `_g15.zip` | Versiones anteriores del proyecto. Reemplazadas por `tiendas_sm_proyecto_g16.zip`. |

**Diferencias que conviene tener presentes:** el ERS, el DAD y el DDS describen el sistema con un alcance y un detalle mayores que los del MVP codificado (por ejemplo, el DDS ya define la venta de contado, los lotes y las alertas como casos de uso "por construir"). Cuando un documento formal y el código no coincidan, **el código y las 16 fichas describen lo que realmente existe hoy**.

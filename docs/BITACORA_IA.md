# Bitácora de auditoría del uso de IA — TIENDAS S.M (FPI-16)

Consolidado de las guías 1 a 16, más la etapa de IS II con Claude Code (sección 7). Se separan con claridad los hallazgos **reales** de los ejemplos **simulados**.

## 1. Cómo se usó la IA
- La IA generativa (Claude) produjo borradores de los documentos de las guías, el código del MVP, las pruebas, los diagramas,
  los scripts de Git y de CI, y el panel HTML. El desarrollador definió el contexto, tomó las decisiones y debe poder explicar
  y defender todo (política de uso de IA del proyecto).
- Tamaño del código actual: 537 líneas del sistema (`tiendas_sm/`) y 717 de pruebas (`tests/`).
  Proporción generada con apoyo de IA: **prácticamente el 100 %** (el desarrollador no lo escribió a mano).
  Revisado y validado por el desarrollador: **[CONFIRMAR: qué partes leíste, ejecutaste y modificaste]**.
- Datos: ninguna prueba ni consulta a la IA usó datos reales de clientes, contraseñas ni información confidencial.

## 2. Hallazgos reales en lo generado con IA (20 de las guías 1 a 16; 11 más en la sección 7)
| N.° | Guía | Hallazgo | Cómo se detectó |
| --- | --- | --- | --- |
| 1–8 | 12 | 8 code smells en el primer borrador: Long Method, Feature Envy, código duplicado (5 copias), cadenas y números mágicos, clase grande, dependencia oculta, código muerto, nombres poco claros | Auditoría de código y script `medir_calidad.py` |
| 9 | 13 | Ids inexistentes producían `AttributeError` (BUG-01, antes DT-06) | Revisión de código del PR 1, ejecutando el código |
| 10 | 12 | El vencimiento del crédito ignoraba el plazo del cliente (BUG-02, antes DT-02) | Auditoría de código |
| 11–12 | 14 | Mensajes de stock insuficiente y de abono excedido sin las cantidades que piden los criterios (CN-02 y CN-03) | Pruebas de caja negra derivadas de los criterios Gherkin |
| 13 | 14 | Primera medición de cobertura errónea (63,9 % en vez de 98,7 %) por un error en el script | Comparar el resultado con lo esperado |
| 14 | 12 | Una prueba generada estaba mal escrita (contenía instrucciones sin sentido) | Revisión de las pruebas al ejecutarlas |
| 15 | 15 | Una prueba marcada como falla esperada que ya pasaba hacía fallar toda la suite | Probar el script del kit de punta a punta |
| 16 | 15 | Un parche del README no encajaba con el README real | Probar el script del kit de punta a punta |
| 17 | 16 | La FPI-10 decía que la venta de contado quedaba cubierta, pero el código solo tiene la venta a crédito (RF-05 parcial) | Al armar el panel del proyecto y cruzar requisitos con el código |
| 18–20 | 9 | En el modelo entidad-relación propuesto por una IA: entidades más allá de los requisitos (Devolución, Usuario y Rol, ConfiguracionAlerta, MovimientoCaja); nombre `costo_compra_referencia` distinto de «precio de compra»; fórmula que usa `cantidad_recibida`, que no es un atributo | Comparar con el catálogo de requisitos y los términos del negocio |

## 3. Ejemplos de taller simulados (14) — no cuentan como hallazgos reales
En el ejercicio 5 de las guías 4 a 15 (y en los ejercicios 4 y 5 de la guía 3) el prompt y la respuesta de la IA fueron
**redactados como ejemplo** para practicar la auditoría. Sus hallazgos (sobrediseño, criterios subjetivos, mocks innecesarios,
secretos en YAML, etc.) ilustran riesgos reales, pero no fueron salidas obtenidas de una ejecución registrada.
**[CONFIRMAR: si repetiste alguno con una IA real, súmalo a la sección 2.]**

## 4. Licencias y dependencias
- Rechazadas: **0** de forma formal. Decisión de diseño: el MVP usa solo la biblioteca estándar de Python (sin dependencias externas).
- Única herramienta externa: `ruff`, solo en el pipeline de CI. **Verificar su licencia antes de IS II.**

## 5. Seguridad
- Ningún secreto en el repositorio ni en el pipeline (`permissions: contents: read`).
- Riesgo ilustrado en el taller (simulado): token y contraseña en texto plano y `|| true` en un YAML generado por IA.

## 6. Lecciones sobre el uso de IA
1. Las pruebas escritas por la misma IA que escribió el código comparten sus puntos ciegos: los casos de caja negra derivados de
   los criterios de aceptación encontraron defectos que 23 pruebas de la IA no vieron.
2. La IA añade alcance si no se le pone límite (29 entidades frente a 8 con requisito).
3. Todo script o configuración generado debe ejecutarse de punta a punta antes de confiar en él.
4. «Revisado» solo vale si el desarrollador puede explicar el código sin la IA.

## 7. Tareas de IS II con Claude Code (noviembre de 2026)

### 7.1 Qué se hizo y cómo
- **Herramienta:** Claude Code (asistente de programación de Anthropic) trabajando sobre el repositorio local, siguiendo `CLAUDE.md` y los
  mensajes de tareas preparados para las fichas FPI-17 a FPI-24 (tareas 1 a 8).
- **Trabajo hecho con la IA:** venta de contado (UC-02), DT-09, puertos del núcleo (ADR-04, Guía 4), TD-01, TD-04, TD-14, listar clientes,
  interfaz Tkinter del punto de venta (tarea 8), escenarios E-02/E-03/E-05, migración de `ventas`, TD-05 y TD-07 (parcial), y la evidencia
  TDD de la FPI-24. En total, 56 commits después del commit inicial (contando los 13 merges), en 13 ramas fusionadas en `main` con *merge commit*.
- **Forma de trabajo:** la IA proponía un plan, el desarrollador lo aprobaba o lo ajustaba, y después se escribía primero la prueba que
  fallaba. Al final de esta etapa el desarrollador pidió que la IA continuara sin aprobar cada paso (interfaz, tareas 5, 6 y 7).
- **Tamaño actual:** 901 líneas en `tiendas_sm/`, 343 en la interfaz (`interfaz_tk/` e `iniciar_tienda.py`) y 1.658 en `tests/`.
  Generado con IA: prácticamente el 100 %. Revisado por el desarrollador: **[CONFIRMAR: qué partes leíste, ejecutaste y modificaste]**.
- **Decisiones que tomó el desarrollador, no la IA:** trabajar solo en local sin GitHub; aprobar cada plan; la numeración TD; la base de datos
  en la carpeta del usuario; los datos de ejemplo con `--datos-de-ejemplo`; fusionar la interfaz sin revisarla a mano.
- **Datos:** solo datos ficticios en pruebas, datos de ejemplo y consultas. Ningún secreto, contraseña ni dato real de clientes.

### 7.2 Hallazgos reales de esta etapa (21 a 31)
Todos ocurrieron en esta sesión de trabajo. Varios son errores **de la propia IA**, detectados antes de fusionar.

| N.° | Hallazgo | Cómo se detectó | Resultado |
| --- | --- | --- | --- |
| 21 | Las ventas descontaban existencias sin registrar su movimiento de inventario (TD-01) | Revisión del código al construir la venta de contado | Corregido con prueba primero |
| 22 | `Cliente` aceptaba nombre vacío, límite negativo y plazo 0; con nombre `None`, SQLite lanzaba `IntegrityError` (DT-09 / TD-04) | Revisión del plan contra el DDS (UC-05) | Corregido en el dominio con prueba primero |
| 23 | Una base creada antes de la venta de contado no tenía las columnas nuevas y vender de contado fallaba | Al revisar la tarea 7 (DIF-06) | Migración con `ALTER TABLE` |
| 24 | Las primeras pruebas de TD-01 provocaban la falla **antes** de insertar el movimiento: no probaban el caso importante | Revisión de las pruebas recién escritas por la IA | Se agregó la prueba de falla en el propio movimiento |
| 25 | El presentador usaba el campo `ticket` para devolver la venta: funcionaba, pero era confuso de defender | Autorrevisión antes del commit | Se cambió a devolver `(venta, error)` |
| 26 | La IA escribió en la documentación un total de pruebas equivocado (101 en vez de 100) y, en otro cambio, una ruta con `\t` que se convirtió en tabulador | Ejecutar las pruebas y revisar el texto con `grep` | Corregidos antes del commit |
| 27 | **La ventana Tkinter pasaba todas sus pruebas automáticas, pero al abrirla de verdad** el panel de cobro salía aplastado, las filas cortaban letras y la línea de mensajes quedaba fuera de la ventana en 1024 × 600 | Abrir la ventana real y tomar capturas | Corregido y comprobado con capturas |
| 28 | La prueba de E-05 relacionaba ventas y movimientos por fecha; en Windows dos ventas seguidas pueden tener la misma fecha y hora, y `movimientos_inventario` no guarda el número de la venta | La prueba falló al ejecutarla | Prueba ajustada; deuda registrada sin número TD |
| 29 | La prueba de E-02 usaba el código de salida 1, el mismo de una excepción sin capturar: podía pasar por la razón equivocada | Autorrevisión de la prueba | Se usa el código 3 |
| 30 | La IA **inventó un número de deuda (TD-15)** en un mensaje de commit sin conocer el catálogo TD de las fichas | Autorrevisión del mensaje | Mensaje corregido («pendiente de numerar») antes de compartir el commit |
| 31 | La venta de contado cambió 4 archivos de `tiendas_sm/` cuando el criterio E-04 permitía 3; y las pruebas de `iniciar_tienda.py` se escribieron después del código | Comparar el trabajo con los criterios de las tareas | Declarado como desviación en `DECISIONES.md` (no se oculta) |
| 32 | La guía de la tarea 13 anunciaba «168 pruebas en verde» con el parche de telemetría; al aplicarlo dieron 172, porque el parche se probó con un `main` anterior | Correr la suite y comparar con la cifra anunciada | Se reporta la cifra real (172) y la causa en `DECISIONES.md` |
| 33 | El log de telemetría guarda la hora en UTC y el tablero agrupa por ese día: una venta nocturna en Colombia aparece al día siguiente | Revisar las líneas reales del `.jsonl` de la prueba | Anotado como recomendación sin aplicar (no se cambió la lógica del parche) |
| 34 | Al registrar en la telemetría la revisión de la base (spans `abrir_base` y `respaldar_base`), el tablero y `slo_mensual.py` los habrían contado como **ventas**, porque no filtraban por operación | Pensar qué otras partes leen el mismo log antes de escribir en él | Prueba en ROJO primero; `solo_ventas` en `slo_mensual.py`, que también usa el tablero |
| 35 | Un comando de la IA dejó un `cat > /dev/null` sobrante que se quedó esperando entrada y bloqueó la terminal 2 minutos; el cambio no se aplicó | Revisar `git status` antes de seguir | Se detuvo la tarea, se comprobó que no hubo cambios a medias y se repitió desde un archivo de script |

### 7.3 Lo que no se verificó
- `ruff` no se ejecutó nunca en esta etapa: no está instalado en el equipo; lo correrá el CI al subir las ramas.
- TD-05 (Python 3.13) se probó simulando la entrada: en el equipo solo hay Python 3.12.
- El pipeline de GitHub, los Pull Requests y sus revisiones **no existen todavía**: todo está en el repositorio local.
- E-01 (venta de 5 productos en menos de 60 s) no se ha medido con personas.

### 7.4 Lecciones nuevas
5. Las pruebas automáticas de una interfaz no ven el diseño: hay que abrir la ventana real (hallazgo 27).
6. La IA también se equivoca en lo «pequeño» (números, rutas, identificadores): hay que revisar textos y mensajes, no solo el código
   (hallazgos 26 y 30).
7. Una prueba que pasa no basta: hay que preguntarse si pasaría aunque el código estuviera mal (hallazgos 24 y 29).

# Bitácora de auditoría del uso de IA — TIENDAS S.M (FPI-16)

Consolidado de las guías 1 a 16. Se separan con claridad los hallazgos **reales** de los ejemplos **simulados**.

## 1. Cómo se usó la IA
- La IA generativa (Claude) produjo borradores de los documentos de las guías, el código del MVP, las pruebas, los diagramas,
  los scripts de Git y de CI, y el panel HTML. El desarrollador definió el contexto, tomó las decisiones y debe poder explicar
  y defender todo (política de uso de IA del proyecto).
- Tamaño del código actual: 537 líneas del sistema (`tiendas_sm/`) y 717 de pruebas (`tests/`).
  Proporción generada con apoyo de IA: **prácticamente el 100 %** (el desarrollador no lo escribió a mano).
  Revisado y validado por el desarrollador: **[CONFIRMAR: qué partes leíste, ejecutaste y modificaste]**.
- Datos: ninguna prueba ni consulta a la IA usó datos reales de clientes, contraseñas ni información confidencial.

## 2. Hallazgos reales en lo generado con IA (20)
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

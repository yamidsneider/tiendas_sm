# Dossier Técnico Final — TIENDAS S.M (FPI-32)

**Autor:** Yamid Sneider Merchan Castro (desarrollador único) · **Fecha:** 5 de noviembre de 2026 · **Programa:** Ingeniería de Software I y II, Universidad de Pamplona.

> Regla de este dossier: cada afirmación tiene su fuente (archivo del repositorio, ficha FPI o medición ejecutada). Lo que todavía no existe se marca **PENDIENTE**. No se inventan URL, PR, ejecuciones ni cifras.

## 1. Ficha técnica

**URL del sistema en producción.** No aplica: TIENDAS S.M es una aplicación de escritorio, sin servidor (ADR-03). Su «producción» definida es la versión Latest de GitHub Releases (ADR-11), que todavía no existe. Se ejecuta en el equipo con python iniciar_tienda.py (base en %LOCALAPPDATA%\TIENDAS_SM\tiendas_sm.db).

**Repositorio y release.** PENDIENTE: el repositorio es solo local. Revisado el 5-nov-2026: .git/config no tiene remoto, no hay etiquetas (refs/tags vacío) y hay 21 ramas locales. Trabajar solo en local fue decisión del desarrollador (bitácora §7.1). Para cerrar: crear el repositorio en GitHub, hacer push, etiquetar v1.0.0 y dejar que corran ci.yml, ci-security.yml y deploy.yml (tarea 16). URL: ______________________.

**Video demo.** PENDIENTE: el video no se ha grabado. Guion de 5 minutos listo en salidas/cierre/Dossier_Final.md: (1) Problema y usuario, 30 s. (2) Venta de contado y a crédito en la ventana real, con rechazo por stock y por cupo, 2 min. (3) Pruebas, cobertura y linter en vivo, 1 min. (4) ADR-03 con datos, 1 min. (5) Qué falta y por qué, 30 s. URL: ______________________.

**Cómo ejecutarlo:** `python iniciar_tienda.py --datos-de-ejemplo` (datos ficticios). Pruebas: `python -m unittest discover -s tests`. Cobertura: `python medir_cobertura.py --minimo 90`.

## 2. Línea de tiempo de IS II (FPI-17 a FPI-31)

| Ficha | Decisión clave | ¿Se mantuvo? | Estado final |
|---|---|---|---|
| FPI-17 | ADR-01: congelar la línea base y evolucionar sin reescribir; pagar primero TD-01 y TD-04 | Se mantuvo | TD-01 y TD-04 pagadas; 77 → 164 pruebas |
| FPI-18 | ADR-02: drivers integridad, usabilidad y mantenibilidad; escenarios E-01 a E-05 | Se mantuvo | E-02, E-03 y E-05 automatizados; E-01 sin medir con personas |
| FPI-19 | ADR-03: monolito de escritorio con SQLite local | Se mantuvo | Base de todas las adaptaciones de las guías 6 a 15 |
| FPI-20 | ADR-04: hexagonal ligero con puertos.py | Se mantuvo | Prueba de arquitectura en la suite; refactores sin tocar el dominio |
| FPI-21 | ADR-05: no distribuir; 4 contextos (Catálogo, Inventario, Ventas y Créditos) | Se mantuvo | Sin red ni servicios; costo $0 |
| FPI-22 | ADR-06: contrato OpenAPI con JWT, solo diseño | Se mantuvo como diseño | No se implementó API (no hay servidor); openapi.yaml en salidas |
| FPI-23 | ADR-07: SQLite efímero y componentes reales en las pruebas | Se mantuvo | Suite en memoria: 164 pruebas en 0,7 s |
| FPI-24 | ADR-08: prueba primero y presupuesto de rendimiento ligado a 1 caja | Se mantuvo | Ciclos TDD en evidencia_fpi24; p95 de 1,1 ms por venta |
| FPI-25 | ADR-09: CI de 3 jobs con Quality Gates | Se mantuvo | ci.yml en main, con SHA fijados; nunca ejecutado en GitHub (sin remoto) |
| FPI-26 | ADR-10: imagen Docker de verificación, no instalador | Cambió a solo documentar | Dockerfile y compose en salidas; no construidos |
| FPI-27 | ADR-11: Continuous Delivery de escritorio por Releases | Se mantuvo | deploy.yml y healthcheck en main; sin release publicado |
| FPI-28 | ADR-12: Semgrep + Trivy, gate en alta y crítica | Se ajustó | ci-security.yml en main; Semgrep no detecta SQL con f-string (TD-17), la barrera es ruff |
| FPI-29 | ADR-13: telemetría ligera compatible con OTel | Se mantuvo | Ensayada con 168 pruebas; parche pendiente (tarea 13) |
| FPI-30 | ADR-14: SLO de 99,5 % por ventas, Runbook de 2 niveles | Se mantuvo | Runbook verificado en copia; tarea 14 pendiente |
| FPI-31 | ADR-15: deuda por impacto y disparador; TD-13 | Se mantuvo | TD-13 en 3 commits de ensayo (39 → 0,6 ms); tarea 15 pendiente |

## 3. Defensa de decisiones (ADR)

| ADR | Decisión | Evidencia |
|---|---|---|
| ADR-03 | Monolito de escritorio con SQLite local (no web ni microservicios) | p95 de 1,1 ms por venta con 1 caja; 0 errores hasta 50 cajas (p95 432 ms); alternativa distribuida ≈ US$ 45 al mes; restauración en menos de 1 ms con el Runbook (FPI-24, 21 y 30). |
| ADR-04 | Hexagonal ligero: el núcleo no depende de la base de datos | La prueba de arquitectura pasa en cada ejecución; TD-13 cambió el cálculo del saldo tocando solo el repositorio y un stub; la telemetría se agregó con un adaptador sin cambiar ServicioDeVentas (FPI-29 y 31). |
| ADR-11 | Entrega con aprobación humana, healthcheck y rollback | El healthcheck detectó 4 de 4 paquetes dañados; la suite con 99 % de cobertura dejó pasar TD-01, lo que justifica la aprobación humana (FPI-17 y 27). |
| ADR-13 | Telemetría ligera con muestreo y sin datos personales | +4 % de tiempo con muestreo de 0,2 frente a +19 % al 100 %; estimación con −4,8 % de error; 0 coincidencias de datos personales en el log (FPI-29, semana simulada). |

### Trade-off principal: ¿por qué no web ni microservicios?

| Argumento | Dato real | Fuente |
|---|---|---|
| El volumen no lo pide | 1 caja y ~80 ventas al día. Una venta tarda 1,1 ms de p95; el umbral del negocio (E-03) es 1 s: unas 900 veces de margen. | FPI-18 y FPI-24 (medición de la capa de servicios) |
| La concurrencia tampoco | 5 cajas simultáneas: p95 1,4 ms. 20 cajas: p95 82 ms. 50 cajas: p95 432 ms y máximo 3,3 s, con 0 errores. El límite de SQLite aparece mucho más allá de la tienda. | FPI-24 |
| Costo | Una alternativa distribuida mínima costaba unos US$ 45 al mes (sin NAT), contra $0 del escritorio. | FPI-21, Ejercicio 3 |
| Operación | Restaurar la base dañada toma menos de 1 ms de operación de archivos y 4 comandos verificados. En la nube habría red, credenciales y un proveedor de por medio. | FPI-30 (simulacro INC-SIM-01) |
| Observabilidad | Semana simulada: p95 diario de 1,27 a 1,66 ms; 0 fallas técnicas en 593 operaciones. | FPI-29 (datos simulados, no de la tienda) |
| Lo que se pierde | No hay acceso remoto ni varias sucursales. Si llegan, el ADR-03 se revisa con datos (el umbral medido es 20 o más cajas simultáneas). | ADR-03 y FPI-24 |

## 4. Estado verificable (5-nov-2026)

| Indicador | Estado real |
|---|---|
| Pruebas | 164 en verde (5 de la ventana se saltan sin pantalla), en 0,7 s. Ejecutado el 5-nov-2026 sobre la copia del repositorio. |
| Cobertura de líneas | 98,2 % (606 de 617) con medir_cobertura.py; el gate exige 90 %. |
| Complejidad | V(G) máximo 5, promedio 1,59 (120 funciones; medir_complejidad.py). |
| Análisis estático y seguridad (ruff E9, F, S, C901) | 0 hallazgos con las reglas del CI; excepciones justificadas en ruff.toml. |
| Vulnerabilidades críticas pendientes | No medido con Semgrep ni Trivy (nunca se ejecutaron). Inventario manual: 0 dependencias de terceros en ejecución; acciones fijadas por SHA. |
| SLO (99,5 % de ventas sin falla técnica) | Sin datos reales: la tienda no usa el sistema. En la semana simulada, 100 % (0 fallas técnicas). |
| CI/CD y uptime | Nunca ejecutados: el repositorio no tiene remoto. Uptime: no aplica (escritorio). |

## 5. Bitácora forense de IA (consolidado)

| Indicador | Valor | Fuente |
|---|---|---|
| Hallazgos reales en lo generado con IA (bitácora del repositorio) | 31: 20 de IS I y 11 de las tareas con Claude Code | docs/BITACORA_IA.md, secciones 2 y 7.2 |
| Auditorías de IA en los talleres de IS II | 15, todas con salidas reales de una IA (en IS I, 14 ejemplos fueron simulados) | Ejercicio 5 de las guías 1 a 15 |
| Preguntas de auditoría que encontraron un problema verificado | 36 de 48 (guías 2 y 6 a 15) | Tablas de auditoría de cada ficha |
| Alucinaciones de hechos inexistentes | 9: estado «REGISTRADA», tiendas_sm.__main__, DB_PATH, tabla «creditos», rutas y archivos inventados (main.py, venv), TD-15 inventado, «101 pruebas», «venta de contado cubierta» (FPI-10) y el atributo cantidad_recibida | Guías 6, 10 y 14; bitácora 17, 18–20, 26 y 30 |
| Licencias o dependencias rechazadas | 6 dependencias rechazadas o fijadas: SDK de OpenTelemetry, servidor de Grafana y Prometheus, Render y Docker Hub, ruff y coverage sin versión, trivy-action por etiqueta y el cambio a modo WAL. 0 licencias restrictivas encontradas. | ADR-09, 11, 12 y 13; FPI-30 |
| Fugas de datos personales prevenidas | 3: OpenAPI con nombre y límite de crédito; texto de excepciones y seudónimo con monto en la telemetría; acceso del cliente a los reportes de seguridad | FPI-22, 29 y 28 |


**Los tres hallazgos éticos más significativos del programa:**

- 1. La cobertura no es confianza. La suite con 99 % de cobertura, escrita por la misma IA que escribió el código, no detectó que la venta no registraba su movimiento de inventario (TD-01). Los casos derivados de los criterios de aceptación sí encuentran esos defectos. Firmar una entrega «porque el CI está verde» habría sido engañar al cliente.
- 2. La IA inventa con formato creíble, y la herramienta de seguridad también es una dependencia. Inventó un número de deuda, una tabla y un módulo ejecutable, y fijó Trivy por una etiqueta mutable justo meses después de que esas etiquetas fueran secuestradas para robar credenciales (CVE-2026-33634, verificado en el aviso de SUSE). Ninguna de esas salidas «se veía mal».
- 3. La privacidad se diseña, no se agrega. Tres veces la IA propuso exponer datos personales (respuestas de la API, mensajes de error en la telemetría y acceso del cliente a los reportes). La Ley 1581 hace responsable al que trata los datos, no a la IA.

**La IA que asistió estos documentos también se equivocó, y se registra:**

- • Un Runbook que respaldaba bases dañadas con nombre de respaldo bueno (FPI-30).
- • Parches que reescribían archivos completos por los finales de línea (FPI-31).
- • Un simulador que leía mal la salida de un paso (FPI-27).
- • Un YAML con un «:» que lo invalidaba (FPI-25).
- Los cuatro se detectaron ejecutando, no leyendo.

**Pendiente del propio estudiante: la bitácora del repositorio aún tiene dos campos «[CONFIRMAR: qué partes leíste, ejecutaste y modificaste]» sin llenar. Deben completarse antes de entregar.**


**Evaluación del uso responsable de la IA:** 3 de 5. La IA auditora dio 4 de 5 con un extracto; la bitácora completa muestra supervisión humana sin documentar ([CONFIRMAR] vacíos) y una etapa sin aprobación paso a paso.

## 6. Deuda técnica residual aceptada

| Componente | Deuda | Justificación y plan |
|---|---|---|
| Seguridad: acceso a datos (TD-06) | Sin autenticación (deliberada; CR-01 sin aprobar) | Aceptada solo con datos ficticios. Bloquea el piloto con datos reales hasta decidir CR-01 (H1). |
| Inventario (TD-02) | Sin lotes ni vencimientos (deliberada y prudente) | Sin costo hoy; se paga en H3 si el propietario demuestra pérdidas por productos vencidos. |
| Ventas (TD-09) | Cohesión baja de ServicioDeVentas, LCOM1 15 (empeoró) | Se paga en H2, antes de agregar otro caso de venta. |
| Operación (TD-16) | Respaldo manual y sin revisión al abrir | No aceptable para un piloto: tarea 14 en H1. |
| Documentación (TD-11) | ERS 1.1, DAD y DDS desactualizados | Se actualizan en H1; mientras tanto, la verdad es el código y DECISIONES.md. |
| Créditos y trazabilidad (TD-10, TD-15, TD-12, TD-08) | Abonos simples, movimiento sin id_venta, plazo fijo, fechas sin zona | Bajo impacto con 1 caja; programados en H2 y H3 (FPI-31). |

Roadmap: H1 piloto seguro (dic. 2026–ene. 2027), H2 operación diaria (feb.–mar. 2027), H3 perecederos y alertas (abr.–may. 2027), cada uno con su disparador (FPI-31).

## 7. Lecciones del programa

Técnicas. La arquitectura correcta es la que el problema pide, no la que impresiona: un monolito de escritorio con SQLite resolvió una tienda de barrio con 1,1 ms por venta y costo cero, y cada vez que una guía pedía servidores, contenedores o nubes, la decisión honesta fue adaptar y medir. Las pruebas son la red que permite cambiar con calma, como mostró la refactorización de TD-13 (65 veces más rápida y el mismo resultado). Pero una cobertura del 99 % no garantiza nada si las pruebas no salen de los requisitos.

De proceso. Las decisiones escritas (ADR) sirven de verdad: permitieron defender por qué no hay microservicios, por qué hay aprobación humana o por qué la telemetría no usa Grafana. El inventario de deuda funcionó porque se revisó contra el código y no contra la intención: 4 ítems pagados, 5 iguales y 1 que empeoró. Y «medir antes de opinar» resolvió discusiones: concurrencia, costo de la telemetría, saldo lento.

Éticas. Prácticamente todo el código lo generó una IA, y eso no reduce mi responsabilidad: la aumenta. La IA inventó tablas, módulos, números y estados con formato impecable, propuso exponer datos personales y recomendó prácticas que ya habían sido explotadas. Lo detecté ejecutando y comparando con los requisitos, no leyendo. Reconozco mi falla: hubo una etapa en que dejé que la IA avanzara sin aprobar cada paso, y la bitácora todavía no dice qué revisé yo. Eso se corrige antes de entregar.

De trabajo en equipo. Como desarrollador único, el «equipo» fue el desarrollador más la IA. La lección es la misma que con personas: dividir el trabajo no divide la responsabilidad. Cada tarea tuvo un plan aprobado, una prueba que fallaba primero y una revisión, y cuando se saltó un paso (pruebas escritas después del código) quedó declarado.

Lo que haría distinto: subir el repositorio a GitHub desde el primer día, para que el CI corriera de verdad, y validar con un tendero real antes de agregar más funcionalidades. El sistema está bien verificado; falta validarlo.

## 8. Guion del video demo (5 minutos)
1. **(0:00–0:30) Problema.** El tendero lleva inventario y fiado en cuaderno; no sabe cuánto le deben ni qué se agota.
2. **(0:30–2:30) Demo en vivo** con `--datos-de-ejemplo`: venta de contado con cambio; venta a crédito con cliente y vencimiento; rechazo por stock («Solo hay N disponibles…») y por cupo; el inventario baja.
3. **(2:30–3:30) Calidad en vivo:** `python -m unittest discover -s tests` (164 OK), `python medir_cobertura.py --minimo 90` (98,2 %), ruff con las reglas del CI (0 hallazgos).
4. **(3:30–4:30) ADR-03 con datos:** 1,1 ms por venta, 0 errores hasta 50 cajas, US$ 45 al mes de la alternativa distribuida.
5. **(4:30–5:00) Honestidad:** qué falta (GitHub y CI ejecutado, piloto con tienda real, tareas 13 a 15) y por qué.

## 9. Pendientes para certificar el cierre
- [ ] Crear el repositorio en GitHub, hacer push, ver en verde `ci.yml`, `ci-security.yml` y `deploy.yml`, y etiquetar `v1.0.0` (tarea 16).
- [ ] Grabar el video con el guion de la sección 8.
- [ ] Completar los `[CONFIRMAR]` de `docs/BITACORA_IA.md` y aclarar «revisión de código del PR 1».
- [ ] Tareas 13, 14 y 15 (telemetría, confiabilidad y TD-13).

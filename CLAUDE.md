# TIENDAS S.M — contexto para Claude Code

Sistema de gestión de inventario, ventas y créditos para tiendas de barrio. Proyecto académico individual de
**Ingeniería de Software I** (Ingeniería de Sistemas, Universidad de Pamplona). Autor: Yamid Sneider Merchan Castro.
Es un **MVP**: sencillo, realizable por un estudiante y defendible en una sustentación.

@docs/contexto/CONTEXTO_PROYECTO.md

## Reglas de trabajo (lo más importante)
1. **Español**, con lenguaje claro de estudiante universitario. Cuando escribas código, explica en pocas líneas qué hace y por qué,
   para que Yamid pueda entenderlo y defenderlo. Él es responsable final de todo lo que entregue.
2. **No inventes requisitos ni los presentes como aprobados.** Distingue siempre: *definido*, *preliminar* y *recomendación*.
   Si crees que hace falta una función nueva, proponla como recomendación y **pregunta antes** de programarla.
3. **Mantén el alcance pequeño.** No agregues proveedores, pedidos, caja, devoluciones, facturación, reportes, roles ni
   usuarios: son ampliación **CR-02 / CR-01 sin aprobar** (hoy *Won't Have*). Tampoco hay borrar productos ni anular ventas (DT-08).
4. **Antes de cambiar una decisión importante, explica por qué conviene** y espera su visto bueno. Registra el cambio con causa e impacto.
5. **Trazabilidad:** cada cambio cita su historia o requisito (HU-xx, RF-xx, CU-01, RNF-xx, BUG-xx, DT-xx). Conserva el nombre **TIENDAS S.M**.
6. **Honestidad ante todo.** No digas que algo funciona si no lo ejecutaste. Corre las pruebas antes de dar una tarea por terminada
   y reporta lo que falló o quedó pendiente.
7. **Datos y seguridad:** nunca datos reales de clientes, contraseñas, tokens ni claves en código, pruebas, commits ni consultas. Todo dato de prueba es ficticio.
8. Pregunta cuando una decisión dependa del propietario de la tienda (ver «Pendientes por confirmar»). **No asumas la respuesta.**

## Stack y decisiones técnicas
- **Python 3** (solo biblioteca estándar) · **SQLite** · interfaz de **escritorio con Tkinter** (primera versión: punto de venta) · pruebas con **unittest**.
- Dinero: **enteros en pesos colombianos** (sin centavos ni `float`).
- Reglas de diseño: Clean Code, SOLID **selectivo** con «hexagonal ligero» (ADR-04): los contratos de persistencia viven en `puertos.py`
  (`RepositorioDeVentas`, `PuertoDeProductos`, `PuertoDeClientes`, con `obtener`, `guardar` y `listar`) y el núcleo no importa SQLite (`test_arquitectura`); no se crea un puerto por cada clase,
  funciones pequeñas, sin números mágicos, validaciones compartidas en `validaciones.py`, nombres en español y `snake_case`.
- Una operación que cambia venta + inventario + deuda se guarda **todo o nada** (RNF-04) dentro de una transacción.

## Estructura del repositorio
```
tiendas_sm/          dominio.py, servicios.py, puertos.py, repositorios.py, base_de_datos.py, validaciones.py, aplicacion.py,
                     presentador.py (lógica de la pantalla, sin Tkinter), datos_de_ejemplo.py (ficticios)
interfaz_tk/         ventana_punto_de_venta.py (solo dibuja; no cuenta en la cobertura) · iniciar_tienda.py abre la app
tests/               test_comportamiento, test_unitarias_dobles, test_caja_negra, test_integracion_incremental, test_defectos_corregidos,
                     test_venta_de_contado, test_arquitectura, test_presentador, test_iniciar_tienda, test_interfaz_tk (se salta sin pantalla), test_escenarios_calidad, test_migracion_esquema, test_medir_cobertura, test_healthcheck_paquete
scripts/             healthcheck_paquete.py (revisa el .zip publicado; lo usa el CD)
docs/                CI.md, FLUJO_GIT.md, defectos/BUG-01.md y BUG-02.md, BITACORA_IA.md, HOJA_DE_RUTA_IS2.md, contexto/, referencia/
.github/workflows/ci.yml   pipeline de 3 jobs (FPI-25): linter -> test (3.12 y 3.13) -> analysis (cobertura ≥ 90 %, SonarCloud)
.github/workflows/deploy.yml   entrega continua por GitHub Releases con healthcheck y rollback (FPI-27)
.github/workflows/ci-security.yml   Semgrep (SAST) y Trivy (SCA, secretos) (FPI-28) · ruff.toml y .trivyignore: excepciones justificadas
medir_calidad.py · medir_complejidad.py · medir_cobertura.py · correr_regresion.py · calcular_metricas.py · demo_en_vivo.py
```

**Ignora** las carpetas `evidencia_fpi12/`, `evidencia_fpi14/`, `evidencia_fpi15/` y `evidencia_fpi24/`: son evidencia de las fichas (incluye una copia vieja del código en
`evidencia_fpi12/v1_antes/`). No las edites ni las uses como fuente del código; el código vigente está en `tiendas_sm/`.

## Comandos
```
python -m unittest discover -s tests -v          # debe dar OK (164 pruebas)
python medir_cobertura.py --minimo 90            # cobertura de líneas (hoy ≈ 98 %)
python correr_regresion.py tiendas_sm/servicios.py   # pruebas relacionadas con un archivo
python demo_en_vivo.py --sin-pausas              # demostración narrada del flujo crítico
python iniciar_tienda.py --datos-de-ejemplo      # abre el punto de venta (datos en %LOCALAPPDATA%\TIENDAS_SM)
ruff check --select E9,F63,F7,F82,F401,F841,S,C901 --config "lint.mccabe.max-complexity = 10" tiendas_sm interfaz_tk tests scripts iniciar_tienda.py   # job linter (ruff==0.16.9)
```

## Arquitectura (resumen)
- **Dominio:** `Producto`, `Existencia` (hoy ligada al producto, sin `Lote`), `Cliente`, `Venta`, `DetalleVenta`, `CuentaPorCobrar`.
- **Servicios:** `ServicioDeProductos`, `ServicioDeClientes`, `ControlInventario`, `ControlCredito`, `ServicioDeVentas`
  (coordina el flujo crítico **CU-01: registrar venta a crédito**). `Aplicacion` arma y conecta todo.
- **Reglas clave:** una venta no puede dejar el stock negativo (el mensaje dice cuántas unidades hay); un abono no puede superar el saldo
  (el mensaje dice el saldo); el crédito disponible es `límite − saldo pendiente`; la venta guarda el **precio vigente** al venderse;
  el vencimiento del crédito usa el **plazo del cliente**.

## Flujo de Git (GitHub Flow)
- `main` está protegida: **todo entra por Pull Request** con el CI en verde. Nunca hagas commit directo a `main`.
- Una rama por tarea: `feature/`, `fix/`, `refactor/`, `docs/`, `test/`, `ci/`. Commits atómicos: `tipo(alcance): qué` y, si hace falta, el **porqué**.
- Un defecto por PR: primero la prueba que lo reproduce, después la corrección. No mezcles un refactor con funcionalidad nueva.
- Fusiona con *merge commit* (no squash) para conservar los commits atómicos. Versionado SemVer (`v0.1.x`).

## Estado actual (resumen; detalle en `docs/contexto/ESTADO_Y_PENDIENTES.md`)
- **Hecho:** HU-01 a HU-04 (venta **a crédito** y **de contado** en efectivo), HU-06, CU-01, CU-02, puertos del núcleo (ADR-04), 164 pruebas en verde, CI configurado, BUG-01, BUG-02, DT-09, TD-01, TD-04, TD-05, TD-07 y TD-14 corregidos; pipeline de la Guía 9, entrega continua de la Guía 11 y seguridad de la Guía 12.
- **Pendiente, en este orden de prioridad:**
  1. **Interfaz Tkinter:** punto de venta hecho; faltan medir E-01 con personas y las demás pantallas
     (referencia visual y de flujos: `docs/referencia/tiendas_sm_dashboard.html`).
  2. ~~Venta de contado~~ (hecha: UC-02, solo efectivo).
  3. **Validar las reglas con el propietario** de una tienda real.
  4. Acceso con usuario/contraseña (RNF-03, CR-01 aplazada).
  5. Lotes, vencimientos y alertas (RF-10 a RF-13; Should/Could Have).

## Pendientes por confirmar con el propietario (no asumir)
Qué hacer con stock insuficiente · qué lote se descuenta primero · reglas del crédito (tope, plazo, mora) · datos para registrar un cliente ·
nivel mínimo de stock (¿uno general o por producto?) · días de aviso de vencimiento · salida manual de mercancía · usuarios y contraseñas (CR-01) ·
ampliar el sistema (CR-02).

## Dónde está el resto del contexto (léelo bajo demanda)
- Requisitos, historias, criterios Gherkin y prioridades: `docs/contexto/REQUISITOS.md`
- Decisiones por fase (FPI-01 a FPI-16): `docs/contexto/DECISIONES.md`
- Qué falta y cómo empezar: `docs/contexto/ESTADO_Y_PENDIENTES.md`
- Documentos formales (texto convertido de los Word): `docs/contexto/ERS_TIENDAS_SM.md`, `DAD_TIENDAS_SM.md` y `DDS_TIENDAS_SM.md`.
  Describen más alcance que el MVP codificado; si no coinciden con el código, manda el código y las 16 fichas.
- Auditoría de uso de IA: `docs/BITACORA_IA.md` · Hoja de ruta: `docs/HOJA_DE_RUTA_IS2.md`

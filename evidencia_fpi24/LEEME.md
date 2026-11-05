# Evidencia de TDD — Guía 8 (FPI-24), tarea 3 (TD-04)

Salida **real** de `python -m unittest discover -s tests -v` en cada commit de las fases rojo → verde → refactor.
Se generó el 2026-11-05 volviendo a cada commit en una copia aparte del repositorio (con `git worktree`), sin modificar
el código. Python 3.12.0 en Windows. Los datos de las pruebas son ficticios.

## Por qué hay dos ciclos y no uno

La tarea 3 pide validar el cliente y el stock mínimo. La parte del cliente se hizo antes, como **DT-09** (rama
`fix/dt-09-validar-cliente`), y el resto como **TD-04** (rama `fix/td-04-validaciones`). La equivalencia está registrada en
`docs/contexto/DECISIONES.md` («Equivalencia de numeraciones»). Cada ciclo tiene sus tres commits.

| Fase | Commit | Archivo | Resultado |
| --- | --- | --- | --- |
| Cliente — ROJO | `ac7c879` test(clientes): reproducir DT-09 | `1_cliente_ROJO_ac7c879.txt` | 98 pruebas, **FAILED (failures=4)**: nombre vacío, límite negativo, plazo < 1 y la prueba unitaria no lanzan `ValueError` |
| Cliente — VERDE | `3a49ad7` fix(clientes): validar nombre, límite y plazo | `2_cliente_VERDE_3a49ad7.txt` | 98 pruebas, **OK** |
| Cliente — REFACTOR | `0b06a22` refactor(productos): usar exigir_texto_obligatorio | `3_cliente_REFACTOR_0b06a22.txt` | 98 pruebas, **OK** |
| Stock mínimo — ROJO | `e58d10b` test(productos): CN-09 | `4_stock_minimo_ROJO_e58d10b.txt` | 108 pruebas, **FAILED (errors=2)**: `registrar_producto()` no acepta `stock_minimo` |
| Stock mínimo — VERDE | `9aacca0` fix(productos): validar stock mínimo | `5_stock_minimo_VERDE_9aacca0.txt` | 108 pruebas, **OK** |
| Stock mínimo — REFACTOR | `8e9b5c2` refactor(clientes): usar exigir_no_negativo | `6_stock_minimo_REFACTOR_8e9b5c2.txt` | 108 pruebas, **OK** |

Entre un ciclo y otro el total de pruebas sube de 98 a 108 porque en medio se fusionaron los puertos (Guía 4) y TD-01.

## Lo que esta evidencia NO muestra

- No hay enlace a Pull Request: los commits están en el repositorio local; los PR se abren al subir las ramas a GitHub.
- El refactor de ejemplo que sugería la tarea (`exigir_mayor_a_cero` con mensaje opcional) no se hizo; los refactors fueron
  `exigir_texto_obligatorio` y `exigir_no_negativo`.
- `ruff` no se ejecutó en local (no está instalado); lo ejecuta el CI.

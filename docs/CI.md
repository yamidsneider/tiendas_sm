# Integración Continua (CI) de TIENDAS S.M — pipeline de la Guía 9 (FPI-25, ADR-09)

Archivo del pipeline: `.github/workflows/ci.yml` (GitHub Actions). Se ejecuta en cada Pull Request hacia `main` y en cada push a `main`.
Tiene **tres jobs encadenados**: si uno falla, los siguientes no se ejecutan y el pipeline queda en rojo.

| Job (nombre del check) | Qué hace | Falla si… |
| --- | --- | --- |
| `linter` | `ruff==0.16.9` con errores reales (E9, F63, F7, F82, F401, F841), seguridad (`S`) y complejidad ciclomática `C901` ≤ 10, sobre `tiendas_sm`, `interfaz_tk`, `tests` e `iniciar_tienda.py` | hay un error, un riesgo de seguridad o una función con V(G) > 10 |
| `test (Python 3.12)` y `test (Python 3.13)` | compila, arma la `Aplicacion` y corre toda la suite (`unittest`) | hay un error de sintaxis o falla cualquier prueba |
| `analysis` | Quality Gate de cobertura (`medir_cobertura.py --minimo 90`), `coverage==7.13.4` genera `coverage.xml` para SonarCloud, análisis de SonarCloud (si hay token) y, solo en `main`, un `.zip` del código con el SHA del commit | la cobertura baja de 90 % o SonarCloud no aprueba su Quality Gate |

## Versiones fijas y comprobadas (TD-07)
- `ruff==0.16.9` y `coverage==7.13.4`: comprobadas en PyPI el 2026-11-05.
- Actions fijadas por **SHA** (con la etiqueta en un comentario), comprobado con `git ls-remote` el 2026-11-05:
  `actions/checkout` v6, `actions/setup-python` v6, `SonarSource/sonarqube-scan-action` v7 y `actions/upload-artifact` v6.
- `.github/dependabot.yml` revisa cada semana las actions y abre un PR cuando hay una versión nueva.

## Python 3.13 (TD-05)
`medir_cobertura.py` ignora los números de línea `None` que entrega `trace` en Python 3.13. En el equipo de desarrollo solo hay
Python 3.12: el arreglo se probó simulando esa entrada (`tests/test_medir_cobertura.py`). La primera ejecución real en 3.13 es la del CI.
El job `analysis` sigue en 3.12.

## Pruebas de la interfaz en el CI
- `tests/test_interfaz_tk.py` necesita pantalla. El runner de GitHub (Linux) no la tiene, así que esas 5 pruebas **se saltan**
  (`skipped`): en el CI no cuentan como aprobadas. Se ejecutan en el computador del desarrollador.
- La lógica de la pantalla está en `tiendas_sm/presentador.py` y sí se prueba en el CI. Por eso `interfaz_tk/` no entra en la cobertura.

## Lo que hay que hacer en GitHub (no se puede hacer desde el código)
1. **Fusionar** el PR cuando los cuatro checks estén en verde y **guardar el enlace de la ejecución** (pestaña *Actions*): es la evidencia de la FPI-25.
2. **Regla de `main`** (*Settings → Branches* o *Rules → Rulesets*): exigir Pull Request y los checks
   **`linter`**, **`test (Python 3.12)`**, **`test (Python 3.13)`** y **`analysis`**; quitar el check viejo `pruebas`; no permitir saltarla.
   Los nombres aparecen en la lista después de la primera ejecución del pipeline.
3. *Settings → Code security*: activar **Secret scanning** y **Push protection**.
4. **SonarCloud** (cuando se quiera activar esa capa): crear la organización y el proyecto desde GitHub, desactivar *Automatic Analysis*,
   generar el token y guardarlo en *Settings → Secrets and variables → Actions* como el secreto **`SONAR_TOKEN`**; en la pestaña
   *Variables* crear **`SONAR_ORGANIZATION`** y **`SONAR_PROJECT_KEY`**. Mientras no exista el token, el paso de SonarCloud se omite con
   un aviso y los demás Quality Gates siguen bloqueando.
5. **Prueba del bloqueo:** abrir un PR de prueba con una aserción rota, comprobar que queda en rojo y que el botón de fusionar está
   bloqueado, tomar la captura y cerrar el PR sin fusionar.

## Seguridad
- El pipeline usa `permissions: contents: read`. El único secreto es `SONAR_TOKEN`, que **nunca** se escribe en un archivo:
  se lee con `${{ secrets.SONAR_TOKEN }}`. `SONAR_ORGANIZATION` y `SONAR_PROJECT_KEY` no son secretos (son *variables*).
- `coverage.xml` y `.coverage` están en `.gitignore`: se generan en el CI y no se suben al repositorio.

## Cómo correr lo mismo en el computador
```
ruff check --select E9,F63,F7,F82,F401,F841,S,C901 --config "lint.mccabe.max-complexity = 10" tiendas_sm interfaz_tk tests iniciar_tienda.py
python -m compileall -q tiendas_sm interfaz_tk tests iniciar_tienda.py
python -m unittest discover -s tests -v
python medir_cobertura.py --minimo 90
```
`ruff` y `coverage` no vienen con Python: se instalan con `pip install ruff==0.16.9 coverage==7.13.4` (de preferencia en un entorno virtual).

## Entrega continua por GitHub Releases (FPI-27, ADR-11)
TIENDAS S.M es de escritorio (ADR-03): «producción» es la versión marcada como **Latest** en GitHub Releases, que es la que descarga
la tienda. Archivo: `.github/workflows/deploy.yml`. Solo usa el `GITHUB_TOKEN` automático: ningún secreto ni servicio externo.

**Flujo al publicar una etiqueta `vX.Y.Z`:** `verificar` (pruebas y cobertura sobre el commit de la etiqueta) → `publicar` (espera la
**aprobación** del environment `produccion`; arma `tiendas_sm-vX.Y.Z.zip` con su `.sha256` y lo publica como *prerelease*) →
`healthcheck` (descarga lo publicado y ejecuta `scripts/healthcheck_paquete.py`: integridad SHA-256, contenido y una venta de humo con
su movimiento `SALIDA_VENTA`, sin abrir Tkinter) → `promover` a **Latest** si todo salió bien, o **rollback automático** si el
healthcheck falló (la versión queda como «RETIRADA» y la anterior sigue siendo Latest).

**Preparar una sola vez (en GitHub):** *Settings → Environments → New environment* `produccion` → *Required reviewers*: tu usuario.

**Publicar una versión** (desde `main` actualizado):
```
git switch main
git pull
git tag v0.1.0
git push origin v0.1.0
```
En *Actions → CD* aprueba el job `publicar`. Guarda el enlace de la ejecución y el de la página `…/releases/tag/v0.1.0`.

**Rollback manual** (un fallo descubierto después de promover): *Actions → CD → Run workflow*, con `version_mala` (por ejemplo `v0.1.1`) y
`version_estable` (por ejemplo `v0.1.0`). También pide la aprobación de `produccion`. La estable vuelve a ser Latest y la mala queda
como «RETIRADA».

**Probar el healthcheck en el computador:**
```
git archive --format=zip -o t.zip HEAD tiendas_sm
python scripts/healthcheck_paquete.py --paquete t.zip
```
Debe terminar en `HEALTHCHECK OK` (código 0). Con un `.zip` dañado o una suma que no coincide termina con código 1.

**Opciones de `gh` comprobadas** en el manual oficial (cli.github.com, 2026-11-05): `--verify-tag`, `--prerelease`, `--latest`,
`--pattern`, `--dir`, `--title`, `--notes`, `-R/--repo` y `gh release view --json/-q` (sin etiqueta muestra la última versión).
**`--prerelease=false` no aparece escrita así** en la página de `gh release edit`; la misma página usa `--draft=false`, que es el mismo
mecanismo, pero se confirmará en la primera ejecución real.

## Regresión
`python correr_regresion.py <archivos que cambiaron>` elige las pruebas que se relacionan con el cambio. El pipeline siempre corre la suite completa.

# Integración Continua (CI) de TIENDAS S.M

Archivo del pipeline: `.github/workflows/ci.yml` (GitHub Actions). Se ejecuta en cada Pull Request hacia `main` y en cada push a `main`.

| Paso | Qué hace | Falla si… |
| --- | --- | --- |
| Build | `compileall` y arma la `Aplicacion` | hay un error de sintaxis o de importación |
| Lint | `ruff` con reglas de errores reales (E9, F63, F7, F82, F401, F841) | hay nombres sin definir, importaciones o variables sin usar |
| Test | `python -m unittest discover -s tests -v` | falla cualquier prueba |
| Cobertura | `python medir_cobertura.py --minimo 90` | la cobertura de líneas baja de 90 % |

## Versiones de Python y dependencias del CI (TD-05 y TD-07)
- El job corre con una **matriz de Python 3.12 y 3.13**: aparecen dos chequeos, `pruebas (Python 3.12)` y `pruebas (Python 3.13)`.
  En las reglas de `main` hay que exigir **los dos** (el nombre del chequeo cambió; antes era solo `pruebas`).
- `medir_cobertura.py` ignora los números de línea `None` que entrega `trace` en Python 3.13 (TD-05). En el equipo de desarrollo
  solo hay Python 3.12: el arreglo se probó simulando esa entrada; la primera prueba real en 3.13 será la del CI.
- **ruff sigue sin versión fija:** la tarea pedía fijarlo a la versión instalada, pero en el equipo de desarrollo no hay ruff instalado.
  Cuando se instale, se fija con `pip install ruff==<versión>`.
- **Las actions siguen por etiqueta** (`@v4`, `@v5`): fijarlas por SHA exige comprobar el SHA real en GitHub, y no se inventa.
- `.github/dependabot.yml` revisa cada semana las actions y abre un PR si hay versiones nuevas.

## Pruebas de la interfaz en el CI
- `interfaz_tk/` e `iniciar_tienda.py` se compilan y pasan por `ruff` igual que el resto.
- `tests/test_interfaz_tk.py` necesita pantalla. El runner de GitHub (Linux) no la tiene, así que esas 5 pruebas
  **se saltan** (`skipped`): en el CI no cuentan como aprobadas. Se ejecutan en el computador del desarrollador.
- La lógica de la pantalla está en `tiendas_sm/presentador.py` y sí se prueba en el CI (`tests/test_presentador.py`).
  Por eso `interfaz_tk/` no entra en la cobertura y el presentador sí.

## Que el pipeline bloquee la fusión (hay que configurarlo en GitHub)
*Settings → Rules → Rulesets* (o *Branches → Branch protection rules*) sobre `main`:
1. Activar **Require status checks to pass before merging**.
2. Elegir los chequeos **pruebas (Python 3.12)** y **pruebas (Python 3.13)**. Aparece en la lista después de la primera ejecución del pipeline.
3. Activar **Require branches to be up to date before merging**.
Con eso, un Pull Request con pruebas en rojo no se puede fusionar.

## Seguridad
- El pipeline **no usa secretos ni tokens**: el proyecto no los necesita.
- `permissions: contents: read` limita lo que puede hacer el token automático.
- Si algún día hiciera falta un secreto, se guarda en *Settings → Secrets and variables → Actions* y se lee con `${{ secrets.NOMBRE }}`; nunca se escribe en el archivo.

## Regresión
`python correr_regresion.py <archivos que cambiaron>` elige las pruebas que se relacionan con el cambio. El pipeline siempre corre la suite completa.

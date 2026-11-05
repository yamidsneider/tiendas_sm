# Integración Continua (CI) de TIENDAS S.M

Archivo del pipeline: `.github/workflows/ci.yml` (GitHub Actions). Se ejecuta en cada Pull Request hacia `main` y en cada push a `main`.

| Paso | Qué hace | Falla si… |
| --- | --- | --- |
| Build | `compileall` y arma la `Aplicacion` | hay un error de sintaxis o de importación |
| Lint | `ruff` con reglas de errores reales (E9, F63, F7, F82, F401, F841) | hay nombres sin definir, importaciones o variables sin usar |
| Test | `python -m unittest discover -s tests -v` | falla cualquier prueba |
| Cobertura | `python medir_cobertura.py --minimo 90` | la cobertura de líneas baja de 90 % |

## Pruebas de la interfaz en el CI
- `interfaz_tk/` e `iniciar_tienda.py` se compilan y pasan por `ruff` igual que el resto.
- `tests/test_interfaz_tk.py` necesita pantalla. El runner de GitHub (Linux) no la tiene, así que esas 5 pruebas
  **se saltan** (`skipped`): en el CI no cuentan como aprobadas. Se ejecutan en el computador del desarrollador.
- La lógica de la pantalla está en `tiendas_sm/presentador.py` y sí se prueba en el CI (`tests/test_presentador.py`).
  Por eso `interfaz_tk/` no entra en la cobertura y el presentador sí.

## Que el pipeline bloquee la fusión (hay que configurarlo en GitHub)
*Settings → Rules → Rulesets* (o *Branches → Branch protection rules*) sobre `main`:
1. Activar **Require status checks to pass before merging**.
2. Elegir el chequeo **pruebas** (nombre del job). Aparece en la lista después de la primera ejecución del pipeline.
3. Activar **Require branches to be up to date before merging**.
Con eso, un Pull Request con pruebas en rojo no se puede fusionar.

## Seguridad
- El pipeline **no usa secretos ni tokens**: el proyecto no los necesita.
- `permissions: contents: read` limita lo que puede hacer el token automático.
- Si algún día hiciera falta un secreto, se guarda en *Settings → Secrets and variables → Actions* y se lee con `${{ secrets.NOMBRE }}`; nunca se escribe en el archivo.

## Regresión
`python correr_regresion.py <archivos que cambiaron>` elige las pruebas que se relacionan con el cambio. El pipeline siempre corre la suite completa.

# Primer mensaje para Claude Code (cópialo tal cual)

Lee `CLAUDE.md` y los archivos de `docs/contexto/`. Después haz esto, en este orden y sin escribir código todavía:

1. Corre `python -m unittest discover -s tests` y dime cuántas pruebas pasan.
2. Resúmeme en 10 líneas cómo entiendes el proyecto, el estado actual y las reglas que debes respetar, para confirmar que tienes el contexto correcto.
3. Revisa `tiendas_sm/` y `docs/referencia/tiendas_sm_dashboard.html`, y proponme un **plan por pasos** para construir la interfaz de escritorio con Tkinter
   (qué archivos crearías, cómo la pantalla llamaría a `Aplicacion`, qué pruebas escribirías y qué parte se puede probar sin pantalla).
4. Hazme las preguntas que necesites antes de empezar. No asumas ninguna regla de la lista «Pendientes por confirmar».

Espera mi aprobación del plan antes de crear o modificar archivos. Trabaja en una rama nueva y no hagas commit directo a `main`.

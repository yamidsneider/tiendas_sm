# Estado actual y por dónde seguir

## Qué existe y funciona
Lógica de negocio en Python con SQLite: productos, entradas de mercancía, clientes, venta **a crédito** con validación de stock y de límite, venta **de contado** en efectivo con cálculo del cambio (UC-02),
descuento automático del inventario, cuenta por cobrar con el plazo del cliente, abonos y saldo, y el guardado "todo o nada".
106 pruebas en verde (unitarias con dobles, caja negra, integración, flujo completo, venta de contado y regresión de defectos), cobertura ≈ 99 %, CI configurado.
**No hay interfaz de usuario todavía** (la demo `demo_en_vivo.py` es por consola).

## Qué falta (en orden de prioridad)
1. **Interfaz de escritorio con Tkinter.** Replicar los flujos del prototipo `docs/referencia/tiendas_sm_dashboard.html` (punto de venta, productos, existencias,
   clientes, créditos y abonos, alertas). Reglas: la interfaz **solo llama a los servicios** (`Aplicacion`); la lógica de negocio no se duplica en la pantalla.
   Mostrar siempre los mensajes de error del dominio tal como llegan (ya dicen cuántas unidades hay o cuál es el saldo).
2. ~~Venta de contado~~ — **hecha** en la rama `feature/venta-de-contado` (efectivo; transferencia y mixto son CR-02).
3. **Validación con el propietario** de las reglas pendientes (lista en `CLAUDE.md`).
4. Acceso con usuario y contraseña (CR-01) — solo si se aprueba.
5. Lotes y vencimientos, y alertas (RF-10 a RF-13) — Should/Could Have; implica quitar la deuda DT-01.
6. Arreglos menores: DT-08, DT-05, pruebas de interfaz.

## Cómo trabajar cada tarea
1. Crea una rama (`feature/…`, `fix/…`). 2. Escribe primero la prueba que falla. 3. Implementa lo mínimo. 4. Corre `python -m unittest discover -s tests`.
5. Si cambia un comportamiento o una decisión, regístralo en `docs/contexto/DECISIONES.md`. 6. Abre un Pull Request con la plantilla del repo.

## Lo que NO sabemos (no lo inventes)
Cómo atiende realmente un vendedor, qué equipo e internet tiene la tienda, qué datos pide el propietario de sus clientes, y las reglas de la lista «Pendientes por confirmar».

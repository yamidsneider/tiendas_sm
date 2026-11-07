# Estado actual y por dónde seguir

## Qué existe y funciona
Lógica de negocio en Python con SQLite: productos, entradas de mercancía, clientes, venta **a crédito** con validación de stock y de límite, venta **de contado** en efectivo con cálculo del cambio (UC-02),
descuento automático del inventario, cuenta por cobrar con el plazo del cliente, abonos y saldo, y el guardado "todo o nada".
275 pruebas en verde (unitarias con dobles, caja negra, integración, flujo completo, venta de contado, regresión de defectos,
arquitectura, presentadores y pantallas), cobertura ≈ 98,8 %, CI configurado (las 37 pruebas de pantallas se saltan en el CI: no hay pantalla).
**Interfaz Tkinter con el diseño del borrador HTML** (`python iniciar_tienda.py`): menú lateral con las 6 secciones aprobadas.

| Sección | Qué hace | Trazabilidad |
| --- | --- | --- |
| Punto de venta | Buscar, carrito, cobro de contado (F9) y a crédito (F4), ticket | HU-04, CU-01, CU-02 |
| Ventas | Las últimas 50 ventas y su ticket (solo consulta) | RF-05 |
| Productos | Catálogo, nuevo producto y cambio del precio de venta | HU-01, HU-02, RF-01, RF-02 |
| Existencias | Disponibles, entrada de mercancía y últimos movimientos | HU-03, RF-03, RF-04 |
| Clientes | Lista con deuda, nuevo cliente y detalle con cuentas pendientes | HU-05, RF-07 |
| Créditos y abonos | Cuentas por cobrar, total por cobrar y registro de abonos | HU-06, RF-09 |

## Qué falta (en orden de prioridad)
1. **Interfaz de escritorio con Tkinter** — las 6 secciones aprobadas están hechas (rama `app/pantallas`, falta el PR a `main`).
   **Falta:** medir E-01/RNF-01 a mano con personas. Las secciones del borrador que no están (lotes, alertas, configuración, tablero)
   esperan al propietario; proveedores, pedidos y caja son CR-02. Reglas: la interfaz **solo llama a los servicios** (`Aplicacion`) por
   un presentador sin Tkinter; la lógica de negocio no se duplica en la pantalla y los mensajes del dominio se muestran tal como llegan.
   - *Recomendación sin aprobar:* **«Editar cliente»** (hoy solo se registra y se consulta, RF-07). Antes de programarla hay que decidir
     qué datos se cambian, qué pasa si el límite nuevo queda por debajo de la deuda y si el plazo nuevo afecta las cuentas ya abiertas
     (lo prudente: solo ventas nuevas, como el precio vigente de HU-02). Las dos últimas son reglas del crédito: van al propietario.
2. ~~Venta de contado~~ — **hecha** en la rama `feature/venta-de-contado` (efectivo; transferencia y mixto son CR-02).
3. **Validación con el propietario** de las reglas pendientes (lista en `CLAUDE.md`).
4. Acceso con usuario y contraseña (CR-01) — solo si se aprueba.
5. Lotes y vencimientos, y alertas (RF-10 a RF-13) — Should/Could Have; implica quitar la deuda DT-01.
6. Arreglos menores: DT-08, DT-05, pruebas de pantallas en el CI (hoy se saltan sin pantalla).

## Cómo trabajar cada tarea
1. Crea una rama (`feature/…`, `fix/…`). 2. Escribe primero la prueba que falla. 3. Implementa lo mínimo. 4. Corre `python -m unittest discover -s tests`.
5. Si cambia un comportamiento o una decisión, regístralo en `docs/contexto/DECISIONES.md`. 6. Abre un Pull Request con la plantilla del repo.

## Lo que NO sabemos (no lo inventes)
Cómo atiende realmente un vendedor, qué equipo e internet tiene la tienda, qué datos pide el propietario de sus clientes, y las reglas de la lista «Pendientes por confirmar».

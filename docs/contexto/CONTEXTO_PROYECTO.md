# Contexto general del proyecto TIENDAS S.M

Proyecto académico de **Ingeniería de Software I** (Ingeniería de Sistemas, Universidad de Pamplona). Se desarrolla por fases;
hay que **mantener coherencia y trazabilidad** y no cambiar decisiones anteriores sin justificarlo.

## Información general
- **Nombre:** TIENDAS S.M · **MVP:** sistema de gestión de inventario, ventas y créditos para tiendas de barrio.
- **Integrante / rol:** Yamid Sneider Merchan Castro, diseñador y desarrollador del sistema.
- **Usuarios principales:** propietario o administrador, vendedor o encargado de caja, encargado de bodega/inventario.

## Problema que busca solucionar
Las tiendas de barrio necesitan controlar productos, existencias, ventas, créditos de clientes y mercancía almacenada. Cuando esto se
lleva a mano es difícil conocer las existencias reales, saber qué reponer, controlar las deudas de los clientes y detectar productos
próximos a vencer. TIENDAS S.M centraliza esa información en un solo sistema.

## Alcance inicial del MVP (definido)
Gestión de productos, inventario, bodega y clientes · registro y control de ventas · ventas a crédito · pagos o abonos y saldo pendiente
de cada cliente · lotes y fechas de vencimiento · alertas de bajo stock y de lotes próximos a vencer · precio de compra y de venta.
**No agregar funcionalidades como requisito confirmado sin consultar.**

## Información mínima de los productos
Nombre · precio de compra · precio de venta · cantidad disponible · lote · fecha de vencimiento (cuando aplique) · nivel de stock para alertas.
Código de barras, categoría, proveedor, marca, unidad de medida, impuestos y presentación pueden **recomendarse**, pero **no son requisitos** hasta que se aprueben.

## Modelo de ciclo de vida: Incremental
1. Productos e inventario · 2. Ventas · 3. Clientes y créditos · 4. Lotes, vencimientos y alertas. (División preliminar; puede ajustarse con justificación.)

## Stakeholders
Propietario o administrador · vendedor o encargado de caja · encargado de bodega/inventario · cliente de la tienda (actor indirecto; sus datos deben protegerse) ·
diseñador y desarrollador.

## Decisiones que NUNCA se asumen (hay que preguntar o presentar alternativas)
Roles, usuarios y contraseñas · datos exactos del cliente · datos adicionales de productos · proveedores · categorías · código de barras · facturación ·
reportes · devoluciones y anulaciones · descuentos · impuestos · cálculo de ganancias · nivel mínimo de stock · días de alerta de vencimiento ·
reglas completas de créditos y abonos · copias de seguridad · funcionamiento con o sin internet.

## Uso de Inteligencia Artificial
La IA es una herramienta de apoyo. Todo lo que genere debe ser **comprendido, revisado y validado** antes de incorporarse. No se entregan a la IA
contraseñas, información confidencial del negocio ni datos reales de clientes. La responsabilidad final de decisiones, documentación y código es del desarrollador.

## Instrucciones para la IA que ayude
1. Mantén siempre el nombre **TIENDAS S.M**. 2. Mantén coherencia con las decisiones anteriores. 3. No inventes requisitos presentándolos como aprobados.
4. Si ves necesaria una función nueva, preséntala como **recomendación**. 5. Diferencia requisitos definidos, preliminares y recomendaciones.
6. Recuerda el modelo **Incremental**. 7. Prioriza un MVP sencillo y realizable por un estudiante. 8. Evita aumentar el alcance innecesariamente.
9. En actividades académicas usa lenguaje natural de estudiante universitario, claro y poco técnico. 10. Mantén trazabilidad entre fases.
11. Antes de modificar una decisión importante, explica por qué convendría. 12. Cuando escribas código, explica brevemente qué hace para que pueda defenderlo.

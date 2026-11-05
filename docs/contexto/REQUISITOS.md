# Requisitos, historias y prioridades (FPI-05, FPI-06, FPI-07, FPI-08)

## Requisitos funcionales
| ID | Requisito | Prioridad (MoSCoW) | Historia | Estado en el código |
| --- | --- | --- | --- | --- |
| RF-01 | Registrar, consultar y actualizar productos | Must | HU-01, HU-02 | Programado |
| RF-02 | Precio de compra y de venta de cada producto | Must | HU-01 | Programado |
| RF-03 | Controlar la cantidad disponible | Must | HU-03 | Programado (el stock mínimo se registra y valida, TD-04) |
| RF-04 | Entradas y salidas de inventario | Must | HU-03 | **Parcial** (entradas y salidas por venta sí, TD-01; salida manual por confirmar, H-1) |
| RF-05 | Registrar ventas | Must | HU-04, CU-01, CU-02 | Programado (a crédito y de contado en efectivo; transferencia y mixto son CR-02) |
| RF-06 | Descontar del inventario lo vendido | Must | HU-04 | Programado |
| RF-07 | Registrar clientes | Must | HU-05 | **Parcial** (valida nombre, límite y plazo por DT-09; sin control de duplicados; datos por definir) |
| RF-08 | Venta a crédito asociada a un cliente | Must | CU-01 | Programado |
| RF-09 | Abonos y saldo pendiente | Must | HU-06 | Programado |
| RF-10 | Registrar lotes | Should | HU-07 | Pendiente (DT-01) |
| RF-11 | Fecha de vencimiento del lote | Should | HU-07 | Pendiente |
| RF-12 | Alerta de stock bajo | Should | HU-08 | Pendiente (nivel mínimo por definir) |
| RF-13 | Alerta de lotes próximos a vencer | Could | HU-09 | Pendiente (días por definir) |

## Requisitos no funcionales (valores propuestos, sin validar con el propietario)
- RNF-01 Usabilidad: una venta de hasta 5 productos en menos de 1 minuto tras 10 minutos de explicación.
- RNF-02 Desempeño: consultas en menos de 2 s con hasta 1.000 productos.
- RNF-03 Seguridad: sin credenciales válidas no se accede a datos de clientes y créditos; contraseñas nunca en texto plano (depende de CR-01, aplazada).
- RNF-04 Consistencia: venta, descuento de inventario y deuda se guardan juntos o ninguno (**ya implementado y probado**).
- RNF-05 Mantenibilidad: todas las pruebas anteriores deben seguir pasando antes de integrar un cambio.

## Restricciones
R-01 proyecto individual dentro del semestre · R-02 alcance limitado a RF-01..RF-13 · R-03 datos personales de clientes según la Ley 1581 de 2012
(Colombia; **confirmar con el docente**) · R-04 sin datos reales en pruebas ni en herramientas de IA · R-05 tecnología, equipo y conectividad de la tienda por confirmar.

## Historias de usuario (criterios Gherkin resumidos; detalle en la FPI-06)
- **HU-01** Registrar producto con nombre, precios y cantidad inicial. Rechaza nombre vacío o precios negativos.
- **HU-02** Consultar y actualizar un producto. Cambiar el precio **no altera ventas anteriores**.
- **HU-03** Entrada de mercancía: 5 + 10 = 15. Cantidad 0 o negativa se rechaza.
- **HU-04** Venta de varios productos: A 2×2.500 + B 1×3.000 = 8.000 y descuenta el inventario. Si pide 3 y hay 1, **rechaza e informa que solo hay 1**.
- **HU-05** Registrar cliente (saldo inicial 0; duplicados por definir).
- **HU-06** Abono: deuda 50.000 − abono 20.000 = saldo 30.000; abono mayor al saldo se rechaza **mostrando el saldo**; pagar todo deja la cuenta PAGADA.
- **HU-07** Lote con fecha de vencimiento (Should) · **HU-08** alerta de stock bajo (Should) · **HU-09** alerta de lotes por vencer (Could).
- **CU-01 Registrar venta a crédito (flujo crítico):** el vendedor elige cliente y productos → el sistema verifica stock por línea, calcula el total, valida el
  crédito (límite − saldo pendiente) → descuenta el inventario, crea la cuenta por cobrar con el plazo del cliente y confirma, **todo o nada**.
  Alternativos: cliente inexistente, stock insuficiente (propuesta: rechazar e informar), venta sin productos, crédito no permitido, falla al guardar (se revierte todo).

## Hallazgos de la revisión técnica (FPI-08) y solicitudes de cambio
H-1 salida manual de mercancía sin historia · H-2 stock insuficiente sin regla confirmada · H-3 RNF-03 sin requisito funcional de acceso · H-4 consultas vs reportes ·
H-5 nivel mínimo y días de alerta sin definir. **CR-01** (acceso con usuario y contraseña): **aplazada**. **CR-02** (ampliar a proveedores, pedidos, caja, pagos mixtos,
devoluciones, usuarios y roles; 29 entidades en total): **propuesta sin aprobar**.

## Modelo de dominio (FPI-09)
29 entidades clasificadas: **núcleo** (Producto, Existencia, MovimientoInventario, Lote, Venta, DetalleVenta, Cliente, CuentaPorCobrar, Pago, AplicacionPago, Alerta, Ubicación),
**ampliación** (Categoria, Empleado, Proveedor, ProductoProveedor, PedidoCompra, DetallePedido, RecepcionCompra, DetalleRecepcion, DetallePago, Caja, SesionCaja) y
**sugerencias de IA** (MovimientoCaja, Devolucion, DetalleDevolucion, Usuario, Rol, ConfiguracionAlerta). El MVP implementa solo 8 clases del núcleo.

# Hoja de ruta hacia Ingeniería de Software II — TIENDAS S.M

Estado de partida: lógica de negocio con 77 pruebas en verde, CI configurado, sin interfaz de usuario y sin validación con el propietario.

| Prioridad | Pendiente | Por qué quedó pendiente | Referencia |
| --- | --- | --- | --- |
| Alta | Validar con el propietario las reglas propuestas: stock insuficiente, plazo y límite del crédito, nivel mínimo de stock, días de aviso, datos del cliente, salida manual | No se hizo la entrevista ni la observación en una tienda real | FPI-04, FPI-08 |
| Alta | Interfaz de escritorio con Tkinter | No se pudo construir ni probar en el entorno de trabajo; se priorizó la lógica y las pruebas | FPI-12 |
| Alta | Venta de contado (RF-05 parcial) | Solo se programó la venta a crédito, que es el flujo crítico | FPI-07, FPI-10 |
| Alta | Acceso con usuario y contraseña (RNF-03, CR-01) | Decisión de usuarios y roles pendiente con el propietario | FPI-08 |
| Media | Lotes, vencimientos y alertas (RF-10 a RF-13, DT-01) | Son Should y Could Have | FPI-07 |
| Media | Medir usabilidad y desempeño (RNF-01 y RNF-02) | Necesitan la interfaz | FPI-05 |
| Media | Decidir CR-02 (proveedores, pedidos, caja, pagos mixtos, devoluciones) y migrar abonos al modelo de pagos (DT-03) | Ampliación de alcance no aprobada | FPI-09 |
| Baja | Eliminar o probar `Venta.anular` (DT-08); parámetros del constructor de `ServicioDeVentas` (DT-05) | Poco impacto en el MVP | FPI-14, FPI-12 |
| Baja | Release final con SemVer y pruebas de interfaz | Dependen de la interfaz | FPI-13 |

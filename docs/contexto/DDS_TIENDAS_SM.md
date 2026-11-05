# DDS TIENDAS S.M — Documento de Diseño Detallado (conversión de texto del Word)

> Conversión automática a texto para que Claude Code pueda leer el documento. El original es el archivo .docx.

UNIVERSIDAD DE PAMPLONA

Programa Académico de Ingeniería de Sistemas

Documento de Diseño Detallado del Software

Sistema de gestión de inventario, ventas y créditos para tiendas de barrio · TIENDAS S.M


| DECISIÓN SOLICITADA: Aprobar el diseño técnico detallado como línea base para construir los incrementos pendientes, definir los contratos de los servicios y ejecutar las pruebas de cada incremento. |
|---|


| Campo | Información |
|---|---|
| Cliente | Propietario o administrador de la tienda de barrio piloto |
| Unidad responsable | Administración de la tienda |
| Documentos base | ERS v1.1, DAD v0.9 y prototipo visual (HTML) |
| Versión | 0.9 - Para revisión técnica y funcional |
| Fecha | 12 de octubre de 2026 |
| Clasificación | Documento técnico de diseño |


## Control del documento


| Versión | Fecha | Descripción | Estado |
|---|---|---|---|
| 0.9 | 12/10/2026 | Primera línea base del diseño detallado derivada del ERS y el DAD. | Para revisión |
| 1.0 |  | Ajustes derivados de la validación del cliente. | Pendiente |


### Registro de aprobación


| Rol | Nombre | Decisión | Firma | Fecha |
|---|---|---|---|---|
| Responsable funcional / propietario de la tienda |  | Aprobado [ ]  Ajustes [ ] |  |  |
| Vendedor o encargado de caja (usuario) |  | Aprobado [ ]  Ajustes [ ] |  |  |
| Docente asesor – Ingeniería de Software I |  | Aprobado [ ]  Ajustes [ ] |  |  |
| Responsable técnico |  | Aprobado [ ]  Ajustes [ ] |  |  |


| LÍNEA BASE: Una vez aprobado, los cambios de estados, permisos, reglas del crédito, modelo de datos o contratos de los servicios deben tramitarse mediante control de cambios. |
|---|


## Contenido

- 1. Propósito y alcance del diseño
- 2. Decisiones técnicas y SOLID
- 3. Diseño de componentes
- 4. Modelo de dominio
- 5. Estados y reglas de transición
- 6. Contratos de casos de uso
- 7. Diseño de datos
- 8. Diseño de servicios
- 9. Diseño de interfaz por función
- 10. Ventas, ticket y cálculo de saldos
- 11. Alertas y avisos
- 12. Seguridad y auditoría
- 13. Manejo de errores y concurrencia
- 14. Despliegue y operación
- 15. Estrategia de pruebas
- 16. Trazabilidad y aprobación

## 1. Propósito y alcance del diseño

Este DDS traduce la arquitectura propuesta en especificaciones implementables. Define los límites de los componentes, los contratos de los servicios, las entidades, las restricciones, las pantallas, las reglas de seguridad y las pruebas, sin reemplazar las decisiones pendientes del propietario de la tienda.


### 1.1 Objetivos verificables

- Eliminar ambigüedades antes de programar lo que falta.
- Asegurar que las catorce reglas de negocio (RN-01 a RN-14) se implementen en el dominio, los datos, los servicios y las pruebas.
- Separar responsabilidades para facilitar el mantenimiento y la evolución.
- Proporcionar una base común para desarrollo, pruebas, seguridad y aceptación del cliente.
- Conservar la trazabilidad desde el requisito hasta la evidencia de prueba.

### 1.2 Alcance técnico


| Incluido | No incluido en la primera versión |
|---|---|
| Aplicación de escritorio; productos y precios; existencias y entradas; ventas de contado y a crédito; clientes con límite y plazo; cuentas por cobrar y abonos; lotes y alertas; consultas en pantalla; registro de movimientos. | Facturación electrónica, proveedores y pedidos, corte de caja, pagos mixtos, devoluciones, usuarios y roles, reportes formales y aplicaciones web o móviles (CR-01 y CR-02 sin aprobar). |
| Impresión opcional del ticket y respaldo copiando el archivo de la base de datos. | Integraciones no confirmadas con el propietario: DIAN, pasarelas de pago y correo. |


## 2. Decisiones técnicas y aplicación de SOLID


| ARQUITECTURA: Monolito modular por capas (presentación, aplicación, dominio e infraestructura). La aplicación se ejecuta como una sola unidad, pero cada módulo conserva sus reglas y sus contratos. |
|---|


| ID | Área | Decisión | Justificación |
|---|---|---|---|
| DEC-01 | Lenguaje | Python 3.12, solo biblioteca estándar | Sencillo para un MVP académico y sin dependencias que instalar. |
| DEC-02 | Interfaz | Tkinter | Viene con Python en Windows y sirve para una aplicación de escritorio. |
| DEC-03 | Datos | SQLite con el módulo sqlite3 | Un solo archivo, sin servidor, con transacciones y llaves foráneas. |
| DEC-04 | Dinero | Números enteros en pesos | Evita errores de redondeo y los centavos no se usan. |
| DEC-05 | Fechas | Texto ISO (AAAA-MM-DD) en la base de datos | Se ordenan bien y no dependen de la configuración del equipo. |
| DEC-06 | Identificadores | Enteros autoincrementales | Suficientes para un solo equipo y fáciles de leer. |
| DEC-07 | Persistencia | Repositorios por agregado y una interfaz en el borde | Aísla las reglas del negocio de SQLite y permite pruebas con dobles. |
| DEC-08 | Pruebas | unittest y unittest.mock | Sin dependencias externas y ya integradas en la suite. |
| DEC-09 | Entrega | GitHub Flow, Actions y releases | Cambios revisados, pruebas automáticas y versiones etiquetadas. |


### 2.1 Responsabilidades SOLID


| Principio | Aplicación concreta | Control de revisión |
|---|---|---|
| SRP | Un servicio por intención: vender, controlar inventario, controlar crédito, gestionar productos y gestionar clientes. | Ningún servicio mezcla reglas, consultas SQL y pantalla. |
| OCP | Las formas de pago y la selección de lote son puntos de extensión; hoy no se abstraen porque solo hay contado y crédito. | Se reevalúa al aprobar CR-02 o la regla de lotes. |
| LSP | Cualquier implementación de RepositorioDeVentas cumple el mismo contrato y los mismos errores. | Pruebas con un doble del repositorio. |
| ISP | Una interfaz pequeña: guardar la transacción, consultar cuentas, obtener una cuenta y guardar un abono. | No hay interfaces generales con métodos ajenos. |
| DIP | Los servicios reciben sus repositorios por constructor y no importan SQLite. | Revisión de dependencias en cada Pull Request. |


## 3. Diseño de componentes

Figura 1. Componentes del sistema y dirección de dependencias.


| Módulo | Responsabilidad | Objetos principales | Fachada pública |
|---|---|---|---|
| productos | Datos, precios y validaciones del producto. | Producto | ServicioDeProductos |
| inventario | Existencias, entradas, salidas y movimientos. | Existencia, movimientos | ControlInventario |
| ventas | Armado de la venta, total y confirmación. | Venta, DetalleVenta | ServicioDeVentas |
| clientes | Datos del cliente, límite y plazo. | Cliente | ServicioDeClientes |
| creditos | Crédito disponible, saldo, abonos y vencimiento. | CuentaPorCobrar, abonos | ControlCredito |
| lotes y alertas | Lotes con vencimiento y evaluación de alertas (pendiente). | Lote, Alerta (calculada) | Por construir |
| persistencia | Base de datos y repositorios con SQLite. | BaseDeDatos, repositorios | RepositorioDeVentas y repositorios |
| composición | Crea los objetos y los conecta. | Aplicacion | Aplicacion |


### 3.1 Regla de dependencia entre módulos

- Los módulos se comunican por los métodos públicos de los servicios; no consultan tablas de otro módulo.
- Las consultas del panel pueden leer datos sin duplicar reglas ni saltarse las validaciones.
- Las transacciones críticas abarcan la venta, sus líneas, la cuenta por cobrar y las existencias.
- El ticket se arma después de confirmar la transacción, a partir de los datos guardados.

## 4. Modelo de dominio


### 4.1 Agregados y límites de consistencia


| Agregado raíz | Entidades y valores | Invariantes |
|---|---|---|
| Producto | Existencia, precio de compra, precio de venta, stock mínimo | Nombre obligatorio; precios y stock mínimo no negativos; código no repetido; existencias nunca negativas. |
| Venta | DetalleVenta, estado, total | Al menos un detalle; total igual a la suma de subtotales; cada detalle conserva su precio aplicado. |
| CuentaPorCobrar | Abonos, estado, vencimiento | Saldo = monto original − abonos y nunca negativo; cada abono es mayor a cero y no supera el saldo. |
| Cliente | Límite, plazo, crédito habilitado | Crédito disponible = límite − saldo pendiente; sin crédito habilitado no se vende a crédito. |
| Lote (pendiente) | Código, cantidad, fecha de vencimiento | La fecha de vencimiento es obligatoria; las existencias del producto son la suma de sus lotes. |


### 4.2 Políticas del dominio y de la aplicación

ReglaDeStock: verifica que la cantidad pedida, sumando las líneas repetidas del mismo producto, no supere las existencias.

ReglaDeCredito: determina si un cliente puede endeudarse: crédito habilitado y total menor o igual al crédito disponible.

CalculoDeTotal: suma cantidad por precio aplicado de cada línea.

CalculoDeSaldo: resta los abonos de la deuda original y decide si la cuenta queda pagada.

PoliticaDeLote (propuesta): al vender, descuenta primero el lote que vence antes.

PoliticaDeAlertas: compara las existencias con el stock mínimo y los lotes con los días de aviso.


### 4.3 Hechos del dominio


| Hecho | Se produce cuando | Efecto |
|---|---|---|
| VentaConfirmada | Se guarda la venta. | Descuento de existencias y movimiento de venta. |
| CuentaCreada | Se confirma una venta a crédito. | Deuda del cliente y fecha de vencimiento. |
| EntradaRegistrada | Llega mercancía. | Aumento de existencias y movimiento de entrada. |
| AbonoRegistrado | El cliente paga una parte. | Disminución del saldo. |
| CuentaPagada | El saldo llega a cero. | Estado final de la cuenta. |
| StockBajoDetectado | Las existencias llegan al mínimo. | Alerta de reposición. |
| LoteProximoAVencer | Faltan N días o menos. | Alerta de vencimiento. |

En el MVP no hay un bus de eventos: estos hechos se reflejan en los movimientos guardados y en las consultas. Se nombran para dejar claros los efectos de cada operación.


## 5. Estados y reglas de transición

Figura 2. Máquinas de estado resumidas.


| ID | Origen | Destino | Actor | Condición |
|---|---|---|---|---|
| T-01 | Venta en construcción | Venta confirmada | Vendedor | Al menos un producto y existencias suficientes (y crédito, si es a crédito). |
| T-02 | Venta confirmada | Cuenta abierta | Sistema | La venta es a crédito. |
| T-03 | Cuenta abierta | Cuenta abierta | Vendedor | Abono mayor a cero y menor al saldo. |
| T-04 | Cuenta abierta | Cuenta pagada | Vendedor | Abono igual al saldo. |
| T-05 | Cuenta abierta | Cuenta vencida | Sistema | Pasó la fecha de vencimiento con saldo mayor a cero. |
| T-06 | Cuenta vencida | Cuenta pagada | Vendedor | Abono igual al saldo. |
| T-07 | Stock suficiente | Por reponer | Sistema | Existencias menores o iguales al stock mínimo. |
| T-08 | Por reponer | Stock suficiente | Bodega | Entrada que supera el stock mínimo. |
| T-09 | Lote vigente | Próximo a vencer | Sistema | Faltan N días o menos. |
| T-10 | Próximo a vencer | Vencido o agotado | Sistema / bodega | Llega la fecha o se venden todas las unidades. |


### 5.1 Evaluación determinista del crédito


| Condición | Resultado | Acción automática |
|---|---|---|
| El cliente no tiene crédito habilitado. | RECHAZADA | No se crea la venta; se informa el motivo. |
| El total supera el crédito disponible. | RECHAZADA | No se crea la venta; se informa el crédito disponible. |
| El total es menor o igual al crédito disponible (el valor exacto es válido). | ACEPTADA | Se crea la venta, se descuenta el inventario y se abre la cuenta. |

Orden de validación: primero las existencias y después el crédito. Ninguna de las dos validaciones cambia datos.


## 6. Contratos de casos de uso


### UC-01 · Registrar venta a crédito (CU-01)

Entrada: Cliente y lista de líneas (producto y cantidad).

Validaciones: cliente existente con crédito habilitado; productos existentes; cantidades enteras mayores a cero; existencias suficientes sumando líneas repetidas; total menor o igual al crédito disponible.

Resultado: Venta confirmada, existencias descontadas y cuenta por cobrar abierta con vencimiento igual a la fecha más el plazo del cliente; todo en una transacción.

Hechos del dominio: VentaConfirmada, CuentaCreada

Figura 3. Secuencia de registro de una venta a crédito.


### UC-02 · Registrar venta de contado (CU-02, por construir)

Entrada: Lista de líneas, forma de pago y, en efectivo, valor recibido.

Validaciones: productos y cantidades válidos; existencias suficientes; efectivo recibido mayor o igual al total.

Resultado: Venta confirmada y existencias descontadas, sin cuenta por cobrar; cambio calculado.

Hechos del dominio: VentaConfirmada


### UC-03 · Gestionar productos (CU-03)

Entrada: Nombre, precios de compra y de venta, stock mínimo y cantidad inicial.

Validaciones: nombre obligatorio; precios y stock mínimo no negativos; código no repetido; producto existente al actualizar.

Resultado: Producto registrado o actualizado; las ventas anteriores no cambian.

Hechos del dominio: EntradaRegistrada (si hay cantidad inicial)


### UC-04 · Registrar entrada de mercancía (CU-04)

Entrada: Producto, cantidad y, si vence, código de lote y fecha de vencimiento.

Validaciones: producto existente; cantidad entera mayor a cero; lote y fecha obligatorios si el producto vence.

Resultado: Existencias aumentadas y movimiento de entrada guardado.

Hechos del dominio: EntradaRegistrada


### UC-05 · Gestionar clientes (CU-05)

Entrada: Nombre, indicador de crédito, límite y plazo.

Validaciones: nombre obligatorio; límite no negativo; plazo de al menos un día.

Resultado: Cliente registrado o actualizado.

Hechos del dominio: Ninguno


### UC-06 · Registrar abono (CU-06)

Entrada: Cuenta por cobrar y valor del abono.

Validaciones: cuenta existente; valor entero mayor a cero; valor menor o igual al saldo.

Resultado: Abono guardado y saldo recalculado; la cuenta queda pagada si el saldo es cero.

Hechos del dominio: AbonoRegistrado, CuentaPagada


### UC-07 · Registrar lote (CU-07, por construir)

Entrada: Producto que vence, código de lote, cantidad y fecha de vencimiento.

Validaciones: producto marcado como que vence; fecha válida; si el lote ya existe, la fecha debe coincidir.

Resultado: Lote creado o ampliado y existencias del producto actualizadas.

Hechos del dominio: EntradaRegistrada


### UC-08 · Consultar alertas (CU-08, por construir)

Entrada: Ninguna: usa los datos guardados y los parámetros.

Validaciones: stock mínimo y días de aviso válidos.

Resultado: Lista de productos por reponer, lotes por vencer y créditos vencidos; no modifica datos.

Hechos del dominio: StockBajoDetectado, LoteProximoAVencer


## 7. Diseño de datos

Figura 4. Modelo lógico de entidades principales.


| Tabla | Propósito | Restricción principal |
|---|---|---|
| productos | Catálogo con precios y stock mínimo. | nombre NOT NULL; precios enteros; código y categoría recomendados, aún sin implementar |
| existencias | Cantidad disponible por producto. | PK y FK a productos; cantidad no negativa (regla del dominio) |
| movimientos_inventario | Historial de entradas, salidas y ventas. | FK a productos; tipo, cantidad y fecha obligatorios |
| clientes | Personas con crédito. | nombres NOT NULL; límite y plazo obligatorios |
| ventas | Operaciones de contado y a crédito. | FK opcional a clientes; total obligatorio |
| detalles_venta | Líneas de cada venta. | FK a ventas y productos; precio aplicado y subtotal |
| cuentas_por_cobrar | Deuda de cada venta a crédito. | FK a ventas y clientes; monto y vencimiento |
| abonos | Pagos de cada cuenta. | FK a cuentas_por_cobrar; valor entero |
| lotes (pendiente) | Grupos de unidades con vencimiento. | UNIQUE(producto, código); fecha de vencimiento obligatoria |


### 7.1 Reglas de persistencia

- Las ventas, los abonos y los movimientos no se eliminan físicamente desde la aplicación.
- Los valores monetarios se guardan como enteros y las fechas como texto ISO.
- Las llaves foráneas están activadas en cada conexión.
- Las restricciones de la base de datos refuerzan las reglas, pero la explicación funcional vive en el dominio.
- Las consultas usan parámetros, nunca texto concatenado.
- El esquema se crea al iniciar; cuando cambie, se documentará una migración manual antes de la primera instalación real.

### 7.2 Transacciones críticas


| Operación | Límite transaccional |
|---|---|
| Registrar venta a crédito | Validar; insertar la venta; insertar los detalles; insertar la cuenta por cobrar; actualizar las existencias. Si algo falla, se revierte todo. |
| Registrar venta de contado (por construir) | Validar; insertar la venta y los detalles; actualizar las existencias. |
| Registrar entrada | Actualizar la existencia (o el lote) e insertar el movimiento. |
| Registrar abono | Insertar el abono y actualizar el estado de la cuenta. |
| Registrar producto | Insertar el producto y su existencia inicial en cero; luego registrar la entrada inicial. |


## 8. Diseño de servicios


### 8.1 Convenciones

- Los servicios se llaman con nombres en español y estilo snake_case, y reciben datos simples o líneas de venta.
- Los valores monetarios son enteros en pesos.
- Los servicios devuelven objetos del dominio, no filas de la base de datos.
- Las operaciones que cambian datos son atómicas; las consultas no tienen efectos.
- Los errores del negocio son excepciones con un mensaje claro, que la interfaz muestra tal como llega.
- La interfaz solo llama a los servicios; no contiene reglas ni SQL.

| Operación | Servicio | Resultado |
|---|---|---|
| registrar_producto(nombre, precio_compra, precio_venta, cantidad_inicial=0) | ServicioDeProductos | Producto |
| actualizar_precio(id_producto, nuevo_precio) | ServicioDeProductos | Producto |
| registrar_entrada(id_producto, cantidad) | ServicioDeProductos | Existencia |
| registrar_cliente(nombres, credito_habilitado, limite_credito, plazo_credito_dias) | ServicioDeClientes | Cliente |
| registrar_venta_a_credito(id_cliente, lineas) | ServicioDeVentas | Venta |
| registrar_venta_de_contado(lineas, forma_de_pago, recibido) (por construir) | ServicioDeVentas | Venta |
| hay_disponible(producto, cantidad) · cantidad_disponible(producto) | ControlInventario | Verdadero o falso · entero |
| registrar_abono(id_cuenta, monto) | ControlCredito | CuentaPorCobrar |
| cuentas_del_cliente(id_cliente) · saldo_pendiente(cliente) | ControlCredito | Lista de cuentas · entero |
| guardar_transaccion(venta, cuenta, existencias) | RepositorioDeVentas | Nada (o error) |


### 8.2 Ejemplos de error de negocio


| StockInsuficiente · «Solo hay 1 disponibles de Producto A» La venta no se registra. El mensaje incluye la cantidad que sí hay, para que el vendedor ajuste la cantidad o quite el producto, y no cambia ningún dato. |
|---|


| ValueError · «El abono (60000) no puede ser mayor al saldo pendiente, que es 30000» El abono no se registra y la cuenta conserva su saldo. El mensaje muestra cuánto se debe. |
|---|


## 9. Diseño de interfaz por función


| Perfil | Navegación principal | Control clave |
|---|---|---|
| Propietario | Panel, productos, existencias, clientes, créditos y abonos, alertas y parámetros. | Cambios de precio y de límite con confirmación. |
| Vendedor | Punto de venta, clientes, abonos y consulta de precios. | Botón de confirmar deshabilitado mientras la venta no sea válida. |
| Encargado de bodega | Existencias, entrada de mercancía, lotes y alertas. | Lote y fecha obligatorios en productos que vencen. |


### 9.1 Ficha del punto de venta

- Encabezado: búsqueda por código o nombre con sugerencias y cantidad.
- Cuerpo: tabla de la venta con precio, cantidad con botones más y menos, importe y botón para quitar.
- Panel lateral: total grande, número de productos y botones Cobrar de contado y Vender a crédito.
- Diálogo de cobro: en contado, forma de pago, valor recibido y cambio; a crédito, cliente, límite, deuda, crédito disponible y plazo.
- Cierre: ticket de la venta con la opción de imprimir.

### 9.2 Criterios de uso y accesibilidad


| Criterio | Especificación |
|---|---|
| Ventana | Tamaño mínimo de 1024 × 600 píxeles; se adapta al redimensionar. |
| Teclado | Orden lógico, foco visible, Esc cierra los diálogos y atajos propuestos F2, F4 y F9. |
| Contraste | Mínimo WCAG AA; el color no es el único indicador de estado (se acompaña de texto). |
| Tablas | Con búsqueda y filtros; con muchos productos se muestran por páginas o con desplazamiento. |
| Mensajes | Lenguaje claro, con las cantidades concretas y junto al campo con el error. |
| Dinero | Con separador de miles y símbolo de pesos, por ejemplo $ 17.300. |
| Confirmaciones | Antes de confirmar una venta o de registrar un abono; el botón se desactiva tras el primer clic. |


## 10. Ventas, ticket y cálculo de saldos


### 10.1 Ciclo de la venta


| Paso | Control |
|---|---|
| Armado | Producto existente y cantidad entera mayor a cero; si ya está en la venta, se suman las cantidades. |
| Existencias | Se compara la suma pedida por producto con las existencias; si no alcanza, se informa cuántas hay. |
| Cálculo | Cada línea toma el precio vigente; el total es la suma de los subtotales. |
| Crédito | En ventas a crédito se valida el crédito disponible del cliente. |
| Confirmación | Una sola transacción: venta, detalles, cuenta (si aplica) y existencias. |
| Ticket | Se genera desde la venta guardada y no se almacena aparte. |
| Después | La venta no se modifica ni se borra; una corrección se haría con una operación nueva (fuera del alcance actual). |


### 10.2 Reglas de cálculo

Subtotal = cantidad × precio aplicado. Total = suma de los subtotales. Cambio = valor recibido − total. Saldo de una cuenta = deuda original − suma de los abonos. Deuda del cliente = suma de los saldos de sus cuentas. Crédito disponible = límite − deuda del cliente. Vencimiento = fecha de la venta + plazo del cliente. Todos los valores son enteros en pesos.


| CONTROL DE INTEGRIDAD: El saldo y la deuda no se guardan como valores editables: se calculan a partir de la deuda original y de los abonos. Así no pueden quedar desactualizados. |
|---|


### 10.3 Contenido mínimo del ticket

- Número de venta, fecha y hora.
- Líneas vendidas con cantidad, nombre, precio aplicado y subtotal.
- Total, forma de pago y cambio en pagos en efectivo.
- En ventas a crédito: nombre del cliente y fecha de vencimiento.
- Aviso de que es un comprobante interno y no una factura.

### 10.4 Versionamiento del ticket

El ticket se regenera desde los datos de la venta; si cambia el formato, los tickets antiguos se generan con el formato nuevo. Si se aprueba la facturación, se definirá un consecutivo único y un archivo versionado.


## 11. Alertas y avisos


| Alerta | Destinatario | Momento | Contenido mínimo |
|---|---|---|---|
| Stock bajo | Propietario y bodega | Al abrir el panel y tras cada venta o entrada | Producto, existencias, stock mínimo y pedido pendiente (CR-02). |
| Lote por vencer | Propietario y bodega | Al abrir el panel | Producto, lote, unidades y días para vencer. |
| Crédito vencido | Propietario y vendedor | Al abrir el panel | Cliente, saldo y días de atraso. |


### 11.1 Evaluación de las alertas

- Las alertas se calculan a partir de los datos guardados; no se almacenan.
- Se recalculan al abrir el panel y después de cada venta, entrada o abono.
- Se ordenan por urgencia: lotes vencidos o por vencer, créditos vencidos y productos por reponer.
- El MVP no envía correos ni mensajes externos; todo se muestra en la pantalla.

### 11.2 Validación de parámetros


| Regla | Respuesta |
|---|---|
| Stock mínimo negativo o no numérico | Se rechaza con un mensaje claro. |
| Días de aviso que no son un número entero de 0 o más | Se rechaza y se conserva el valor anterior. |
| Plazo de crédito menor a un día | Se rechaza. |
| Lote sin código o sin fecha de vencimiento | Se rechaza la entrada. |
| Fecha de vencimiento anterior a hoy | Se advierte al usuario antes de guardar (propuesta, por confirmar). |


## 12. Seguridad y auditoría


### 12.1 Controles de acceso


| Capa | Control |
|---|---|
| Autenticación | Depende de CR-01 (aplazada): usuario y contraseña con hash, nunca en texto plano. |
| Servicios | Validan cada entrada; los permisos por función se aplican cuando exista CR-01. |
| Datos | Consultas parametrizadas, llaves foráneas y archivo de la base de datos con los permisos del sistema operativo. |
| Archivos | El archivo de la base de datos y sus copias se guardan en una carpeta con acceso restringido. |
| Administración | Acciones sensibles (cambiar precios, límites o restablecer datos) con confirmación. |
| Observabilidad | Los mensajes y registros no incluyen datos personales innecesarios. |


### 12.2 Eventos obligatorios de auditoría

- Entradas, salidas y ventas de inventario (hoy se guardan en movimientos_inventario).
- Ventas de contado y a crédito con el precio aplicado.
- Abonos y cambios de saldo.
- Cambios de precio de un producto (recomendado).
- Cambios de límite o de plazo de un cliente (recomendado).
- Restablecimiento de datos y copias de respaldo.

### 12.3 Estructura de auditoría


| Campo | Descripción |
|---|---|
| id_evento | Número único del evento. |
| fecha_hora | Fecha y hora del equipo. |
| accion | Código estable de la operación (por ejemplo, VENTA_A_CREDITO o ABONO). |
| entidad / id_entidad | Objeto afectado: producto, cliente, venta o cuenta. |
| valor_anterior / valor_nuevo | Resumen de los valores cambiados, sin datos innecesarios. |
| motivo | Obligatorio cuando aplique (por ejemplo, un cambio de límite). |
| resultado | Éxito o error, con el mensaje del error. |

Hoy solo existe el registro de movimientos de inventario; la bitácora completa es una recomendación pendiente de aprobar.


## 13. Manejo de errores y concurrencia


| Error | Tipo | Cuándo ocurre |
|---|---|---|
| StockInsuficiente: «Solo hay N disponibles de X» | Negocio | La cantidad pedida supera las existencias. |
| CreditoNoPermitido | Negocio | El cliente no tiene crédito o el total supera el crédito disponible. |
| ValueError: «La venta no tiene productos» | Validación | Se intenta confirmar una venta vacía. |
| ValueError: «La cantidad debe ser mayor a cero» | Validación | Cantidad, entrada o abono de 0 o negativo. |
| ValueError: «El producto no existe» / «La cuenta por cobrar no existe» / «El cliente no existe» | Validación | Se usa un identificador que no está registrado. |
| ValueError: «El abono (V) no puede ser mayor al saldo pendiente, que es S» | Validación | El abono supera el saldo de la cuenta. |
| ValueError: «El nombre es obligatorio» / «Los precios no pueden ser negativos» | Validación | Datos inválidos al registrar un producto. |
| sqlite3.Error | Técnico | Falla de la base de datos; se revierte la transacción. |


### 13.1 Concurrencia e idempotencia

- El MVP funciona en un solo equipo con un solo punto de venta; no se admite compartir el mismo archivo desde varios equipos.
- SQLite serializa las escrituras y las transacciones evitan estados parciales.
- Un doble clic en Confirmar no debe duplicar la venta: la interfaz desactiva el botón tras el primer clic.
- Una operación que falla se puede reintentar sin efectos a medias.

## 14. Despliegue y operación


| Elemento | Diseño |
|---|---|
| Aplicación | Carpeta con el código, que se ejecuta con Python 3.12; la forma de empaquetarla (ejecutable) está por definir. |
| Base de datos | Un archivo SQLite en la carpeta de datos del usuario de la tienda. |
| Respaldo | Copia del archivo de la base de datos, con la fecha en el nombre, hecha por el propietario. |
| Actualizaciones | Cada versión se publica como release de GitHub con SemVer (por ejemplo, v0.1.1). |
| Ambientes | Desarrollo (equipo del desarrollador), pruebas (GitHub Actions) y producción (equipo de la tienda). |
| Secretos | No hay: el sistema no usa claves y el pipeline no usa secretos. |
| Observabilidad | Mensajes de error claros y registro de movimientos. |


### 14.1 Objetivos operativos iniciales


| Indicador | Objetivo inicial | Medición |
|---|---|---|
| Respuesta | Consultas de existencias y precio en menos de 2 s con 1.000 productos (RNF-02). | Cronómetro en una prueba. |
| Venta rápida | Una venta de 5 productos en menos de 1 minuto (RNF-01). | Prueba con 3 personas. |
| Cobertura de pruebas | Al menos 90 % de líneas. | medir_cobertura.py en el pipeline. |
| Recuperación | Restaurar la copia de la base de datos en menos de 30 minutos (propuesta). | Ensayo de restauración. |
| Volumen | Operar con 10.000 ventas sin lentitud notable (propuesta). | Prueba con datos ficticios. |


## 15. Estrategia de pruebas


| Nivel | Objeto | Herramienta | Criterio |
|---|---|---|---|
| Unitarias | Reglas del dominio y servicios con dobles | unittest y mock | Ramas críticas cubiertas. |
| Integración | Repositorios y servicios con SQLite real | unittest | Transacciones y restricciones. |
| Caja negra | Criterios de aceptación y valores límite | unittest | CN-01 a CN-08 aprobados. |
| Regresión | Defectos corregidos | unittest | BUG-01 y BUG-02 sin reaparecer. |
| Calidad | Funciones largas, complejidad y código muerto | Scripts propios y ruff | Sin hallazgos en el pipeline. |
| Interfaz | Flujos reales por función | Pruebas manuales y de Tkinter | Pendiente de construir. |
| Rendimiento | Consultas con 1.000 productos | Cronómetro | Menos de 2 s (pendiente). |
| Recuperación | Respaldo y restauración | Procedimiento manual | Datos restaurados. |


### 15.1 Escenarios obligatorios de aceptación


| ID | Escenario | Resultado esperado |
|---|---|---|
| PA-01 | Venta con más unidades de las que hay | Rechazo, mensaje con las unidades disponibles y sin cambios. |
| PA-02 | Mismo producto en dos líneas que, sumadas, no alcanzan | Rechazo; no se descuenta nada. |
| PA-03 | Confirmar una venta sin productos | Rechazo y no se guarda nada. |
| PA-04 | Venta a crédito a un cliente sin crédito | Se rechaza con el motivo. |
| PA-05 | Venta igual al crédito disponible y otra de un peso más | La primera se acepta y la segunda se rechaza. |
| PA-06 | Abono mayor al saldo y abono por todo el saldo | El primero se rechaza mostrando el saldo; el segundo deja la cuenta pagada. |
| PA-07 | Cambio de precio después de una venta | La venta anterior conserva su precio. |
| PA-08 | Falla simulada al guardar una venta a crédito | No quedan la venta, el descuento ni la deuda. |
| PA-09 | Entrada de 0 o negativa, o a un producto inexistente | Rechazo con un mensaje claro y sin cambios. |
| PA-10 | Entrada de un producto que vence sin lote o sin fecha | Rechazo (pendiente de construir). |
| PA-11 | Cliente con plazo de 15 días | El vencimiento es la fecha de la venta más 15 días. |
| PA-12 | Alertas de stock y de vencimiento en el valor límite | Aparecen en el límite y no un valor después (pendiente de construir). |


## 16. Trazabilidad y aprobación


| Req. | Regla | Módulo | Caso | Prueba |
|---|---|---|---|---|
| RN-01 | Stock suficiente | inventario / ventas | UC-01, UC-02 | PA-01, PA-02 |
| RN-02 | Venta con productos | ventas | UC-01, UC-02 | PA-03 |
| RN-03 | Crédito permitido | creditos / clientes | UC-01 | PA-04, PA-05 |
| RN-04 | Saldo y abonos | creditos | UC-06 | PA-06 |
| RN-05 | Precio vigente | productos / ventas | UC-01, UC-03 | PA-07 |
| RN-06 | Todo o nada | ventas / persistencia | UC-01, UC-02 | PA-08 |
| RN-07 | Movimientos válidos | inventario | UC-04 | PA-09 |
| RN-08 | Lote con vencimiento | lotes y alertas | UC-04, UC-07 | PA-10 |
| RN-09 | Stock mínimo | lotes y alertas | UC-08 | PA-12 |
| RN-10 | Aviso de vencimiento | lotes y alertas | UC-08 | PA-12 |
| RN-11 | Plazo del crédito | creditos | UC-01 | PA-11 |
| RN-12 | Selección de lote | inventario | UC-01, UC-07 | PA-10 |
| RN-13 | Registros permanentes | persistencia | Todos | Revisión: no hay operación de borrado |
| RN-14 | Datos del producto | productos | UC-03 | PA-09 |


### 16.1 Correspondencia SWEBOK v4


| Área | Evidencia en este DDS |
|---|---|
| Requisitos | Trazabilidad, reglas, contratos y criterios. |
| Arquitectura | Componentes, dependencias y despliegue. |
| Diseño | Dominio, datos, servicios, estados, interfaz y secuencias. |
| Construcción | Convenciones, módulos y transacciones. |
| Pruebas | Niveles, herramientas y escenarios obligatorios. |
| Seguridad | Validación, datos personales, integridad y respaldo. |
| Operaciones | Ambientes, respaldo y objetivos operativos. |
| Calidad | Revisiones SOLID, accesibilidad y puertas de aceptación. |
| Configuración | Versionado del código, del esquema y de los documentos. |
| Mantenimiento | Módulos desacoplados, parámetros y contratos estables. |


### 16.2 Decisiones pendientes del cliente


| ID | Decisión | Impacto |
|---|---|---|
| DP-01 | Qué hacer con el stock insuficiente y qué lote se descuenta primero. | ControlInventario y reglas de venta. |
| DP-02 | Reglas del crédito: tope, plazo, mora e intereses. | ControlCredito y cuentas. |
| DP-03 | Datos del cliente y cómo evitar duplicados. | Cliente y ServicioDeClientes. |
| DP-04 | Stock mínimo (general o por producto) y días de aviso. | Alertas y parámetros. |
| DP-05 | Salida manual de mercancía. | ControlInventario y movimientos. |
| DP-06 | Usuarios y contraseñas (CR-01). | Seguridad y permisos. |
| DP-07 | Ampliación CR-02, facturación, impuestos y ganancias. | Alcance y modelo de datos. |
| DP-08 | Equipo, instalación, empaquetado y respaldo. | Despliegue y operación. |


### 16.3 Puerta de aprobación

- [  ] Los estados y las transiciones corresponden a la operación real de la tienda.
- [  ] Las responsabilidades y restricciones por función son correctas.
- [  ] Las catorce reglas de negocio están correctamente diseñadas y trazadas.
- [  ] El modelo de datos y la seguridad son aceptables para el propietario.
- [  ] Las decisiones DP-01 a DP-08 tienen respuesta o responsable asignado.
- [  ] Se autoriza construir la interfaz, la venta de contado y los lotes con alertas.

| Concepto final | Marcar | Observaciones |
|---|---|---|
| Aprobado sin cambios | [  ] |  |
| Aprobado con ajustes menores | [  ] |  |
| Requiere nueva revisión | [  ] |  |


| Nombre y cargo | Firma | Fecha |
|---|---|---|
|  |  |  |

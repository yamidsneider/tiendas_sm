# ERS TIENDAS S.M — Especificación de Requisitos (conversión de texto del Word)

> Conversión automática a texto para que Claude Code pueda leer el documento. El original es el archivo .docx.

UNIVERSIDAD DE PAMPLONA

Programa Académico de Ingeniería de Sistemas

Especificación de Requisitos de Software

Sistema de gestión de inventario, ventas y créditos para tiendas de barrio · TIENDAS S.M


| PROPÓSITO DE APROBACIÓN Este documento define el alcance funcional y técnico propuesto para validación del propietario de la tienda y del docente asesor. La aprobación autoriza su uso como línea base para diseño, estimación y desarrollo. |
|---|


| Campo | Información |
|---|---|
| Cliente | Propietario o administrador de la tienda de barrio piloto |
| Unidad responsable | Administración de la tienda |
| Tipo de producto | Aplicación de escritorio para Windows con base de datos local (Python, SQLite y Tkinter) |
| Versión del documento | 1.1 – Para aprobación |
| Fecha | 8 de octubre de 2026 |
| Estado | Para revisión y aprobación del cliente |


## Control del documento


| Versión | Fecha | Descripción | Estado |
|---|---|---|---|
| 1.0 | 15/09/2026 | Catálogo preliminar de requisitos del MVP (RF-01 a RF-13 y requisitos no funcionales preliminares). | Sustituida |
| 1.1 | 08/10/2026 | Integra historias de usuario, priorización MoSCoW, reglas de negocio, criterios de aceptación y decisiones pendientes tras la revisión técnica. | Para aprobación |


### Registro de aprobación


| Rol | Nombre | Decisión | Firma | Fecha |
|---|---|---|---|---|
| Cliente / propietario de la tienda |  | Aprobado ☐  Con ajustes ☐  Rechazado ☐ |  |  |
| Docente asesor – Ingeniería de Software I |  | Aprobado ☐  Con ajustes ☐  Rechazado ☐ |  |  |
| Responsable técnico |  | Aprobado ☐  Con ajustes ☐  Rechazado ☐ |  |  |


| EFECTO DE LA APROBACIÓN: Los cambios posteriores que afecten alcance, reglas de negocio o criterios de aceptación deberán registrarse mediante control de cambios (solicitud CR-xx con análisis de impacto y decisión explícita). |
|---|


## 1. Introducción


### 1.1 Propósito

Definir los requisitos funcionales, reglas de negocio, atributos de calidad y condiciones de aceptación del sistema TIENDAS S.M, que apoyará al propietario, al vendedor y al encargado de bodega de una tienda de barrio en el control de productos, existencias, ventas, créditos y vencimientos. El documento constituye la línea base para validar el producto antes del diseño detallado y la construcción.


### 1.2 Alcance

El sistema centralizará la operación diaria de la tienda: registro de productos con sus precios; control de existencias con entradas de mercancía; registro de ventas de contado y a crédito con descuento automático del inventario; registro de clientes con su límite de crédito; abonos y saldo pendiente de cada cliente; y, como funciones posteriores, el manejo de lotes con fecha de vencimiento y las alertas de stock bajo y de lotes próximos a vencer. Sustituirá el cuaderno de fiado, el control de inventario en papel y la revisión manual de fechas de vencimiento mediante un registro único, el cálculo automático de totales y saldos y la trazabilidad de cada movimiento.

El desarrollo sigue el modelo de ciclo de vida Incremental en cuatro incrementos: (1) productos e inventario; (2) ventas; (3) clientes y créditos; (4) lotes, vencimientos y alertas.


### 1.3 Fuera del alcance de esta versión

- Facturación y comprobantes electrónicos, impuestos y cálculo de ganancias.
- Proveedores, pedidos de compra y recepción de mercancía (ampliación CR-02, pendiente de aprobación).
- Corte de caja, pagos mixtos y devoluciones o anulaciones de ventas (ampliación CR-02, pendiente de aprobación).
- Reportes formales y estadísticas; solo se incluyen consultas en pantalla.
- Usuarios, roles y contraseñas (solicitud de cambio CR-01, aplazada hasta confirmar con el propietario).
- Copias de seguridad automáticas, aplicación móvil, aplicación web y funcionamiento en línea.

### 1.4 Enfoque de ingeniería

La solución se desarrollará conforme a prácticas de SWEBOK v4, con trazabilidad entre requisitos, historias de usuario, diseño, código y pruebas. La arquitectura aplicará los principios SOLID de forma selectiva: responsabilidades separadas entre inventario, crédito y ventas, y una abstracción para la persistencia que desacopla las reglas de negocio de la base de datos. El MVP usa únicamente la biblioteca estándar de Python.


## 2. Actores y responsabilidades


| Actor | Responsabilidades |
|---|---|
| Propietario o administrador | Registrar y actualizar productos, precios y stock mínimo; registrar clientes y habilitar su crédito; consultar existencias, ventas, deudas y alertas; confirmar las reglas pendientes del negocio. |
| Vendedor o encargado de caja | Registrar ventas de contado y a crédito; consultar precios y disponibilidad; registrar los abonos de los clientes. |
| Encargado de bodega / inventario | Registrar entradas de mercancía, lotes y fechas de vencimiento; atender las alertas de stock bajo y de vencimiento. |
| Cliente de la tienda (actor indirecto) | No usa el sistema. Sus compras a crédito y sus abonos los registra el vendedor; sus datos deben protegerse. |
| Sistema | Validar reglas, descontar el inventario, calcular totales y saldos, generar alertas, guardar cada operación de forma completa o no guardarla y conservar el historial. |


## 3. Flujo funcional propuesto

- El propietario registra los productos con su precio de compra, su precio de venta y su stock mínimo.
- El encargado de bodega registra las entradas de mercancía; si el producto vence, registra el lote y su fecha de vencimiento.
- El propietario registra a los clientes que podrán comprar a crédito, con su límite y su plazo de pago.
- El vendedor registra la venta: busca los productos, indica las cantidades y el sistema calcula el total con el precio vigente.
- El sistema verifica que haya existencias suficientes de cada producto; si no, rechaza la venta e informa cuántas unidades hay.
- Si la venta es de contado, el vendedor confirma el cobro; si es a crédito, elige al cliente y el sistema valida su crédito disponible.
- Al confirmar, el sistema guarda la venta, descuenta el inventario y, si es a crédito, crea la cuenta por cobrar con su fecha de vencimiento, todo en una sola operación.
- Cuando el cliente paga, el vendedor registra el abono y el sistema actualiza el saldo pendiente hasta dejar la cuenta pagada.
- El sistema genera alertas de productos con stock bajo y de lotes próximos a vencer.
- El propietario consulta existencias, ventas, deudas y alertas para decidir qué reponer, qué vender primero y a quién cobrar.

## 4. Estados del negocio


| Código | Estado | Condición de salida |
|---|---|---|
| V01 | Venta en construcción | El vendedor confirma la venta o la cancela antes de guardarla. |
| V02 | Venta confirmada | Estado final: la venta no se modifica ni se borra. |
| C01 | Cuenta por cobrar abierta | Se registra un abono parcial o llega la fecha de vencimiento sin pagar. |
| C02 | Cuenta por cobrar vencida | Se registran abonos que cubran el saldo. |
| C03 | Cuenta por cobrar pagada | Estado final: saldo igual a cero. |
| S01 | Stock suficiente | Las existencias llegan al stock mínimo o por debajo. |
| S02 | Stock por reponer | Entrada de mercancía que supere el stock mínimo, o se agotan las existencias. |
| S03 | Producto agotado | Entrada de mercancía. |
| L01 | Lote vigente | Faltan N días o menos para el vencimiento. |
| L02 | Lote próximo a vencer | Llega la fecha de vencimiento o el lote se agota por ventas. |
| L03 | Lote vencido | Retiro de las unidades del inventario (salida manual por confirmar). |
| L04 | Lote agotado | Estado final: sin unidades disponibles. |


## 5. Requisitos funcionales


### 5.1 Productos y precios


| ID | Requisito | Prioridad | Historia |
|---|---|---|---|
| RF-01 | Permitir registrar, consultar y actualizar productos con nombre, código de barras o interno (recomendado) y categoría (recomendado). No se permite eliminar productos. | Must | HU-01, HU-02 |
| RF-02 | Registrar el precio de compra y el precio de venta de cada producto, como enteros en pesos, y usar el precio de venta vigente en cada venta. Cambiar un precio no altera las ventas ya registradas. | Must | HU-01, HU-02 |


### 5.2 Inventario y bodega


| ID | Requisito | Prioridad | Historia |
|---|---|---|---|
| RF-03 | Controlar y mostrar la cantidad disponible de cada producto, con su stock mínimo. | Must | HU-03 |
| RF-04 | Registrar entradas de mercancía con cantidad y fecha. Las salidas por venta se registran automáticamente. La salida manual (mermas, daños) queda por confirmar con el propietario. | Must | HU-03 |


### 5.3 Ventas


| ID | Requisito | Prioridad | Historia |
|---|---|---|---|
| RF-05 | Registrar ventas de uno o varios productos, de contado o a crédito, calculando el total con el precio de venta de cada producto. | Must | HU-04 |
| RF-06 | Descontar del inventario la cantidad vendida de cada producto al confirmar la venta, y rechazar la venta si no hay existencias suficientes, informando cuántas unidades hay. | Must | HU-04 |


### 5.4 Clientes, créditos y abonos


| ID | Requisito | Prioridad | Historia |
|---|---|---|---|
| RF-07 | Registrar clientes con nombre, indicador de crédito habilitado, límite de crédito y plazo de pago. Los datos adicionales del cliente están por definir. | Must | HU-05 |
| RF-08 | Realizar ventas a crédito asociadas a un cliente con crédito habilitado, sin superar su crédito disponible, y crear la cuenta por cobrar con su fecha de vencimiento. | Must | CU-01 |
| RF-09 | Registrar abonos y mantener actualizado el saldo pendiente. Permitir consultar, por cliente, la deuda, los abonos y el saldo. | Must | HU-06 |


### 5.5 Lotes, vencimientos y alertas


| ID | Requisito | Prioridad | Historia |
|---|---|---|---|
| RF-10 | Registrar lotes de los productos que vencen, con código y cantidad. | Should | HU-07 |
| RF-11 | Registrar la fecha de vencimiento de cada lote; es obligatoria para los productos que vencen. | Should | HU-07 |
| RF-12 | Generar una alerta cuando la cantidad disponible de un producto sea menor o igual a su stock mínimo. | Should | HU-08 |
| RF-13 | Generar una alerta de los lotes con unidades que venzan dentro de los próximos N días. | Could | HU-09 |


## 6. Reglas de negocio obligatorias


| ID | Nombre | Definición |
|---|---|---|
| RN-01 | Stock suficiente | No se puede vender más de lo disponible. Si la cantidad pedida supera las existencias, el sistema rechaza la venta e informa cuántas unidades hay (regla propuesta, por confirmar). Si el mismo producto aparece en varias líneas, se suman sus cantidades. |
| RN-02 | Venta con productos | Una venta solo puede confirmarse con al menos un producto de cantidad mayor a cero. |
| RN-03 | Crédito permitido | Una venta a crédito exige un cliente con crédito habilitado y un total que no supere su crédito disponible (límite menos saldo pendiente). Un total igual al crédito disponible es válido. |
| RN-04 | Saldo y abonos | Saldo pendiente = deuda original − abonos. Un abono debe ser mayor a cero y no puede superar el saldo; al rechazarlo, el sistema muestra el saldo. Con saldo cero la cuenta queda pagada. |
| RN-05 | Precio vigente | Cada venta guarda el precio de venta vigente al momento de venderse. Un cambio posterior de precio no modifica las ventas ya registradas. |
| RN-06 | Todo o nada | Guardar la venta, descontar el inventario y registrar la deuda se hace en una sola operación. Si algo falla, no se guarda nada. |
| RN-07 | Movimientos válidos | Toda entrada o salida de inventario tiene una cantidad mayor a cero, se registra con su fecha y hora y no puede dejar las existencias en negativo. |
| RN-08 | Lote con vencimiento | Un producto que vence solo recibe entradas asociadas a un lote con código y fecha de vencimiento. Las existencias del producto son la suma de sus lotes. |
| RN-09 | Stock mínimo | Un producto se considera por reponer cuando sus existencias son menores o iguales a su stock mínimo. El stock mínimo es por producto (propuesta, por confirmar). |
| RN-10 | Aviso de vencimiento | Se alerta de todo lote con unidades que venza dentro de N días o menos, o que ya haya vencido. El valor inicial propuesto de N es 7 días (por confirmar). |
| RN-11 | Plazo del crédito | La fecha de vencimiento de una cuenta es la fecha de la venta más el plazo del cliente; si el cliente no tiene plazo propio, se usan 30 días (por confirmar). |
| RN-12 | Selección de lote | Al vender un producto que vence, se descuenta primero el lote que vence antes (propuesta, por confirmar). |
| RN-13 | Registros permanentes | Las ventas, los abonos y los movimientos de inventario no se modifican ni se eliminan. La anulación de ventas no forma parte del alcance. |
| RN-14 | Datos del producto | El nombre es obligatorio; los precios y el stock mínimo no pueden ser negativos; el código, si se usa, no puede repetirse. |


## 7. Datos de venta, comprobante y consultas


### 7.1 Datos obligatorios de la venta

- Fecha y hora; tipo de venta: de contado o a crédito.
- Por cada producto: código, nombre, cantidad, precio aplicado y subtotal.
- Total de la venta.
- Cliente: obligatorio en las ventas a crédito.
- Forma de pago en las ventas de contado: efectivo (con cálculo del cambio). Transferencia y pago mixto forman parte de la ampliación CR-02.

### 7.2 Contenido mínimo del ticket

El sistema entrega un ticket interno de la venta; no es una factura. Incluye número de venta, fecha y hora, las líneas vendidas con su precio, el total, la forma de pago, el cambio en pagos en efectivo y, si la venta es a crédito, el nombre del cliente y la fecha de vencimiento.


| CONTINUIDAD OPERATIVA: Si ocurre un error al guardar una venta, el sistema no deja datos a medias: revierte la venta, el descuento del inventario y la deuda, y muestra un mensaje claro para que el vendedor pueda reintentar. |
|---|


### 7.3 Consultas que sustituyen los cuadernos


| Consulta | Contenido mínimo |
|---|---|
| Existencias | Producto, cantidad disponible, stock mínimo y estado (suficiente, por reponer o agotado). |
| Cuentas por cobrar | Cliente, venta de origen, deuda original, abonos, saldo, fecha de vencimiento y estado (al día, vencida o pagada). |
| Ventas | Número, fecha y hora, tipo, cliente, productos vendidos y total. |
| Alertas | Productos por reponer, lotes próximos a vencer y créditos vencidos, con la acción sugerida. |

Las consultas se muestran en pantalla. La exportación a Excel o CSV y los reportes formales son una recomendación y no forman parte del alcance aprobado.


## 8. Requisitos no funcionales


| ID | Atributo | Requisito |
|---|---|---|
| RNF-01 | Usabilidad | Tras una explicación de 10 minutos, un vendedor registra una venta de hasta 5 productos en menos de 1 minuto, sin ayuda (valor propuesto, por validar). |
| RNF-02 | Rendimiento | Las consultas de existencias y de precio responden en menos de 2 segundos con hasta 1.000 productos registrados (valor propuesto, por validar). |
| RNF-03 | Seguridad | Sin credenciales válidas no se accede a los datos de clientes y créditos, y las contraseñas nunca se guardan en texto plano. Depende de la solicitud CR-01, aplazada. |
| RNF-04 | Consistencia | La venta, el descuento del inventario y la deuda se guardan juntos o no se guarda ninguno. |
| RNF-05 | Mantenibilidad | Arquitectura modular, pruebas automáticas de las reglas críticas y todas las pruebas anteriores aprobadas antes de integrar un cambio. |
| RNF-06 | Compatibilidad | Funciona en Windows 10 y 11 con Python 3.12, sin instalar dependencias externas. |
| RNF-07 | Conectividad | Funciona sin conexión a internet; los datos se guardan en un archivo SQLite local. |
| RNF-08 | Respaldo | El propietario puede copiar el archivo de la base de datos como respaldo manual; se recomienda una copia diaria. La copia automática está por definir. |
| RNF-09 | Privacidad | Los datos personales de los clientes se tratan según la Ley 1581 de 2012 (por confirmar su aplicación con el docente). Las pruebas y las consultas a herramientas de IA usan solo datos ficticios. |
| RNF-10 | Trazabilidad | Ventas, entradas, salidas y abonos quedan registrados con fecha y hora y no se modifican ni se borran desde la aplicación. |


## 9. Arquitectura técnica de referencia

Se propone una aplicación de escritorio monolítica y modular, organizada por capas. Esta decisión mantiene la operación sencilla para una tienda de barrio y deja límites claros por si más adelante se separan módulos.


| Capa / módulo | Responsabilidad |
|---|---|
| Presentación | Interfaz de escritorio con Tkinter: punto de venta, productos, existencias, clientes, créditos y alertas (pendiente de construir). |
| Aplicación | Servicios que coordinan los casos de uso: ServicioDeProductos, ServicioDeClientes, ServicioDeVentas, ControlInventario y ControlCredito. |
| Dominio | Reglas de productos, existencias, clientes, ventas, detalles de venta y cuentas por cobrar. |
| Infraestructura | Base de datos SQLite y repositorios que guardan y consultan la información. |
| Módulos funcionales | Productos; inventario; ventas; clientes y créditos; lotes y alertas. |


### 9.1 Aplicación de SOLID


| Principio | Aplicación exigida |
|---|---|
| S – Responsabilidad única | ServicioDeVentas solo coordina; ControlInventario concentra las reglas de existencias y ControlCredito las del crédito. |
| O – Abierto/cerrado | No se aplica a las formas de pago: hoy solo hay contado y crédito. Se reevaluará si se aprueba la ampliación CR-02. |
| L – Sustitución de Liskov | El MVP no usa herencia; el principio se revisará si se agregan jerarquías. |
| I – Segregación de interfaces | Una sola interfaz pequeña y cohesiva para la persistencia de ventas y créditos. |
| D – Inversión de dependencias | Los servicios dependen de la abstracción RepositorioDeVentas, no de SQLite. |


## 10. Auditoría y control de cambios

El sistema conservará un registro de los eventos críticos que no podrá editarse desde la aplicación. Como mínimo guardará fecha y hora, acción, producto o cliente afectado y valores involucrados.

- Entradas de mercancía y salidas de inventario, incluidas las ventas.
- Ventas de contado y a crédito, con el precio aplicado en cada línea.
- Abonos y cambios de saldo de las cuentas por cobrar.
- Cambios de precio de un producto (recomendado).
- Cambios del límite o del plazo de crédito de un cliente (recomendado).
Toda modificación al alcance, a las reglas o a los criterios de aceptación se registra como solicitud de cambio (CR-xx) con análisis de impacto en requisitos, diseño, código, pruebas y documentación, y con una decisión explícita. Hoy están registradas CR-01 (acceso con usuario y contraseña), aplazada, y CR-02 (ampliación a proveedores, pedidos, caja, pagos mixtos, devoluciones y roles), propuesta sin aprobar. Los cambios al código entran por Pull Request con revisión y con el pipeline de integración continua en verde.


## 11. Criterios de aceptación de negocio


| ID | Criterio verificable |
|---|---|
| CA-01 | Con nombre, precios y cantidad válidos, el producto se guarda y aparece en la lista. |
| CA-02 | Un producto sin nombre, o con un precio negativo, no se guarda y el mensaje indica cuál campo es inválido. |
| CA-03 | Al subir el precio de venta de 2.500 a 2.700, las ventas anteriores conservan 2.500 y las nuevas usan 2.700. |
| CA-04 | Una entrada de 10 unidades a un producto con 5 deja las existencias en 15 y queda registrada con su fecha. |
| CA-05 | Una entrada de cantidad 0 o negativa se rechaza y las existencias no cambian. |
| CA-06 | Una venta de 2 unidades de un producto a 2.500 y 1 de otro a 3.000 da un total de 8.000 y descuenta ambas cantidades del inventario. |
| CA-07 | Si se piden 3 unidades de un producto con 1 en existencia, la venta se rechaza y el mensaje informa que solo hay 1. |
| CA-08 | Una venta sin productos se rechaza y no se guarda nada. |
| CA-09 | Una venta a crédito crea la cuenta por cobrar por el total y con vencimiento igual a la fecha de venta más el plazo del cliente. |
| CA-10 | Un cliente sin crédito habilitado no puede comprar a crédito. |
| CA-11 | Con un límite de 50.000 sin deuda, una venta de 50.000 se acepta y una de 50.001 se rechaza. |
| CA-12 | Si ocurre una falla al guardar una venta a crédito, no quedan la venta, el descuento del inventario ni la deuda. |
| CA-13 | Con una deuda de 50.000, un abono de 20.000 deja un saldo de 30.000. |
| CA-14 | Un abono de 60.000 con saldo de 30.000 se rechaza y el mensaje muestra el saldo. |
| CA-15 | Al abonar todo el saldo, la cuenta queda como pagada. |
| CA-16 | Una entrada de un producto que vence sin código de lote o sin fecha de vencimiento se rechaza. |
| CA-17 | Con stock mínimo 5, un producto con 5 unidades aparece en las alertas de stock bajo y uno con 6 no aparece. |
| CA-18 | Con aviso de 7 días, un lote que vence en 7 días aparece en las alertas y uno que vence en 8 días no aparece. |


## 12. Supuestos, dependencias y decisiones pendientes


| Tipo | Definición / decisión requerida |
|---|---|
| Supuesto | La tienda cuenta con un computador con Windows 10 u 11 donde se instalará el sistema. |
| Supuesto | Al inicio, el sistema lo usan el propietario y el vendedor desde el mismo equipo. |
| Dependencia | Python 3.12 instalado en el equipo de la tienda. |
| Pendiente | Confirmar qué hacer cuando se vende más de lo que hay: rechazar la venta (propuesta) u otra regla. |
| Pendiente | Confirmar qué lote se descuenta primero al vender productos que vencen. |
| Pendiente | Definir las reglas del crédito: tope por cliente, plazo, mora e intereses. |
| Pendiente | Definir los datos que se piden para registrar un cliente y cómo evitar duplicados. |
| Pendiente | Definir el nivel mínimo de stock (uno general o uno por producto) y los días de aviso de vencimiento. |
| Pendiente | Confirmar si hace falta la salida manual de mercancía (mermas, daños, consumo propio). |
| Pendiente | Decidir si habrá usuarios y contraseñas (CR-01). |
| Pendiente | Decidir si se aprueba ampliar el sistema (CR-02): proveedores, pedidos, caja, pagos mixtos y devoluciones. |
| Pendiente | Definir facturación, impuestos y la forma de calcular las ganancias. |
| Pendiente | Definir si se necesitan copias de seguridad automáticas y la exportación de datos. |


## 13. Entregables esperados

- Documento de requisitos aprobado y matriz de trazabilidad (Anexo A).
- Documentos de arquitectura (DAD) y de diseño detallado (DDS).
- Prototipo visual de la interfaz validado con el propietario.
- Código fuente versionado en GitHub, revisado mediante Pull Requests y documentado.
- Pruebas unitarias, de caja negra, de integración y de regresión, ejecutadas en el pipeline de integración continua.
- Manual de usuario y plan de respaldo de la base de datos.
- Demostración del flujo crítico (venta a crédito) y acta de aceptación del producto.

## 14. Declaración de aprobación

Mediante la firma de este documento, las partes confirman que el alcance, los requisitos y las reglas aquí consignados representan la necesidad funcional acordada. Las decisiones pendientes deberán resolverse antes del diseño detallado del componente afectado.


| Por el cliente | Por el equipo responsable |
|---|---|
| Nombre: __________________________________ | Nombre: __________________________________ |
| Cargo: ___________________________________ | Cargo: ___________________________________ |
| Firma: ___________________________________ | Firma: ___________________________________ |
| Fecha: ___________________________________ | Fecha: ___________________________________ |


| DECISIÓN DEL CLIENTE: ☐ Aprobado sin cambios     ☐ Aprobado con ajustes anexos     ☐ Requiere revisión adicional |
|---|


## Anexo A. Matriz de trazabilidad


| Requisito | Historia / caso de uso | Reglas | Criterios de aceptación | Módulo de diseño |
|---|---|---|---|---|
| RF-01 | HU-01, HU-02 | RN-05, RN-14 | CA-01, CA-02, CA-03 | ServicioDeProductos, Producto |
| RF-02 | HU-01, HU-02 | RN-05 | CA-01, CA-03 | Producto, DetalleVenta |
| RF-03 | HU-03 | RN-07 | CA-04 | Existencia, ControlInventario |
| RF-04 | HU-03 | RN-07, RN-13 | CA-04, CA-05 | ServicioDeProductos, ControlInventario |
| RF-05 | HU-04 | RN-02, RN-05 | CA-06, CA-08 | ServicioDeVentas, Venta, DetalleVenta |
| RF-06 | HU-04 | RN-01, RN-06 | CA-06, CA-07, CA-12 | ControlInventario, ServicioDeVentas |
| RF-07 | HU-05 | RN-03 | CA-10 | ServicioDeClientes, Cliente |
| RF-08 | CU-01 | RN-03, RN-06, RN-11 | CA-09, CA-10, CA-11, CA-12 | ControlCredito, CuentaPorCobrar, ServicioDeVentas |
| RF-09 | HU-06 | RN-04 | CA-13, CA-14, CA-15 | ControlCredito, CuentaPorCobrar |
| RF-10, RF-11 | HU-07 | RN-08, RN-12 | CA-16 | Lote (pendiente de construir) |
| RF-12 | HU-08 | RN-09 | CA-17 | Alertas (pendiente de construir) |
| RF-13 | HU-09 | RN-10 | CA-18 | Alertas (pendiente de construir) |

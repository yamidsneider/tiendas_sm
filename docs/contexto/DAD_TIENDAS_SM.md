# DAD TIENDAS S.M — Documento de Análisis y Diseño (conversión de texto del Word)

> Conversión automática a texto para que Claude Code pueda leer el documento. El original es el archivo .docx.

UNIVERSIDAD DE PAMPLONA

Programa Académico de Ingeniería de Sistemas

Documento de Análisis y Diseño

Sistema de gestión de inventario, ventas y créditos para tiendas de barrio · TIENDAS S.M


| DECISIÓN SOLICITADA: Aprobar el flujo operativo, la arquitectura propuesta, el modelo de información y el plan de construcción como línea base para continuar el desarrollo. |
|---|


| Campo | Información |
|---|---|
| Cliente | Propietario o administrador de la tienda de barrio piloto |
| Unidad responsable | Administración de la tienda |
| Documento relacionado | ERS TIENDAS S.M, versión 1.1 |
| Versión | 0.9 - Para revisión técnica y funcional |
| Fecha | 10 de octubre de 2026 |
| Clasificación | Documento técnico de proyecto |


## Control del documento


| Versión | Fecha | Cambio | Estado |
|---|---|---|---|
| 0.9 | 10/10/2026 | Primera línea base de análisis y diseño derivada del ERS 1.1. | Para revisión |
| 1.0 |  | Ajustes aprobados por el cliente. | Pendiente |


### Registro de aprobación


| Rol | Nombre | Decisión | Firma | Fecha |
|---|---|---|---|---|
| Responsable funcional / propietario de la tienda |  | Aprobado [ ]  Ajustes [ ] |  |  |
| Vendedor o encargado de caja (usuario) |  | Aprobado [ ]  Ajustes [ ] |  |  |
| Docente asesor – Ingeniería de Software I |  | Aprobado [ ]  Ajustes [ ] |  |  |
| Responsable técnico |  | Aprobado [ ]  Ajustes [ ] |  |  |


| CONTROL DE CAMBIOS: Después de la aprobación, cualquier cambio que altere reglas, alcance o criterios de aceptación deberá evaluarse, estimarse y registrarse como solicitud de cambio (CR-xx). |
|---|


## Contenido

- 1. Propósito y línea base
- 2. Principios y decisiones de diseño
- 3. Modelo del proceso y estados
- 4. Actores y permisos
- 5. Casos de uso
- 6. Arquitectura de software
- 7. Diseño de datos
- 8. Interfaces e integraciones
- 9. Seguridad, datos y auditoría
- 10. Experiencia de usuario
- 11. Calidad y pruebas
- 12. Backlog y plan de construcción
- 13. Riesgos y decisiones pendientes
- 14. Trazabilidad SWEBOK y aprobación

## 1. Propósito y línea base


### 1.1 Objetivo

Transformar los requisitos del ERS en una solución técnica coherente, verificable y construible. El documento define responsabilidades, estados, componentes, información, interfaces y criterios de calidad sin sustituir las decisiones pendientes del propietario de la tienda.


### 1.2 Alcance de esta fase

- Modelar el ciclo operativo de la tienda: productos, entradas de mercancía, ventas, créditos, abonos y alertas.
- Definir las funciones autorizadas para el propietario, el vendedor y el encargado de bodega.
- Proponer una arquitectura de escritorio modular y mantenible, con SOLID aplicado de forma selectiva.
- Definir las entidades principales, las interfaces, los controles de seguridad y la auditoría.
- Organizar el desarrollo en incrementos demostrables, siguiendo el modelo Incremental.

### 1.3 Supuestos


| ID | Supuesto de diseño | Validación requerida |
|---|---|---|
| SUP-01 | La tienda dispone de un computador con Windows 10 u 11 y Python 3.12 instalado. | Confirmar el equipo disponible. |
| SUP-02 | La tienda opera con un solo punto de venta; todos los usuarios trabajan en el mismo equipo y sin red. | Confirmar cuántos equipos y personas atienden. |
| SUP-03 | Los valores monetarios son pesos enteros, sin centavos. | Confirmar con el propietario. |
| SUP-04 | Solo una parte de los productos vence y se maneja por lotes. | Confirmar cuáles productos. |
| SUP-05 | Las reglas pendientes (stock insuficiente, lote, crédito) se parametrizan y no se fijan en el código. | Confirmar las decisiones D-01 a D-11. |


## 2. Principios y decisiones de diseño


| DECISIÓN ARQUITECTÓNICA: Iniciar con una aplicación de escritorio monolítica y modular, con base de datos local SQLite. Esta opción reduce la complejidad operativa de una tienda de barrio y conserva límites internos claros para crecer sin reescribir. |
|---|


### 2.1 Principios


| ID | Principio | Aplicación |
|---|---|---|
| P-01 | Trazabilidad | Todo requisito se relaciona con una historia o caso de uso, un componente, una prueba y una evidencia. |
| P-02 | Operación completa o nada | Una venta, el descuento del inventario y la deuda se guardan juntos o no se guarda ninguno. |
| P-03 | Historial permanente | Las ventas, los abonos y los movimientos de inventario no se modifican ni se borran. |
| P-04 | Precio vigente | Cada venta conserva el precio con que se vendió; un cambio de precio no altera el pasado. |
| P-05 | Reglas en el dominio | Las reglas de stock y de crédito viven en el núcleo de negocio; la pantalla no las duplica. |
| P-06 | Simplicidad | MVP realizable por un estudiante: solo biblioteca estándar de Python y una sola base de datos local. |
| P-07 | Parámetros configurables | Los días de aviso, el plazo por defecto y el stock mínimo se ajustan sin cambiar el código. |
| P-08 | Interfaz ágil y accesible | El punto de venta se maneja con teclado, con buen contraste y mensajes comprensibles. |


### 2.2 Aplicación de SOLID


| Principio | Decisión en la solución |
|---|---|
| S - Responsabilidad única | ServicioDeVentas coordina el flujo; ControlInventario concentra las reglas de existencias y ControlCredito las del crédito. |
| O - Abierto/cerrado | No se aplica a las formas de pago, porque hoy solo existen contado y crédito. Se reevalúa si se aprueba CR-02. |
| L - Sustitución de Liskov | El MVP no usa herencia. Cualquier implementación de RepositorioDeVentas debe cumplir el mismo contrato. |
| I - Segregación de interfaces | Una sola interfaz pequeña, RepositorioDeVentas, en el borde de la persistencia. |
| D - Inversión de dependencias | Los servicios dependen de la abstracción del repositorio; SQLite es solo una implementación. |


## 3. Modelo del proceso y estados

Figura 1. Ciclo operativo propuesto.


### 3.1 Macroflujo operativo

- El propietario registra los productos con su precio de compra, su precio de venta y su stock mínimo.
- El encargado de bodega registra las entradas de mercancía y, en los productos que vencen, el lote y su fecha de vencimiento.
- El propietario o el vendedor registran a los clientes que podrán comprar a crédito, con su límite y su plazo.
- El vendedor arma la venta con los productos y las cantidades, y el sistema calcula el total con el precio vigente.
- El sistema verifica las existencias de cada producto y, en una venta a crédito, el crédito disponible del cliente.
- Al confirmar, el sistema guarda la venta, descuenta el inventario y, si es a crédito, crea la cuenta por cobrar, todo en una operación.
- Cuando el cliente paga, el vendedor registra el abono y el sistema recalcula el saldo.
- El sistema evalúa las alertas de stock bajo, de lotes por vencer y de créditos vencidos.
- El propietario consulta existencias, ventas y deudas y decide qué reponer, qué vender primero y a quién cobrar.
- Todas las operaciones quedan registradas; ninguna venta ni abono se elimina.

### 3.2 Estados y transiciones


| Cód. | Estado actual | Responsable | Acción válida | Siguiente |
|---|---|---|---|---|
| V01 | Venta en construcción | Vendedor | Confirmar la venta | V02 |
| V02 | Venta confirmada | Sistema | Descontar inventario y, si es a crédito, crear la cuenta | C01 (crédito) o final |
| C01 | Cuenta abierta | Vendedor | Registrar abono; o llegar la fecha de vencimiento | C01, C02 o C03 |
| C02 | Cuenta vencida | Vendedor | Registrar abono | C02 o C03 |
| C03 | Cuenta pagada | Sistema | Estado final (saldo cero) | — |
| S01 | Stock suficiente | Sistema | Vender hasta llegar al stock mínimo | S02 |
| S02 | Stock por reponer | Bodega | Registrar entrada de mercancía | S01 o S03 |
| S03 | Producto agotado | Bodega | Registrar entrada de mercancía | S02 o S01 |
| L01 | Lote vigente | Sistema | Faltar N días o menos para vencer | L02 |
| L02 | Lote próximo a vencer | Vendedor / bodega | Vender primero; o llegar el vencimiento | L03 o L04 |
| L03 | Lote vencido | Bodega | Retirar las unidades (salida manual por confirmar) | L04 |
| L04 | Lote agotado | Sistema | Estado final | — |


| REGLA DE CONSISTENCIA: Si no hay existencias suficientes o el crédito no alcanza, la venta no cambia ningún dato. Si ocurre una falla al guardar, el sistema revierte la venta, el descuento y la deuda y muestra el error. |
|---|


## 4. Actores y permisos


### 4.1 Matriz de capacidades


| Capacidad | Propietario | Vendedor | Bodega |
|---|---|---|---|
| Consultar productos, existencias y precios | Sí | Sí | Sí |
| Registrar y actualizar productos y precios | Sí | No | No |
| Definir el stock mínimo | Sí | No | No |
| Registrar entradas de mercancía | Sí | No | Sí |
| Registrar lotes y vencimientos | Sí | No | Sí |
| Registrar ventas de contado y a crédito | Sí | Sí | No |
| Registrar clientes | Sí | Sí | No |
| Habilitar crédito y definir límite y plazo | Sí | No | No |
| Registrar abonos | Sí | Sí | No |
| Consultar deudas y saldos | Sí | Sí | No |
| Consultar alertas | Sí | Sí | Sí |
| Registrar salida manual de mercancía* | Sí | No | Sí |
| Cambiar parámetros del sistema | Sí | No | No |

* Función por confirmar con el propietario (hallazgo H-1).

El MVP todavía no controla el acceso por usuario: esta matriz documenta quién debe realizar cada acción y será de cumplimiento obligatorio si se aprueba la solicitud CR-01.


### 4.2 Restricciones de autorización

- El vendedor no cambia precios ni límites de crédito.
- Nadie puede borrar ventas, abonos ni movimientos de inventario.
- La bodega no registra ventas ni abonos.
- El cliente de la tienda no tiene acceso al sistema; sus datos solo los ve el personal autorizado.
- Los cambios de precio y de límite de crédito deberían registrarse con fecha y valor anterior (recomendado).

## 5. Casos de uso


### 5.1 Catálogo


| ID | Caso de uso | Actores | Requisitos relacionados |
|---|---|---|---|
| CU-01 | Registrar venta a crédito | Vendedor | RF-05, RF-06, RF-08 |
| CU-02 | Registrar venta de contado | Vendedor | RF-05, RF-06 |
| CU-03 | Gestionar productos y precios | Propietario | RF-01, RF-02 |
| CU-04 | Registrar entrada de mercancía | Bodega / propietario | RF-03, RF-04 |
| CU-05 | Gestionar clientes y crédito | Propietario / vendedor | RF-07, RF-08 |
| CU-06 | Registrar abono | Vendedor | RF-09 |
| CU-07 | Gestionar lotes y vencimientos | Bodega | RF-10, RF-11 |
| CU-08 | Consultar alertas | Propietario / bodega / vendedor | RF-12, RF-13 |
| CU-09 | Consultar existencias, ventas y deudas | Propietario / vendedor | RF-03, RF-09 |
| CU-10 | Registrar salida manual de mercancía (por confirmar) | Bodega / propietario | RF-04 |


### 5.2 Especificaciones de casos críticos


#### CU-01. Registrar venta a crédito

Actor principal: Vendedor o encargado de caja

Precondiciones: Existen productos con existencias y un cliente registrado con crédito habilitado.

Disparador: El vendedor selecciona Vender a crédito.

Flujo principal

1.  El vendedor busca cada producto por código o nombre e indica la cantidad.

2.  Por cada línea, el sistema verifica que haya existencias suficientes (sumando las líneas repetidas del mismo producto) y toma el precio vigente.

3.  El sistema calcula el total de la venta.

4.  El vendedor elige al cliente; el sistema muestra su límite, su deuda actual y su crédito disponible.

5.  El sistema valida que el total no supere el crédito disponible.

6.  Al confirmar, en una sola operación el sistema guarda la venta con sus líneas, descuenta el inventario y crea la cuenta por cobrar con vencimiento igual a la fecha más el plazo del cliente.

7.  El sistema muestra el ticket con el total y la fecha de vencimiento.

Excepciones y alternativas

- Si no hay existencias suficientes, la venta se rechaza y el mensaje informa cuántas unidades hay.
- Si la venta no tiene productos, no se puede confirmar.
- Si el cliente no tiene crédito o el total supera el crédito disponible, se rechaza e informa el crédito disponible.
- Si ocurre una falla al guardar, se revierte todo y se muestra el error para reintentar.
Postcondición: Venta confirmada (V02), inventario descontado y cuenta por cobrar abierta (C01).

Trazabilidad: RF-05, RF-06, RF-08, RN-01, RN-02, RN-03, RN-05, RN-06, RN-11, CA-06 a CA-12


#### CU-02. Registrar venta de contado

Actor principal: Vendedor o encargado de caja

Precondiciones: Existen productos con existencias.

Disparador: El vendedor selecciona Cobrar de contado.

Flujo principal

1.  El vendedor agrega los productos y las cantidades; el sistema verifica las existencias y calcula el total.

2.  El vendedor elige la forma de pago; en efectivo, escribe el valor recibido y el sistema calcula el cambio.

3.  Al confirmar, en una sola operación el sistema guarda la venta y descuenta el inventario.

4.  El sistema muestra el ticket con el total y el cambio.

Excepciones y alternativas

- Si el efectivo recibido no alcanza para el total, no se confirma la venta.
- Si no hay existencias suficientes, se rechaza e informa cuántas unidades hay.
- La transferencia y el pago mixto pertenecen a la ampliación CR-02.
Postcondición: Venta confirmada (V02) e inventario descontado, sin cuenta por cobrar.

Trazabilidad: RF-05, RF-06, RN-01, RN-02, RN-05, RN-06, CA-06, CA-07, CA-08


#### CU-04. Registrar entrada de mercancía

Actor principal: Encargado de bodega o propietario

Precondiciones: El producto está registrado.

Disparador: El usuario selecciona Registrar entrada.

Flujo principal

1.  El usuario elige el producto e indica la cantidad que llega.

2.  Si el producto vence, escribe el código del lote y su fecha de vencimiento.

3.  El sistema valida la cantidad y suma las unidades a las existencias (o al lote).

4.  El sistema registra el movimiento con fecha y hora y actualiza el estado del stock.

Excepciones y alternativas

- Una cantidad de 0 o negativa se rechaza y las existencias no cambian.
- Si el producto no existe, el sistema muestra un mensaje claro y no guarda nada.
- Un producto que vence sin lote o sin fecha de vencimiento se rechaza.
Postcondición: Existencias aumentadas y movimiento de entrada registrado.

Trazabilidad: RF-03, RF-04, RF-10, RF-11, RN-07, RN-08, CA-04, CA-05, CA-16


#### CU-06. Registrar abono

Actor principal: Vendedor o encargado de caja

Precondiciones: El cliente tiene una cuenta por cobrar con saldo mayor a cero.

Disparador: El vendedor selecciona Registrar abono.

Flujo principal

1.  El vendedor elige al cliente y la cuenta; el sistema muestra la deuda, los abonos y el saldo.

2.  El vendedor escribe el valor del abono.

3.  El sistema valida que el valor sea mayor a cero y no supere el saldo.

4.  El sistema registra el abono con fecha y hora y recalcula el saldo; si queda en cero, marca la cuenta como pagada.

Excepciones y alternativas

- Un abono mayor al saldo se rechaza y el mensaje muestra cuánto se debe.
- Un abono de 0 o negativo se rechaza.
- Si la cuenta no existe, el sistema muestra un mensaje claro.
Postcondición: Abono registrado y saldo actualizado (C01, C02 o C03).

Trazabilidad: RF-09, RN-04, RN-13, CA-13, CA-14, CA-15


#### CU-08. Consultar alertas

Actor principal: Propietario, encargado de bodega o vendedor

Precondiciones: Existen productos, lotes o cuentas registrados.

Disparador: El usuario abre la pantalla de alertas.

Flujo principal

1.  El sistema compara las existencias de cada producto con su stock mínimo.

2.  El sistema busca los lotes con unidades que vencen dentro de los próximos N días.

3.  El sistema identifica las cuentas por cobrar vencidas.

4.  El sistema muestra la lista priorizada, con el producto, el lote o el cliente y la acción sugerida.

Excepciones y alternativas

- Si no hay alertas, se muestra un mensaje que lo indica.
- Los valores de stock mínimo y N son parámetros por confirmar con el propietario.
Postcondición: Lista de alertas visible; no se modifica ningún dato.

Trazabilidad: RF-12, RF-13, RN-09, RN-10, CA-17, CA-18


## 6. Arquitectura de software

Figura 2. Vista lógica de la arquitectura propuesta.


### 6.1 Plataforma tecnológica propuesta


| Capa | Tecnología base | Responsabilidad |
|---|---|---|
| Interfaz | Python 3.12 + Tkinter | Pantallas, formularios, atajos de teclado y ticket de venta. |
| Aplicación y dominio | Python 3.12 (solo biblioteca estándar) | Casos de uso, reglas de negocio y validaciones. |
| Datos | SQLite 3 (módulo sqlite3) | Persistencia local, restricciones, llaves foráneas y transacciones. |
| Pruebas | unittest, unittest.mock | Pruebas unitarias, de caja negra, de integración y de regresión. |
| Calidad | Scripts propios y ruff en el CI | Cobertura, complejidad ciclomática, funciones largas y código muerto. |
| Control de versiones | Git + GitHub | GitHub Flow, Pull Requests con revisión y releases con SemVer. |
| Integración continua | GitHub Actions | Build, lint, pruebas y cobertura mínima en cada Pull Request. |
| Distribución | Por definir | Ejecutar con Python instalado o generar un ejecutable para Windows. |


| CONDICIÓN: Las versiones indicadas son la línea base de 2026. Antes de cerrar la arquitectura hay que confirmar que el equipo de la tienda soporta Python 3.12 (Tkinter viene incluido en la instalación de Python para Windows) y definir cómo se instalará y se respaldará el sistema. |
|---|


### 6.2 Módulos internos


| Módulo | Responsabilidad |
|---|---|
| Productos | ServicioDeProductos y Producto: datos, precios y validaciones del producto. |
| Inventario | ControlInventario, Existencia y movimientos: cantidades, entradas y salidas. |
| Ventas | ServicioDeVentas, Venta y DetalleVenta: armado de la venta, total y confirmación. |
| Clientes | ServicioDeClientes y Cliente: datos, límite y plazo de crédito. |
| Créditos | ControlCredito, CuentaPorCobrar y abonos: crédito disponible, saldo y vencimiento. |
| Lotes y alertas | Lotes con vencimiento y evaluación de alertas (pendiente de construir). |
| Persistencia | BaseDeDatos y repositorios con SQLite; implementa RepositorioDeVentas. |
| Composición | Aplicacion: crea los objetos y los conecta; es el único punto de arranque. |
| Interfaz | Pantallas de Tkinter que llaman a los servicios (pendiente de construir). |


### 6.3 Reglas de dependencia

- La interfaz no accede directamente a la base de datos; llama a los servicios de aplicación.
- Los servicios coordinan el dominio y las transacciones; no contienen consultas SQL.
- El dominio no depende de Tkinter ni de SQLite.
- La persistencia implementa las interfaces definidas por la aplicación.
- Cada módulo expone métodos públicos y no consulta las tablas privadas de otro.
- Los colaboradores se entregan por constructor; no se crean dentro de las clases.

## 7. Diseño de datos


### 7.1 Entidades principales


| Entidad | Finalidad | Relaciones clave |
|---|---|---|
| Producto | Datos del artículo, precios y stock mínimo. | Existencia, DetalleVenta, Lote |
| Existencia | Cantidad disponible de un producto. | Producto, MovimientoInventario |
| MovimientoInventario | Entradas, salidas y ventas con fecha y hora. | Producto |
| Cliente | Persona con crédito: límite y plazo. | Venta, CuentaPorCobrar |
| Venta | Operación de contado o a crédito con su total. | DetalleVenta, Cliente, CuentaPorCobrar |
| DetalleVenta | Línea vendida con precio aplicado y subtotal. | Venta, Producto |
| CuentaPorCobrar | Deuda de una venta a crédito con su vencimiento. | Venta, Cliente, Abono |
| Abono | Pago parcial o total de una deuda. | CuentaPorCobrar |
| Lote (pendiente) | Grupo de unidades con fecha de vencimiento. | Producto |
| Alerta (calculada) | Aviso derivado de las existencias, los lotes y las cuentas; no se guarda. | Producto, Lote, CuentaPorCobrar |


### 7.2 Restricciones de integridad

- Las existencias nunca pueden ser negativas y cada producto tiene una sola existencia.
- Una venta confirmada tiene al menos un detalle, y cada detalle guarda el precio con que se vendió.
- Una venta a crédito tiene exactamente un cliente y una cuenta por cobrar.
- Un abono es mayor a cero y no supera el saldo; el saldo se calcula (deuda − abonos) y no se edita.
- El código de un producto no puede repetirse.
- Las llaves foráneas están activadas en la base de datos.
- Un lote de un producto que vence tiene código y fecha de vencimiento.

### 7.3 Política de historial

No se aplicará borrado físico de ventas, abonos ni movimientos de inventario durante la operación normal. La anulación de ventas no forma parte del alcance; si se aprueba, se representará con un estado, un motivo y una fecha. El respaldo se hace copiando el archivo de la base de datos.


## 8. Interfaces e integraciones


### 8.1 Contratos de servicios iniciales


| Operación | Servicio | Usada por |
|---|---|---|
| registrar_producto(nombre, precio_compra, precio_venta, cantidad_inicial) | ServicioDeProductos | Propietario |
| actualizar_precio(id_producto, nuevo_precio) | ServicioDeProductos | Propietario |
| registrar_entrada(id_producto, cantidad) | ServicioDeProductos | Bodega |
| registrar_cliente(nombres, credito_habilitado, limite_credito, plazo_credito_dias) | ServicioDeClientes | Propietario / vendedor |
| registrar_venta_a_credito(id_cliente, lineas) | ServicioDeVentas | Vendedor |
| registrar_venta_de_contado(lineas, forma_de_pago) (por construir) | ServicioDeVentas | Vendedor |
| registrar_abono(id_cuenta, monto) | ControlCredito | Vendedor |
| cuentas_del_cliente(id_cliente) y saldo_pendiente(cliente) | ControlCredito | Propietario / vendedor |
| guardar_transaccion(venta, cuenta, existencias) | RepositorioDeVentas | ServicioDeVentas |

Los nombres son contratos de referencia. Las firmas definitivas están en el código fuente y en las pruebas, que se versionan juntos.


### 8.2 Salidas del sistema


| Salida | Destinatario | Contenido mínimo |
|---|---|---|
| Ticket de venta | Cliente y vendedor | Número, fecha y hora, líneas, total, forma de pago, cambio y, si es a crédito, cliente y vencimiento. |
| Alertas | Propietario | Productos por reponer, lotes por vencer y créditos vencidos, con la acción sugerida. |
| Copia de respaldo | Propietario | Archivo de la base de datos con fecha en el nombre. |

- El MVP no envía correos ni se integra con servicios externos.
- La impresión del ticket es opcional y se define con el propietario.
- La facturación electrónica y otras integraciones quedan fuera del alcance.

## 9. Seguridad, datos y auditoría


### 9.1 Controles de seguridad


| ID | Control | Aplicación |
|---|---|---|
| SEC-01 | Acceso con usuario y contraseña | Depende de CR-01 (aplazada). Si se aprueba, las contraseñas se guardan con hash y nunca en texto plano. |
| SEC-02 | Permisos por función | Aplicar la matriz de la sección 4 cuando se defina el acceso por usuario. |
| SEC-03 | Protección de datos personales | Guardar solo los datos necesarios del cliente; tratar los datos según la Ley 1581 de 2012 (por confirmar con el docente). |
| SEC-04 | Validación de entradas | Validar tipos y rangos; usar consultas SQL parametrizadas para evitar inyección. |
| SEC-05 | Secretos | El sistema no usa claves; el pipeline de CI no usa secretos y tiene permisos de solo lectura. |
| SEC-06 | Respaldo | Copia del archivo de la base de datos; se recomienda diaria. La copia automática está por definir. |
| SEC-07 | Integridad | Transacciones, llaves foráneas y operaciones de todo o nada. |
| SEC-08 | Datos de prueba | Solo datos ficticios en pruebas y en consultas a herramientas de IA. |
| SEC-09 | Control de cambios | Todo cambio entra por Pull Request con revisión de código y pipeline en verde. |


### 9.2 Auditoría obligatoria

- Entradas y salidas de inventario, incluidas las ventas.
- Ventas de contado y a crédito, con el precio aplicado en cada línea.
- Abonos y cambios de saldo.
- Cambios de precio de un producto (recomendado).
- Cambios de límite o de plazo de crédito de un cliente (recomendado).
- Restablecimiento de datos y copias de respaldo.

| REGISTRO MÍNIMO: Identificador del evento, fecha y hora, acción, producto o cliente afectado, valores involucrados y resultado. No se guardan contraseñas ni datos innecesarios del cliente. |
|---|


## 10. Experiencia de usuario


### 10.1 Mapa de pantallas


| Perfil | Pantallas principales |
|---|---|
| Común | Panel de inicio con alertas; configuración; ayuda. |
| Propietario | Productos; clientes y crédito; existencias; ventas; créditos y abonos; alertas; parámetros. |
| Vendedor | Punto de venta; clientes; abonos; consulta de precios y disponibilidad. |
| Encargado de bodega | Existencias; entrada de mercancía; lotes y vencimientos; alertas. |

El prototipo visual de estas pantallas está en el archivo tiendas_sm_dashboard.html y sirve para validar el diseño con el propietario antes de programar la interfaz.


### 10.2 Reglas de interacción

- Mostrar siempre el total de la venta en un lugar grande y visible.
- Permitir buscar el producto por código o nombre y agregarlo con la tecla Enter; atajos de teclado propuestos: F2 buscar, F9 cobrar de contado y F4 vender a crédito.
- Mostrar la disponibilidad de cada producto y avisar cuánto queda cuando se pide de más.
- Deshabilitar el botón de confirmar cuando la venta no es válida y explicar la razón.
- Confirmar las acciones sensibles y mostrar mensajes con las cantidades concretas.
- Cumplir contraste, navegación por teclado, etiquetas de formulario y mensajes comprensibles.
- Adaptar las tablas extensas con búsqueda y filtros.

## 11. Calidad y pruebas


### 11.1 Estrategia


| Nivel | Objetivo | Ejemplos |
|---|---|---|
| Unitarias | Validar reglas sin base de datos, con stubs y mocks. | Existencias, crédito disponible, abonos, total de la venta. |
| Integración | Validar la base de datos real por niveles ascendentes. | Repositorios, controles y servicio de ventas completo. |
| Caja negra | Probar desde los criterios de aceptación y valores límite. | Límite exacto de crédito, stock − 1, stock y stock + 1. |
| Regresión | Evitar que un defecto corregido vuelva a aparecer. | Ids inexistentes y plazo de crédito del cliente. |
| Interfaz | Validar los flujos reales con el propietario y el vendedor. | Venta rápida, cobro, abono y alertas (pendiente). |
| Aceptación | Validar los escenarios con usuarios de la tienda. | Ciclo completo de venta a crédito y abono. |
| Rendimiento | Comprobar el tiempo de respuesta acordado. | Consultas con 1.000 productos (pendiente). |
| Respaldo | Confirmar que se puede restaurar. | Copiar y restaurar el archivo de la base de datos. |


### 11.2 Casos de aceptación obligatorios


| ID | Escenario | Resultado esperado |
|---|---|---|
| AC-01 | Stock insuficiente (CA-07) | La venta se rechaza y el mensaje informa cuántas unidades hay. |
| AC-02 | Límite de crédito exacto (CA-11) | Una venta igual al crédito disponible se acepta y una de un peso más se rechaza. |
| AC-03 | Falla al guardar (CA-12) | No quedan la venta, el descuento ni la deuda. |
| AC-04 | Precio vigente (CA-03) | Un cambio de precio no altera las ventas anteriores. |
| AC-05 | Abono mayor al saldo (CA-14) | Se rechaza y el mensaje muestra el saldo. |
| AC-06 | Pago total (CA-15) | La cuenta queda pagada con saldo cero. |
| AC-07 | Entrada inválida (CA-05) | Una cantidad de 0 o negativa no cambia las existencias. |
| AC-08 | Lote sin fecha (CA-16) | Un producto que vence no recibe entradas sin lote y sin fecha. |
| AC-09 | Total de la venta (CA-06) | El total es la suma de precio por cantidad y el inventario baja lo vendido. |
| AC-10 | Plazo del cliente (CA-09) | El vencimiento es la fecha de la venta más el plazo del cliente. |
| AC-11 | Alerta de stock (CA-17) | Con stock mínimo 5, un producto con 5 aparece y uno con 6 no. |
| AC-12 | Alerta de vencimiento (CA-18) | Con aviso de 7 días, un lote a 7 días aparece y uno a 8 no. |


### 11.3 Criterios de salida a producción

- Cero defectos críticos o altos abiertos en las reglas de stock, crédito y abonos.
- Todos los escenarios AC-01 a AC-12 aprobados con evidencia.
- Todas las pruebas automáticas pasan en el pipeline y la cobertura es de al menos 90 %.
- Prueba de respaldo y restauración ejecutada.
- Manual de usuario disponible y piloto con el propietario y el vendedor.
- Las decisiones D-01 a D-11 confirmadas o con responsable y fecha.

## 12. Backlog y plan de construcción


### 12.1 Incrementos recomendados


| Inc. | Objetivo | Alcance principal | Demostración | Estado |
|---|---|---|---|---|
| I1 | Productos e inventario | Productos, precios, existencias y entradas (HU-01 a HU-03). | Producto registrado y entrada reflejada en el stock. | Lógica hecha |
| I2 | Ventas | Venta a crédito y de contado con descuento de inventario (HU-04, CU-01, CU-02). | Venta con total correcto e inventario actualizado. | Crédito hecho; contado pendiente |
| I3 | Clientes y créditos | Clientes, límite, cuentas por cobrar y abonos (HU-05, HU-06). | Venta fiada y abono con saldo actualizado. | Lógica hecha |
| I4 | Lotes y alertas | Lotes con vencimiento y alertas (HU-07 a HU-09). | Alerta de stock bajo y de lote por vencer. | Pendiente |
| I5 | Interfaz de escritorio | Pantallas de Tkinter para los incrementos anteriores. | Venta completa desde la pantalla. | Pendiente |
| I6 | Cierre y puesta en marcha | Respaldo, manual, acceso (si se aprueba CR-01) y piloto. | Piloto aceptado por el propietario. | Pendiente |


### 12.2 Ceremonias y evidencias

- Planificación: seleccionar historias con criterios de aceptación y dependencias claras (Sprints de una semana).
- Revisión: demostrar el software funcionando al docente asesor y, cuando sea posible, al propietario.
- Control de calidad: pruebas automatizadas y revisión de código antes de integrar.
- Trazabilidad: actualizar la relación requisito, caso de uso y prueba en cada incremento.
- Cierre de incremento: registrar la aceptación, las observaciones y la deuda técnica.
- Gestión de cambios: evaluar el impacto de cada CR-xx en alcance, datos, seguridad y cronograma.

### 12.3 Equipo mínimo recomendado


| Rol | Dedicación sugerida | Responsabilidad |
|---|---|---|
| Propietario de la tienda (Product Owner) | Por demanda | Aclara las reglas, prioriza y acepta los incrementos. |
| Responsable técnico y desarrollador | 1 persona | Análisis, diseño, desarrollo, pruebas y documentación. |
| Docente asesor | Semanal | Revisión académica y de calidad. |
| Revisor de código | Por Pull Request | Compañero o docente que revisa los cambios. |
| Usuarios piloto (vendedor y bodega) | Según prueba | Validan la interfaz y los flujos reales. |


## 13. Riesgos y decisiones pendientes


| ID | Riesgo | Prob. | Impacto | Tratamiento |
|---|---|---|---|---|
| R-01 | Reglas del negocio sin confirmar con el propietario (stock, lote, crédito) | Alta | Alta | Entrevista y observación en la tienda; parámetros configurables. |
| R-02 | Sin interfaz no se pueden validar la usabilidad ni el rendimiento | Alta | Alta | Construir una interfaz mínima con prioridad; usar el prototipo. |
| R-03 | Pérdida de datos por falla del equipo | Media | Alta | Respaldo diario del archivo y prueba de restauración. |
| R-04 | Exposición de los datos y las deudas de los clientes | Media | Alta | Acceso con contraseña (CR-01), minimizar datos y Ley 1581. |
| R-05 | Baja adopción: el vendedor prefiere el cuaderno | Media | Media | Interfaz rápida por teclado, capacitación y piloto. |
| R-06 | Ampliación del alcance sin control (CR-02) | Media | Media | Control de cambios y priorización MoSCoW. |
| R-07 | Código generado con IA que el desarrollador no domina | Media | Alta | Revisión, pruebas, bitácora de IA y práctica de sustentación. |
| R-08 | Crecimiento del archivo de datos y lentitud | Baja | Media | Medir el rendimiento con más de 1.000 productos y revisar índices. |


### 13.1 Decisiones que debe confirmar el cliente


| ID | Decisión pendiente |
|---|---|
| D-01 | Qué hacer cuando se vende más de lo que hay (rechazar la venta es la propuesta). |
| D-02 | Qué lote se descuenta primero al vender productos que vencen. |
| D-03 | Reglas del crédito: tope por cliente, plazo, mora e intereses. |
| D-04 | Datos que se piden al registrar un cliente y cómo evitar duplicados. |
| D-05 | Stock mínimo: uno general o uno por producto, y su valor. |
| D-06 | Días de anticipación para avisar un vencimiento. |
| D-07 | Si hace falta la salida manual de mercancía (mermas, daños, consumo propio). |
| D-08 | Si habrá usuarios y contraseñas (CR-01). |
| D-09 | Si se aprueba la ampliación CR-02: proveedores, pedidos, caja, pagos mixtos y devoluciones. |
| D-10 | Facturación, impuestos y forma de calcular las ganancias. |
| D-11 | Política de respaldo y forma de instalación en el equipo de la tienda. |


## 14. Trazabilidad SWEBOK y aprobación


### 14.1 Correspondencia con áreas de conocimiento


| Área SWEBOK v4 | Aplicación en el proyecto |
|---|---|
| Requisitos de software | ERS 1.1, reglas de negocio, casos de uso y criterios de aceptación. |
| Diseño de software | Arquitectura, módulos, datos, interfaces, seguridad y experiencia de usuario. |
| Construcción de software | Backlog incremental, estándares de código, SOLID selectivo y contratos de servicios. |
| Pruebas de software | Estrategia multinivel, casos de caja negra y escenarios obligatorios. |
| Mantenimiento | Modularidad, parámetros, historial y gestión de deuda técnica. |
| Gestión de configuración | Versiones de código, base de datos y documentos con Git y GitHub. |
| Gestión de ingeniería | Incrementos, equipo, riesgos, decisiones y aceptación. |
| Proceso de ingeniería | Flujo definido, evidencia por etapa y mejora iterativa. |
| Modelos y métodos | Estados, casos de uso, arquitectura y modelo de dominio. |
| Calidad de software | Controles, pruebas, revisiones de código y criterios de salida. |
| Seguridad del software | Validación de entradas, protección de datos, integridad y respaldo. |
| Práctica profesional | Responsabilidad, trazabilidad, uso responsable de IA y aprobación formal. |


### 14.2 Puerta de aprobación


| RESULTADO ESPERADO: La firma de este documento autoriza convertir el análisis en el prototipo visual validado, el diseño detallado (DDS) y la construcción de los incrementos pendientes, empezando por la interfaz de escritorio y la venta de contado. |
|---|

- [  ] El flujo y los estados representan la operación real de la tienda.
- [  ] La matriz de permisos refleja las responsabilidades reales.
- [  ] Las reglas de stock, crédito, abonos y todo o nada son correctas.
- [  ] La arquitectura y las tecnologías son compatibles con el equipo de la tienda.
- [  ] El plan de incrementos es realista para el tiempo disponible.
- [  ] Las decisiones D-01 a D-11 tienen respuesta o responsable y fecha.
- [  ] El cliente autoriza continuar con los incrementos pendientes.

| Concepto final | Marcar | Observaciones |
|---|---|---|
| Aprobado sin cambios | [  ] |  |
| Aprobado con ajustes menores | [  ] |  |
| Requiere nueva revisión | [  ] |  |


| Nombre y cargo | Firma | Fecha |
|---|---|---|
|  |  |  |

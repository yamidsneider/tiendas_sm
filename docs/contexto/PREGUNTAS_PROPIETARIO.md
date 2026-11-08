# TIENDAS S.M — Preguntas para el propietario de la tienda

Cuestionario para validar las reglas que **no se deben suponer** (FPI-04, «Pendientes por confirmar» de `CLAUDE.md`).
Se lleva impreso a la entrevista. Cada pregunta dice **qué hace hoy la app**, para que el propietario diga si le sirve o qué cambiar.
Al terminar, las respuestas se registran en `DECISIONES.md` (con fecha) y lo que cambie se programa con su prueba.

**Antes de empezar:** explicar que es un proyecto académico, que no se graba nada sin permiso y que **no se anotan nombres,
teléfonos ni deudas reales** de sus clientes (solo las reglas). Mostrar la app en el computador con los datos de ejemplo.

| Dato de la entrevista | Respuesta |
| --- | --- |
| Fecha y lugar | |
| Tipo de tienda y número de personas que atienden | |
| Equipo disponible (computador, pantalla, impresora) y si hay internet | |

---

## 1. Ventas

**1.1 Cuando se pide más de lo que hay en el sistema.**
*Hoy:* la venta no se deja hacer y el mensaje dice cuántas unidades hay.
¿Le sirve así? ¿O a veces el sistema está desactualizado y necesita vender igual?
> Respuesta:

**1.2 Formas de pago.** *Hoy:* solo efectivo (con el cambio calculado) o a crédito (fiado).
¿Recibe transferencias (Nequi, Daviplata, etc.)? ¿Una misma venta se paga a veces con dos formas?
> Respuesta:

**1.3 Ticket.** *Hoy:* se puede imprimir un comprobante interno (no es factura).
¿Lo necesita impreso? ¿Qué impresora tiene o tendría? ¿Le pide factura algún cliente?
> Respuesta:

**1.4 Código de barras.** *Hoy:* el producto se busca por su nombre.
¿Tiene o piensa comprar un lector de código de barras? ¿Sus productos traen código?
> Respuesta:

**1.5 Errores en una venta ya cobrada.** *Hoy:* las ventas no se anulan ni se devuelven.
¿Qué hace hoy cuando se equivoca o un cliente devuelve algo? ¿Con qué frecuencia pasa?
> Respuesta:

## 2. Crédito (fiado) y abonos

**2.1 Límite de crédito.** *Hoy:* cada cliente tiene su propio límite; no se le fía si la venta supera lo que le queda disponible.
¿Usa un tope igual para todos o depende de la persona? ¿Cuánto, más o menos?
> Respuesta:

**2.2 Plazo para pagar.** *Hoy:* cada cliente tiene su plazo; el que se propone es de 30 días.
¿Qué plazo da normalmente? ¿Es igual para todos?
> Respuesta:

**2.3 Cuando el cliente se atrasa (mora).** *Hoy:* la app no marca las cuentas vencidas ni cobra intereses.
¿Cobra algún interés o recargo? ¿Le sigue fiando a quien ya está atrasado? ¿Quiere ver la lista de los atrasados?
> Respuesta:

**2.4 Bajar el límite a quien ya debe.** *Hoy (preliminar):* se permite; solo impide fiarle más hasta que abone.
¿Le parece bien, o prefiere que el sistema no deje bajar el límite por debajo de lo que el cliente debe?
> Respuesta:

**2.5 Abonos.** *Hoy:* un abono no puede ser mayor a lo que se debe en esa cuenta.
¿Los clientes abonan a una compra en particular o a «lo que deben en total»?
> Respuesta:

## 3. Clientes

**3.1 Datos para registrar a un cliente.** *Hoy:* solo nombre, si tiene crédito, límite y plazo.
¿Qué más necesita para reconocerlo o cobrarle (teléfono, dirección, apodo)? Recordar que son datos personales y hay que cuidarlos.
> Respuesta:

**3.2 Clientes con el mismo nombre.** ¿Le ha pasado? ¿Cómo los distingue?
> Respuesta:

## 4. Inventario

**4.1 Stock mínimo (aviso de «por reponer»).** *Hoy:* no hay aviso.
¿Quiere un aviso cuando quede poco de un producto? ¿Un número igual para todos (por ejemplo 5) o uno distinto por producto?
> Respuesta:

**4.2 Productos que se vencen.** *Hoy:* no se manejan lotes ni fechas de vencimiento.
¿Qué productos se le vencen (lácteos, pan, carnes)? ¿Quiere un aviso? ¿Con cuántos días de anticipación?
> Respuesta:

**4.3 Qué se vende primero.** Si hay dos lotes del mismo producto, ¿se debe vender primero el que vence antes?
> Respuesta:

**4.4 Salidas que no son ventas.** *Hoy:* el inventario solo baja con las ventas.
¿Se dañan o se pierden productos, o la familia consume de la tienda? ¿Quiere registrarlo y con qué motivos?
> Respuesta:

## 5. Uso del sistema

**5.1 Usuarios y contraseñas.** *Hoy:* no hay; cualquiera que abra la app puede usarla.
¿Quién más usaría el computador? ¿Necesita que cada persona entre con su clave o que algunas cosas solo las haga usted?
> Respuesta:

**5.2 Copias de seguridad.** *Hoy:* al cerrar se guarda una copia en el mismo computador (las 7 más recientes).
¿Quiere además copiarla a una memoria USB o a otro lugar? ¿Cada cuánto?
> Respuesta:

**5.3 Otras necesidades (ampliación, no aprobada).** ¿Le serviría manejar proveedores, pedidos, el cierre de caja del día o
reportes de ventas y ganancias? ¿Cuál sería lo más importante para usted?
> Respuesta:

## 6. Prueba de uso (E-01)

Pedirle que registre una venta a crédito en la app con los datos de ejemplo, sin ayuda, y anotar:

| Medida | Resultado |
| --- | --- |
| Tiempo para registrar la venta (minutos y segundos) | |
| Dudas o errores durante la prueba | |
| ¿Qué le pareció fácil y qué difícil? | |

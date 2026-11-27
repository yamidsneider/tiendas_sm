# Hoja de ruta: de MVP a app completa — TIENDAS S.M

Creada en noviembre de 2026. Punto de partida: rama `app/web` (app de escritorio pywebview, grupos A y B del
propietario, 423 pruebas en verde). Cada fase es una rama `feature/…` con sus pruebas primero (ROJO → VERDE),
se registra en `docs/contexto/DECISIONES.md` y entra por Pull Request.

**Estado de aprobación:** el orden y las fases los aprobó el desarrollador. Lo marcado como *preguntar al propietario*
no se asume: se programa la opción más prudente, se deja como *preliminar* y se confirma después.

## Orden y por qué

| Fase | Qué | Por qué en este orden | Estado |
| --- | --- | --- | --- |
| 1 | **Reportes de ventas**: hoy, últimos 7 días y este mes. Vendido, devuelto, neto, por forma de pago, abonos recibidos, ganancia y productos más vendidos | No depende de reglas del propietario y sus totales los reusa el cierre de caja (fase 4) | Hecha (`feature/reporte-ventas`, fusionada en `app/web`) |
| 2 | **Usuarios y roles** jefe / empleado con contraseña (CR-01, RNF-03) | El propietario pidió «clave del jefe» (4.4, 5.1). Las fases 3 y 4 necesitan saber quién está en turno | Hecha (`feature/usuarios-y-roles`): clave al abrir, 2 roles; permisos del empleado preliminares |
| 3 | **Salida manual de mercancía** con motivo (daño, vencido, consumo propio) y clave del jefe (4.4) | Hoy el inventario solo baja con ventas y se descuadra | Hecha (`feature/salida-manual`): el empleado necesita la clave del jefe; motivos preliminares |
| 4 | **Caja**: abrir turno con base, cerrar con arqueo (esperado contra contado) | Lo más usado al final del día; reusa reportes y usuarios | Hecha (`feature/caja`): base del día, turno que sobrevive a cerrar la app, revisar y contar de nuevo |
| 5 | **Respaldo fuera del PC y restaurar desde la app** (5.2: respaldo al cerrar turno) | Hoy los respaldos quedan en el mismo disco | Hecha (`feature/respaldos-en-carpeta`): carpeta visible del PC (respuesta del desarrollador), al cerrar app y caja, restaurar |
| 6 | **Configuración de la tienda** (nombre, NIT, dirección en el ticket) y **desactivar productos** | Detalles que pide una tienda real; bajo riesgo | Hecha (`feature/tienda-y-productos-inactivos`): preliminar, sin respuesta del propietario |
| 7 | **Estado de cuenta del cliente** para imprimir (compras y abonos) | Ayuda a cobrar el fiado | Pendiente |
| 8 | **Proveedores y compras** (CR-02, 5.3) | Ampliación grande; necesita aprobación del propietario | Pendiente |
| 9 | **Lotes ligados al inventario** (DT-01) | Hoy los lotes son solo aviso; cambia cómo se descuenta | Pendiente |

**Fuera de esta ruta** (solo si se pide): categorías, facturación electrónica DIAN, varias cajas en red.

## Preguntas al propietario por fase (no asumir)

- **Fase 1:** ¿qué considera «ganancia»? Se programa como *precio de venta − precio de compra* de lo vendido, sin gastos
  (arriendo, servicios). Las ventas hechas antes de esta fase no guardaron el costo: su ganancia usa el precio de compra actual.
- **Fase 2:** *respondido:* 2 empleados; clave al abrir la app; permisos por rol. *Falta confirmar:* la lista exacta de lo
  que puede el empleado (hoy: vender, consultar, entradas, lotes y abonos).
- **Fase 3:** *falta confirmar* los motivos (hoy: Dañado, Vencido, Consumo propio, Otro). Autoriza el jefe (respuesta 4.4).
- **Fase 4:** *respondido:* base distinta cada día; se abre al iniciar el día y se cierra cuando haga falta; si falta o
  sobra se muestra y se puede contar de nuevo. *Falta confirmar:* si los abonos llegan en efectivo o por transferencia.
- **Fase 5:** *respondido:* en una carpeta del mismo PC.
- **Fase 8:** ¿lleva cuentas por pagar a proveedores o solo quiere registrar lo que compra?

## Cierre del proyecto (en paralelo, no son funciones)
Medir E-01/RNF-01 con personas · PR de `app/web` a `main` · actualizar README y `ESTADO_Y_PENDIENTES.md` (cifras de pruebas viejas).

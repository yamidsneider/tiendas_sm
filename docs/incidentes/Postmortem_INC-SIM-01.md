# Postmortem sin culpables — INC-SIM-01: base dañada tras un apagón (SIMULADO)

**Estado:** simulacro. Los hechos técnicos se reprodujeron en una copia del sistema el 5-nov-2026; la línea de tiempo de la tienda es **hipotética** (no ocurrió en una tienda real). Datos ficticios.
**Autor:** Yamid Sneider Merchan Castro · **Severidad:** alta (caja sin sistema 30 min y ventas por re-digitar) · **Formato:** sin culpables: se buscan fallas de proceso, no personas.

## Resumen
Tras un corte de energía, la base `tiendas_sm.db` quedó con una página dañada. La aplicación **abrió y siguió vendiendo** porque no tocaba esa página; 30 minutos después, al consultar créditos, falló con `database disk image is malformed`. Se restauró el respaldo de la noche anterior con el Runbook y se re-digitaron desde el cuaderno las ventas del día.

## Impacto (hipotético, con los números del sistema)
- 30 minutos sin poder consultar créditos ni registrar ventas.
- Las ventas del día posteriores al último respaldo se perdieron de la base (en el simulacro: 3 de 15) y se re-digitaron desde el cuaderno.
- Presupuesto de error: cada intento fallido es una falla técnica (`DatabaseError`); con 80 ventas/día, el presupuesto mensual del SLO 99,5 % es de unas 12 fallas.

## Línea de tiempo (hipotética; los tiempos técnicos son medidos)
| Hora | Hecho |
|---|---|
| 18:40 | Corte de energía (CENS). El computador se apaga sin cerrar la aplicación. |
| 18:55 | Vuelve la luz. La aplicación abre y registra ventas con normalidad (**reproducido**: con la página 2 dañada, la aplicación abrió y contó las ventas). |
| 19:25 | Al consultar un cliente aparece `database disk image is malformed`. La caja pasa al cuaderno (Runbook, Nivel 1). |
| 19:35 | Nivel 2 ejecuta `PRAGMA integrity_check`: «database disk image is malformed» (**reproducido**). |
| 19:45 | Restauración del respaldo de anoche: el archivo dañado se renombra, no se borra (**medido**: la operación de archivos tarda menos de 1 ms; el resto es tiempo humano). `integrity_check` = ok. |
| 19:55 | La caja vuelve a vender; se re-digitan las ventas del cuaderno. |

## Causa raíz (de proceso, no de persona)
1. **El respaldo era manual** (RNF-08: «basta copiar ese archivo»). Depende de que alguien se acuerde; el último fue de la noche anterior.
2. **Nadie verifica la integridad al arrancar.** El daño fue silencioso: la aplicación funcionó 30 minutos sobre una base dañada, y cada venta de ese rato se escribió sobre un archivo comprometido.
3. **No había un procedimiento escrito** para seguir vendiendo sin sistema ni para restaurar (no existía el Runbook).
4. Factor contribuyente: computador sin regulador ni UPS en una zona con cortes de energía.

Nadie «hizo algo mal»: la persona de la caja usó el sistema como siempre; el sistema no le avisó del daño ni le dio cómo recuperarse.

## Qué funcionó
- La transacción «todo o nada» (RNF-04): ninguna venta quedó a medias.
- El mensaje del presentador («no quedó nada a medias») evitó que se repitieran cobros.
- La telemetría (FPI-29) registra el tipo de error técnico al 100 %, así que la falla queda contada.

## Acciones preventivas
| Acción | Tipo | Dueño | Estado |
|---|---|---|---|
| Respaldo automático al cerrar la aplicación con la API de SQLite, verificando integridad, conservando 7 | Prevenir pérdida | Yamid (tarea 14) | Hecho en el código (`tiendas_sm/respaldo.py`, `tests/test_respaldo.py`); falta usarlo en la tienda real |
| `PRAGMA quick_check` al abrir; si falla, mensaje claro y no se vende sobre la base dañada | Detectar | Yamid (tarea 14) | Hecho en el código (`revisar_al_abrir`); la ventana del mensaje no se probó a mano |
| Runbook impreso junto a la caja + cuaderno de contingencia | Responder | Yamid / tienda | Hecho (Runbook v1.0) |
| Simulacro de restauración una vez al mes | Practicar | Yamid | PENDIENTE (primer simulacro hecho en copia) |
| Regulador o UPS | Mitigar | Propietario | Por decidir (costo) |

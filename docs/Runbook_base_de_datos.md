# Runbook — La base de datos no responde (TIENDAS S.M)

**Componente:** base SQLite de la caja (`tiendas_sm.db`) · **Versión:** 1.0 (5-nov-2026, FPI-30, ADR-14)
**Responsables reales:** Nivel 1 = la persona que atiende la caja. Nivel 2 = Yamid Sneider Merchan Castro (único desarrollador), teléfono: ____________.
**Dónde está la base:** `%LOCALAPPDATA%\TIENDAS_SM\tiendas_sm.db` (la ruta la fija `iniciar_tienda.py`). Ahí mismo quedan `telemetria.jsonl` y los respaldos.

> Todos los comandos de este Runbook se ejecutaron y se comprobaron el 5-nov-2026 sobre una copia del sistema (Python 3.12, una carpeta igual a la de la tienda). Solo usan el Python con el que ya funciona la tienda: no hay que instalar nada ni pagar ninguna herramienta. Se escriben en la ventana «Símbolo del sistema» (cmd) de Windows. **PENDIENTE:** repetirlos una vez en el computador real de la tienda.

## 1. Cuándo usar este Runbook (alertas)

| Señal | Qué significa |
|---|---|
| La caja muestra «No se pudo guardar la venta; no quedó nada a medias. Intente de nuevo.» **dos veces seguidas** | La base no aceptó la escritura (bloqueo o daño). La venta NO quedó a medias. |
| La venta tarda unos 5 segundos y luego sale ese mismo mensaje | Bloqueo: otro programa tiene la base ocupada (`database is locked`, comprobado: falla a los 5,01 s). |
| Al abrir aparece «La base de datos está dañada. No venda en el sistema: use el cuaderno y llame al soporte (Runbook)» | La revisión al abrir (`PRAGMA quick_check`, tarea 14) encontró daño. El punto de venta **no se abre**: vaya directo a 3.1 y 4.B. |
| La aplicación no abre, o aparece «database disk image is malformed» | Archivo dañado (típico después de un apagón). |
| En `telemetria.jsonl` aparecen errores `OperationalError` o `DatabaseError` | Fallas técnicas: consumen el presupuesto de error (SLO 99,5 %). |

Los mensajes «Solo hay N disponibles…», «El cliente no puede comprar a crédito…» o «efectivo insuficiente» **no** son fallas: es el sistema funcionando bien. No activan este Runbook.

## 2. Nivel 1 — La persona de la caja (primeros 5 minutos)

1. **No pierda ventas:** siga vendiendo en el **cuaderno de contingencia** (hora, productos, cantidad, total, contado o crédito y, si es crédito, el cliente con su firma).
2. Anote la **hora** en que empezó y tome una **foto** del mensaje.
3. Cierre la aplicación con la **X** de la ventana. Si hay **dos ventanas** de TIENDAS S.M abiertas, cierre las dos.
4. Abra la aplicación **una sola vez** e intente una venta.
   - Si funciona: siga normal y avise a Nivel 2 ese mismo día (no es urgente).
   - Si no funciona: **no repita más intentos**; llame a Nivel 2. **No borre ni mueva ningún archivo.**

## 3. Nivel 2 — Diagnóstico (desarrollador)

Cierre la aplicación antes de empezar.

**3.1 ¿La base está sana?**
```
python -c "import os,sys,sqlite3,shutil,datetime,json; C=os.path.join(os.environ['LOCALAPPDATA'],'TIENDAS_SM'); DB=os.path.join(C,'tiendas_sm.db'); print(sqlite3.connect(DB).execute('PRAGMA integrity_check').fetchone()[0])"
```
- `ok` → la base está bien: vaya a 4.A (bloqueo).
- `database disk image is malformed` (o cualquier otra cosa distinta de `ok`) → vaya a 4.B (daño).

**3.2 ¿Qué fallas técnicas registró la telemetría?** (requiere la FPI-29 en el repositorio)
```
python -c "import os,sys,sqlite3,shutil,datetime,json; C=os.path.join(os.environ['LOCALAPPDATA'],'TIENDAS_SM'); DB=os.path.join(C,'tiendas_sm.db'); L=[json.loads(x) for x in open(os.path.join(C,'telemetria.jsonl'),encoding='utf-8') if 'ERROR' in x]; [print(l['marca_tiempo'], l['error.tipo'], l['duracion_ms']) for l in L[-10:]]"
```
Muestra los últimos 10 errores, con hora, tipo y duración. Una duración de unos 5.000 ms con `OperationalError` es un bloqueo.

**3.3 ¿Cuántas ventas hay?**
```
python -c "import os,sys,sqlite3,shutil,datetime,json; C=os.path.join(os.environ['LOCALAPPDATA'],'TIENDAS_SM'); DB=os.path.join(C,'tiendas_sm.db'); print('ventas:', sqlite3.connect(DB).execute('SELECT COUNT(*) FROM ventas').fetchone()[0])"
```

## 4. Recuperación

### 4.A Bloqueo (`database is locked`)
1. Abra el **Administrador de tareas** (Ctrl + Shift + Esc) → pestaña Procesos. Cierre cualquier otra ventana de TIENDAS S.M y cualquier programa que tenga abierta la base (por ejemplo, un visor de SQLite).
2. Repita 3.1 (debe decir `ok`) y abra la aplicación **una sola vez**.
3. Comprobado: al liberar el bloqueo, la siguiente venta entra sin problemas y no se pierde nada.

### 4.B Archivo dañado (`database disk image is malformed`)
1. **No borre nada.** El archivo dañado se conserva: el comando de restauración lo **renombra** (`.danado_fecha`) para analizarlo después.
2. Vea los respaldos disponibles y elija el más reciente (`respaldo_AAAA-MM-DDTHHMM.db`):
```
python -c "import os,sys,sqlite3,shutil,datetime,json; C=os.path.join(os.environ['LOCALAPPDATA'],'TIENDAS_SM'); DB=os.path.join(C,'tiendas_sm.db'); [print(f) for f in sorted(os.listdir(C))]"
```
3. Restaure ese respaldo:
```
python -c "import os,sys,sqlite3,shutil,datetime,json; C=os.path.join(os.environ['LOCALAPPDATA'],'TIENDAS_SM'); DB=os.path.join(C,'tiendas_sm.db'); r=os.path.join(C,sys.argv[1]); assert os.path.isfile(r), 'no existe '+r; os.replace(DB, DB+'.danado_'+datetime.datetime.now().isoformat(timespec='minutes').replace(':','')); shutil.copy2(r, DB); print('restaurado desde', r)" respaldo_AAAA-MM-DDTHHMM.db
```
   Si el nombre del respaldo está mal escrito, el comando se detiene sin tocar nada (comprobado: «no existe …»).
4. Verifique (debe decir `ok`) y cuente las ventas:
```
python -c "import os,sys,sqlite3,shutil,datetime,json; C=os.path.join(os.environ['LOCALAPPDATA'],'TIENDAS_SM'); DB=os.path.join(C,'tiendas_sm.db'); print(sqlite3.connect(DB).execute('PRAGMA integrity_check').fetchone()[0])"
python -c "import os,sys,sqlite3,shutil,datetime,json; C=os.path.join(os.environ['LOCALAPPDATA'],'TIENDAS_SM'); DB=os.path.join(C,'tiendas_sm.db'); print('ventas:', sqlite3.connect(DB).execute('SELECT COUNT(*) FROM ventas').fetchone()[0])"
```
5. Abra la aplicación y registre en el sistema las ventas del **cuaderno de contingencia** posteriores a la hora del respaldo, en orden de hora.

## 5. Después del incidente
- Escriba el Postmortem sin culpables (plantilla de la FPI-30) en `docs/incidentes/`.
- Cuente la falla en el presupuesto de error: `python slo_mensual.py telemetria.jsonl --mes AAAA-MM`. Si dice «PRESUPUESTO AGOTADO», no se entregan funciones nuevas hasta corregir la causa (ADR-14).

## 6. Prevención (de rutina)
- **Respaldo automático** (tarea 14): cada vez que se cierra la aplicación, primero se revisa la base con `PRAGMA integrity_check`;
  si da `ok`, se crea `respaldo_AAAA-MM-DDTHHMM.db` en la misma carpeta y se conservan los **7 más recientes**. Si la base está
  dañada **no** se crea el respaldo, la consola dice «No se creó el respaldo: revise la base con el Runbook» y la telemetría registra
  `BaseDeDatosDanada`. El comando manual de abajo sigue sirviendo para un respaldo extra (por ejemplo, antes de copiarlo a la USB):
```
python -c "import os,sys,sqlite3,shutil,datetime,json; C=os.path.join(os.environ['LOCALAPPDATA'],'TIENDAS_SM'); DB=os.path.join(C,'tiendas_sm.db'); r=sqlite3.connect(DB).execute('PRAGMA integrity_check').fetchone()[0]; assert r=='ok', 'base dañada, NO se respalda: '+r; d=os.path.join(C,'respaldo_'+datetime.datetime.now().isoformat(timespec='minutes').replace(':','')+'.db'); o=sqlite3.connect(d); sqlite3.connect(DB).backup(o); o.close(); print('respaldo:', d)"
```
  Primero comprueba que la base esté sana: si está dañada, **no crea el respaldo** y termina con error («database disk image is malformed» o «base dañada, NO se respalda»); comprobado. Así nunca se guarda un respaldo dañado con nombre de respaldo bueno. Usa la API de copia de SQLite, que es segura incluso con la aplicación abierta.
- Una vez al mes: copie el respaldo más reciente a una memoria USB que no se quede en la tienda, y **practique 4.B** con una copia.
- Un regulador o UPS para el computador si el presupuesto de la tienda lo permite: los apagones son la causa más probable de daño.

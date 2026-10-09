# Práctica 2 — Silver, Gold y orquestación

| | |
|---|---|
| **Nombre** | Federico ‹apellido› |
| **student_id** | `federico` |
| **Escala** | `small` |
| **Esquema** | `‹catálogo›.bigdata_federico` |
| **Job** | `bigdata_federico_silver_gold` — ‹URL del Job› |

## 1. DAG del Job

![DAG del Job](img/dag.png)

El Job tiene cuatro tareas en línea: `ingest_bronze → build_silver → build_gold → validate`. Todas corren en Serverless. Los parámetros del Job son `student_id=federico`, `scale=small`, `expected_batch_id` y `job_run_id={{job.run_id}}`.

## 2. Resultados de las ejecuciones

| Corrida | `expected_batch_id` | Resultado | `silver_rows` | `quarantine_rows` | `gold_rows` | `gold_total_amount` | `idempotence_compared` |
|---|---|---|---:|---:|---:|---:|---|
| 1ª (Job, 03/10 13:15 UTC) | batch_002 | OK | 50.149 | 53 | 598 | 50.286.183,33 | false |
| 2ª (Job, reejecución, 13:17) | batch_002 | OK | 50.149 | 53 | 598 | 50.286.183,33 | true |
| 3ª (Job, reejecución, 13:27) | batch_002 | OK | 50.149 | 53 | 598 | 50.286.183,33 | true |
| 4ª (Job, 13:38) | batch_003 | OK | 50.349 | 55 | 669 | 50.431.198,33 | false |
| 5ª (manual, 09/10) | batch_003 | OK | 50.349 | 55 | 669 | 50.431.198,33 | true |

Las reejecuciones no cargaron archivos nuevos. El historial de `bronze_transactions_incremental` muestra solo dos `COPY INTO` (versiones 1 y 2, de 204 filas cada uno): las reejecuciones no generaron ninguna versión porque no había nada que cargar. El `MERGE` no insertó ni actualizó filas, Gold se reconstruyó con los mismos valores y `validate` comparó las métricas contra la corrida anterior sin diferencias (`idempotence_compared = true`).

`gold_rows` cuenta las filas de `gold_daily_sales`, es decir, grupos día × país × categoría × canal, no transacciones.

### Cantidades de `batch_002`

| Aceptadas | Rechazadas |
|---:|---:|
| 201 | 2 |

> Nota: estas cantidades corresponden a la corrida con `batch_002` (200 transacciones nuevas + la corrección de la 42). Después de `batch_003`, la 42 pasa a tener `source_batch_id = batch_003` en Silver, porque esa es su versión vigente. Por eso, en el estado final, `gold_batch_summary` muestra 200 aceptadas para `batch_002` y 201 para `batch_003`.

## 3. `COPY INTO` vs. `MERGE`

Resuelven problemas distintos y en niveles distintos:

- **`COPY INTO`** trabaja a nivel **archivo**. Responde a la pregunta "¿este archivo ya lo cargué?". Registra en la tabla Delta destino qué archivos ingirió, así que reejecutar la ingesta no duplica un CSV ya procesado. No mira el contenido: si el mismo registro llega dentro de otro archivo, lo carga igual.
- **`MERGE`** trabaja a nivel **registro de negocio**. Responde a la pregunta "¿esta transacción ya existe y cuál es su versión vigente?". Actualiza una transacción existente si llega una versión más nueva (como la corrección de la 42) e inserta las que no existen.

Juntos dan idempotencia de punta a punta: ni archivos repetidos ni registros repetidos.

## 4. Visualizaciones

### Consigna 1 — Evolución temporal
![Consigna 1](img/c1.png)

**Respuesta:** El 2026-03-01 fue a la vez el día de mayor monto ($7.310.840,77) y el de más transacciones (7.236), así que los dos máximos coinciden. Su ticket promedio ($1.010,34) es prácticamente igual al general ($1.001,63): ese día no vendió más caro, vendió más veces. El pico de monto lo explica el volumen, no el ticket.

### Consigna 2 — Canal y fraude
![Consigna 2](img/c2.png)

**Respuesta:** `transfer` tiene la mayor tasa global de fraude: 13,91% (2.327 de 16.723), contra 12,97% de `wallet` y 12,54% de `card`. La tasa se calculó como `SUM(fraud_transactions) / SUM(transaction_count)`. La conclusión se sostiene al mirar el volumen: los tres canales tienen casi la misma cantidad de transacciones (~16.700 cada uno), así que la diferencia no viene de que un canal tenga pocos casos. Con ese n, la diferencia de ~1 punto entre `transfer` y `wallet` es estadísticamente significativa (z ≈ 2,5), aunque chica en magnitud.

### Consigna 3 — País y categoría
![Consigna 3](img/c3.png)

**Respuesta:** La combinación de mayor monto es Brasil / `home` ($2.361.959,97). No hay una categoría dominante en todos los países: `home` lidera en BR, UY y CL, y `books` en AR y MX. Los montos líderes de cada país son muy parecidos (entre $2,17 M y $2,36 M), así que el mercado está bastante repartido. Elegí un mapa de calor porque muestra las dos dimensiones a la vez. Además, ordenar filas y columnas por total y recuadrar el líder de cada país deja ver tanto el máximo global como las diferencias entre mercados.

### Consigna 4 — Calidad del pipeline
![Consigna 4](img/c4.png)

**Respuesta:** El lote inicial tuvo 0,10% de rechazo (51 de 49.999), mientras que `batch_002` y `batch_003` tuvieron 0,99% (2 de 202 y 2 de 203). En proporción, los lotes nuevos rechazan unas 10 veces más, aunque en valor absoluto el inicial tiene muchos más rechazos (51 contra 2). Los lotes nuevos son mucho más chicos, así que cada rechazo pesa varios puntos porcentuales. Además, el generador introduce rechazos a propósito, por lo que su tasa más alta no indica necesariamente una fuente de peor calidad. Por eso comparo proporciones y no cantidades absolutas.

---

## 5. Preguntas de análisis

Todas las consultas asumen `USE SCHEMA bigdata_federico;`.

### 1. Filas físicas por lote en `bronze_transactions_incremental`

```sql
SELECT source_batch_id, COUNT(*) AS filas_fisicas
FROM bronze_transactions_incremental
GROUP BY source_batch_id
ORDER BY source_batch_id;
```

| source_batch_id | filas_fisicas |
|---|---:|
| batch_002 | 204 |
| batch_003 | 204 |

Cada lote es un único CSV, y `COPY INTO` lo cargó una sola vez aunque el Job corrió varias veces.

### 2. Aceptadas y rechazadas por lote, reconciliadas con Gold

```sql
WITH acc AS (
  SELECT source_batch_id, COUNT(*) AS aceptadas FROM silver_transactions GROUP BY source_batch_id
), rej AS (
  SELECT source_batch_id, COUNT(*) AS rechazadas FROM silver_transactions_quarantine GROUP BY source_batch_id
), calc AS (
  SELECT COALESCE(a.source_batch_id, r.source_batch_id) AS source_batch_id,
         COALESCE(a.aceptadas, 0) AS aceptadas, COALESCE(r.rechazadas, 0) AS rechazadas
  FROM acc a FULL OUTER JOIN rej r ON a.source_batch_id = r.source_batch_id
)
SELECT c.*, g.accepted_transactions AS gold_aceptadas, g.rejected_transactions AS gold_rechazadas,
       (c.aceptadas = g.accepted_transactions AND c.rechazadas = g.rejected_transactions) AS reconcilia
FROM calc c FULL OUTER JOIN gold_batch_summary g ON c.source_batch_id = g.source_batch_id
ORDER BY c.source_batch_id;
```

| source_batch_id | aceptadas | rechazadas | gold_aceptadas | gold_rechazadas | reconcilia |
|---|---:|---:|---:|---:|---|
| batch_002 | 200 | 2 | 200 | 2 | true |
| batch_003 | 201 | 2 | 201 | 2 | true |
| initial | 49.948 | 51 | 49.948 | 51 | true |

Silver y cuarentena reconcilian exactamente con `gold_batch_summary` en todos los lotes. En cambio, Bronze no suma lo mismo que aceptadas + rechazadas:

| source_batch_id | filas Bronze | duplicados exactos | sin duplicados | aceptadas + rechazadas |
|---|---:|---:|---:|---:|
| batch_002 | 204 | 1 | 203 | 202 |
| batch_003 | 204 | 1 | 203 | 203 |
| initial | 50.011 | 11 | 50.000 | 49.999 |

Por ejemplo, `batch_003` trajo 204 filas a Bronze, pero Silver creció en 200 filas (de 50.149 a 50.349) y la cuarentena en 2 (de 53 a 55). La diferencia se explica así: 204 = 200 nuevas + 2 rechazadas + 1 actualización de la transacción 42 + 1 duplicado exacto. Hay dos motivos:

1. Los **duplicados exactos** se eliminan con `dropDuplicates` antes de clasificar.
2. Las **versiones reemplazadas** de una misma transacción no se cuentan. La 42 tiene una versión en `initial` y otra en cada lote nuevo, pero en Silver queda una sola fila, atribuida al lote de su versión vigente (`batch_003`). Por eso a `initial` y a `batch_002` les "falta" una fila cada uno, y `batch_003` cuenta 201 (200 nuevas + la 42).

### 3. Motivos de rechazo por lote

```sql
SELECT source_batch_id, quality_reason, COUNT(*) AS registros
FROM silver_transactions_quarantine
GROUP BY source_batch_id, quality_reason
ORDER BY source_batch_id, registros DESC;
```

| source_batch_id | quality_reason | registros |
|---|---|---:|
| batch_002 | INVALID_AMOUNT | 1 |
| batch_002 | UNKNOWN_CUSTOMER | 1 |
| batch_003 | INVALID_AMOUNT | 1 |
| batch_003 | UNKNOWN_CUSTOMER | 1 |
| initial | INVALID_AMOUNT | 51 |

Detalle de los rechazos de los lotes nuevos:

| lote | transaction_id | customer_id | amount | motivo |
|---|---:|---:|---|---|
| batch_002 | 50620 | 19 | `N/A` | INVALID_AMOUNT |
| batch_002 | 50621 | 5999 | 27.84 | UNKNOWN_CUSTOMER |
| batch_003 | 50830 | 20 | `N/A` | INVALID_AMOUNT |
| batch_003 | 50831 | 5999 | 28.85 | UNKNOWN_CUSTOMER |

Coinciden con los casos que introduce el generador. Cada lote nuevo trae dos registros inválidos a propósito: uno con importe `N/A` (que `try_cast` convierte en `NULL`) y uno con `customer_id = 5999`, que no existe en `silver_customers` para la escala `small`. En el lote inicial, los 51 rechazos son todos importes no numéricos, que ya había detectado el diagnóstico de la práctica 1.

Los otros dos casos del generador no aparecen en cuarentena porque no son errores de calidad: el duplicado exacto se elimina con `dropDuplicates` y la corrección de la 42 se resuelve con el `MERGE`.

### 4. Seguimiento de la transacción 42

```sql
SELECT source_batch_id, transaction_id, amount, event_ts, updated_at
FROM bronze_transactions_all
WHERE try_cast(transaction_id AS BIGINT) = 42
ORDER BY updated_at;

SELECT transaction_id, amount, source_batch_id, updated_at
FROM silver_transactions
WHERE transaction_id = 42;
```

Bronze:

| source_batch_id | amount | updated_at |
|---|---:|---|
| initial | 600.11 | 2026-03-06 02:07:52 |
| batch_002 | 1999.99 | 2026-03-10 02:00:00 |
| batch_003 | 1999.99 | 2026-03-11 02:00:00 |

Silver:

| transaction_id | amount | source_batch_id | updated_at |
|---:|---:|---|---|
| 42 | 1999.99 | batch_003 | 2026-03-11 02:00:00 |

En Bronze existen 3 versiones: la original (`source_batch_id = 'initial'`, con `updated_at = event_ts`) y las correcciones de los lotes nuevos. En Silver quedó la de `updated_at` más reciente, con `amount = 1999.99` y `source_batch_id = batch_003`. La eligen dos mecanismos, y el historial de la tabla muestra cada uno en acción:

| versión | corrida | filas fuente | insertadas | actualizadas |
|---:|---|---:|---:|---:|
| 1 | batch_002 | 50.149 | 50.149 | 0 |
| 2 | batch_002 (reejecución) | 50.149 | 0 | 0 |
| 3 | batch_002 (reejecución) | 50.149 | 0 | 0 |
| 4 | batch_003 | 50.349 | 200 | **1** |
| 5 | batch_003 (manual) | 50.349 | 0 | 0 |

- En la **versión 1**, Silver se creó por primera vez, ya con `batch_002` disponible. El `row_number()` eligió la versión de `batch_002` antes del `MERGE`, así que la 42 se insertó directamente corregida y no hubo `UPDATE`.
- En la **versión 4**, la 42 ya existía en Silver con `updated_at` del 10/03. Llegó la de `batch_003` con el 11/03, se cumplió `s.updated_at > t.updated_at` y el `MERGE` hizo el único `UPDATE` de toda la historia.

### 5. Una fila por `transaction_id` en Silver

```sql
SELECT COUNT(*) AS filas, COUNT(DISTINCT transaction_id) AS ids_distintos,
       COUNT(*) - COUNT(DISTINCT transaction_id) AS diferencia
FROM silver_transactions;

SELECT transaction_id, COUNT(*) FROM silver_transactions
GROUP BY transaction_id HAVING COUNT(*) > 1;
```

Resultado: `filas = ids_distintos = 50.349`, `diferencia = 0`, ningún ID nulo, y la segunda consulta no devuelve filas. Si la deduplicación hubiera fallado, veríamos `diferencia > 0` y algún `transaction_id` con `COUNT(*) > 1`. Esto es justamente lo que controla `silver_no_duplicate_ids` en `04_validate_pipeline`.

### 6. Tasa de rechazo por lote

```sql
SELECT source_batch_id, accepted_transactions, rejected_transactions,
       ROUND(rejected_transactions / (accepted_transactions + rejected_transactions), 4) AS tasa_rechazo
FROM gold_batch_summary ORDER BY source_batch_id;
```

| source_batch_id | aceptadas | rechazadas | total | tasa_rechazo |
|---|---:|---:|---:|---:|
| batch_002 | 200 | 2 | 202 | 0,99% |
| batch_003 | 201 | 2 | 203 | 0,99% |
| initial | 49.948 | 51 | 49.999 | 0,10% |

No es correcto comparar solo cantidades absolutas. El lote `initial` tiene 49.999 registros y los lotes nuevos unos 200, así que el inicial tiene muchos más rechazos en valor absoluto (51 contra 2) aunque su tasa sea diez veces menor. La tasa normaliza por tamaño. Aun así, con lotes chicos cada rechazo mueve mucho la tasa: es una estimación con alta variabilidad.

### 7. Día de mayor monto y día de más transacciones

```sql
WITH d AS (
  SELECT sale_date, SUM(total_amount) AS monto_total, SUM(transaction_count) AS transacciones,
         ROUND(SUM(total_amount) / SUM(transaction_count), 2) AS ticket_promedio
  FROM gold_daily_sales GROUP BY sale_date
)
SELECT *, RANK() OVER (ORDER BY monto_total DESC) AS rank_monto,
          RANK() OVER (ORDER BY transacciones DESC) AS rank_transacciones
FROM d QUALIFY rank_monto = 1 OR rank_transacciones = 1;
```

| sale_date | monto_total | transacciones | ticket_promedio | rank_monto | rank_transacciones |
|---|---:|---:|---:|---:|---:|
| 2026-03-01 | 7.310.840,77 | 7.236 | 1.010,34 | 1 | 1 |

Ambos máximos coinciden en el 2026-03-01: la consulta devuelve una sola fila con los dos rankings en 1. `gold_daily_sales` tiene grano día × país × categoría × canal, así que primero hay que volver a agregar por `sale_date`. Si los máximos no coinciden, el día de mayor monto tuvo un ticket promedio más alto: monto = cantidad × ticket.

### 8. Canal con mayor tasa global de fraude

```sql
SELECT payment_channel, SUM(transaction_count) AS transacciones, SUM(fraud_transactions) AS fraudes,
       ROUND(SUM(fraud_transactions) / SUM(transaction_count), 4) AS tasa_global,
       ROUND(AVG(fraud_rate), 4) AS promedio_de_tasas_incorrecto
FROM gold_daily_sales GROUP BY payment_channel ORDER BY tasa_global DESC;
```

| payment_channel | transacciones | fraudes | tasa_global | promedio de tasas (incorrecto) |
|---|---:|---:|---:|---:|
| transfer | 16.723 | 2.327 | 13,91% | 13,91% |
| wallet | 16.724 | 2.169 | 12,97% | 12,76% |
| card | 16.902 | 2.119 | 12,54% | 12,47% |

`transfer` tiene la mayor tasa global de fraude. No corresponde promediar `fraud_rate` porque cada fila de Gold es un grupo (día × país × categoría × canal) con distinta cantidad de transacciones. El promedio simple le da el mismo peso a un grupo de 1 transacción que a uno de 200: un grupo con 1 transacción fraudulenta aporta un 100% que distorsiona el resultado. La tasa correcta es el cociente de las sumas, que equivale a un promedio ponderado por `transaction_count`. En estos datos el ranking no cambia, pero el promedio simple ya da valores distintos (`wallet`: 12,76% contra 12,97%); con grupos más desparejos podría dar vuelta el orden.

### 9. País y categoría con mayor monto

```sql
-- Máximo global
SELECT country, category, SUM(total_amount) AS monto_total
FROM gold_daily_sales GROUP BY country, category ORDER BY monto_total DESC LIMIT 1;

-- Líder por país
WITH cc AS (SELECT country, category, SUM(total_amount) AS monto_total
            FROM gold_daily_sales GROUP BY country, category)
SELECT country, category AS categoria_lider, monto_total FROM cc
QUALIFY ROW_NUMBER() OVER (PARTITION BY country ORDER BY monto_total DESC) = 1
ORDER BY monto_total DESC;
```

Máximo global: **BR / home**, con $2.361.959,97.

| country | categoría líder | monto_total |
|---|---|---:|
| BR | home | 2.361.959,97 |
| UY | home | 2.323.924,46 |
| AR | books | 2.267.722,26 |
| MX | books | 2.235.941,63 |
| CL | home | 2.167.748,03 |

`home` lidera en tres países y `books` en dos: la categoría dominante cambia según el mercado.

### 10. Auditoría y reejecución de `batch_002`

```sql
SELECT * FROM pipeline_run_audit ORDER BY recorded_at;
```

| job_run_id | expected_batch_id | silver_rows | quarantine_rows | gold_rows | gold_total_amount | recorded_at (UTC) | idempotence_compared |
|---|---|---:|---:|---:|---:|---|---|
| 1038526875346305 | batch_002 | 50149 | 53 | 598 | 50286183.33 | 2026-10-03 13:15 | false |
| 1060738437890635 | batch_002 | 50149 | 53 | 598 | 50286183.33 | 2026-10-03 13:17 | true |
| 911412694103647 | batch_002 | 50149 | 53 | 598 | 50286183.33 | 2026-10-03 13:27 | true |
| 238524314824912 | batch_003 | 50349 | 55 | 669 | 50431198.33 | 2026-10-03 13:38 | false |
| interactive | batch_003 | 50349 | 55 | 669 | 50431198.33 | 2026-10-09 13:47 | true |

Entre las dos primeras filas (`batch_002` y su reejecución) se mantienen iguales `silver_rows`, `quarantine_rows`, `gold_rows` y `gold_total_amount`. Cambian `job_run_id` y `recorded_at`, porque son dos corridas distintas. La columna que demuestra la comparación es **`idempotence_compared`**:

- En la primera fila es `false`, porque no había una corrida previa del mismo lote para comparar.
- En la segunda es `true`. `04_validate_pipeline` encontró que la fila anterior tenía el mismo `expected_batch_id` y verificó con un `assert` que las cuatro métricas fueran idénticas.

Si hubieran diferido, la tarea habría fallado y la fila no se habría escrito.

La primera corrida de `batch_003` también tiene `false`: la fila anterior era de `batch_002` y sus métricas tenían que cambiar, porque había datos nuevos. La corrida manual del 09/10 vuelve a dar `true` frente a la de `batch_003`.

---

## 6. Interpretación del código y del pipeline

### 11. ¿Qué resuelve `COPY INTO`? (`01_ingest_bronze_incremental`, celda de `COPY INTO`)

Resuelve la **carga incremental e idempotente de archivos**. Lee todo el directorio `incoming/transactions/`, pero solo inserta los archivos que todavía no cargó en esa tabla. Para lograrlo guarda, en el estado de la tabla Delta destino (`bronze_transactions_incremental`), la lista de archivos ya ingeridos, identificados por su ruta y metadatos. En la siguiente ejecución saltea esos archivos, y por eso la segunda corrida del Job insertó 0 filas.

El control es por archivo físico, no por contenido: un registro repetido dentro de un archivo nuevo se carga igual, y eso lo resuelve Silver. Forzar una recarga requiere `COPY_OPTIONS ('force' = 'true')`.

### 12. ¿Por qué `UNION ALL` en `bronze_transactions_all`? (`01_ingest_bronze_incremental`, celda de la vista)

Bronze debe ser un **registro fiel de todo lo recibido**. `UNION` (sin `ALL`) eliminaría filas idénticas, lo que ocultaría evidencia (el duplicado exacto del generador desaparecería sin dejar rastro), y además obligaría a un shuffle costoso para comparar filas. `UNION ALL` solo concatena.

Los duplicados de negocio se resuelven en **Silver** (`02_build_silver`, celda de tipado y deduplicación). Ahí está la lógica para decidir qué versión gana: `dropDuplicates` para copias exactas y `row_number()` por `_record_key` ordenado por `updated_at` para las correcciones. Esa es una regla de negocio, no de ingesta, y si mañana cambia, se puede reprocesar desde Bronze, que conserva todo.

### 13. `source_batch_id='initial'` y `updated_at = event_ts` (`01_ingest_bronze_incremental`, celda de la vista)

La tabla `bronze_transactions` de la práctica 1 no tiene las columnas `source_batch_id` ni `updated_at`, y para hacer `UNION ALL` ambas partes necesitan el mismo esquema. Entonces:

- `'initial'` etiqueta el origen, para poder rastrear y agrupar ese lote como cualquier otro.
- `event_ts` es la mejor aproximación disponible del momento de la última modificación: si no hubo corrección, la versión vigente es la del momento en que ocurrió la transacción.

Efecto sobre la 42: su versión inicial tiene `updated_at = event_ts`, y las correcciones traen un `updated_at` posterior. Por eso ganan en el `row_number()` y cumplen `s.updated_at > t.updated_at` en el `MERGE`, que ejecuta el `UPDATE`. Si la corrección trajera un `updated_at` anterior al `event_ts` original, no se aplicaría.

Detalle fino: ante un empate en `updated_at`, el desempate es `source_batch_id DESC`, y `'initial'` es mayor que `'batch_00x'` en orden alfabético. En ese caso ganaría la versión inicial.

### 14. `try_cast` vs. `cast` (`quality_rules.py`, `add_transaction_types`)

Con el modo ANSI que usa Databricks, `cast('N/A' AS DECIMAL(12,2))` lanza un error y hace fallar toda la tarea por un solo registro malo. `try_cast` devuelve `NULL` en lugar de fallar. Así el pipeline sigue corriendo, el `NULL` se detecta en las reglas de calidad y el registro va a cuarentena con su motivo. El resto del lote se procesa normalmente.

Es el mismo patrón que usó el diagnóstico de la práctica 1 para contar `invalid_amounts`.

### 15. Una sola `quality_reason` y el orden de las reglas (`quality_rules.py`, `add_quality_reason`)

‹Confirmar con el código de `quality_rules.py`.› La razón se asigna con una expresión condicional evaluada en orden (`CASE WHEN … WHEN …` / `F.when(...).when(...)`), y **la primera condición que se cumple gana**. Si un registro viola varias reglas (por ejemplo, importe inválido y cliente inexistente), solo se registra la primera, y las demás quedan ocultas.

El orden importa por tres razones:

1. Define qué se informa, y por lo tanto el conteo por motivo de la pregunta 3.
2. Conviene evaluar primero los problemas estructurales (ID nulo o no numérico, tipos inválidos) y después los referenciales (cliente o producto inexistente), que tienen sentido solo si el dato es interpretable.
3. La clave del `MERGE` de cuarentena incluye `quality_reason`. Si se cambia el orden de las reglas, el mismo registro podría reinsertarse con otro motivo y quedar duplicado en cuarentena.

### 16. `_record_key` y `row_number` (`02_build_silver`, celda de tipado y deduplicación)

```python
record_key = coalesce(transaction_id_typed::string,
                      sha2(concat_ws("||", coalesce(col, "<NULL>") for col in raw_columns), 256))
```

- Si `transaction_id` se convierte bien a número, la clave es el ID. Así todas las versiones de la misma transacción comparten partición, y `row_number()` ordenado por `updated_at_typed DESC NULLS LAST, source_batch_id DESC` deja con `_rn = 1` solo la versión más reciente.
- Si el ID es nulo o no numérico (por ejemplo `'abc'`), `try_cast` da `NULL`. Sin el hash, todos esos registros caerían en una única partición `NULL` y `row_number` conservaría solo uno: los demás desaparecerían sin llegar ni a Silver ni a cuarentena, y se rompería la reconciliación. El hash de todas las columnas crudas le da a cada registro inválido distinto su propia clave, así cada uno sigue su camino hacia la cuarentena.
- El `coalesce(..., "<NULL>")` es necesario porque `concat_ws` saltea los nulos. Sin él, filas como `('a', NULL, 'b')` y `('a', 'b', NULL)` producirían el mismo string y el mismo hash.

### 17. Cláusulas del `MERGE` de `silver_transactions` (`02_build_silver`, celda del `MERGE`)

```sql
MERGE INTO silver_transactions t USING _valid_transactions s ON t.transaction_id = s.transaction_id
WHEN MATCHED AND s.updated_at > t.updated_at THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
```

- **UPDATE:** el ID ya existe en Silver y la versión entrante es estrictamente más nueva. Es el caso de la corrección de la 42.
- **INSERT:** el ID no existe en Silver, es decir, una transacción nueva.
- **Nada:** el ID existe con el mismo `updated_at` (o uno posterior). Esto es lo que pasa en una reejecución, y es lo que hace idempotente al `MERGE`: no reescribe filas iguales ni acepta versiones viejas.

### 18. Gold reconstruido vs. Silver con `MERGE`

| | Ventaja | Limitación |
|---|---|---|
| **Gold, `CREATE OR REPLACE`** (`03_build_gold`) | Simple y determinista: siempre es una función exacta de Silver. Las correcciones históricas (la 42 cambia el monto de un día pasado) se reflejan solas, sin calcular qué agregados tocar. | Recalcula todo en cada corrida, con un costo que crece con el volumen histórico aunque haya llegado un solo archivo. |
| **Silver, `MERGE`** (`02_build_silver`) | Aplica inserciones y correcciones fila a fila sin reescribir la tabla y conserva un historial Delta interpretable (UPDATE e INSERT por versión). | Lógica más delicada: si la clave, la condición o el orden de versiones están mal, se duplican o pierden registros. Además, el `MERGE` tiene su propio costo de join. En esta práctica, Silver relee todo `bronze_transactions_all` en cada corrida; en producción convendría leer solo lo nuevo. |

### 19. ¿Por qué `expected_batch_id` no detecta el archivo?

El descubrimiento lo hace **`COPY INTO` en la tarea `ingest_bronze`** (`01_ingest_bronze_incremental`). Mira el directorio y carga cualquier archivo que no haya visto, sin necesitar que nadie le diga cuál es. Así funciona un pipeline real: los archivos llegan desde sistemas externos sin aviso.

`expected_batch_id` solo se usa en **`validate`** (`04_validate_pipeline`), como expectativa de prueba: qué lote debe haber llegado a Bronze, Silver, cuarentena y Gold, y si la corrección de la 42 vino de ese lote. Los otros notebooks declaran el widget, pero no lo usan para procesar.

### 20. Si falla `build_silver`

Por las dependencias del DAG, `build_gold` y `validate` no se ejecutan: quedan como *Upstream failed* / omitidas, y la corrida del Job termina en estado fallido. Así:

- Gold no se reconstruye sobre un Silver incompleto y sigue mostrando la versión de la última corrida exitosa.
- No se registra una fila en `pipeline_run_audit` con métricas inconsistentes.

Además, cada escritura Delta es atómica: un `MERGE` que falla a mitad no deja la tabla a medio escribir. Después de corregir el problema se puede usar **Repair run**, que reejecuta solo la tarea fallida y las que dependen de ella.

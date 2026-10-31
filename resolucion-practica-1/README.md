   ```markdown
   # Mi primer proyecto

   Soy Fede y estoy aprendiendo a usar GitHub.

   ## Mi objetivo

   Quiero organizar mis trabajos de Big Data.
   ```markdown
   ## Mi primer avance

   Hoy creé un repositorio y guardé mi primer commit.
   ```
Namespace: workspace.bigdata_federico
Volumen:    /Volumes/workspace/bigdata_federico/landing
Filas:     {'customers': 100, 'products': 30, 'transactions': 1000, 'events': 3000}

+---------+----------------+
|catalog  |schema          |
+---------+----------------+
|workspace|bigdata_federico|
+---------+----------------+

+----------------+-----------+
|database        |volume_name|
+----------------+-----------+
|bigdata_federico|landing    |
+----------------+-----------+

+--------+---------+-----------+
|database|tableName|isTemporary|
+--------+---------+-----------+
+--------+---------+-----------+

Tres observaciones:

CSV no guarda tipos: todo es texto y la inferencia es costosa e inestable. JSON guarda tipos básicos y estructuras anidadas, pero no fechas.
Parquet guarda un esquema físico tipado y es columnar, así que se lee solo lo necesario.
Delta suma sobre Parquet un log transaccional: versiones, historial, ACID, estadísticas y control de esquema.

Las 5 V:

Volumen: 200k eventos y 50k transacciones, que son la parte grande y creciente.
Velocidad: eventos y transacciones con timestamp, que llegan de forma continua.
Variedad: cuatro formatos (CSV, Parquet, JSON anidado) y distintos niveles de estructura.
Veracidad: duplicados, amount no numérico e is_fraud como texto.
Valor: unir clientes, productos, transacciones y comportamiento para detección de fraude y análisis de ventas.

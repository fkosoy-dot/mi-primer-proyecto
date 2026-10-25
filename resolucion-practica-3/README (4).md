TP3
Federico Kosoy
Escala: small
Id: federico

## Preguntas

Las preguntas son cortas: buscan comprobar que entendiste la idea de cada modelo y sus ventajas y desventajas. Cuando piden un dato, copiá el número que te dio el notebook (puede variar un poco según tu escala). Alcanza con una a tres oraciones por respuesta.

### CAP y PACELC (`01_cap_pacelc`)

1. Con la red partida, ¿qué respondió la réplica `C` en modo CP y qué respondió en modo AP? ¿Qué propiedad de CAP sacrifica cada modo?
En modo CP, responde error si no tiene quorum, se sacrifica disponibilidad. En modo AP, nunca da error, pero muestra el valor desactualizado ante partici�n, se sacrifica consistencia.
2. En modo AP, ¿qué saldo quedó en las tres réplicas después de la reparación y qué escritura se perdió?
Despu�s de la reparaci�n, el saldo es 50 para todos. En el paso 5, se pierde la escritura 50 en A y B.
3. Según el gráfico de latencia, ¿cuál es la p99 con `W=1` y con `W=3`? ¿Qué se gana a cambio de esperar más réplicas? (PACELC)
W	p50_ms	p99_ms
1	3.8	9.6
2	6.5	18
3	45	55.6
Se gana consistencia al esperar mas replicas.
4. Con cinco réplicas partidas en `ABC | DE`, ¿qué lado pudo seguir escribiendo en modo CP y por qué?
En CP gana la mayor�a (quorum). Por lo tanto, el lado es ABC.

### Clave-valor (`02_clave_valor`)

5. ¿Cuántas veces más rápido fue el GET en memoria que el GET con Spark? ¿Por qué Redis guarda los datos en memoria?
0.0002 ms vs 578 ms.
6. ¿Por qué para contar los clientes de AR hubo que leer y parsear todos los valores? Mencioná una ventaja y una desventaja del modelo clave-valor.
Es una caracter�stica de spark. Ventaja: es muy r�pido y escala horizontalmente. Desventaja: el valor es opaco para el motor.. las consultas son limitadas.
6. Al pasar de 4 a 5 nodos, ¿qué porcentaje de claves se movió con `hash mod N` y con hashing consistente? ¿Por qué conviene el segundo?
de	a	vnodes	movidas_mod_%	movidas_anillo_%	carga_max_anillo_%
4	5	100	79.6	21.2	21.2

### Documental (`03_documental`)

7. ¿Cuántas filas devolvió la consulta relacional del cliente 42 y cuántos documentos la documental? ¿Qué datos quedaron embebidos dentro del documento?
11 filas en relacional, contra uno en docuemtnal. {"country":"CL","segment":"regular","created_date":"2024-02-12","email":"user_42@example.test"}
8. Al leer documentos con campos distintos, ¿qué hizo Spark con los campos que faltaban en algunos? ¿Por qué se dice que el modelo documental tiene esquema flexible?
Spark asigna el valor null. Porque acepta que cada documento declare su propiaestrucutra.
9. ¿Cuánto pesa el documento más grande? ¿Qué problema aparece si un documento crece sin límite?
5.2 KB. Puede traer complicaciones de limitaci�n f�sica de lmacenamiento y procesamiento deficiente.
11. Para calcular el monto por categoría hubo que usar `explode`. ¿Qué tipo de consultas resuelve bien el modelo documental y cuáles le cuestan más?
El explode es justamente el s�ntoma: el documento estaba modelado para una consulta distinta (traer la compra completa) y hubo que �aplanarlo� para agregar por un atributo de los elementos internos.

### Grafos (`04_grafos`)

12. ¿Cuántos nodos `Customer`, nodos `Device` y aristas `USES` tiene el grafo?
label	nodos	marcados
Device	2361	0
Customer	5000	738
5,400 aristas USES
13. ¿Cuántos joins necesitó SQL para el patrón de 2 saltos y para el de 4? ¿Por qué Neo4j recorre relaciones más eficientemente que una base relacional?
11 y 12joins respectivamente. Porque no depende de los JOINs, recorre la rama determinada y eso lo hace mas eficiente.
14. ¿Cuántas iteraciones tardó en converger la búsqueda de componentes conexos y cuántos nodos tiene el componente más grande?
12 iteraciones. El componente mas grande tiene 23 nodos.
15. ¿Qué porcentaje de aristas quedó entre máquinas distintas al repartir los nodos con `hash(id) mod 4`? ¿Por qué es difícil distribuir una base de grafos?
74.4%. porque cada arista cuyos extremos quedan en m�quinas distintas obliga a un salto por la red.
### Vectorial (`05_vectorial`)

16. ¿Qué representa el vector de cada cliente y qué mide la similitud coseno?
El vector de cada cliente representa su comportamiento. Mide que tan parecidos son los comportamientos normalizados entre clientes.
17. ¿Qué porcentaje de clientes marcados hay entre los vecinos de clientes marcados y cuál es la tasa base? ¿Para qué sirve buscar "vecinos parecidos"?
Marcados entre los vecinos: de clientes marcados 31.6% � de no marcados 13.2% � tasa base 14.8%. Sirve para clasificar y desarrollar estrategias comerciales por ejemplo.
18. En la curva del índice IVF, ¿qué recall y qué porcentaje de vectores escaneados se obtienen con `nprobe=4`? ¿Qué se gana y qué se pierde con la búsqueda aproximada (ANN)?
0.872. se gana velocidad y ecscalabilidad, pero se pierde exactitud.
### Columnar (`06_columnar`)

19. ¿Cuánto ocupan los datos en CSV, JSON y Parquet? ¿Qué columnas leyó Spark para la consulta de `amount` sobre Parquet (`ReadSchema`)? ¿Cuántos archivos se pueden saltear con los datos ordenados?
50, 121 y 5.3respectivamente (MB). Se saltean 7 de 8 archivos.
20. ¿Por qué el formato columnar es bueno para analítica y poco conveniente para modificar una fila por vez?
Es buen formato para anal�tica porque lee solo lo que que requiere para la consulta puntual. No covienepara modificar una fila por vez porque es muy alto el costo de computo de tener quw recorrer todas las columnas para reconstruis una fila.
## Entrega



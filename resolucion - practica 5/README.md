# TP5

**Federico Kosoy**

Federico

small

> Las preguntas son cortas. Cuando piden un dato, copiá el valor que te dieron tus notebooks: como cada uno elige sus experimentos, **los números van a variar entre alumnos**. Alcanza con una a tres oraciones por respuesta.

---

## Datos y tracking (`00_preflight`, `01_primer_run`)

**1. ¿Cuántas filas tiene cada split de `ml_features` y qué porcentaje de contracargos hay en cada uno? ¿Por qué se separa por fecha y no al azar?**

| split  | filas  | % contracargos |
|--------|-------:|---------------:|
| train  | 35654  | 11.05          |
| test   | 7129   | 10.38          |
| nuevas | 7165   | 11.05          |

Separa por fecha porque cada rango de fechas tiene una función diferente en el pipeline.

**2. ¿Qué accuracy obtiene un "modelo" que siempre dice que no hay contracargo? ¿Por qué la práctica usa el PR-AUC como métrica principal?**

Diciendo siempre "NO", accuracy da 89%. Se usa PR-AUC porque resume de más a menos riesgosas las transacciones.

**3. ¿Qué quedó registrado en el run `01_manual_logistica` como parámetros, métricas y artefactos? ¿Qué diferencia hay entre un experimento y un run?**

Un run es un caso particular de un experimento.

**4. ¿Cuántos parámetros registró autolog y qué métricas? ¿Qué no registra autolog que sí registramos a mano?**

Registró 46 parámetros. Métricas:

```python
{'training_accuracy_score': 0.91, 'training_f1_score': 0.887, 'training_log_loss': 0.229,
 'training_precision_score': 0.901, 'training_recall_score': 0.91, 'training_roc_auc': 0.899,
 'training_score': 0.91}
```

El registro manual sirve para registrar lo propio del problema, autolog registra todo.

**5. ¿Dieron las mismas métricas `01_repro_a` y `01_repro_b`? Nombrá las cuatro cosas que hay que fijar para que un run sea reproducible.**

Dieron las mismas métricas. Datos, código, semilla, entorno.

**6. ¿Qué pasó al llamar al modelo sin la columna `amount`? ¿Para qué sirve la firma (*signature*) del modelo?**

La firma (signature) declara qué columnas y tipos espera el modelo y qué devuelve. Si alguien le pasa datos que no cumplen el contrato, MLflow lo frena antes de predecir cualquier cosa:

---

## Tus experimentos (`02_mis_experimentos`)

**7. ¿Cuál fue tu mejor run (modelo, variables, hiperparámetros y PR-AUC)? ¿Cuánto mejoró respecto de usar sólo `rule_alert` (`solo_regla`)?**

**8. Con el mismo modelo, ¿cuánto cambió el PR-AUC al pasar de `basicas` a `cliente` y a `completas`? ¿Qué variables resultaron más importantes en tu mejor run?**

**9. Con `completas`, ¿qué modelo anduvo mejor: logística, bosque o boosting? ¿Por qué un modelo de árboles puede aprovechar combinaciones de variables (por ejemplo, de noche *y* por transferencia) que una logística no ve?**

**10. ¿Qué cambió en precision, recall y cantidad de alertas al usar `class_weight = balanced`? ¿Cambió mucho el PR-AUC?**

**11. ¿Qué pasó al bajar el umbral? ¿Por qué el PR-AUC no depende del umbral y el F1 sí?**

**12. ¿Qué hiperparámetro barriste y con qué valor obtuviste el mejor PR-AUC de test? ¿Hubo valores con `train_pr_auc` mucho más alto que el de test? ¿Cómo se llama ese fenómeno?**

### Resultados de runs

Accuracy y AUC mejoran al pasar a random forest.

| run | modelo | features | class_weight | umbral | C | n_estimators | max_depth | learning_rate | train_pr_auc | pr_auc | roc_auc | accuracy | precision | recall | f1 | notebook |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 01_repro_b | random_forest | cliente | ninguno | 0.5 | null | 100 | 8 | null | 0.594 | 0.51 | 0.869 | 0.909 | 0.722 | 0.207 | 0.321 | 1 |
| 01_repro_a | random_forest | cliente | ninguno | 0.5 | null | 100 | 8 | null | 0.594 | 0.51 | 0.869 | 0.909 | 0.722 | 0.207 | 0.321 | 1 |
| logistic_regression-basicas-u0.5 | logistic_regression | basicas | ninguno | 0.5 | 0.1 | null | null | null | 0.341 | 0.339 | 0.794 | 0.897 | 0.527 | 0.039 | 0.073 | 2 |
| 01_manual_logistica | logistic_regression | basicas | ninguno | 0.5 | 1 | null | null | null | 0.341 | 0.339 | 0.794 | 0.896 | 0.493 | 0.045 | 0.082 | 1 |
| logistic_regression-basicas-u0.4 | logistic_regression | basicas | balanced | 0.4 | 0.1 | null | null | null | 0.34 | 0.338 | 0.793 | 0.615 | 0.19 | 0.828 | 0.309 | 2 |
| logistic_regression-basicas-u0.4 | logistic_regression | basicas | balanced | 0.4 | 0.1 | null | null | null | 0.34 | 0.338 | 0.793 | 0.615 | 0.19 | 0.828 | 0.309 | 2 |
| logistic_regression-basicas-u0.5 | logistic_regression | basicas | balanced | 0.5 | 0.1 | null | null | null | 0.34 | 0.338 | 0.793 | 0.706 | 0.226 | 0.754 | 0.347 | 2 |

### Barrido de HP `max_depth`

Controlar max_depth optimiza accuracy y AUC.

| max_depth | test_pr_auc | test_roc_auc | test_accuracy | test_precision | test_recall | test_f1 | test_alertas | train_pr_auc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 0.324 | 0.806 | 0.703 | 0.227 | 0.777 | 0.352 | 2528 | 0.341 |
| 5 | 0.339 | 0.806 | 0.67 | 0.212 | 0.804 | 0.336 | 2801 | 0.368 |
| 8 | 0.324 | 0.804 | 0.699 | 0.224 | 0.774 | 0.348 | 2554 | 0.432 |
| sin_limite | 0.21 | 0.708 | 0.841 | 0.251 | 0.266 | 0.258 | 785 | 0.989 |

---

## Comparar y elegir (`03_comparar_y_elegir`)

**13. ¿Coincidieron tu mejor run por PR-AUC y tu mejor run por accuracy? Explicá por qué pueden no coincidir.**

Sí, coincidieron. Pueden no coincidir si se evita la acción de no alertar.

**14. En el gráfico de PR-AUC de train contra test, ¿qué runs quedan más lejos de la diagonal y qué indica eso?**

Los runs que quedan lejos son los que tienen overfitting, no aciertan porque aprenden a predecir mal, de memoria.

**15. ¿Qué ventaja tiene consultar los runs con `mlflow.search_runs` en lugar de mirarlos en la interfaz? Escribí el `filter_string` que usarías para traer sólo tus bosques con PR-AUC de test mayor a 0,55.**

Te devuelve los runs como un `pandas.DataFrame`, así que la consulta es reproducible y programable. La interfaz sirve para explorar a ojo; `search_runs` sirve para decidir con código.

```python
runs = mlflow.search_runs(
    experiment_names=["mi_experimento"],
    filter_string="params.model_type = 'random_forest' AND metrics.test_pr_auc > 0.55",
    order_by=["metrics.test_pr_auc DESC"],
)
```

**16. En fraude, ¿qué cuesta más, una alerta falsa o un contracargo no detectado? Si el equipo de riesgo sólo puede revisar una cantidad fija de alertas por día, ¿cómo usarías el umbral?**

- **Contracargo no detectado:** perdés el monto de la transacción, más el fee del contracargo, más el costo operativo de la disputa. Si la tasa de contracargos sube, también podés caer en programas de monitoreo de Visa o Mastercard, con multas.
- **Alerta falsa:** cuesta minutos de un analista y algo de fricción con un cliente legítimo, por ejemplo una compra demorada o rechazada.

---

## Registro, uso y monitoreo (`04_registro_y_uso`)

**17. ¿Se pudo registrar el modelo en Unity Catalog? Indicá nombre, versión y alias (o el error, si falló). ¿Qué ventaja tiene cargar `models:/...@champion` en lugar de `runs:/<run_id>/model`?**

✅ Registrado: `workspace.bigdata_federico.fraud_model` versión 1 con alias `champion`.

**18. ¿Cuántas transacciones nuevas se puntuaron y cuántas generaron alerta? ¿Qué columnas de `ml_predictions` permiten auditar cada decisión? ¿Por qué el umbral se guarda fuera del modelo?**

Transacciones puntuadas: 7,165 · alertas: 220 (3.1%)

**19. Cuando llegaron los contracargos, ¿el PR-AUC sobre `nuevas` fue parecido al de test? En la campaña simulada, ¿qué pasó con el porcentaje de alertas? ¿Qué es el drift y por qué se puede detectar antes de tener las etiquetas?**

| métrica | test (al entrenar) | nuevas (producción) |
|---|---:|---:|
| pr_auc | 0.51 | 0.509 |
| roc_auc | 0.869 | 0.868 |
| precision | 0.722 | 0.705 |
| recall | 0.207 | 0.196 |
| f1 | 0.321 | 0.306 |
| accuracy | 0.909 | 0.902 |
| alertas | 212 | 220 |

---

## Cierre

**20. Ubicá lo que hiciste en el ciclo de vida de MLOps (datos, entrenamiento, tracking, registro, despliegue, monitoreo). ¿Qué faltaría para tener este modelo en producción real? Nombrá al menos dos cosas.**

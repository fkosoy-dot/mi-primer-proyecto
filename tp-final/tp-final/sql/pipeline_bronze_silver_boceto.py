"""Boceto de Lakeflow Declarative Pipeline (ex Delta Live Tables) para cotizaciones.

Muestra cómo se implementarían la ingesta en Bronze y los controles de calidad en Silver.
Es ilustrativo: no se ejecutó (la Variante 1 no exige implementar la plataforma).
"""
import dlt
from pyspark.sql import functions as F

KAFKA_SERVERS = spark.conf.get("comparador.kafka_servers")  # se configura en el pipeline, sin credenciales en el código


# ---------- Bronze: tal cual llega, append-only ----------
@dlt.table(name="bronze_cotizaciones", comment="Mensajes crudos del topic 'cotizaciones'.")
def bronze_cotizaciones():
    return (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_SERVERS)
        .option("subscribe", "cotizaciones")
        .option("startingOffsets", "earliest")
        .load()
        .select(
            F.col("value").cast("string").alias("payload_json"),
            F.col("timestamp").alias("_kafka_ts"),
            F.col("partition").alias("_kafka_partition"),
            F.col("offset").alias("_kafka_offset"),
            F.current_timestamp().alias("_ingested_at"),
        )
    )


ESQUEMA = """
  cotizacion_id STRING, busqueda_id STRING, proveedor STRING, categoria_codigo STRING,
  origen_lat DOUBLE, origen_lon DOUBLE, destino_lat DOUBLE, destino_lon DOUBLE,
  ts_cotizacion TIMESTAMP, fuente STRING, moneda STRING,
  precio DOUBLE, precio_min DOUBLE, precio_max DOUBLE,
  eta_seg INT, duracion_seg INT, distancia DOUBLE, unidad_distancia STRING,
  multiplicador_dinamico DOUBLE
"""


# ---------- Silver: limpio, tipado, deduplicado ----------
@dlt.table(name="silver_cotizaciones", comment="Una fila por cotización válida y única.")
@dlt.expect_or_drop("precio_positivo", "precio_ars > 0")
@dlt.expect_or_drop("moneda_ars", "moneda = 'ARS'")
@dlt.expect_or_drop("proveedor_valido", "proveedor IN ('Uber', 'DiDi', 'Cabify')")
@dlt.expect_or_drop("coordenadas_en_amba", "en_amba")
@dlt.expect("eta_razonable", "eta_min BETWEEN 0 AND 60")                          # se registra, no se descarta
@dlt.expect("precio_km_plausible", "precio_por_km_ars IS NULL OR precio_por_km_ars < 20000")
def silver_cotizaciones():
    df = (
        dlt.read_stream("bronze_cotizaciones")
        .select(F.from_json("payload_json", ESQUEMA).alias("c"), "_ingested_at")
        .select("c.*", "_ingested_at")
        .withWatermark("ts_cotizacion", "10 minutes")
        .dropDuplicatesWithinWatermark(["cotizacion_id"])
    )
    # La API de Uber informa la distancia en millas: se normaliza a km.
    distancia_km = F.when(F.col("unidad_distancia") == "mi", F.col("distancia") * 1.609344).otherwise(F.col("distancia"))
    precio_ars = F.coalesce(F.col("precio"), (F.col("precio_min") + F.col("precio_max")) / 2)
    return (
        df.withColumn("distancia_km", F.round(distancia_km, 2))
        .withColumn("precio_ars", F.round(precio_ars, 2))
        .withColumn("precio_por_km_ars", F.round(F.col("precio_ars") / F.col("distancia_km"), 2))
        .withColumn("es_precio_cerrado", F.col("precio").isNotNull())
        .withColumn("en_amba", F.col("origen_lat").between(-35.3, -34.2) & F.col("origen_lon").between(-59.3, -57.8))
        .withColumn("eta_min", (F.col("eta_seg") / 60).cast("int"))
        .withColumn("duracion_estimada_min", (F.col("duracion_seg") / 60).cast("int"))
        # Las coordenadas exactas se reemplazan por celdas H3 (privacidad): resolución 9 en Silver, 8 en Gold.
        .withColumn("h3_origen_r9", F.expr("h3_longlatash3string(origen_lon, origen_lat, 9)"))
        .withColumn("h3_destino_r9", F.expr("h3_longlatash3string(destino_lon, destino_lat, 9)"))
        .drop("origen_lat", "origen_lon", "destino_lat", "destino_lon", "precio", "eta_seg", "duracion_seg",
              "distancia", "unidad_distancia")
    )

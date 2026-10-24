-- Modelo de datos Gold (Databricks SQL, tablas Delta en Unity Catalog)
-- Catálogo: comparador · Esquema: gold
-- Es una propuesta de diseño: no se ejecutó sobre una plataforma real.
-- Convención: *_key = clave sustituta entera; *_id = identificador de negocio (UUID).

CREATE SCHEMA IF NOT EXISTS comparador.gold;

-- ---------- Dimensiones ----------

CREATE TABLE IF NOT EXISTS comparador.gold.dim_proveedor (
  proveedor_key            INT     NOT NULL,   -- PK
  nombre                   STRING  NOT NULL,   -- Uber, DiDi, Cabify
  tipo_integracion         STRING  NOT NULL,   -- api, partner, crowd
  comision_derivacion_pct  DECIMAL(5,2),       -- % acordado por viaje derivado (supuesto comercial)
  CONSTRAINT pk_dim_proveedor PRIMARY KEY (proveedor_key)
);

-- SCD tipo 2: las apps renombran o redefinen categorías; se guarda cada versión.
CREATE TABLE IF NOT EXISTS comparador.gold.dim_categoria (
  categoria_key        INT     NOT NULL,       -- PK (una por versión)
  proveedor_key        INT     NOT NULL,       -- FK dim_proveedor
  categoria_codigo     STRING  NOT NULL,       -- id estable del proveedor (ej. product_id de Uber)
  nombre_comercial     STRING  NOT NULL,       -- UberX, DiDi Express, Cabify Lite
  segmento_homologado  STRING  NOT NULL,       -- Economico, Confort, Taxi, Premium
  capacidad            INT,
  valido_desde         DATE    NOT NULL,
  valido_hasta         DATE,                   -- NULL = versión vigente
  CONSTRAINT pk_dim_categoria PRIMARY KEY (categoria_key),
  CONSTRAINT fk_cat_prov FOREIGN KEY (proveedor_key) REFERENCES comparador.gold.dim_proveedor
);

CREATE TABLE IF NOT EXISTS comparador.gold.dim_zona (
  zona_key          INT     NOT NULL,          -- PK
  h3_index          STRING  NOT NULL,          -- celda H3 resolución 8 (~0,7 km²)
  barrio            STRING,                    -- CABA; NULL fuera de CABA
  comuna_o_partido  STRING  NOT NULL,
  es_aeropuerto     BOOLEAN NOT NULL,
  lat_centroide     DECIMAL(9,6),
  lon_centroide     DECIMAL(9,6),
  CONSTRAINT pk_dim_zona PRIMARY KEY (zona_key)
);

CREATE TABLE IF NOT EXISTS comparador.gold.dim_fecha (
  fecha_key            INT     NOT NULL,       -- PK, formato AAAAMMDD
  fecha                DATE    NOT NULL,
  dia_semana           STRING  NOT NULL,
  es_feriado           BOOLEAN NOT NULL,
  hay_paro_transporte  BOOLEAN NOT NULL,
  CONSTRAINT pk_dim_fecha PRIMARY KEY (fecha_key)
);

CREATE TABLE IF NOT EXISTS comparador.gold.dim_tiempo (
  minuto_key  INT     NOT NULL,                -- PK, 0..1439 (minuto del día)
  hora        INT     NOT NULL,
  franja      STRING  NOT NULL,                -- madrugada, pico_manana, valle, pico_tarde, noche
  CONSTRAINT pk_dim_tiempo PRIMARY KEY (minuto_key)
);

CREATE TABLE IF NOT EXISTS comparador.gold.dim_clima (
  clima_key      INT       NOT NULL,           -- PK, una fila por hora (AMBA)
  hora           TIMESTAMP NOT NULL,
  lluvia_mm      DECIMAL(5,1),
  temperatura_c  DECIMAL(4,1),
  alerta_smn     BOOLEAN,
  CONSTRAINT pk_dim_clima PRIMARY KEY (clima_key)
);

CREATE TABLE IF NOT EXISTS comparador.gold.dim_evento (
  evento_key           INT       NOT NULL,     -- PK
  tipo                 STRING    NOT NULL,     -- partido, recital, paro, corte
  zona_key             INT       NOT NULL,     -- FK dim_zona (sede)
  inicio               TIMESTAMP NOT NULL,
  fin                  TIMESTAMP NOT NULL,
  asistencia_estimada  INT,
  CONSTRAINT pk_dim_evento PRIMARY KEY (evento_key),
  CONSTRAINT fk_evento_zona FOREIGN KEY (zona_key) REFERENCES comparador.gold.dim_zona
);

-- Sin datos personales: usuario_key es un hash con sal del id interno.
CREATE TABLE IF NOT EXISTS comparador.gold.dim_usuario (
  usuario_key             STRING NOT NULL,     -- PK
  fecha_alta              DATE   NOT NULL,
  app_habitual_declarada  STRING,              -- la app que el usuario dice usar normalmente
  segmento                STRING,
  CONSTRAINT pk_dim_usuario PRIMARY KEY (usuario_key)
);

-- ---------- Hechos ----------

-- Grano: una búsqueda de un usuario (origen, destino, momento).
CREATE TABLE IF NOT EXISTS comparador.gold.fact_busqueda (
  busqueda_id             STRING    NOT NULL,  -- PK
  usuario_key             STRING    NOT NULL,  -- FK dim_usuario
  zona_origen_key         INT       NOT NULL,  -- FK dim_zona
  zona_destino_key        INT       NOT NULL,  -- FK dim_zona
  fecha_key               INT       NOT NULL,  -- FK dim_fecha
  ts_busqueda             TIMESTAMP NOT NULL,
  n_cotizaciones          INT       NOT NULL,
  n_proveedores           INT       NOT NULL,
  precio_min_ars          DECIMAL(12,2),
  precio_max_ars          DECIMAL(12,2),
  dispersion_pct          DECIMAL(6,2),        -- (max / min - 1) * 100, mismo segmento
  categoria_elegida_key   INT,                 -- FK dim_categoria; NULL si no eligió
  convirtio               BOOLEAN   NOT NULL,  -- abrió el deep link de alguna app
  ahorro_vs_habitual_ars  DECIMAL(12,2),       -- precio app habitual - precio elegido
  latencia_ms             INT       NOT NULL,
  CONSTRAINT pk_fact_busqueda PRIMARY KEY (busqueda_id)
)
PARTITIONED BY (fecha_key);

-- Grano: una cotización de un proveedor, para una categoría, en un instante.
CREATE TABLE IF NOT EXISTS comparador.gold.fact_cotizacion (
  cotizacion_id           STRING    NOT NULL,  -- PK
  busqueda_id             STRING,              -- FK fact_busqueda; NULL si viene del panel de muestreo
  proveedor_key           INT       NOT NULL,  -- FK dim_proveedor
  categoria_key           INT       NOT NULL,  -- FK dim_categoria (versión vigente al momento)
  zona_origen_key         INT       NOT NULL,  -- FK dim_zona
  zona_destino_key        INT       NOT NULL,  -- FK dim_zona
  fecha_key               INT       NOT NULL,  -- FK dim_fecha
  minuto_key              INT       NOT NULL,  -- FK dim_tiempo
  clima_key               INT,                 -- FK dim_clima
  evento_key              INT,                 -- FK dim_evento; NULL si no hay evento cercano
  ts_cotizacion           TIMESTAMP NOT NULL,  -- event time
  ts_ingesta              TIMESTAMP NOT NULL,
  fuente                  STRING    NOT NULL,  -- api, partner, crowd, panel
  precio_ars              DECIMAL(12,2) NOT NULL,  -- precio cerrado o punto medio del rango
  precio_min_ars          DECIMAL(12,2),
  precio_max_ars          DECIMAL(12,2),
  precio_por_km_ars       DECIMAL(10,2),
  eta_min                 INT,
  duracion_estimada_min   INT,
  distancia_km            DECIMAL(6,2),
  multiplicador_dinamico  DECIMAL(4,2),        -- NULL si el proveedor no lo informa
  es_precio_cerrado       BOOLEAN   NOT NULL,
  CONSTRAINT pk_fact_cotizacion PRIMARY KEY (cotizacion_id)
)
PARTITIONED BY (fecha_key)
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
-- Además: Z-ORDER / liquid clustering por (zona_origen_key, zona_destino_key, proveedor_key).

-- ---------- Agregado Gold para el índice de precios ----------

-- Grano: ventana de 5 minutos × par de zonas × segmento × proveedor.
CREATE TABLE IF NOT EXISTS comparador.gold.agg_indice_precio_5min (
  ventana_inicio       TIMESTAMP NOT NULL,
  zona_origen_key      INT       NOT NULL,
  zona_destino_key     INT       NOT NULL,
  segmento_homologado  STRING    NOT NULL,
  proveedor_key        INT       NOT NULL,
  n_cotizaciones       INT       NOT NULL,
  precio_mediano_ars   DECIMAL(12,2),
  precio_p25_ars       DECIMAL(12,2),
  precio_p75_ars       DECIMAL(12,2),
  precio_km_mediano    DECIMAL(10,2),
  fue_mas_barato       BOOLEAN              -- mediana más baja del segmento en esa ventana
)
PARTITIONED BY (DATE(ventana_inicio));

-- ---------- Ejemplos de preguntas de negocio ----------

-- P1. ¿Qué app fue más barata en el segmento económico por franja horaria, último mes?
SELECT t.franja, p.nombre AS proveedor,
       AVG(CASE WHEN a.fue_mas_barato THEN 1 ELSE 0 END) AS pct_ventanas_mas_barata
FROM comparador.gold.agg_indice_precio_5min a
JOIN comparador.gold.dim_proveedor p ON a.proveedor_key = p.proveedor_key
JOIN comparador.gold.dim_tiempo t
  ON t.minuto_key = HOUR(a.ventana_inicio) * 60 + MINUTE(a.ventana_inicio)
WHERE a.segmento_homologado = 'Economico'
  AND a.ventana_inicio >= current_date() - INTERVAL 30 DAYS
GROUP BY t.franja, p.nombre
ORDER BY t.franja, pct_ventanas_mas_barata DESC;

-- P2. ¿Cuánto ahorraron los usuarios que eligieron a través del comparador? (KPI principal)
SELECT f.fecha, COUNT(*) AS busquedas,
       AVG(CAST(b.convirtio AS INT))            AS tasa_conversion,
       PERCENTILE(b.ahorro_vs_habitual_ars, 0.5) AS ahorro_mediano_ars
FROM comparador.gold.fact_busqueda b
JOIN comparador.gold.dim_fecha f ON b.fecha_key = f.fecha_key
WHERE b.convirtio
GROUP BY f.fecha
ORDER BY f.fecha;

-- P3. ¿Cuánto sube el precio con lluvia, por proveedor? (insumo del modelo de ML)
SELECT p.nombre, (c.lluvia_mm > 0) AS llueve,
       PERCENTILE(q.precio_por_km_ars, 0.5) AS precio_km_mediano
FROM comparador.gold.fact_cotizacion q
JOIN comparador.gold.dim_proveedor p ON q.proveedor_key = p.proveedor_key
JOIN comparador.gold.dim_clima c ON q.clima_key = c.clima_key
GROUP BY p.nombre, (c.lluvia_mm > 0);

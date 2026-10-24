# TP Final — Big Data y MLOps (2026)

**Estudiante:** Federico Kosoy
**Variante elegida:** 1 — Investigación: caso de negocio y arquitectura de datos, con la extensión opcional de MLOps.

## Objetivo

Proponer un caso de negocio en el que Big Data aporta valor: **RutaJusta**, una app hipotética que compara en tiempo real las tarifas de Uber, DiDi y Cabify para un mismo viaje en el AMBA. El trabajo incluye:

- la necesidad de negocio y los KPIs;
- las fuentes de datos;
- una arquitectura lakehouse en Databricks;
- el modelo de datos dimensional y la justificación de las decisiones;
- un caso de MLOps que predice si conviene pedir ahora o esperar unos minutos.

Es una propuesta fundamentada: no implementa la plataforma, como indica la consigna de la Variante 1.

## Contenido de la carpeta

| Ruta | Qué es |
| --- | --- |
| `docs/TP_Final_Comparador_Movilidad.md` | **Documento principal del TP** (secciones 1 a 7 de la consigna) |
| `docs/TP_Final_Comparador_Movilidad.pdf` | El mismo documento en PDF |
| `diagramas/arquitectura.svg` / `.png` | Diagrama de arquitectura (Figura 5) |
| `diagramas/modelo_estrella.svg` / `.png` | Diagrama del modelo de datos en estrella (Figura 6) |
| `diagramas/generar_modelo_estrella.py` | Script que genera el diagrama en estrella |
| `diagramas/modelo_datos_completo.mmd` / `.png` | Diagrama entidad-relación completo, con tipos (Mermaid) |
| `diagramas/mlops.mmd` / `.png` | Flujo de entrenamiento, despliegue y monitoreo (Figura 7, Mermaid) |
| `graficos/*.png` | Gráficos del problema, los datos y el volumen (Figuras 1 a 4) |
| `graficos/generar_graficos.py` | Script que genera los gráficos a partir de `datos/` |
| `datos/precios_observados_2024.csv` | Precios publicados por iProfesional (2024), con la fuente |
| `datos/precios_observados_2021.csv` | Precios publicados por iProUP (2021), con la fuente |
| `datos/usuarios_activos_2026.csv` | Usuarios activos por app (estimación de terceros, 2026) |
| `datos/supuestos_volumen.csv` | Supuestos propios para estimar el volumen de datos |
| `sql/modelo_gold.sql` | DDL de las tablas Gold (Delta / Unity Catalog) y consultas de ejemplo para las preguntas de negocio |
| `sql/pipeline_bronze_silver_boceto.py` | Boceto del pipeline Bronze → Silver con controles de calidad (ilustrativo, no ejecutado) |

## Cómo revisar el trabajo

1. Leer `docs/TP_Final_Comparador_Movilidad.md`. GitHub muestra las imágenes en el mismo documento. Si no, usar el PDF.
2. Cada número del documento está etiquetado:
    - **[OBSERVADO]**: dato publicado por una fuente;
    - **[ESTIMACIÓN DE TERCEROS]**: cifra publicada que la propia fuente presenta como estimación;
    - **[SUPUESTO]**: valor propio, no observado.

## Cómo reproducir los gráficos y diagramas

Desde la carpeta `tp-final/`:

```bash
pip install pandas matplotlib
python graficos/generar_graficos.py             # regenera graficos/*.png e imprime los valores calculados
python diagramas/generar_modelo_estrella.py     # regenera diagramas/modelo_estrella.svg

# Diagramas Mermaid (opcional, requiere Node):
npx -p @mermaid-js/mermaid-cli mmdc -i diagramas/mlops.mmd -o diagramas/mlops.png -w 2000 -b white
npx -p @mermaid-js/mermaid-cli mmdc -i diagramas/modelo_datos_completo.mmd -o diagramas/modelo_datos_completo.png -w 2000 -b white
```

Los SVG (`arquitectura.svg`, `modelo_estrella.svg`) se abren en cualquier navegador.

## Fuentes de datos

- iProfesional (07/09/2026; 19/08/2024; 04/09/2026), iProUP (05/02/2021), Infobae (08/05/2026) y la documentación de Uber Developers. Los links completos están en la sección Referencias del documento.
- No se usan credenciales ni datos personales. Los datos observados provienen de notas periodísticas públicas.

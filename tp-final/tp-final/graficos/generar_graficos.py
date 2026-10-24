"""Genera los gráficos del TP a partir de los CSV de la carpeta datos/.

Uso (desde tp-final/):
    pip install pandas matplotlib
    python graficos/generar_graficos.py

Cada gráfico indica en el subtítulo si los valores son OBSERVADOS (fuente publicada)
o ESTIMADOS (supuestos propios, ver datos/supuestos_volumen.csv).
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager

BASE = Path(__file__).resolve().parent.parent
DATOS = BASE / "datos"
SALIDA = BASE / "graficos"

# Paleta (rol -> color). Una sola serie por gráfico: azul de dato + tinta neutra.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SERIE = "#2a78d6"
SERIE_SUAVE = "#a9c8ef"

for nombre in ("Inter", "DejaVu Sans"):
    if any(nombre in f.name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = nombre
        break
plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK_2,
    "xtick.color": INK_2,
    "ytick.color": INK,
    "font.size": 11,
})


def base_ejes(ax):
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=0)


def titulos(fig, titulo, subtitulo):
    fig.text(0.02, 0.965, titulo, fontsize=14, fontweight="bold", color=INK, va="top")
    fig.text(0.02, 0.905, subtitulo, fontsize=10, color=INK_2, va="top")


def miles(x):
    return f"{x:,.0f}".replace(",", ".")


# 1. Brecha de precio para el mismo viaje (observado, 2024)
def grafico_brecha_2024():
    df = pd.read_csv(DATOS / "precios_observados_2024.csv")
    df["min"] = df[["precio_a_ars", "precio_b_ars"]].min(axis=1)
    df["max"] = df[["precio_a_ars", "precio_b_ars"]].max(axis=1)
    df["brecha_pct"] = (df["max"] / df["min"] - 1) * 100
    df["barata"] = df.apply(lambda r: r.app_a if r.precio_a_ars <= r.precio_b_ars else r.app_b, axis=1)
    df["cara"] = df.apply(lambda r: r.app_b if r.precio_a_ars <= r.precio_b_ars else r.app_a, axis=1)
    df = df.sort_values("brecha_pct")

    fig, ax = plt.subplots(figsize=(9, 4.8))
    fig.subplots_adjust(left=0.24, right=0.80, top=0.80, bottom=0.12)
    ax.barh(df["destino"], df["brecha_pct"], color=SERIE, height=0.6)
    for y, r in enumerate(df.itertuples()):
        ax.text(r.brecha_pct + 1, y, f"{r.brecha_pct:.0f}%", va="center", color=INK, fontsize=10.5, fontweight="bold")
        ax.text(r.brecha_pct + 8, y, f"{r.barata} {miles(r.min)} vs {r.cara} {miles(r.max)}",
                va="center", color=INK_2, fontsize=9)
    ax.set_xlim(0, 70)
    ax.set_xlabel("Cuánto más cobra la app más cara que la más barata (%)")
    base_ejes(ax)
    titulos(fig, "El mismo viaje puede costar hasta 58% más según la app",
            "OBSERVADO · Desde el Obelisco, mediodía de día hábil, precios en ARS. "
            "Fuente: iProfesional, 19/08/2024.\nLa app más barata cambia según el destino.")
    fig.savefig(SALIDA / "01_brecha_precios_2024.png", dpi=200)
    plt.close(fig)
    return df


# 2. Un mismo viaje, seis precios (observado, 2021)
def grafico_mismo_viaje_2021():
    df = pd.read_csv(DATOS / "precios_observados_2021.csv").sort_values("precio_ars")
    etiquetas = [f"{a} · {s}" for a, s in zip(df.app, df.servicio)]
    colores = [SERIE if seg == "Economico" else SERIE_SUAVE for seg in df.segmento]

    fig, ax = plt.subplots(figsize=(9, 4.4))
    fig.subplots_adjust(left=0.26, right=0.95, top=0.78, bottom=0.13)
    ax.barh(etiquetas, df["precio_ars"], color=colores, height=0.6)
    for y, v in enumerate(df["precio_ars"]):
        ax.text(v + 12, y, f"${miles(v)}", va="center", color=INK, fontsize=10.5)
    ax.set_xlim(0, 1100)
    ax.set_xlabel("Precio cotizado (ARS de feb-2021)")
    base_ejes(ax)
    eco = df[df.segmento == "Economico"].precio_ars
    titulos(fig, f"En el segmento económico, UberX costaba {eco.max() / eco.min():.1f} veces lo que DiDi Express".replace(".", ","),
            "OBSERVADO · Cabildo y Juramento → Casa Rosada, mismo día y hora. Fuente: iProUP, 05/02/2021.\n"
            "Azul: segmento económico. Celeste: taxi y premium.")
    fig.savefig(SALIDA / "02_mismo_viaje_2021.png", dpi=200)
    plt.close(fig)


# 3. Tamaño del mercado (estimación de terceros, 2026)
def grafico_usuarios():
    df = pd.read_csv(DATOS / "usuarios_activos_2026.csv")
    df["medio"] = (df.usuarios_activos_min + df.usuarios_activos_max) / 2
    df = df.sort_values("medio")

    fig, ax = plt.subplots(figsize=(9, 3.6))
    fig.subplots_adjust(left=0.12, right=0.92, top=0.72, bottom=0.17)
    ax.barh(df["app"], df["medio"] / 1e6, color=SERIE, height=0.55)
    for y, r in enumerate(df.itertuples()):
        if r.usuarios_activos_min != r.usuarios_activos_max:
            ax.errorbar(r.medio / 1e6, y, xerr=[[(r.medio - r.usuarios_activos_min) / 1e6],
                                                 [(r.usuarios_activos_max - r.medio) / 1e6]],
                        color=INK, capsize=4, linewidth=1.2)
            txt = f"{r.usuarios_activos_min / 1e3:.0f}–{r.usuarios_activos_max / 1e3:.0f} mil"
        else:
            txt = f"{r.medio / 1e6:.1f} M".replace(".", ",") if r.medio >= 1e6 else f"{r.medio / 1e3:.0f} mil"
        ax.text(r.usuarios_activos_max / 1e6 + 0.1, y, txt, va="center", color=INK, fontsize=10.5)
    ax.set_xlim(0, 5.2)
    ax.set_xlabel("Usuarios activos (millones)")
    base_ejes(ax)
    titulos(fig, "Uber concentra la mayoría de los usuarios: unos 5,3 millones entre las tres apps",
            "ESTIMACIÓN DE TERCEROS · Sensor Tower citado por iProfesional, 07/09/2026. Período de medición no informado;\n"
            "un mismo usuario puede estar en varias apps, así que la suma sobreestima personas únicas.")
    fig.savefig(SALIDA / "03_usuarios_activos_2026.png", dpi=200)
    plt.close(fig)


# 4. Volumen de datos esperado (estimación propia)
def calcular_volumen():
    s = pd.read_csv(DATOS / "supuestos_volumen.csv")
    s["busquedas_dia"] = s.usuarios_activos_mensuales * s.busquedas_por_usuario_mes / 30
    s["cotizaciones_usuarios_dia"] = s.busquedas_dia * s.cotizaciones_por_busqueda
    s["cotizaciones_dia"] = s.cotizaciones_usuarios_dia + s.cotizaciones_panel_dia
    s["gb_crudo_dia"] = s.cotizaciones_dia * s.kb_por_cotizacion / 1e6
    s["tb_crudo_anio"] = s.gb_crudo_dia * 365 / 1e3
    s["cotizaciones_seg_pico"] = s.cotizaciones_dia / 86400 * 5  # pico = 5x el promedio
    return s


def grafico_volumen(s):
    fig, ax = plt.subplots(figsize=(9, 3.8))
    fig.subplots_adjust(left=0.12, right=0.95, top=0.72, bottom=0.17)
    ax.barh(s["escenario"][::-1], s["cotizaciones_dia"][::-1] / 1e6, color=SERIE, height=0.55)
    for y, r in enumerate(s.iloc[::-1].itertuples()):
        ax.text(r.cotizaciones_dia / 1e6 + 0.08, y,
                f"{r.cotizaciones_dia / 1e6:.2f} M/día · {r.gb_crudo_dia:.1f} GB/día crudo · pico ~{r.cotizaciones_seg_pico:.0f}/s".replace(".", ","),
                va="center", color=INK, fontsize=9.5)
    ax.set_xlim(0, 10.5)
    ax.set_xlabel("Cotizaciones por día (millones)")
    base_ejes(ax)
    titulos(fig, "El volumen se multiplica por 17 entre el año 1 y el año 3",
            "ESTIMACIÓN PROPIA · 50 mil → 1 millón de usuarios activos mensuales, 10 búsquedas/mes, 18 cotizaciones por búsqueda,\n"
            "más un panel de 57.600 cotizaciones/día. Supuestos en datos/supuestos_volumen.csv.")
    fig.savefig(SALIDA / "04_volumen_estimado.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    brecha = grafico_brecha_2024()
    grafico_mismo_viaje_2021()
    grafico_usuarios()
    vol = calcular_volumen()
    grafico_volumen(vol)
    print(brecha[["destino", "barata", "min", "cara", "max", "brecha_pct"]].round(1).to_string(index=False))
    print(vol.round(2).T.to_string())

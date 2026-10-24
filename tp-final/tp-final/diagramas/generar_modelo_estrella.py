"""Genera diagramas/modelo_estrella.svg (vista en estrella del modelo Gold).

Uso (desde tp-final/): python diagramas/generar_modelo_estrella.py
El detalle completo de atributos y tipos está en modelo_datos_completo.mmd y en sql/modelo_gold.sql.
"""
from pathlib import Path

LH = 19
BOXES = {
    # nombre: (x, y, ancho, título, [(etiqueta, texto)], tipo)
    "fact_cotizacion": (560, 230, 480, "FACT_COTIZACION", [
        ("PK", "cotizacion_id"),
        ("FK", "busqueda_id (null si viene del panel)"),
        ("FK", "proveedor_key · categoria_key"),
        ("FK", "zona_origen_key · zona_destino_key"),
        ("FK", "fecha_key · minuto_key"),
        ("FK", "clima_key · evento_key"),
        ("", "ts_cotizacion (event time) · ts_ingesta · fuente"),
        ("", "precio_ars · precio_min/max_ars · precio_por_km_ars"),
        ("", "eta_min · duracion_estimada_min · distancia_km"),
        ("", "multiplicador_dinamico · es_precio_cerrado"),
    ], "fact"),
    "fact_busqueda": (560, 690, 480, "FACT_BUSQUEDA", [
        ("PK", "busqueda_id"),
        ("FK", "usuario_key · zona_origen/destino_key · fecha_key"),
        ("FK", "categoria_elegida_key (null si no eligió)"),
        ("", "n_proveedores · precio_min/max_ars · dispersion_pct"),
        ("", "convirtio · ahorro_vs_habitual_ars · latencia_ms"),
    ], "fact"),
    "dim_zona": (40, 110, 320, "DIM_ZONA", [("PK", "zona_key"), ("", "h3_index (res. 8) · barrio"), ("", "comuna_o_partido · es_aeropuerto")], "dim"),
    "dim_fecha": (40, 300, 320, "DIM_FECHA", [("PK", "fecha_key"), ("", "fecha · dia_semana"), ("", "es_feriado · hay_paro_transporte")], "dim"),
    "dim_tiempo": (40, 490, 320, "DIM_TIEMPO", [("PK", "minuto_key"), ("", "hora · franja horaria")], "dim"),
    "dim_clima": (40, 650, 320, "DIM_CLIMA", [("PK", "clima_key"), ("", "hora · lluvia_mm"), ("", "temperatura_c · alerta_smn")], "dim"),
    "dim_proveedor": (1210, 110, 350, "DIM_PROVEEDOR", [("PK", "proveedor_key"), ("", "nombre · tipo_integracion"), ("", "comision_derivacion_pct")], "dim"),
    "dim_categoria": (1210, 300, 350, "DIM_CATEGORIA (SCD2)", [("PK", "categoria_key"), ("FK", "proveedor_key"), ("", "nombre_comercial · segmento_homologado"), ("", "valido_desde · valido_hasta")], "dim"),
    "dim_evento": (1210, 510, 350, "DIM_EVENTO", [("PK", "evento_key"), ("FK", "zona_key"), ("", "tipo · inicio · fin · asistencia")], "dim"),
    "dim_usuario": (1210, 720, 350, "DIM_USUARIO", [("PK", "usuario_key (hash)"), ("", "fecha_alta · app_habitual_declarada")], "dim"),
}
# (dimensión, lado, hecho, lado, fracción en dim, fracción en hecho, x del codo)
LINKS = [
    ("dim_zona", "r", "fact_cotizacion", "l", 0.5, 0.12, 400),
    ("dim_fecha", "r", "fact_cotizacion", "l", 0.5, 0.38, 440),
    ("dim_tiempo", "r", "fact_cotizacion", "l", 0.5, 0.62, 480),
    ("dim_clima", "r", "fact_cotizacion", "l", 0.4, 0.88, 520),
    ("dim_proveedor", "l", "fact_cotizacion", "r", 0.5, 0.12, 1125),
    ("dim_categoria", "l", "fact_cotizacion", "r", 0.5, 0.38, 1125),
    ("dim_evento", "l", "fact_cotizacion", "r", 0.5, 0.75, 1125),
    ("dim_usuario", "l", "fact_busqueda", "r", 0.5, 0.5, 1125),
]


def alto(b):
    return 44 + LH * len(b[4]) + 6


def punto(nombre, lado, frac):
    x, y, w, *_ = BOXES[nombre]
    h = alto(BOXES[nombre])
    return {"l": (x, y + h * frac), "r": (x + w, y + h * frac), "t": (x + w * frac, y), "b": (x + w * frac, y + h)}[lado]


def main():
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" font-family="Inter, DejaVu Sans, sans-serif" font-size="13.5">',
         '<rect width="1600" height="900" fill="#ffffff"/>',
         '<text x="40" y="44" font-size="22" font-weight="700" fill="#0b0b0b">Modelo estrella en Gold: una fila por cotización, analizable por app, zona, hora, clima y evento</text>',
         '<text x="40" y="72" font-size="14" fill="#52514e">PK = clave primaria · FK = clave foránea · las líneas van de la dimensión (1) al hecho (N). fact_busqueda también usa dim_zona, dim_fecha y dim_categoria (dimensiones conformadas).</text>',
         '<g fill="none" stroke="#8a8984" stroke-width="1.5">']
    for a, sa, b, sb, fa, fb, xm in LINKS:
        x1, y1 = punto(a, sa, fa)
        x2, y2 = punto(b, sb, fb)
        o.append(f'<path d="M{x1:.0f} {y1:.0f}H{xm}V{y2:.0f}H{x2:.0f}"/>')
        dx = 8 if x2 > x1 else -8
        a1, a2 = ("start", "end") if dx > 0 else ("end", "start")
        o.append(f'<text x="{x1 + dx:.0f}" y="{y1 - 6:.0f}" stroke="none" fill="#52514e" font-size="12" text-anchor="{a1}">1</text>')
        o.append(f'<text x="{x2 - dx:.0f}" y="{y2 - 6:.0f}" stroke="none" fill="#52514e" font-size="12" text-anchor="{a2}">N</text>')
    x1, y1 = punto("fact_busqueda", "t", 0.5)
    x2, y2 = punto("fact_cotizacion", "b", 0.5)
    o.append(f'<path d="M{x1:.0f} {y1:.0f}V{y2:.0f}"/>')
    o.append(f'<text x="{x1 + 8:.0f}" y="{y1 - 8:.0f}" stroke="none" fill="#52514e" font-size="12">1 búsqueda</text>')
    o.append(f'<text x="{x2 + 8:.0f}" y="{y2 + 18:.0f}" stroke="none" fill="#52514e" font-size="12">N cotizaciones (≈18)</text>')
    o.append('</g>')
    for nombre, (x, y, w, titulo, lineas, tipo) in BOXES.items():
        h = alto(BOXES[nombre])
        if tipo == "fact":
            o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#e3eefb" stroke="#2a78d6" stroke-width="2"/>')
        else:
            o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#ffffff" stroke="#6b6a65" stroke-width="1.4"/>')
        o.append(f'<text x="{x + 14}" y="{y + 26}" font-weight="700" font-size="14.5" fill="#0b0b0b">{titulo}</text>')
        o.append(f'<line x1="{x}" x2="{x + w}" y1="{y + 36}" y2="{y + 36}" stroke="{"#2a78d6" if tipo == "fact" else "#c9c8c3"}"/>')
        for i, (tag, txt) in enumerate(lineas):
            ty = y + 56 + i * LH
            if tag:
                o.append(f'<text x="{x + 14}" y="{ty}" font-size="11.5" font-weight="700" fill="#52514e">{tag}</text>')
            o.append(f'<text x="{x + 44}" y="{ty}" fill="#0b0b0b">{txt}</text>')
    fx, fy, fw, *_ = BOXES["fact_cotizacion"]
    o.append(f'<text x="{fx + fw}" y="{fy - 10}" text-anchor="end" font-size="12.5" fill="#52514e">Grano: una cotización de un proveedor, para una categoría, en un instante</text>')
    bx, by, bw, *_ = BOXES["fact_busqueda"]
    o.append(f'<text x="{bx + bw}" y="{by + alto(BOXES["fact_busqueda"]) + 20}" text-anchor="end" font-size="12.5" fill="#52514e">Grano: una búsqueda de un usuario (origen, destino, momento)</text>')
    o.append('</svg>')
    (Path(__file__).resolve().parent / "modelo_estrella.svg").write_text("\n".join(o), encoding="utf-8")


if __name__ == "__main__":
    main()

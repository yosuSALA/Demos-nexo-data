"""
Demo: Generador Automático de Reportes PDF por Entidad
======================================================
Stack: polars · matplotlib · jinja2 · weasyprint

Uso:
    python generador_pdfs.py
    python generador_pdfs.py --parquet ../datos_limpios.parquet --top 10

Salida: demo2/output_pdfs/Reporte_<Entidad>_<Periodo>.pdf
"""

import os
import sys
import time

# Forzar UTF-8 en stdout para Windows (evita UnicodeEncodeError con emojis/símbolos)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import argparse
import warnings
from pathlib import Path
from datetime import datetime

import polars as pl
import matplotlib
matplotlib.use("Agg")           # sin GUI, necesario para generación en batch
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from jinja2 import Environment, FileSystemLoader

warnings.filterwarnings("ignore")

# ─── Rutas base ─────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR
OUTPUT_DIR   = BASE_DIR / "output_pdfs"
TEMP_DIR     = BASE_DIR / "assets" / "tmp_graficos"
PARQUET_DEFAULT = BASE_DIR.parent / "datos_limpios.parquet"

# ─── Parámetros de datos ─────────────────────────────────────────────────────
ENTITY_TYPES = [
    "NEGOCIO FIDUCIARIO INSCRITO",
    "FONDO DE INVERSION",
    "ADMINISTRADORA DE FONDOS Y FIDEICOMISOS",
]

# Códigos de cuenta resumen en los datos de SUPERCIAS
ACCOUNT_INGRESOS  = "6999"   # TOTAL INGRESOS
ACCOUNT_GASTOS    = "7992"   # TOTAL GASTOS
ACCOUNT_PATRIMONIO = "698"   # TOTAL PATRIMONIO NETO

PALETTE = {
    "ingreso":   "#059669",
    "gasto":     "#dc2626",
    "resultado": "#1a3a6e",
    "fondo":     "#f9fafb",
}


# ═══════════════════════════════════════════════════════════════════════════
# 1. CARGA Y PREPARACIÓN DE DATOS
# ═══════════════════════════════════════════════════════════════════════════

def cargar_datos(ruta_parquet: Path) -> pl.DataFrame:
    """Carga el parquet y filtra solo entidades fiduciarias / fondos."""
    print(f"[1/4] Cargando datos desde {ruta_parquet.name} ...")
    df = pl.read_parquet(ruta_parquet)

    df_filtrado = df.filter(pl.col("entity_type").is_in(ENTITY_TYPES))
    print(f"      {len(df_filtrado):,} registros para {df_filtrado['company_name'].n_unique():,} entidades")
    return df_filtrado


def seleccionar_top_entidades(df: pl.DataFrame, top_n: int) -> list[str]:
    """Devuelve lista con los top N nombres de entidad por volumen total."""
    ranking = (
        df.group_by("company_name")
        .agg(pl.col("value").abs().sum().alias("volumen"))
        .sort("volumen", descending=True)
        .head(top_n)
    )
    return ranking["company_name"].to_list()


def extraer_metricas(df: pl.DataFrame, empresa: str) -> dict:
    """
    Para una empresa, extrae las métricas clave del período más reciente
    disponible con datos de ingresos/gastos.
    """
    sub = df.filter(pl.col("company_name") == empresa)

    # Buscar período con datos de cuenta totales
    def suma_cuenta(codigo: str, df_e: pl.DataFrame) -> float:
        rows = df_e.filter(pl.col("account_code") == codigo)
        return float(rows["value"].sum()) if len(rows) > 0 else 0.0

    # Período más reciente con datos de ingresos
    filas_ing = sub.filter(pl.col("account_code") == ACCOUNT_INGRESOS).sort("date", descending=True)
    periodo_ref = filas_ing["date"].head(1).to_list()[0] if len(filas_ing) > 0 else sub["date"].max()

    sub_periodo = sub.filter(pl.col("date") == periodo_ref)

    ingresos   = suma_cuenta(ACCOUNT_INGRESOS,   sub_periodo)
    gastos     = suma_cuenta(ACCOUNT_GASTOS,     sub_periodo)
    patrimonio = suma_cuenta(ACCOUNT_PATRIMONIO, sub_periodo)
    resultado  = ingresos - gastos

    # Tabla de cuentas: top 6 por valor absoluto (excluye las de totales)
    cuentas_detail = (
        sub_periodo
        .filter(~pl.col("account_code").is_in([ACCOUNT_INGRESOS, ACCOUNT_GASTOS, ACCOUNT_PATRIMONIO]))
        .sort(pl.col("value").abs(), descending=True)
        .head(6)
        .select(["account_name", "value", "date"])
    )

    tabla = [
        {
            "cuenta":    row["account_name"][:55] + ("..." if len(row["account_name"]) > 55 else ""),
            "periodo":   row["date"],
            "valor":     row["value"],
            "valor_fmt": fmt_usd(row["value"]),
        }
        for row in cuentas_detail.to_dicts()
    ]

    # Datos de periodos anteriores para gráfico de tendencia
    periodos_historicos = (
        sub.filter(pl.col("account_code").is_in([ACCOUNT_INGRESOS, ACCOUNT_GASTOS]))
        .sort("date")
        .group_by(["date", "account_code"])
        .agg(pl.col("value").sum())
        .sort("date")
        .tail(20)   # últimas 10 fechas × 2 cuentas
    )

    ruc = sub["ruc"].head(1).to_list()[0] if "ruc" in sub.columns else "N/D"
    tipo = sub["entity_type"].head(1).to_list()[0] if len(sub) > 0 else ""

    return {
        "empresa":               empresa,
        "ruc":                   ruc,
        "tipo_entidad":          tipo,
        "periodo_ref":           periodo_ref,
        "ingresos":              ingresos,
        "gastos":                gastos,
        "resultado":             resultado,
        "patrimonio":            patrimonio,
        "tabla_cuentas":         tabla,
        "historico":             periodos_historicos,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 2. GENERACIÓN DE GRÁFICO
# ═══════════════════════════════════════════════════════════════════════════

def generar_grafico(metricas: dict, ruta_salida: Path) -> Path:
    """
    Genera gráfico de barras Ingresos vs Gastos + línea de Resultado.
    Devuelve la ruta absoluta del PNG guardado.
    """
    empresa    = metricas["empresa"]
    historico  = metricas["historico"]

    # Construir series desde el histórico polars
    df_h = historico.sort("date")
    fechas_ing = df_h.filter(pl.col("account_code") == ACCOUNT_INGRESOS)
    fechas_gas = df_h.filter(pl.col("account_code") == ACCOUNT_GASTOS)

    if len(fechas_ing) == 0:
        # Sin histórico: usar solo barra del período actual
        labels   = [metricas["periodo_ref"]]
        ingresos = [metricas["ingresos"]]
        gastos   = [metricas["gastos"]]
    else:
        # Alinear fechas comunes
        set_ing = set(fechas_ing["date"].to_list())
        set_gas = set(fechas_gas["date"].to_list())
        fechas_comunes = sorted(set_ing | set_gas)

        ing_map = dict(zip(fechas_ing["date"].to_list(), fechas_ing["value"].to_list()))
        gas_map = dict(zip(fechas_gas["date"].to_list(), fechas_gas["value"].to_list()))

        labels   = fechas_comunes[-8:]   # máx 8 períodos para legibilidad
        ingresos = [ing_map.get(f, 0) for f in labels]
        gastos   = [gas_map.get(f, 0) for f in labels]

    resultados = [i - g for i, g in zip(ingresos, gastos)]
    x = range(len(labels))

    # ── Layout ────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 4.5), facecolor=PALETTE["fondo"])
    ax.set_facecolor(PALETTE["fondo"])

    width = 0.35
    bars_i = ax.bar([xi - width/2 for xi in x], ingresos, width,
                    label="Ingresos", color=PALETTE["ingreso"], alpha=0.85, zorder=3)
    bars_g = ax.bar([xi + width/2 for xi in x], gastos,   width,
                    label="Gastos",   color=PALETTE["gasto"],   alpha=0.85, zorder=3)

    # Línea de resultado neto
    ax2 = ax.twinx()
    ax2.plot(list(x), resultados, color=PALETTE["resultado"],
             marker="o", linewidth=2, markersize=5, label="Resultado Neto", zorder=4)
    ax2.set_ylabel("Resultado Neto (USD)", fontsize=8, color=PALETTE["resultado"])
    ax2.tick_params(axis="y", labelcolor=PALETTE["resultado"], labelsize=7)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd_short(v)))

    # Etiquetas en barras (solo si pocas barras)
    if len(labels) <= 4:
        for bar in bars_i:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.01,
                    fmt_usd_short(bar.get_height()), ha="center", va="bottom",
                    fontsize=6.5, color=PALETTE["ingreso"], fontweight="bold")
        for bar in bars_g:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.01,
                    fmt_usd_short(bar.get_height()), ha="center", va="bottom",
                    fontsize=6.5, color=PALETTE["gasto"], fontweight="bold")

    # Estética
    ax.set_xticks(list(x))
    ax.set_xticklabels([l[-7:] for l in labels], rotation=30, ha="right", fontsize=7.5)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd_short(v)))
    ax.tick_params(axis="y", labelsize=7.5)
    ax.set_ylabel("Valor (USD)", fontsize=8)
    ax.set_title(f"Ingresos vs. Gastos — {empresa[:45]}", fontsize=10, fontweight="bold",
                 color="#1a1a2e", pad=12)
    ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)

    # Leyenda combinada
    lines, labels_leg = ax2.get_legend_handles_labels()
    bars_leg = [bars_i, bars_g]
    ax.legend(bars_leg + lines,
              ["Ingresos", "Gastos"] + labels_leg,
              loc="upper left", fontsize=8, framealpha=0.7)

    plt.tight_layout(pad=1.5)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta_salida, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return ruta_salida.resolve()


# ═══════════════════════════════════════════════════════════════════════════
# 3. RENDERIZADO HTML con Jinja2
# ═══════════════════════════════════════════════════════════════════════════

def renderizar_html(metricas: dict, ruta_grafico: Path) -> str:
    """Inyecta variables en template.html y devuelve el HTML completo."""
    import base64

    # Embeber imagen como data URI (compatible xhtml2pdf + WeasyPrint en Windows)
    with open(ruta_grafico, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("ascii")
    data_uri = f"data:image/png;base64,{img_b64}"

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)
    tmpl = env.get_template("template.html")

    return tmpl.render(
        nombre_entidad  = metricas["empresa"],
        ruc             = metricas["ruc"],
        tipo_entidad    = metricas["tipo_entidad"],
        fecha_generacion= datetime.now().strftime("%d/%m/%Y %H:%M"),
        periodo         = metricas["periodo_ref"],
        ingresos_fmt    = fmt_usd(metricas["ingresos"]),
        gastos_fmt      = fmt_usd(metricas["gastos"]),
        resultado       = metricas["resultado"],
        resultado_fmt   = fmt_usd(metricas["resultado"]),
        patrimonio_fmt  = fmt_usd(metricas["patrimonio"]),
        tabla_cuentas   = metricas["tabla_cuentas"],
        ruta_grafico    = data_uri,
    )


# ═══════════════════════════════════════════════════════════════════════════
# 4. CREACIÓN DE PDF con WeasyPrint
# ═══════════════════════════════════════════════════════════════════════════

def crear_pdf(html_content: str, ruta_pdf: Path) -> None:
    """
    Convierte el HTML renderizado a PDF.
    - Linux/Mac con GTK: usa WeasyPrint (mejor fidelidad CSS).
    - Windows o sin GTK:  usa xhtml2pdf (puro Python, sin dependencias nativas).
    """
    ruta_pdf.parent.mkdir(parents=True, exist_ok=True)

    use_weasyprint = (sys.platform != "win32")   # WeasyPrint necesita GTK (no incluido en Windows)

    if use_weasyprint:
        try:
            from weasyprint import HTML
            HTML(string=html_content, base_url=str(BASE_DIR)).write_pdf(str(ruta_pdf))
            return
        except Exception:
            pass   # fallthrough a xhtml2pdf

    import logging
    logging.getLogger("xhtml2pdf").setLevel(logging.ERROR)
    from xhtml2pdf import pisa
    with open(ruta_pdf, "wb") as f:
        result = pisa.CreatePDF(html_content.encode("utf-8"), dest=f,
                                encoding="utf-8")
    if result.err:
        raise RuntimeError(f"xhtml2pdf error code {result.err}")


# ═══════════════════════════════════════════════════════════════════════════
# 5. HELPERS DE FORMATO
# ═══════════════════════════════════════════════════════════════════════════

def fmt_usd(valor: float) -> str:
    """Formato monetario completo: $ 1,234,567.89"""
    signo = "-" if valor < 0 else ""
    return f"{signo}$ {abs(valor):,.2f}"


def fmt_usd_short(valor: float) -> str:
    """Formato compacto para ejes de gráfico: $1.2M, $450K"""
    v = abs(valor)
    signo = "-" if valor < 0 else ""
    if v >= 1_000_000_000:
        return f"{signo}${v/1e9:.1f}B"
    if v >= 1_000_000:
        return f"{signo}${v/1e6:.1f}M"
    if v >= 1_000:
        return f"{signo}${v/1e3:.0f}K"
    return f"{signo}${v:.0f}"


def nombre_archivo_seguro(texto: str) -> str:
    """Convierte nombre de empresa a nombre de archivo válido."""
    import re
    limpio = re.sub(r"[^\w\s-]", "", texto.upper())
    limpio = re.sub(r"\s+", "_", limpio.strip())
    return limpio[:60]


# ═══════════════════════════════════════════════════════════════════════════
# 6. ORQUESTADOR PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

def generar_reportes(ruta_parquet: Path, top_n: int = 10) -> None:
    t0 = time.perf_counter()

    # ── Carga ─────────────────────────────────────────────
    df = cargar_datos(ruta_parquet)

    # ── Selección top N ───────────────────────────────────
    empresas = seleccionar_top_entidades(df, top_n)
    print(f"[2/4] Top {top_n} entidades seleccionadas")
    for i, e in enumerate(empresas, 1):
        print(f"      {i:2d}. {e[:60]}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n[3/4] Generando {len(empresas)} PDFs ...\n")
    pdfs_ok = []

    for idx, empresa in enumerate(empresas, 1):
        t_ini = time.perf_counter()
        nombre_safe = nombre_archivo_seguro(empresa)

        try:
            # Extraer métricas
            metricas = extraer_metricas(df, empresa)
            periodo_safe = metricas["periodo_ref"].replace("-", "")[:6]

            # Gráfico
            ruta_grafico = TEMP_DIR / f"grafico_{nombre_safe}.png"
            generar_grafico(metricas, ruta_grafico)

            # HTML
            html = renderizar_html(metricas, ruta_grafico)

            # PDF
            ruta_pdf = OUTPUT_DIR / f"Reporte_{nombre_safe}_{periodo_safe}.pdf"
            crear_pdf(html, ruta_pdf)

            elapsed = time.perf_counter() - t_ini
            print(f"  [{idx:2d}/{len(empresas)}] OK {empresa[:45]:<45} ({elapsed:.1f}s)")
            pdfs_ok.append(ruta_pdf)

        except Exception as exc:
            print(f"  [{idx:2d}/{len(empresas)}] XX {empresa[:45]:<45} ERROR: {exc}")

    total = time.perf_counter() - t0
    print(f"\n[4/4] Completado: {len(pdfs_ok)}/{len(empresas)} PDFs en {total:.1f}s")
    print(f"      Carpeta: {OUTPUT_DIR.resolve()}")
    print(f"      Promedio por reporte: {total/max(len(pdfs_ok),1):.1f}s")


# ═══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Demo: Generador masivo de reportes PDF")
    parser.add_argument("--parquet", type=Path, default=PARQUET_DEFAULT,
                        help="Ruta al archivo .parquet de datos")
    parser.add_argument("--top", type=int, default=10,
                        help="Número de entidades a reportar (default: 10)")
    args = parser.parse_args()

    if not args.parquet.exists():
        print(f"ERROR: No se encontró el parquet en '{args.parquet}'")
        print("Uso: python generador_pdfs.py --parquet <ruta>")
        sys.exit(1)

    generar_reportes(args.parquet, args.top)


if __name__ == "__main__":
    main()

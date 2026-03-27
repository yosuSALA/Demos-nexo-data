"""
Dashboard Interactivo — Cartera Vencida (Aging Report)
Streamlit + Plotly
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from pathlib import Path
import subprocess
import sys
import os

# ─────────────────────────────────────────────
# CONFIGURACION DE PAGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Aging Report — Cartera Vencida",
    page_icon=":bar_chart:",
    layout="wide",
)

# Directorio del proyecto (para ejecutar scripts y leer CSVs)
DIR_PROYECTO = Path(__file__).resolve().parent

# ─────────────────────────────────────────────
# COLORES POR BUCKET
# ─────────────────────────────────────────────
COLORES_BUCKET = {
    "Pagada":      "#2ecc71",   # verde
    "Vigente":     "#3498db",   # azul
    "1-30 dias":   "#f1c40f",   # amarillo
    "31-60 dias":  "#e67e22",   # naranja
    "61-90 dias":  "#e74c3c",   # rojo
    "+90 dias":    "#8e44ad",   # morado
}

AGING_ORDER = ["Pagada", "Vigente", "1-30 dias", "31-60 dias", "61-90 dias", "+90 dias"]


# ─────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ─────────────────────────────────────────────
def archivos_existen(*nombres: str) -> bool:
    """Verifica si los archivos existen en el directorio del proyecto."""
    return all((DIR_PROYECTO / n).exists() for n in nombres)


def generar_datos():
    """Ejecuta generate_data.py como subproceso."""
    resultado = subprocess.run(
        [sys.executable, str(DIR_PROYECTO / "generate_data.py")],
        capture_output=True, text=True, cwd=str(DIR_PROYECTO),
    )
    return resultado


def ejecutar_etl():
    """Ejecuta etl_transform.py como subproceso."""
    resultado = subprocess.run(
        [sys.executable, str(DIR_PROYECTO / "etl_transform.py")],
        capture_output=True, text=True, cwd=str(DIR_PROYECTO),
    )
    return resultado


def cargar_aging() -> pd.DataFrame:
    """Carga aging_report.csv y normaliza los buckets."""
    df = pd.read_csv(
        DIR_PROYECTO / "aging_report.csv",
        encoding="utf-8-sig",
        parse_dates=["fecha_emision", "fecha_vencimiento"],
    )
    # Normalizar tildes/acentos en aging_bucket para consistencia con colores
    df["aging_bucket"] = (
        df["aging_bucket"]
        .str.replace("dias", "dias", regex=False)   # identidad si ya esta sin tilde
        .str.replace("días", "dias", regex=False)    # normalizar si viene con tilde
    )
    df["aging_bucket"] = pd.Categorical(df["aging_bucket"], categories=AGING_ORDER, ordered=True)
    return df


def cargar_top_deudores() -> pd.DataFrame:
    return pd.read_csv(DIR_PROYECTO / "top_deudores.csv", encoding="utf-8-sig")


def cargar_alertas() -> pd.DataFrame:
    df = pd.read_csv(
        DIR_PROYECTO / "alertas_cobro.csv",
        encoding="utf-8-sig",
        parse_dates=["fecha_vencimiento"],
    )
    return df


def colorear_bucket(val):
    """Devuelve el estilo CSS para una celda segun su bucket."""
    color = COLORES_BUCKET.get(val, "#ffffff")
    return f"background-color: {color}; color: white; font-weight: bold; border-radius: 4px;"


# ─────────────────────────────────────────────
# SIDEBAR — CONTROLES
# ─────────────────────────────────────────────
st.sidebar.title("Panel de Control")
st.sidebar.markdown("---")

st.sidebar.subheader("1. Generar datos sinteticos")
if st.sidebar.button("Generar datos", use_container_width=True):
    with st.spinner("Generando clientes y facturas..."):
        res = generar_datos()
    if res.returncode == 0:
        st.sidebar.success("Datos generados correctamente.")
        st.rerun()
    else:
        st.sidebar.error("Error al generar datos.")
        st.sidebar.code(res.stderr)

st.sidebar.markdown("---")
st.sidebar.subheader("2. Ejecutar ETL")
if st.sidebar.button("Ejecutar ETL", use_container_width=True):
    if not archivos_existen("clientes.csv", "facturas.csv"):
        st.sidebar.warning("Primero genera los datos sinteticos.")
    else:
        with st.spinner("Ejecutando transformacion ETL..."):
            res = ejecutar_etl()
        if res.returncode == 0:
            st.sidebar.success("ETL ejecutado correctamente.")
            st.rerun()
        else:
            st.sidebar.error("Error en el ETL.")
            st.sidebar.code(res.stderr)

st.sidebar.markdown("---")
st.sidebar.caption(f"Fecha de corte: **{date.today().isoformat()}**")

# ─────────────────────────────────────────────
# CONTENIDO PRINCIPAL
# ─────────────────────────────────────────────
st.title("Reporte de Cartera Vencida (Aging Report)")

if not archivos_existen("aging_report.csv", "top_deudores.csv", "alertas_cobro.csv"):
    st.info(
        "No se encontraron archivos de reporte. Usa el panel lateral para:\n"
        "1. **Generar datos sinteticos**\n"
        "2. **Ejecutar ETL**"
    )
    st.stop()

# ── Cargar datos ──
df_aging = cargar_aging()
df_top = cargar_top_deudores()
df_alertas = cargar_alertas()

# ─────────────────────────────────────────────
# METRICAS RESUMEN
# ─────────────────────────────────────────────
st.header("Metricas Generales")

total_facturas = len(df_aging)
total_saldo = df_aging["saldo_pendiente"].sum()
saldo_vencido = df_aging[df_aging["aging_bucket"].isin(["1-30 dias", "31-60 dias", "61-90 dias", "+90 dias"])]["saldo_pendiente"].sum()
facturas_vencidas = df_aging[df_aging["aging_bucket"].isin(["1-30 dias", "31-60 dias", "61-90 dias", "+90 dias"])].shape[0]
n_alertas = len(df_alertas)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Facturas", f"{total_facturas:,}")
col2.metric("Saldo Total Pendiente", f"${total_saldo:,.2f}")
col3.metric("Saldo Vencido", f"${saldo_vencido:,.2f}")
col4.metric("Facturas Vencidas", f"{facturas_vencidas:,}")
col5.metric("Alertas (7 dias)", f"{n_alertas}")

st.markdown("---")

# ─────────────────────────────────────────────
# RESUMEN POR BUCKET
# ─────────────────────────────────────────────
st.header("Resumen por Categoria de Aging")

resumen = (
    df_aging.groupby("aging_bucket", observed=True)["saldo_pendiente"]
    .agg(["count", "sum"])
    .rename(columns={"count": "Num. Facturas", "sum": "Saldo Total"})
    .reset_index()
    .rename(columns={"aging_bucket": "Categoria"})
)
resumen["% del Saldo"] = (resumen["Saldo Total"] / resumen["Saldo Total"].sum() * 100).round(1)

col_tabla, col_dona = st.columns([1, 1])

with col_tabla:
    st.subheader("Tabla resumen")
    # Formatear para mostrar
    resumen_display = resumen.copy()
    resumen_display["Saldo Total"] = resumen_display["Saldo Total"].map("${:,.2f}".format)
    resumen_display["% del Saldo"] = resumen_display["% del Saldo"].map("{:.1f}%".format)
    st.dataframe(
        resumen_display.style.applymap(colorear_bucket, subset=["Categoria"]),
        use_container_width=True,
        hide_index=True,
    )

with col_dona:
    st.subheader("Distribucion de saldo por categoria")
    fig_dona = px.pie(
        resumen, names="Categoria", values="Saldo Total",
        color="Categoria",
        color_discrete_map=COLORES_BUCKET,
        hole=0.45,
    )
    fig_dona.update_traces(textinfo="percent+label", textposition="outside")
    fig_dona.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_dona, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────────
# GRAFICO DE BARRAS — SALDO POR BUCKET
# ─────────────────────────────────────────────
st.header("Saldo Pendiente por Categoria de Aging")

fig_barras = px.bar(
    resumen, x="Categoria", y="Saldo Total",
    color="Categoria",
    color_discrete_map=COLORES_BUCKET,
    text_auto="$.2s",
)
fig_barras.update_layout(
    xaxis_title="Categoria de Aging",
    yaxis_title="Saldo Pendiente ($)",
    showlegend=False,
    yaxis_tickprefix="$",
    yaxis_tickformat=",",
)
st.plotly_chart(fig_barras, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────────
# TOP DEUDORES
# ─────────────────────────────────────────────
st.header("Top 10 Deudores")

col_chart, col_table = st.columns([1.2, 0.8])

with col_chart:
    fig_top = px.bar(
        df_top.sort_values("saldo_vencido_total"),
        x="saldo_vencido_total",
        y="nombre_comercial",
        orientation="h",
        color="segmento",
        text_auto="$.2s",
        labels={
            "saldo_vencido_total": "Saldo Vencido ($)",
            "nombre_comercial": "Cliente",
            "segmento": "Segmento",
        },
    )
    fig_top.update_layout(
        yaxis_title="",
        xaxis_tickprefix="$",
        xaxis_tickformat=",",
        margin=dict(l=10),
        height=450,
    )
    st.plotly_chart(fig_top, use_container_width=True)

with col_table:
    st.subheader("Detalle")
    df_top_display = df_top.copy()
    df_top_display["saldo_vencido_total"] = df_top_display["saldo_vencido_total"].map("${:,.2f}".format)
    df_top_display = df_top_display.rename(columns={
        "nombre_comercial": "Cliente",
        "segmento": "Segmento",
        "saldo_vencido_total": "Saldo Vencido",
        "n_facturas_vencidas": "Facturas",
    })
    st.dataframe(
        df_top_display[["Cliente", "Segmento", "Saldo Vencido", "Facturas"]],
        use_container_width=True,
        hide_index=True,
        height=450,
    )

st.markdown("---")

# ─────────────────────────────────────────────
# AGING POR SEGMENTO
# ─────────────────────────────────────────────
st.header("Saldo Vencido por Segmento")

seg_aging = (
    df_aging[df_aging["saldo_pendiente"] > 0]
    .groupby(["segmento", "aging_bucket"], observed=True)["saldo_pendiente"]
    .sum()
    .reset_index()
    .rename(columns={"segmento": "Segmento", "aging_bucket": "Categoria", "saldo_pendiente": "Saldo"})
)

fig_seg = px.bar(
    seg_aging, x="Segmento", y="Saldo", color="Categoria",
    color_discrete_map=COLORES_BUCKET,
    barmode="stack",
    text_auto="$.2s",
)
fig_seg.update_layout(
    yaxis_title="Saldo Pendiente ($)",
    yaxis_tickprefix="$",
    yaxis_tickformat=",",
)
st.plotly_chart(fig_seg, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────────
# ALERTAS DE COBRANZA
# ─────────────────────────────────────────────
st.header(f"Alertas de Cobranza — Facturas por vencer en 7 dias ({len(df_alertas)})")

if df_alertas.empty:
    st.success("Sin facturas proximas a vencer en los proximos 7 dias.")
else:
    df_alertas_display = df_alertas.copy()
    df_alertas_display["fecha_vencimiento"] = df_alertas_display["fecha_vencimiento"].dt.strftime("%Y-%m-%d")
    df_alertas_display["monto_total"] = df_alertas_display["monto_total"].map("${:,.2f}".format)
    df_alertas_display["saldo_pendiente"] = df_alertas_display["saldo_pendiente"].map("${:,.2f}".format)
    df_alertas_display = df_alertas_display.rename(columns={
        "id_factura": "Factura",
        "id_cliente": "ID Cliente",
        "nombre_comercial": "Cliente",
        "segmento": "Segmento",
        "fecha_vencimiento": "Vencimiento",
        "monto_total": "Monto Total",
        "saldo_pendiente": "Saldo Pendiente",
    })
    st.dataframe(df_alertas_display, use_container_width=True, hide_index=True)

st.markdown("---")

# ─────────────────────────────────────────────
# TABLA COMPLETA — AGING REPORT
# ─────────────────────────────────────────────
st.header("Tabla Completa del Aging Report")

# Filtros
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    filtro_bucket = st.multiselect(
        "Filtrar por categoria de aging",
        options=AGING_ORDER,
        default=AGING_ORDER,
    )
with col_f2:
    segmentos_disponibles = sorted(df_aging["segmento"].dropna().unique().tolist())
    filtro_segmento = st.multiselect(
        "Filtrar por segmento",
        options=segmentos_disponibles,
        default=segmentos_disponibles,
    )
with col_f3:
    filtro_saldo_min = st.number_input("Saldo pendiente minimo ($)", min_value=0.0, value=0.0, step=100.0)

df_filtrado = df_aging[
    (df_aging["aging_bucket"].isin(filtro_bucket))
    & (df_aging["segmento"].isin(filtro_segmento))
    & (df_aging["saldo_pendiente"] >= filtro_saldo_min)
].copy()

st.caption(f"Mostrando {len(df_filtrado):,} de {len(df_aging):,} facturas")

# Formatear para mostrar
df_show = df_filtrado.copy()
df_show["fecha_emision"] = df_show["fecha_emision"].dt.strftime("%Y-%m-%d")
df_show["fecha_vencimiento"] = df_show["fecha_vencimiento"].dt.strftime("%Y-%m-%d")
df_show["monto_total"] = df_show["monto_total"].map("${:,.2f}".format)
df_show["saldo_pendiente"] = df_show["saldo_pendiente"].map("${:,.2f}".format)

st.dataframe(
    df_show.style.applymap(colorear_bucket, subset=["aging_bucket"]),
    use_container_width=True,
    hide_index=True,
    height=500,
)

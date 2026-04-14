"""
Dashboard — Monitor de Vencimiento de Contratos y Obligaciones
Correr con: streamlit run dashboard.py
"""

import sys
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import date

from etl_contratos import generar_datos, transformar, guardar_csv
from alertas_email import procesar_alertas
from config import CSV_PATH

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ── Configuracion de pagina ───────────────────────────────────
st.set_page_config(
    page_title="Monitor de Contratos",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos globales ──────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700; }
  .badge-rojo     { background:#e74c3c; color:#fff; padding:3px 10px;
                    border-radius:4px; font-weight:bold; }
  .badge-amarillo { background:#f39c12; color:#fff; padding:3px 10px;
                    border-radius:4px; font-weight:bold; }
  .badge-verde    { background:#27ae60; color:#fff; padding:3px 10px;
                    border-radius:4px; font-weight:bold; }
  div[data-testid="stSidebarContent"] { background: #1a1a2e; }
</style>
""", unsafe_allow_html=True)


# ── Carga / generacion de datos ───────────────────────────────
@st.cache_data(show_spinner="Procesando datos...")
def cargar_datos(regenerar: bool = False) -> pd.DataFrame:
    if regenerar or not os.path.exists(CSV_PATH):
        df = transformar(generar_datos(n=100))
        guardar_csv(df, CSV_PATH)
    else:
        df = pd.read_csv(CSV_PATH, parse_dates=["fecha_inicio", "fecha_vencimiento"])
        hoy = pd.Timestamp(date.today())
        df["dias_para_vencer"] = (df["fecha_vencimiento"] - hoy).dt.days

        def semaforo(d):
            if d < 15:   return "Rojo"
            elif d <= 30: return "Amarillo"
            return "Verde"

        df["estado_semaforo"] = df["dias_para_vencer"].apply(semaforo)
    return df


COLORES = {"Rojo": "#e74c3c", "Amarillo": "#f39c12", "Verde": "#27ae60"}


# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://img.icons8.com/color/96/000000/contract.png", width=64
    )
    st.title("Monitor de Contratos")
    st.caption(f"Hoy: {date.today().strftime('%d %b %Y')}")
    st.divider()

    regenerar = st.button("↺  Regenerar datos mock", use_container_width=True)
    if regenerar:
        st.cache_data.clear()

    st.subheader("Filtros")
    estados_sel = st.multiselect(
        "Estado semaforo",
        ["Rojo", "Amarillo", "Verde"],
        default=["Rojo", "Amarillo", "Verde"],
    )
    tipo_opts = ["Todos", "Contrato de Arriendo", "Poliza de Seguro",
                 "Garantia", "Permiso Municipal"]
    tipo_sel = st.selectbox("Tipo de obligacion", tipo_opts)

    responsable_sel = st.selectbox(
        "Responsable interno",
        ["Todos"] + [
            "Ana Torres", "Carlos Mendez", "Sofia Reyes",
            "Jorge Quispe", "Valentina Cruz", "Ricardo Morales",
            "Daniela Fuentes", "Andres Salinas",
        ],
    )

    st.divider()
    st.subheader("Alertas por Email")
    if st.button("Enviar alertas ahora", use_container_width=True, type="primary"):
        df_full = cargar_datos(regenerar=False)
        res = procesar_alertas(df_full)
        st.success(
            f"Alertas procesadas: {res['total']}  \n"
            f"Enviadas: {res['enviados']} | Fallidas: {res['fallidos']}  \n"
            f"Modo: `{res['modo']}`"
        )

    st.caption("Modo email: ver `.env` → `EMAIL_MODE`")


# ── Carga datos ───────────────────────────────────────────────
df = cargar_datos(regenerar=regenerar)

# Aplicar filtros
df_f = df[df["estado_semaforo"].isin(estados_sel)].copy()
if tipo_sel != "Todos":
    # Comparacion flexible (normaliza acentos basico)
    df_f = df_f[df_f["tipo"].str.contains(tipo_sel.split()[0], case=False, na=False)]
if responsable_sel != "Todos":
    df_f = df_f[df_f["responsable_interno"].str.contains(
        responsable_sel.split()[0], case=False, na=False
    )]


# ── KPI Cards ─────────────────────────────────────────────────
st.header("Monitor de Vencimiento de Contratos y Obligaciones")

total   = len(df)
rojos   = (df["estado_semaforo"] == "Rojo").sum()
amarillos = (df["estado_semaforo"] == "Amarillo").sum()
verdes  = (df["estado_semaforo"] == "Verde").sum()
valor_riesgo = df[df["estado_semaforo"].isin(["Rojo", "Amarillo"])]["valor_usd"].sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total obligaciones", total)
c2.metric("🔴 Critico (Rojo)", rojos,  delta=f"-{rojos} urgentes", delta_color="inverse")
c3.metric("🟡 Alerta (Amarillo)", amarillos)
c4.metric("🟢 Al dia (Verde)", verdes)
c5.metric("USD en riesgo", f"${valor_riesgo:,.0f}")

st.divider()


# ── Fila de graficos ──────────────────────────────────────────
col_pie, col_bar, col_timeline = st.columns([1, 1.5, 2])

with col_pie:
    st.subheader("Distribucion semaforo")
    conteos = df["estado_semaforo"].value_counts().reset_index()
    conteos.columns = ["Estado", "Cantidad"]
    fig_pie = px.pie(
        conteos, names="Estado", values="Cantidad",
        color="Estado",
        color_discrete_map=COLORES,
        hole=0.45,
    )
    fig_pie.update_traces(textinfo="percent+value", textfont_size=13)
    fig_pie.update_layout(showlegend=True, margin=dict(t=10, b=10))
    st.plotly_chart(fig_pie, use_container_width=True)

with col_bar:
    st.subheader("Obligaciones por tipo")
    tipo_estado = (
        df.groupby(["tipo", "estado_semaforo"])
        .size().reset_index(name="count")
    )
    fig_bar = px.bar(
        tipo_estado, x="count", y="tipo", color="estado_semaforo",
        color_discrete_map=COLORES, orientation="h",
        labels={"count": "Cantidad", "tipo": "", "estado_semaforo": "Estado"},
    )
    fig_bar.update_layout(
        legend_title_text="", margin=dict(t=10, b=10),
        yaxis=dict(tickfont=dict(size=11)),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_timeline:
    st.subheader("Vencimientos proximos 90 dias")
    hoy = pd.Timestamp(date.today())
    prox = df[(df["dias_para_vencer"] >= 0) & (df["dias_para_vencer"] <= 90)].copy()
    prox["mes"] = prox["fecha_vencimiento"].dt.to_period("M").astype(str)
    agrup = prox.groupby(["mes", "estado_semaforo"]).size().reset_index(name="n")
    fig_tl = px.bar(
        agrup, x="mes", y="n", color="estado_semaforo",
        color_discrete_map=COLORES,
        labels={"mes": "Mes", "n": "Obligaciones", "estado_semaforo": "Estado"},
    )
    fig_tl.update_layout(
        legend_title_text="", margin=dict(t=10, b=10),
        xaxis_tickangle=-30,
    )
    st.plotly_chart(fig_tl, use_container_width=True)


# ── Gauge: Porcentaje critico ─────────────────────────────────
st.subheader("Indicador de riesgo global")
pct_critico = round((rojos / total) * 100, 1) if total else 0
col_g1, col_g2 = st.columns([1, 3])

with col_g1:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct_critico,
        number={"suffix": "%", "font": {"size": 36}},
        delta={"reference": 20, "increasing": {"color": "#e74c3c"},
               "decreasing": {"color": "#27ae60"}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar":  {"color": COLORES["Rojo"] if pct_critico > 20 else COLORES["Verde"]},
            "steps": [
                {"range": [0, 20],   "color": "#d5f5e3"},
                {"range": [20, 40],  "color": "#fef9e7"},
                {"range": [40, 100], "color": "#fdecea"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 3},
                "thickness": 0.8, "value": 20,
            },
        },
        title={"text": "% Obligaciones Criticas"},
    ))
    fig_gauge.update_layout(height=250, margin=dict(t=30, b=10, l=20, r=20))
    st.plotly_chart(fig_gauge, use_container_width=True)

with col_g2:
    # Top 5 por valor en riesgo (Rojo)
    st.markdown("**Top 5 contratos criticos por valor USD**")
    top5 = (
        df[df["estado_semaforo"] == "Rojo"]
        .nlargest(5, "valor_usd")
        [["id_obligacion", "tipo", "entidad_relacionada",
          "dias_para_vencer", "valor_usd", "responsable_interno"]]
        .rename(columns={
            "id_obligacion": "ID",
            "tipo": "Tipo",
            "entidad_relacionada": "Entidad",
            "dias_para_vencer": "Dias",
            "valor_usd": "USD",
            "responsable_interno": "Responsable",
        })
    )
    top5["USD"] = top5["USD"].apply(lambda x: f"${x:,.0f}")
    st.dataframe(top5, use_container_width=True, hide_index=True)


# ── Tabla principal ───────────────────────────────────────────
st.divider()
st.subheader(f"Detalle de obligaciones ({len(df_f)} registros)")

def _badge(estado):
    cls = f"badge-{estado.lower()}"
    return f'<span class="{cls}">{estado}</span>'

df_display = df_f[[
    "id_obligacion", "tipo", "entidad_relacionada",
    "fecha_vencimiento", "dias_para_vencer",
    "valor_usd", "responsable_interno", "estado_semaforo",
]].copy()
df_display["fecha_vencimiento"] = df_display["fecha_vencimiento"].dt.strftime("%d/%m/%Y")
df_display["valor_usd"]        = df_display["valor_usd"].apply(lambda x: f"${x:,.0f}")
df_display = df_display.rename(columns={
    "id_obligacion":     "ID",
    "tipo":              "Tipo",
    "entidad_relacionada": "Entidad",
    "fecha_vencimiento": "Vencimiento",
    "dias_para_vencer":  "Dias",
    "valor_usd":         "USD",
    "responsable_interno": "Responsable",
    "estado_semaforo":   "Estado",
})

# Color de fondo por estado
def _colorear_fila(row):
    colores_bg = {
        "Rojo":     "background-color: #c0392b; color: white;",
        "Amarillo": "background-color: #d35400; color: white;",
        "Verde":    "background-color: #27ae60; color: white;",
    }
    bg = colores_bg.get(row["Estado"], "")
    return [bg] * len(row)

styled = df_display.style.apply(_colorear_fila, axis=1)
st.dataframe(styled, use_container_width=True, hide_index=True, height=420)

# Descarga
csv_bytes = df_f.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
st.download_button(
    label="Descargar CSV filtrado",
    data=csv_bytes,
    file_name=f"contratos_filtrado_{date.today()}.csv",
    mime="text/csv",
)

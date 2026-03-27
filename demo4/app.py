"""
Demo #4: Interfaz web para el Bot de Conciliación Bancaria Automática.
Ejecutar: streamlit run app.py
"""

import io
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from conciliacion import generar_datos, conciliar, exportar_excel

# ---------------------------------------------------------------------------
# Configuración de página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Conciliación Bancaria",
    page_icon="🏦",
    layout="wide",
)

st.title("Bot de Conciliación Bancaria Automática")
st.caption("Demo #4 — Cruce automático de extracto bancario vs libro mayor contable")

# ---------------------------------------------------------------------------
# Sidebar — Parámetros
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Configuración")
    n_registros = st.slider("Registros a generar", 20, 200, 50, step=10)
    if st.button("Generar datos y conciliar", type="primary", use_container_width=True):
        st.session_state["run"] = True

    st.divider()
    st.markdown("**Reglas de cruce**")
    st.info("Monto exacto + ventana de ±3 días entre fecha banco y contabilidad")

    st.divider()
    st.markdown(
        "**Archivos generados**\n"
        "- `reporte_conciliacion.xlsx`\n"
        "  - Conciliados\n"
        "  - Faltantes en Banco\n"
        "  - Faltantes en Contabilidad"
    )

# ---------------------------------------------------------------------------
# Ejecución
# ---------------------------------------------------------------------------
if not st.session_state.get("run"):
    st.info("Presiona **Generar datos y conciliar** en la barra lateral para iniciar.")
    st.stop()

# Generar y conciliar
with st.spinner("Generando datos de prueba..."):
    df_banco, df_contabilidad = generar_datos(n_registros)

with st.spinner("Ejecutando motor de conciliación..."):
    resultado = conciliar(df_banco, df_contabilidad)

df_conc = resultado["conciliados"]
df_fb = resultado["faltantes_banco"]
df_fc = resultado["faltantes_contabilidad"]

n_conc = len(df_conc)
n_fb = len(df_fb)
n_fc = len(df_fc)
total = n_conc + n_fb + n_fc
tasa = n_conc / total * 100 if total else 0

# ---------------------------------------------------------------------------
# Métricas principales
# ---------------------------------------------------------------------------
st.subheader("Resumen de Conciliación")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total analizadas", total)
col2.metric("Conciliadas", n_conc)
col3.metric("Faltantes en banco", n_fb)
col4.metric("No registradas", n_fc)
col5.metric("Tasa de conciliación", f"{tasa:.1f}%")

# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    fig_dona = px.pie(
        names=["Conciliados", "Faltantes en banco", "No registradas en contabilidad"],
        values=[n_conc, n_fb, n_fc],
        color_discrete_sequence=["#2ecc71", "#f39c12", "#e74c3c"],
        hole=0.45,
        title="Distribución de resultados",
    )
    fig_dona.update_traces(textinfo="label+value+percent")
    st.plotly_chart(fig_dona, use_container_width=True)

with chart_col2:
    if not df_conc.empty:
        fig_desfase = px.histogram(
            df_conc,
            x="desfase_dias",
            nbins=4,
            title="Distribución de desfase (días) en partidas conciliadas",
            labels={"desfase_dias": "Días de desfase", "count": "Cantidad"},
            color_discrete_sequence=["#3498db"],
        )
        fig_desfase.update_layout(bargap=0.1)
        st.plotly_chart(fig_desfase, use_container_width=True)
    else:
        st.warning("No hay partidas conciliadas para graficar desfase.")

# Montos por categoría
montos_data = []
if not df_conc.empty:
    montos_data.append({"Categoría": "Conciliados", "Monto total": df_conc["monto"].sum()})
if not df_fb.empty:
    montos_data.append({"Categoría": "Faltantes en banco", "Monto total": df_fb["monto"].sum()})
if not df_fc.empty:
    montos_data.append({"Categoría": "No registradas", "Monto total": df_fc["monto"].sum()})

if montos_data:
    df_montos = pd.DataFrame(montos_data)
    fig_montos = px.bar(
        df_montos,
        x="Categoría",
        y="Monto total",
        color="Categoría",
        color_discrete_map={
            "Conciliados": "#2ecc71",
            "Faltantes en banco": "#f39c12",
            "No registradas": "#e74c3c",
        },
        title="Monto total por categoría ($)",
        text_auto=",.2f",
    )
    fig_montos.update_layout(showlegend=False)
    st.plotly_chart(fig_montos, use_container_width=True)

# ---------------------------------------------------------------------------
# Pestañas de detalle
# ---------------------------------------------------------------------------
st.subheader("Detalle de partidas")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    f"Conciliados ({n_conc})",
    f"Faltantes en banco ({n_fb})",
    f"No registradas ({n_fc})",
    "Extracto bancario",
    "Libro mayor",
])

with tab1:
    if not df_conc.empty:
        st.dataframe(
            df_conc.style.applymap(
                lambda _: "background-color: #d5f5e3",
                subset=["estado"],
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No hay partidas conciliadas.")

with tab2:
    if not df_fb.empty:
        st.dataframe(
            df_fb.style.applymap(
                lambda _: "background-color: #fdebd0",
                subset=["estado"],
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("No hay partidas faltantes en banco.")

with tab3:
    if not df_fc.empty:
        st.dataframe(
            df_fc.style.applymap(
                lambda _: "background-color: #fadbd8",
                subset=["estado"],
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("No hay partidas sin registrar en contabilidad.")

with tab4:
    st.dataframe(df_banco, use_container_width=True, hide_index=True)

with tab5:
    st.dataframe(df_contabilidad, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Exportar Excel
# ---------------------------------------------------------------------------
st.subheader("Exportar reporte")

archivo = exportar_excel(resultado)

with open(archivo, "rb") as f:
    st.download_button(
        label="Descargar reporte Excel",
        data=f,
        file_name="reporte_conciliacion.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )

st.success(f"Reporte generado: **{archivo}** — {n_conc} conciliadas, {n_fb + n_fc} diferencias.")

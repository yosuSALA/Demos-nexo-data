"""
app.py — Demo #13: Dashboard de Monitoreo de Precios (Streamlit + Plotly)
Interfaz visual para el sistema de inteligencia competitiva de precios.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import asyncio

from comparador import cargar_datos_empresa, cargar_datos_competidor, calcular_diferencias
from alertas import (
    detectar_alertas,
    calcular_impacto_mensual,
    UMBRAL_ALERTA_PCT,
    VOLUMEN_MENSUAL,
    NOMBRE_COMPETIDOR,
    NOMBRE_EMPRESA,
)

# ─── Configuracion de pagina ──────────────────────────────────────────────────

st.set_page_config(
    page_title="Monitor de Precios — Demo #13",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Monitor de Precios de Competencia")
st.caption("Demo #13 — Sistema de inteligencia competitiva automatizado")

# ─── Barra lateral: Configuracion ─────────────────────────────────────────────

st.sidebar.header("⚙️ Configuracion")

umbral_pct = st.sidebar.slider(
    "Umbral de alerta (%)",
    min_value=1.0,
    max_value=20.0,
    value=UMBRAL_ALERTA_PCT,
    step=0.5,
    help="Diferencia porcentual minima para que un producto genere alerta.",
)

volumen_mensual = st.sidebar.number_input(
    "Volumen mensual por SKU (unidades)",
    min_value=1,
    max_value=10000,
    value=VOLUMEN_MENSUAL,
    step=10,
    help="Unidades vendidas al mes por producto. Se usa para estimar el impacto economico.",
)

paginas = st.sidebar.number_input(
    "Paginas a scrapear",
    min_value=1,
    max_value=50,
    value=3,
    step=1,
    help="Numero de paginas del catalogo del competidor a extraer.",
)

st.sidebar.markdown("---")

CSV_COMPETIDOR = "precios_competidor_A.csv"
csv_existe = os.path.exists(CSV_COMPETIDOR)

st.sidebar.subheader("🔄 Fuente de datos")

usar_csv = st.sidebar.checkbox(
    "Usar CSV existente (sin scraping)",
    value=True,
    help="Carga datos desde el CSV ya generado. No requiere Playwright.",
)

# ─── Scraping o carga de datos ─────────────────────────────────────────────────


@st.cache_data(show_spinner=False)
def cargar_desde_csv():
    """Carga datos del competidor desde CSV existente."""
    df_competidor = cargar_datos_competidor(CSV_COMPETIDOR)
    return df_competidor


def ejecutar_scraping(max_pages: int) -> pd.DataFrame:
    """Ejecuta el scraper de Playwright."""
    from scraper import scrape_competitor
    return asyncio.run(scrape_competitor(max_pages=max_pages))


# Boton de ejecucion
if usar_csv:
    if not csv_existe:
        st.sidebar.warning(
            f"No se encontro `{CSV_COMPETIDOR}`. "
            "Ejecuta primero el scraper o desmarca esta opcion."
        )
    ejecutar = st.sidebar.button("📂 Cargar datos desde CSV", type="primary", use_container_width=True)
else:
    ejecutar = st.sidebar.button(
        f"🌐 Ejecutar scraping ({paginas} pags.)",
        type="primary",
        use_container_width=True,
    )

# ─── Pipeline principal ───────────────────────────────────────────────────────

if ejecutar or ("df_comparacion" in st.session_state):
    # Obtener datos del competidor
    if ejecutar:
        if usar_csv:
            if not csv_existe:
                st.error(f"Archivo `{CSV_COMPETIDOR}` no encontrado. Ejecuta el scraper primero.")
                st.stop()
            with st.spinner("Cargando datos desde CSV..."):
                df_competidor = cargar_desde_csv()
        else:
            with st.spinner(f"Scrapeando {paginas} paginas de {NOMBRE_COMPETIDOR}..."):
                try:
                    df_competidor = ejecutar_scraping(paginas)
                except Exception as e:
                    st.error(
                        f"Error al ejecutar el scraper: {e}\n\n"
                        "Asegurate de tener Playwright instalado: `playwright install chromium`"
                    )
                    st.stop()

        # Comparacion
        df_empresa = cargar_datos_empresa()
        df_comparacion = calcular_diferencias(df_empresa, df_competidor)

        if df_comparacion.empty:
            st.error(
                "No se encontraron productos en comun entre la empresa y el competidor. "
                "Verifica que los nombres coincidan."
            )
            st.stop()

        # Alertas
        df_alertas = detectar_alertas(df_comparacion, umbral_pct=umbral_pct)
        impacto = calcular_impacto_mensual(df_alertas, volumen_mensual=volumen_mensual)

        # Guardar en session_state
        st.session_state["df_comparacion"] = df_comparacion
        st.session_state["df_alertas"] = df_alertas
        st.session_state["impacto"] = impacto
        st.session_state["df_competidor"] = df_competidor

    # Recuperar del session_state
    df_comparacion = st.session_state["df_comparacion"]
    df_alertas = st.session_state["df_alertas"]
    impacto = st.session_state["impacto"]

    # Recalcular si cambian los parametros de la sidebar
    if ejecutar is False:
        df_alertas = detectar_alertas(df_comparacion, umbral_pct=umbral_pct)
        impacto = calcular_impacto_mensual(df_alertas, volumen_mensual=volumen_mensual)
        st.session_state["df_alertas"] = df_alertas
        st.session_state["impacto"] = impacto

    # ─── Metricas resumen ──────────────────────────────────────────────────────

    st.markdown("---")

    n_total = len(df_comparacion)
    n_alertas = len(df_alertas)
    n_mas_caros = (df_comparacion["diff_porcentual"] > 0).sum()
    n_mas_baratos = (df_comparacion["diff_porcentual"] < 0).sum()
    perdida_total = impacto.get("perdida_total", 0.0)
    diff_promedio = df_comparacion["diff_porcentual"].mean()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Productos analizados", n_total)
    col2.metric(
        "Somos mas caros",
        n_mas_caros,
        delta=f"{n_mas_caros}/{n_total}",
        delta_color="inverse",
    )
    col3.metric(
        "Somos mas baratos",
        n_mas_baratos,
        delta=f"{n_mas_baratos}/{n_total}",
        delta_color="normal",
    )
    col4.metric(
        "Alertas activas",
        f"⚠️ {n_alertas}",
        delta=f"umbral: {umbral_pct:.0f}%",
        delta_color="off",
    )
    col5.metric(
        "Perdida estimada/mes",
        f"${perdida_total:,.2f}",
        delta=f"{volumen_mensual} uds/SKU",
        delta_color="off",
    )

    # ─── Tabla de comparacion de precios ───────────────────────────────────────

    st.markdown("---")
    st.subheader("📋 Tabla de Comparacion de Precios")

    # Preparar DataFrame para mostrar con formato
    df_display = df_comparacion.copy()
    df_display = df_display.rename(columns={
        "nombre": "Producto",
        "precio_empresa": f"Precio {NOMBRE_EMPRESA}",
        "precio_competidor": f"Precio {NOMBRE_COMPETIDOR}",
        "disponibilidad": "Disponibilidad",
        "diff_absoluta": "Dif. Absoluta ($)",
        "diff_porcentual": "Dif. Porcentual (%)",
    })

    def colorear_diferencia(val):
        """Aplica color segun el signo de la diferencia."""
        if isinstance(val, (int, float)):
            if val > 0:
                return "background-color: #ffcccc; color: #cc0000"  # rojo — somos mas caros
            elif val < 0:
                return "background-color: #ccffcc; color: #006600"  # verde — somos mas baratos
        return ""

    columnas_color = ["Dif. Absoluta ($)", "Dif. Porcentual (%)"]
    styled = df_display.style.map(
        colorear_diferencia,
        subset=columnas_color,
    ).format({
        f"Precio {NOMBRE_EMPRESA}": "${:.2f}",
        f"Precio {NOMBRE_COMPETIDOR}": "${:.2f}",
        "Dif. Absoluta ($)": "${:+.2f}",
        "Dif. Porcentual (%)": "{:+.2f}%",
    })

    st.dataframe(styled, use_container_width=True, hide_index=True)

    # ─── Tabla de alertas ──────────────────────────────────────────────────────

    st.markdown("---")
    st.subheader(f"🚨 Alertas — Productos con diferencia > {umbral_pct:.0f}%")

    if df_alertas.empty:
        st.success(
            f"Sin alertas activas: todos los precios son competitivos "
            f"(diferencia ≤ {umbral_pct:.0f}%)."
        )
    else:
        df_alertas_display = df_alertas.copy()
        df_alertas_display["perdida_mensual"] = (
            df_alertas_display["diff_absoluta"] * volumen_mensual
        ).round(2)
        df_alertas_display["urgencia"] = df_alertas_display["diff_porcentual"].apply(
            lambda x: "🔴 Critica (≥10%)" if x >= 10 else "🟠 Moderada"
        )

        df_alertas_display = df_alertas_display.rename(columns={
            "nombre": "Producto",
            "precio_empresa": f"Precio Nuestro",
            "precio_competidor": f"Precio Competidor",
            "diff_absoluta": "Dif. ($)",
            "diff_porcentual": "Dif. (%)",
            "perdida_mensual": "Perdida Est./Mes ($)",
            "urgencia": "Urgencia",
        })

        cols_alertas = [
            "Urgencia", "Producto", "Precio Nuestro", "Precio Competidor",
            "Dif. ($)", "Dif. (%)", "Perdida Est./Mes ($)",
        ]

        st.dataframe(
            df_alertas_display[cols_alertas].style.format({
                "Precio Nuestro": "${:.2f}",
                "Precio Competidor": "${:.2f}",
                "Dif. ($)": "${:+.2f}",
                "Dif. (%)": "{:+.1f}%",
                "Perdida Est./Mes ($)": "${:,.2f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

        # Resumen de urgencia
        criticos = (df_alertas["diff_porcentual"] >= 10).sum()
        moderados = len(df_alertas) - criticos
        st.info(
            f"**{len(df_alertas)} alertas**: {criticos} criticas (≥10%) y "
            f"{moderados} moderadas ({umbral_pct:.0f}%-9.9%)"
        )

    # ─── Graficos ──────────────────────────────────────────────────────────────

    st.markdown("---")
    st.subheader("📈 Analisis Visual")

    tab1, tab2, tab3 = st.tabs([
        "Distribucion de diferencias",
        "Impacto economico",
        "Comparativa de precios",
    ])

    # ── Tab 1: Distribucion de diferencias ─────────────────────────────────────
    with tab1:
        fig_hist = px.histogram(
            df_comparacion,
            x="diff_porcentual",
            nbins=15,
            title="Distribucion de Diferencias Porcentuales de Precio",
            labels={"diff_porcentual": "Diferencia Porcentual (%)"},
            color_discrete_sequence=["#636EFA"],
        )
        fig_hist.add_vline(
            x=0, line_dash="dash", line_color="gray",
            annotation_text="Precio igual", annotation_position="top left",
        )
        fig_hist.add_vline(
            x=umbral_pct, line_dash="dot", line_color="red",
            annotation_text=f"Umbral alerta ({umbral_pct:.0f}%)",
            annotation_position="top right",
        )
        fig_hist.add_vline(
            x=-umbral_pct, line_dash="dot", line_color="green",
            annotation_text=f"Ventaja ({umbral_pct:.0f}%)",
            annotation_position="top left",
        )
        fig_hist.update_layout(
            xaxis_title="Diferencia Porcentual (%)",
            yaxis_title="Cantidad de productos",
            bargap=0.1,
        )
        st.plotly_chart(fig_hist, use_container_width=True)

        st.caption(
            "Valores positivos = somos mas caros que el competidor. "
            "Valores negativos = somos mas baratos (ventaja competitiva)."
        )

    # ── Tab 2: Impacto economico ───────────────────────────────────────────────
    with tab2:
        if df_alertas.empty:
            st.info("No hay alertas activas, por lo que no se estima impacto economico.")
        else:
            df_impacto = df_alertas.copy()
            df_impacto["perdida_mensual"] = (
                df_impacto["diff_absoluta"] * volumen_mensual
            ).round(2)
            # Truncar nombres largos
            df_impacto["nombre_corto"] = df_impacto["nombre"].apply(
                lambda x: x[:40] + "..." if len(x) > 40 else x
            )
            df_impacto = df_impacto.sort_values("perdida_mensual", ascending=True)

            fig_impacto = px.bar(
                df_impacto,
                x="perdida_mensual",
                y="nombre_corto",
                orientation="h",
                title=f"Impacto Economico Estimado por Producto (a {volumen_mensual} uds/mes)",
                labels={
                    "perdida_mensual": "Perdida estimada mensual ($)",
                    "nombre_corto": "Producto",
                },
                color="diff_porcentual",
                color_continuous_scale="OrRd",
            )
            fig_impacto.update_layout(
                yaxis_title="",
                coloraxis_colorbar_title="Dif. %",
                height=max(400, len(df_impacto) * 50),
            )
            st.plotly_chart(fig_impacto, use_container_width=True)

            st.metric(
                "Perdida total estimada mensual",
                f"${perdida_total:,.2f} USD",
                delta=f"{len(df_alertas)} productos en alerta",
                delta_color="inverse",
            )

    # ── Tab 3: Comparativa lado a lado ─────────────────────────────────────────
    with tab3:
        df_comp = df_comparacion.copy()
        df_comp["nombre_corto"] = df_comp["nombre"].apply(
            lambda x: x[:40] + "..." if len(x) > 40 else x
        )
        df_comp = df_comp.sort_values("diff_porcentual", ascending=False)

        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            y=df_comp["nombre_corto"],
            x=df_comp["precio_empresa"],
            name=NOMBRE_EMPRESA,
            orientation="h",
            marker_color="#636EFA",
        ))
        fig_comp.add_trace(go.Bar(
            y=df_comp["nombre_corto"],
            x=df_comp["precio_competidor"],
            name=NOMBRE_COMPETIDOR,
            orientation="h",
            marker_color="#EF553B",
        ))
        fig_comp.update_layout(
            title="Comparativa de Precios: Empresa vs. Competidor",
            barmode="group",
            xaxis_title="Precio ($)",
            yaxis_title="",
            height=max(400, len(df_comp) * 55),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    # ─── Pie de pagina ─────────────────────────────────────────────────────────

    st.markdown("---")
    st.caption(
        "Demo #13 — Monitor de Precios de Competencia | "
        "Fuente: books.toscrape.com | "
        f"Productos analizados: {n_total} | "
        f"Umbral de alerta: {umbral_pct:.0f}%"
    )

else:
    # Estado inicial: instrucciones
    st.info(
        "👈 Configura los parametros en la barra lateral y presiona el boton "
        "para cargar los datos y ejecutar el analisis."
    )

    st.markdown("""
### Como funciona

1. **Configura** el umbral de alerta, volumen mensual y paginas en la barra lateral.
2. **Carga los datos** desde un CSV existente (modo demo, sin Playwright) o ejecuta el scraping real.
3. **Analiza** la tabla de comparacion, las alertas y los graficos interactivos.

### Flujo del pipeline

```
Scraping (Playwright)  →  Comparacion de precios  →  Deteccion de alertas
     o CSV existente        Cruce por nombre           Umbral configurable
```
""")

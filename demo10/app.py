"""
Interfaz web para el Cotizador Inteligente con IA.
Ejecutar con:  streamlit run app.py
"""

import os
import tempfile
import streamlit as st
from cotizador import (
    calcular_precio,
    generar_resumen,
    generar_pdf,
    TARIFAS_BASE,
)

# ──────────────────────────────────────────────
# Configuracion de pagina
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Cotizador Inteligente con IA",
    page_icon="📄",
    layout="centered",
)

st.title("Cotizador Inteligente con IA")
st.markdown(
    "Genera cotizaciones profesionales en PDF con un resumen comercial "
    "redactado por inteligencia artificial."
)

# ──────────────────────────────────────────────
# Resumen mock cuando no hay API key
# ──────────────────────────────────────────────

def _resumen_mock(nombre_cliente: str, tipo_servicio: str, precio: dict) -> str:
    """Devuelve un texto de ejemplo cuando la API de OpenAI no esta disponible."""
    return (
        f"Estimado equipo de {nombre_cliente}: nos complace presentarles nuestra "
        f"propuesta de servicios nivel {tipo_servicio}, disenada para maximizar "
        f"el retorno de su inversion. Con un equipo multidisciplinario de "
        f"especialistas y {precio['horas']} horas de trabajo dedicado, nuestro "
        f"enfoque combina metodologias agiles con las mejores practicas de la "
        f"industria para garantizar resultados medibles y sostenibles.\n\n"
        f"La inversion total de USD ${precio['precio_final']:,.2f} refleja un "
        f"compromiso firme con la calidad y la excelencia operativa. Cada etapa "
        f"del proyecto ha sido cuidadosamente planificada para entregar valor "
        f"tangible desde el primer dia. Quedamos a su entera disposicion para "
        f"resolver cualquier duda y avanzar con los siguientes pasos. Sera un "
        f"placer acompanarles en este camino hacia la transformacion."
    )


# ──────────────────────────────────────────────
# Formulario
# ──────────────────────────────────────────────
st.header("Datos de la cotizacion")

with st.form("form_cotizacion"):
    nombre_cliente = st.text_input(
        "Nombre del cliente",
        placeholder="Ej. Grupo Innova S.A.",
    )

    col1, col2 = st.columns(2)
    with col1:
        tipo_servicio = st.selectbox(
            "Tipo de servicio",
            options=list(TARIFAS_BASE.keys()),
        )
    with col2:
        horas_estimadas = st.number_input(
            "Horas estimadas",
            min_value=1,
            max_value=1000,
            value=40,
            step=1,
        )

    urgente = st.toggle("Urgencia alta (+20 % de recargo)")
    nivel_urgencia = "Alto" if urgente else "Normal"

    descripcion = st.text_area(
        "Descripcion del proyecto",
        placeholder="Describe brevemente el alcance del servicio solicitado...",
        height=100,
    )

    enviado = st.form_submit_button("Calcular cotizacion", use_container_width=True)

# ──────────────────────────────────────────────
# Procesamiento
# ──────────────────────────────────────────────
if enviado:
    if not nombre_cliente.strip():
        st.error("Por favor ingresa el nombre del cliente.")
        st.stop()

    # 1. Calcular precio
    precio = calcular_precio(tipo_servicio, int(horas_estimadas), nivel_urgencia)

    # 2. Desglose de precio
    st.header("Desglose de precio")

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Tarifa por hora", f"USD ${precio['tarifa_hora']:,.2f}")
        st.metric("Horas estimadas", f"{precio['horas']}")
        st.metric("Costo base", f"USD ${precio['costo_base']:,.2f}")
    with col_b:
        st.metric("Recargo por urgencia", f"USD ${precio['recargo']:,.2f}")
        st.metric("Subtotal", f"USD ${precio['subtotal']:,.2f}")
        st.metric("Margen operativo (30 %)", f"USD ${precio['ganancia']:,.2f}")

    st.divider()
    st.metric("TOTAL A PAGAR", f"USD ${precio['precio_final']:,.2f}")

    # 3. Resumen con IA (o mock)
    st.header("Resumen ejecutivo")

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key:
        with st.spinner("Generando resumen con inteligencia artificial..."):
            try:
                resumen = generar_resumen(nombre_cliente, tipo_servicio, precio)
            except Exception as e:
                st.warning(f"No se pudo generar el resumen con IA: {e}")
                resumen = _resumen_mock(nombre_cliente, tipo_servicio, precio)
    else:
        st.info(
            "No se detecto la variable OPENAI_API_KEY. "
            "Se utiliza un resumen de ejemplo para la demostracion."
        )
        resumen = _resumen_mock(nombre_cliente, tipo_servicio, precio)

    st.markdown(resumen)

    # 4. Generar PDF y ofrecer descarga
    st.header("Documento PDF")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        ruta_pdf = tmp.name

    generar_pdf(
        nombre_cliente=nombre_cliente,
        tipo_servicio=tipo_servicio,
        nivel_urgencia=nivel_urgencia,
        precio=precio,
        resumen=resumen,
        archivo=ruta_pdf,
    )

    with open(ruta_pdf, "rb") as f:
        contenido_pdf = f.read()

    # Limpiar archivo temporal
    try:
        os.unlink(ruta_pdf)
    except OSError:
        pass

    nombre_archivo = f"cotizacion_{nombre_cliente.strip().replace(' ', '_')}.pdf"

    st.download_button(
        label="Descargar PDF",
        data=contenido_pdf,
        file_name=nombre_archivo,
        mime="application/pdf",
        use_container_width=True,
    )

    st.success("Cotizacion generada exitosamente.")

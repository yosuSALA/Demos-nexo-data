"""
app.py -- Interfaz web Streamlit para el Bot de Envio Masivo de Reportes
=========================================================================
Envuelve la funcionalidad de email_bot.py y setup_mock_data.py en un
dashboard interactivo para visualizar clientes, generar datos de prueba,
enviar reportes y monitorear resultados.
"""

import streamlit as st
import pandas as pd
import smtplib
import logging
import io
import os
from pathlib import Path
from datetime import datetime

# Importar logica existente
from setup_mock_data import crear_csv, crear_pdfs_simulados, CLIENTES, CSV_PATH, REPORTES_DIR
from email_bot import (
    es_email_valido,
    construir_correo,
    abrir_conexion_smtp,
    REMITENTE,
    SMTP_HOST,
    SMTP_PORT,
    LOG_FILE,
)

# ---------------------------------------------------------------------------
# CONFIGURACION DE PAGINA
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Bot de Envio de Reportes",
    page_icon="📧",
    layout="wide",
)

# ---------------------------------------------------------------------------
# ESTADO DE SESION
# ---------------------------------------------------------------------------
if "log_mensajes" not in st.session_state:
    st.session_state.log_mensajes = []
if "resultados" not in st.session_state:
    st.session_state.resultados = None


# ---------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------------------------
def cargar_clientes() -> pd.DataFrame | None:
    """Carga el CSV de clientes si existe."""
    if Path(CSV_PATH).exists():
        return pd.read_csv(CSV_PATH, encoding="utf-8")
    return None


def verificar_pdfs(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega una columna indicando si el PDF existe."""
    df = df.copy()
    df["pdf_existe"] = df["nombre_archivo_pdf"].apply(
        lambda x: "Si" if (REPORTES_DIR / str(x).strip()).exists() else "No"
    )
    df["email_valido"] = df["correo"].apply(
        lambda x: "Si" if es_email_valido(str(x)) else "No"
    )
    return df


def agregar_log(mensaje: str):
    """Agrega un mensaje al registro de la sesion."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_mensajes.append(f"[{timestamp}] {mensaje}")


def ejecutar_envio_masivo() -> dict:
    """
    Ejecuta el envio masivo reutilizando la logica de email_bot.py.
    Devuelve un diccionario con estadisticas y detalles por cliente.
    """
    resultados = {
        "total": 0,
        "enviados": 0,
        "errores": 0,
        "detalles": [],
    }

    # Cargar CSV
    try:
        df = pd.read_csv(CSV_PATH, encoding="utf-8")
    except FileNotFoundError:
        agregar_log("ERROR: No se encontro el CSV. Genera los datos primero.")
        return resultados

    columnas_requeridas = {"id_cliente", "nombre", "correo", "nombre_archivo_pdf"}
    if not columnas_requeridas.issubset(df.columns):
        agregar_log("ERROR: El CSV no tiene las columnas esperadas.")
        return resultados

    resultados["total"] = len(df)
    agregar_log(f"Inicio de envio masivo -- {len(df)} destinatarios")

    # Conexion SMTP
    try:
        smtp = abrir_conexion_smtp()
        agregar_log(f"Conexion SMTP establecida: {SMTP_HOST}:{SMTP_PORT}")
    except Exception as e:
        agregar_log(f"ERROR CRITICO: No se pudo conectar al servidor SMTP: {e}")
        agregar_log("Asegurate de iniciar el servidor SMTP de debug:")
        agregar_log("  python -m smtpd -c DebuggingServer -n localhost:1025")
        return resultados

    # Enviar correos
    with smtp:
        for _, fila in df.iterrows():
            id_c = fila["id_cliente"]
            nombre = str(fila["nombre"]).strip()
            correo = str(fila["correo"]).strip()
            archivo = str(fila["nombre_archivo_pdf"]).strip()

            detalle = {
                "id": id_c,
                "nombre": nombre,
                "correo": correo,
                "estado": "",
                "motivo": "",
            }

            # Validacion de correo
            if not es_email_valido(correo):
                detalle["estado"] = "Error"
                detalle["motivo"] = "Correo invalido"
                resultados["errores"] += 1
                agregar_log(f"[{id_c}] {nombre} -- OMITIDO: correo invalido '{correo}'")
                resultados["detalles"].append(detalle)
                continue

            # Validacion de PDF
            ruta_pdf = REPORTES_DIR / archivo
            if not ruta_pdf.exists():
                detalle["estado"] = "Error"
                detalle["motivo"] = "PDF no encontrado"
                resultados["errores"] += 1
                agregar_log(f"[{id_c}] {nombre} -- OMITIDO: PDF no encontrado '{archivo}'")
                resultados["detalles"].append(detalle)
                continue

            # Construir y enviar
            try:
                msg = construir_correo(nombre, correo, ruta_pdf)
                smtp.sendmail(REMITENTE, correo, msg.as_string())
                detalle["estado"] = "Enviado"
                detalle["motivo"] = "OK"
                resultados["enviados"] += 1
                agregar_log(f"[{id_c}] {nombre} -- ENVIADO a {correo}")
            except smtplib.SMTPRecipientsRefused:
                detalle["estado"] = "Error"
                detalle["motivo"] = "Destinatario rechazado"
                resultados["errores"] += 1
                agregar_log(f"[{id_c}] {nombre} -- ERROR: destinatario rechazado")
            except smtplib.SMTPException as e:
                detalle["estado"] = "Error"
                detalle["motivo"] = f"Error SMTP: {e}"
                resultados["errores"] += 1
                agregar_log(f"[{id_c}] {nombre} -- ERROR SMTP: {e}")
            except Exception as e:
                detalle["estado"] = "Error"
                detalle["motivo"] = f"Error inesperado: {e}"
                resultados["errores"] += 1
                agregar_log(f"[{id_c}] {nombre} -- ERROR inesperado: {e}")

            resultados["detalles"].append(detalle)

    agregar_log(
        f"Envio finalizado: {resultados['enviados']} enviados, "
        f"{resultados['errores']} errores, {resultados['total']} total"
    )
    return resultados


# ---------------------------------------------------------------------------
# INTERFAZ PRINCIPAL
# ---------------------------------------------------------------------------
st.title("Bot de Envio Masivo de Reportes")
st.markdown("Dashboard para la distribucion de estados de cuenta mensuales con PDF adjunto.")
st.divider()

# ---------------------------------------------------------------------------
# BARRA LATERAL -- Configuracion y acciones
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Configuracion SMTP")
    st.code(f"Host: {SMTP_HOST}\nPuerto: {SMTP_PORT}", language="text")
    st.caption(f"Remitente: {REMITENTE}")

    st.divider()

    st.header("Acciones")

    # Boton para generar datos de prueba
    if st.button("Generar datos de prueba", use_container_width=True):
        crear_csv()
        crear_pdfs_simulados()
        agregar_log("Datos de prueba generados correctamente.")
        st.success("Datos de prueba generados.")
        st.rerun()

    st.divider()

    # Informacion de archivos
    csv_existe = Path(CSV_PATH).exists()
    dir_existe = REPORTES_DIR.exists()
    num_pdfs = len(list(REPORTES_DIR.glob("*.pdf"))) if dir_existe else 0

    st.header("Estado de archivos")
    st.markdown(f"- **CSV de clientes:** {'Disponible' if csv_existe else 'No encontrado'}")
    st.markdown(f"- **Directorio reportes:** {'Disponible' if dir_existe else 'No encontrado'}")
    st.markdown(f"- **PDFs generados:** {num_pdfs}")

# ---------------------------------------------------------------------------
# PESTANAS PRINCIPALES
# ---------------------------------------------------------------------------
tab_clientes, tab_envio, tab_log = st.tabs([
    "Lista de Clientes",
    "Enviar Reportes",
    "Registro de Actividad",
])

# --- Pestana 1: Lista de Clientes ---
with tab_clientes:
    st.subheader("Clientes registrados")

    df = cargar_clientes()
    if df is not None:
        df_vista = verificar_pdfs(df)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total de clientes", len(df_vista))
        col2.metric("PDFs disponibles", len(df_vista[df_vista["pdf_existe"] == "Si"]))
        col3.metric("Correos validos", len(df_vista[df_vista["email_valido"] == "Si"]))

        st.dataframe(
            df_vista,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id_cliente": st.column_config.TextColumn("ID"),
                "nombre": st.column_config.TextColumn("Nombre"),
                "correo": st.column_config.TextColumn("Correo"),
                "nombre_archivo_pdf": st.column_config.TextColumn("Archivo PDF"),
                "pdf_existe": st.column_config.TextColumn("PDF Existe"),
                "email_valido": st.column_config.TextColumn("Email Valido"),
            },
        )
    else:
        st.warning(
            "No se encontro el archivo CSV de clientes. "
            "Usa el boton 'Generar datos de prueba' en la barra lateral."
        )

# --- Pestana 2: Enviar Reportes ---
with tab_envio:
    st.subheader("Envio masivo de reportes")

    if not Path(CSV_PATH).exists():
        st.warning("Genera los datos de prueba antes de enviar reportes.")
    else:
        st.info(
            f"Se enviaran correos a todos los clientes del CSV usando "
            f"el servidor SMTP en **{SMTP_HOST}:{SMTP_PORT}**.\n\n"
            f"Para modo local, asegurate de tener corriendo el servidor de debug:\n"
            f"`python -m smtpd -c DebuggingServer -n localhost:1025`"
        )

        if st.button("Enviar Reportes", type="primary", use_container_width=True):
            with st.spinner("Enviando correos..."):
                resultados = ejecutar_envio_masivo()
                st.session_state.resultados = resultados

    # Mostrar resultados si existen
    if st.session_state.resultados is not None:
        res = st.session_state.resultados
        st.divider()
        st.subheader("Resultados del envio")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", res["total"])
        col2.metric("Enviados", res["enviados"])
        col3.metric("Errores", res["errores"])
        tasa = (res["enviados"] / res["total"] * 100) if res["total"] > 0 else 0
        col4.metric("Tasa de exito", f"{tasa:.0f}%")

        if res["detalles"]:
            df_res = pd.DataFrame(res["detalles"])

            st.dataframe(
                df_res,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.TextColumn("ID"),
                    "nombre": st.column_config.TextColumn("Nombre"),
                    "correo": st.column_config.TextColumn("Correo"),
                    "estado": st.column_config.TextColumn("Estado"),
                    "motivo": st.column_config.TextColumn("Detalle"),
                },
            )

# --- Pestana 3: Registro de Actividad ---
with tab_log:
    st.subheader("Registro de actividad de la sesion")

    if st.session_state.log_mensajes:
        log_texto = "\n".join(st.session_state.log_mensajes)
        st.code(log_texto, language="text")

        if st.button("Limpiar registro"):
            st.session_state.log_mensajes = []
            st.rerun()
    else:
        st.info("Aun no hay actividad registrada en esta sesion.")

    # Mostrar archivo de log si existe
    st.divider()
    st.subheader("Archivo de log historico")
    if Path(LOG_FILE).exists():
        contenido_log = Path(LOG_FILE).read_text(encoding="utf-8")
        st.code(contenido_log, language="text")
    else:
        st.info(f"El archivo '{LOG_FILE}' se creara despues del primer envio.")

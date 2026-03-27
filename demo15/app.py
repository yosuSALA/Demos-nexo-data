# =============================================================================
# Demo #15 — Interfaz Streamlit para el Chatbot RAG de Nexo Data
# =============================================================================
# Ejecutar con:  streamlit run app.py
# =============================================================================

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from rag_chatbot import (
    BASE_DIR,
    DOCS_DIR,
    CHROMA_DIR,
    create_sample_pdfs,
    ingest_documents,
    build_qa_chain,
    ask,
)

# ── Configuracion de pagina ─────────────────────────────────────────────────

st.set_page_config(
    page_title="Nexo Data — Chatbot Interno",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Helpers ──────────────────────────────────────────────────────────────────

def _api_key_disponible() -> bool:
    """Verifica si la clave de API de OpenAI esta configurada."""
    return bool(os.environ.get("OPENAI_API_KEY"))


def _obtener_pdfs() -> list[Path]:
    """Devuelve la lista de PDFs en la carpeta de documentos."""
    if DOCS_DIR.exists():
        return sorted(DOCS_DIR.glob("*.pdf"))
    return []


def _vectorstore_existe() -> bool:
    """Verifica si el vectorstore ya fue creado."""
    return CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir())


def _respuesta_demo(pregunta: str) -> dict:
    """Genera una respuesta simulada para el modo demo."""
    respuestas_demo = {
        "vacaciones": (
            "**[Modo demo]** Segun la Politica de Vacaciones de Nexo Data, "
            "los dias de vacaciones dependen de la antiguedad del colaborador:\n\n"
            "- 1 ano: 10 dias habiles\n"
            "- 3 anos: 15 dias habiles\n"
            "- 5 anos: 20 dias habiles\n\n"
            "*Esta es una respuesta simulada. Configura la variable de entorno "
            "`OPENAI_API_KEY` para obtener respuestas reales basadas en tus documentos.*"
        ),
        "servidor": (
            "**[Modo demo]** Segun el Manual de Operaciones, la clave del servidor "
            "de desarrollo es 1234. El servidor de produccion requiere autenticacion "
            "multifactor (MFA).\n\n"
            "*Esta es una respuesta simulada. Configura `OPENAI_API_KEY` para "
            "respuestas reales.*"
        ),
        "onboarding": (
            "**[Modo demo]** Segun la Guia de Onboarding, en la segunda semana "
            "se asigna un buddy/mentor y se realiza el primer PR de practica.\n\n"
            "*Esta es una respuesta simulada. Configura `OPENAI_API_KEY` para "
            "respuestas reales.*"
        ),
        "despliegue": (
            "**[Modo demo]** Segun el Manual de Operaciones, los despliegues a "
            "produccion solo se realizan los martes y jueves entre las 10:00 y "
            "las 12:00 horas.\n\n"
            "*Esta es una respuesta simulada. Configura `OPENAI_API_KEY` para "
            "respuestas reales.*"
        ),
    }

    pregunta_lower = pregunta.lower()
    for clave, respuesta in respuestas_demo.items():
        if clave in pregunta_lower:
            return {"answer": respuesta, "sources": ["documento_ejemplo.pdf"]}

    return {
        "answer": (
            "**[Modo demo]** He recibido tu pregunta. En modo completo, el "
            "sistema buscaria en los documentos internos de Nexo Data para "
            "darte una respuesta precisa con fuentes.\n\n"
            "*Para habilitar respuestas reales, configura la variable de entorno "
            "`OPENAI_API_KEY` con tu clave de API de OpenAI y reinicia la aplicacion.*"
        ),
        "sources": ["modo_demo.pdf"],
    }


# ── Estado de sesion ─────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chain" not in st.session_state:
    st.session_state.chain = None

if "vectorstore_listo" not in st.session_state:
    st.session_state.vectorstore_listo = False

# ── Barra lateral ────────────────────────────────────────────────────────────

with st.sidebar:
    st.image(
        "https://img.icons8.com/fluency/96/building.png",
        width=64,
    )
    st.title("Nexo Data")
    st.caption("Chatbot de Consultas Internas")

    st.divider()

    # -- Estado de la API --
    modo_demo = not _api_key_disponible()
    if modo_demo:
        st.warning(
            "**Modo demo activo.**\n\n"
            "No se detecto `OPENAI_API_KEY`. Las respuestas seran simuladas. "
            "Configura la variable de entorno para usar el modelo real.",
            icon="⚠️",
        )
    else:
        st.success("API Key de OpenAI detectada.", icon="✅")

    st.divider()

    # -- Documentos --
    st.subheader("📄 Documentos")
    pdfs = _obtener_pdfs()
    if pdfs:
        for pdf in pdfs:
            st.markdown(f"- `{pdf.name}`")
    else:
        st.info("No hay documentos en la carpeta.", icon="📁")

    if st.button("📝 Generar PDFs de ejemplo", use_container_width=True):
        with st.spinner("Generando documentos de prueba..."):
            create_sample_pdfs()
        st.success("PDFs de ejemplo creados correctamente.")
        st.rerun()

    st.divider()

    # -- Base de conocimiento --
    st.subheader("🧠 Base de conocimiento")

    if _vectorstore_existe():
        st.success("Vectorstore activo.", icon="✅")
        st.session_state.vectorstore_listo = True
    else:
        st.info("El vectorstore no ha sido creado.", icon="💾")

    btn_disabled = len(pdfs) == 0
    btn_help = "Primero genera o agrega PDFs a la carpeta documentos/" if btn_disabled else None
    if st.button(
        "🚀 Inicializar base de conocimiento",
        use_container_width=True,
        disabled=btn_disabled or modo_demo,
        help=btn_help if btn_disabled else (
            "No disponible en modo demo (se requiere OPENAI_API_KEY)" if modo_demo else None
        ),
    ):
        with st.spinner("Procesando documentos e indexando en ChromaDB..."):
            try:
                ingest_documents()
                st.session_state.chain = build_qa_chain()
                st.session_state.vectorstore_listo = True
                st.success("Base de conocimiento lista.")
                st.rerun()
            except Exception as e:
                st.error(f"Error durante la ingesta: {e}")

    # Cargar cadena existente si hay vectorstore pero no chain
    if (
        st.session_state.chain is None
        and _vectorstore_existe()
        and not modo_demo
    ):
        try:
            st.session_state.chain = build_qa_chain()
            st.session_state.vectorstore_listo = True
        except Exception:
            pass

    st.divider()

    if st.button("🗑️ Limpiar historial", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("Demo #15 — RAG con LangChain + ChromaDB")


# ── Area principal del chat ──────────────────────────────────────────────────

st.title("💬 Chatbot de Consultas Internas")

if modo_demo:
    st.info(
        "**Modo demo:** Las respuestas son simuladas. "
        "Configura la variable de entorno `OPENAI_API_KEY` para habilitar "
        "el motor RAG completo.",
        icon="ℹ️",
    )
elif not st.session_state.vectorstore_listo:
    st.info(
        "Inicializa la base de conocimiento desde la barra lateral "
        "para comenzar a hacer preguntas.",
        icon="ℹ️",
    )

# -- Historial de mensajes --
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            st.caption(f"📄 Fuentes: {', '.join(msg['sources'])}")

# -- Entrada del usuario --
if pregunta := st.chat_input("Escribe tu pregunta sobre los documentos internos..."):
    # Mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    # Generar respuesta
    with st.chat_message("assistant"):
        with st.spinner("Consultando documentos..."):
            if modo_demo:
                resultado = _respuesta_demo(pregunta)
            elif st.session_state.chain is not None:
                try:
                    resultado = ask(pregunta, chain=st.session_state.chain)
                except Exception as e:
                    resultado = {
                        "answer": f"Error al consultar: {e}",
                        "sources": [],
                    }
            else:
                resultado = {
                    "answer": (
                        "La base de conocimiento no esta inicializada. "
                        "Usa el boton de la barra lateral para cargarla."
                    ),
                    "sources": [],
                }

        st.markdown(resultado["answer"])
        if resultado.get("sources"):
            st.caption(f"📄 Fuentes: {', '.join(resultado['sources'])}")

    # Guardar en historial
    st.session_state.messages.append({
        "role": "assistant",
        "content": resultado["answer"],
        "sources": resultado.get("sources", []),
    })

# =============================================================================
# Demo #15 — Chatbot de Consultas Internas con IA (Nexo Data)
# =============================================================================
# Dependencias:
#   pip install langchain langchain-openai langchain-community chromadb pypdf fpdf2
#
# Variables de entorno requeridas:
#   OPENAI_API_KEY  — tu clave de API de OpenAI
# =============================================================================

from __future__ import annotations

import os
import shutil
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ── Rutas por defecto ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "documentos"
CHROMA_DIR = BASE_DIR / "vectorstore"


# =============================================================================
# 1. Ingesta de documentos
# =============================================================================

def ingest_documents(
    docs_folder: str | Path = DOCS_DIR,
    vectorstore_path: str | Path = CHROMA_DIR,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> Chroma:
    """Lee todos los PDFs de *docs_folder*, los fragmenta y los almacena en ChromaDB."""

    docs_folder = Path(docs_folder)
    vectorstore_path = Path(vectorstore_path)

    # Cargar todos los PDFs
    pdf_files = sorted(docs_folder.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No se encontraron PDFs en {docs_folder}")

    all_docs = []
    for pdf in pdf_files:
        loader = PyPDFLoader(str(pdf))
        all_docs.extend(loader.load())

    # Fragmentar
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(all_docs)
    print(f"[ingesta] {len(pdf_files)} PDF(s) → {len(chunks)} fragmentos")

    # Crear / sobrescribir vectorstore
    if vectorstore_path.exists():
        shutil.rmtree(vectorstore_path)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(vectorstore_path),
    )
    print(f"[ingesta] Vectorstore guardado en {vectorstore_path}")
    return vectorstore


# =============================================================================
# 2. Datos de prueba (PDFs simulados)
# =============================================================================

def create_sample_pdfs(output_folder: str | Path = DOCS_DIR) -> None:
    """Genera PDFs falsos para probar el pipeline sin documentos reales."""

    from fpdf import FPDF  # fpdf2

    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    documents = {
        "Politica_de_Vacaciones_NexoData.pdf": (
            "Política de Vacaciones — Nexo Data\n\n"
            "Artículo 1. Todo colaborador con al menos 1 año de antigüedad tiene "
            "derecho a 10 días hábiles de vacaciones al año.\n\n"
            "Artículo 2. A partir de los 3 años de antigüedad, el período se "
            "incrementa a 15 días hábiles.\n\n"
            "Artículo 3. A partir de los 5 años de antigüedad, el período se "
            "incrementa a 20 días hábiles.\n\n"
            "Artículo 4. Las vacaciones deben solicitarse con al menos 15 días "
            "de anticipación a través del sistema interno de RRHH.\n\n"
            "Artículo 5. No se permite acumular más de 5 días de un período "
            "al siguiente sin autorización escrita del jefe directo."
        ),
        "Manual_de_Operaciones_NexoData.pdf": (
            "Manual de Operaciones — Nexo Data\n\n"
            "Sección 1: Acceso a servidores\n"
            "La clave de acceso al servidor principal de desarrollo es 1234. "
            "El servidor de producción requiere autenticación multifactor (MFA) "
            "y la solicitud de acceso debe ser aprobada por el líder de equipo.\n\n"
            "Sección 2: Horarios de despliegue\n"
            "Los despliegues a producción solo se realizan los martes y jueves "
            "entre las 10:00 y las 12:00 horas. Cualquier despliegue fuera de "
            "ventana requiere aprobación del CTO.\n\n"
            "Sección 3: Incidentes\n"
            "En caso de incidente crítico, se debe notificar al canal #ops-alerts "
            "de Slack y registrar un ticket en Jira con prioridad P1 dentro de "
            "los primeros 15 minutos."
        ),
        "Guia_de_Onboarding_NexoData.pdf": (
            "Guía de Onboarding — Nexo Data\n\n"
            "Día 1: Configuración de equipo, cuentas de correo y Slack.\n\n"
            "Día 2: Reunión con el equipo asignado y revisión de objetivos "
            "del primer mes.\n\n"
            "Día 3-5: Capacitación sobre las herramientas internas: Jira, "
            "Confluence, GitHub y el sistema de RRHH.\n\n"
            "Semana 2: Asignación de un buddy/mentor y primer PR de práctica.\n\n"
            "Al finalizar el primer mes, el colaborador debe completar la "
            "evaluación inicial de onboarding en el sistema de RRHH."
        ),
    }

    for filename, content in documents.items():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Helvetica", size=11)
        for line in content.split("\n"):
            pdf.multi_cell(0, 6, line)
        pdf.output(str(output_folder / filename))

    print(f"[setup] {len(documents)} PDF(s) creados en {output_folder}")


# =============================================================================
# 3. Motor de Pregunta y Respuesta
# =============================================================================

_QA_PROMPT_TEMPLATE = """\
Eres un asistente interno de Nexo Data. Responde la pregunta del usuario \
usando EXCLUSIVAMENTE la información que aparece en el contexto proporcionado.

Reglas:
- Si la respuesta está en el contexto, respóndela de forma clara y concisa.
- Al final de tu respuesta, cita la(s) fuente(s) indicando el nombre del archivo PDF.
- Si la información NO está en el contexto, responde exactamente: \
"No tengo información suficiente en los documentos disponibles para responder esa pregunta."

Contexto:
{context}

Pregunta: {question}

Respuesta:"""

QA_PROMPT = PromptTemplate(
    template=_QA_PROMPT_TEMPLATE,
    input_variables=["context", "question"],
)


def build_qa_chain(
    vectorstore_path: str | Path = CHROMA_DIR,
    model_name: str = "gpt-3.5-turbo",
    k: int = 4,
) -> dict:
    """Construye la cadena de QA sobre el vectorstore existente."""

    vectorstore_path = Path(vectorstore_path)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        persist_directory=str(vectorstore_path),
        embedding_function=embeddings,
    )

    llm = ChatOpenAI(model=model_name, temperature=0)
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})

    def _format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | QA_PROMPT
        | llm
        | StrOutputParser()
    )
    return {"chain": chain, "retriever": retriever}


def ask(question: str, chain: dict | None = None) -> dict:
    """Hace una pregunta y devuelve {'answer': str, 'sources': list[str]}."""

    if chain is None:
        chain = build_qa_chain()

    docs = chain["retriever"].invoke(question)
    answer = chain["chain"].invoke(question)

    sources = sorted(
        {Path(doc.metadata.get("source", "desconocido")).name for doc in docs}
    )

    return {
        "answer": answer,
        "sources": sources,
    }


# =============================================================================
# 4. Punto de entrada — demo interactiva
# =============================================================================

def setup() -> dict:
    """Crea los PDFs de prueba, ingesta y devuelve la cadena QA lista."""
    create_sample_pdfs()
    ingest_documents()
    return build_qa_chain()


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠  Configura la variable de entorno OPENAI_API_KEY antes de ejecutar.")
        return

    print("=" * 60)
    print("  Nexo Data — Chatbot de Consultas Internas (Demo #15)")
    print("=" * 60)

    chain = setup()

    sample_questions = [
        "¿Cuántos días de vacaciones me corresponden si tengo 3 años?",
        "¿Cuál es la clave del servidor de desarrollo?",
        "¿Qué pasa en la segunda semana de onboarding?",
        "¿Cuál es el horario permitido para despliegues a producción?",
    ]

    print("\n── Preguntas de ejemplo ──\n")
    for q in sample_questions:
        print(f"🔹 {q}")
        result = ask(q, chain=chain)
        print(f"   {result['answer']}")
        print(f"   📄 Fuentes: {', '.join(result['sources'])}\n")

    # Modo interactivo
    print("── Modo interactivo (escribe 'salir' para terminar) ──\n")
    while True:
        question = input("Tu pregunta: ").strip()
        if not question or question.lower() in ("salir", "exit", "quit"):
            print("¡Hasta luego!")
            break
        result = ask(question, chain=chain)
        print(f"\n{result['answer']}")
        print(f"📄 Fuentes: {', '.join(result['sources'])}\n")


if __name__ == "__main__":
    main()

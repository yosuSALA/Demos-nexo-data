# Demo #15 — Chatbot de Consultas Internas con IA

## Descripcion

Chatbot de consulta interna basado en **RAG (Retrieval-Augmented Generation)** para la empresa ficticia **Nexo Data**. Permite a los colaboradores hacer preguntas en lenguaje natural sobre documentos internos (politicas, manuales, guias) y obtener respuestas precisas con citas a las fuentes originales.

## Tecnologias

| Componente | Tecnologia |
|---|---|
| Interfaz web | Streamlit |
| Orquestacion LLM | LangChain |
| Modelo de lenguaje | OpenAI GPT-3.5-turbo |
| Embeddings | OpenAI text-embedding-3-small |
| Base vectorial | ChromaDB |
| Lectura de PDFs | pypdf |
| Generacion de PDFs de prueba | fpdf2 |

## Estructura del proyecto

```
demo15/
├── app.py                 # Interfaz web con Streamlit
├── rag_chatbot.py         # Logica RAG (ingesta, vectorstore, cadena QA)
├── requirements.txt       # Dependencias de Python
├── README.md              # Este archivo
├── documentos/            # PDFs de entrada (se generan automaticamente)
└── vectorstore/           # Base vectorial ChromaDB (se genera automaticamente)
```

## Instalacion

```bash
pip install -r requirements.txt
```

## Configuracion

Establece tu clave de API de OpenAI como variable de entorno:

```bash
# Linux / macOS
export OPENAI_API_KEY="sk-..."

# Windows (PowerShell)
$env:OPENAI_API_KEY = "sk-..."
```

Si no se configura la clave, la aplicacion se ejecuta en **modo demo** con respuestas simuladas para que puedas explorar la interfaz.

## Ejecucion

### Interfaz web (recomendado)

```bash
streamlit run app.py
```

### Linea de comandos

```bash
python rag_chatbot.py
```

## Uso

1. Abre la aplicacion en el navegador (por defecto `http://localhost:8501`).
2. Si no existen documentos, usa el boton **"Generar PDFs de ejemplo"** en la barra lateral.
3. Haz clic en **"Inicializar base de conocimiento"** para procesar los documentos.
4. Escribe tu pregunta en el chat y recibe la respuesta con las fuentes citadas.

## Preguntas de ejemplo

- Cuantos dias de vacaciones me corresponden si tengo 3 anos?
- Cual es la clave del servidor de desarrollo?
- Que pasa en la segunda semana de onboarding?
- Cual es el horario permitido para despliegues a produccion?

## Modo demo

Cuando no se detecta la variable `OPENAI_API_KEY`, el chatbot funciona en modo demo:

- La interfaz es completamente funcional.
- Las respuestas son simuladas e indican que se necesita la clave de API para obtener respuestas reales.
- Permite explorar la interfaz y el flujo sin incurrir en costos de API.

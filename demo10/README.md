# Demo #10 -- Cotizador Inteligente con IA

## Descripcion

Aplicacion web que genera cotizaciones profesionales en PDF con un resumen comercial redactado por inteligencia artificial (OpenAI). Incluye una interfaz grafica construida con Streamlit que permite ingresar los datos del cliente, visualizar el desglose de precios y descargar el documento generado.

## Funcionalidades

- **Formulario de entrada**: nombre del cliente, tipo de servicio (Basico / Estandar / Premium), horas estimadas, nivel de urgencia y descripcion del proyecto.
- **Motor de precios**: calcula tarifa base, recargo por urgencia (20 %) y margen operativo (30 %).
- **Resumen con IA**: genera un resumen ejecutivo persuasivo mediante la API de OpenAI (modelo gpt-4o-mini). Si no se configura la clave de API, la aplicacion funciona con un texto de ejemplo para fines de demostracion.
- **Generacion de PDF**: crea un documento PDF profesional con los datos del cliente, el resumen ejecutivo y el desglose de inversion.
- **Descarga directa**: boton para descargar el PDF desde la interfaz web.

## Requisitos

- Python 3.10 o superior
- Dependencias listadas en `requirements.txt`

## Instalacion

```bash
pip install -r requirements.txt
```

## Configuracion

Para utilizar la generacion de resumen con IA, define la variable de entorno con tu clave de OpenAI:

```bash
export OPENAI_API_KEY="sk-tu-clave-aqui"
```

En Windows (PowerShell):

```powershell
$env:OPENAI_API_KEY = "sk-tu-clave-aqui"
```

Si no se configura la clave, la aplicacion seguira funcionando con un resumen de ejemplo.

## Ejecucion

### Interfaz web (Streamlit)

```bash
streamlit run app.py
```

### Linea de comandos

```bash
python cotizador.py
```

## Estructura del proyecto

```
demo10/
  cotizador.py       # Logica principal: motor de precios, generacion de resumen con IA y creacion de PDF
  app.py             # Interfaz web con Streamlit
  requirements.txt   # Dependencias del proyecto
  README.md          # Este archivo
```

## Tecnologias utilizadas

- [Streamlit](https://streamlit.io/) -- Interfaz web interactiva
- [OpenAI API](https://platform.openai.com/) -- Generacion de texto con IA
- [FPDF2](https://py-pdf.github.io/fpdf2/) -- Creacion de documentos PDF

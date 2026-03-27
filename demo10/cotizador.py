"""
Demo #10 — Cotizador Inteligente con IA
========================================
Genera cotizaciones profesionales en PDF con resumen comercial redactado por IA.

Dependencias:
    pip install openai fpdf

Configuración:
    Variable de entorno OPENAI_API_KEY con tu clave de OpenAI.
"""

import os
from datetime import date
from openai import OpenAI
from fpdf import FPDF


# ──────────────────────────────────────────────
# 1. Motor de Precios
# ──────────────────────────────────────────────

TARIFAS_BASE = {
    "Básico":   50,   # USD/hora
    "Estándar": 80,
    "Premium":  120,
}

RECARGO_URGENCIA = 0.20   # +20 %
MARGEN_GANANCIA  = 0.30   # +30 %


def calcular_precio(tipo_servicio: str, horas_estimadas: int, nivel_urgencia: str) -> dict:
    """Devuelve un diccionario con el desglose completo del precio."""
    tarifa = TARIFAS_BASE.get(tipo_servicio)
    if tarifa is None:
        raise ValueError(f"Tipo de servicio desconocido: {tipo_servicio}")

    costo_base = tarifa * horas_estimadas

    recargo = costo_base * RECARGO_URGENCIA if nivel_urgencia == "Alto" else 0.0
    subtotal = costo_base + recargo

    ganancia = subtotal * MARGEN_GANANCIA
    precio_final = subtotal + ganancia

    return {
        "tarifa_hora":    tarifa,
        "horas":          horas_estimadas,
        "costo_base":     costo_base,
        "recargo":        recargo,
        "subtotal":       subtotal,
        "ganancia":       ganancia,
        "precio_final":   round(precio_final, 2),
    }


# ──────────────────────────────────────────────
# 2. Generación de Texto Comercial con IA
# ──────────────────────────────────────────────

def generar_resumen(nombre_cliente: str, tipo_servicio: str, precio: dict) -> str:
    """Llama a OpenAI para redactar un resumen ejecutivo persuasivo."""
    client = OpenAI()  # usa OPENAI_API_KEY del entorno

    prompt = (
        f"Eres un redactor comercial senior de una agencia de consultoría tecnológica. "
        f"Redacta un Resumen Ejecutivo persuasivo de exactamente 2 párrafos dirigido a "
        f"'{nombre_cliente}'. El servicio ofrecido es de nivel '{tipo_servicio}', "
        f"contempla {precio['horas']} horas de trabajo y tiene un precio final de "
        f"USD ${precio['precio_final']:,.2f}. "
        f"Explica el valor del servicio, justifica la inversión y cierra con un "
        f"llamado a la acción. Usa un tono profesional pero cercano. Responde solo "
        f"con el texto del resumen, sin títulos ni encabezados."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()


# ──────────────────────────────────────────────
# 3. Generador de PDF
# ──────────────────────────────────────────────

class PDFCotizacion(FPDF):
    """PDF con encabezado y pie de página personalizados."""

    def header(self):
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(30, 60, 120)
        self.cell(0, 12, "Cotización de Servicios", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(30, 60, 120)
        self.set_line_width(0.6)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Página {self.page_no()} | Generado el {date.today():%d/%m/%Y}",
                  align="C")


def _seccion(pdf: FPDF, titulo: str):
    """Imprime un subtítulo con estilo."""
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 60, 120)
    pdf.cell(0, 10, titulo, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def _fila_tabla(pdf: FPDF, concepto: str, valor: str, bold: bool = False):
    """Dibuja una fila de la tabla de desglose."""
    estilo = "B" if bold else ""
    pdf.set_font("Helvetica", estilo, 11)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(120, 8, concepto, border="B")
    pdf.cell(0, 8, valor, border="B", align="R", new_x="LMARGIN", new_y="NEXT")


def generar_pdf(
    nombre_cliente: str,
    tipo_servicio: str,
    nivel_urgencia: str,
    precio: dict,
    resumen: str,
    archivo: str = "cotizacion_cliente.pdf",
) -> str:
    """Genera el PDF y devuelve la ruta del archivo creado."""
    pdf = PDFCotizacion()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # — Datos del cliente —
    _seccion(pdf, "Datos del Cliente")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 7, f"Cliente:   {nombre_cliente}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Servicio:  {tipo_servicio}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Urgencia:  {nivel_urgencia}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Fecha:     {date.today():%d/%m/%Y}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # — Resumen Ejecutivo (IA) —
    _seccion(pdf, "Resumen Ejecutivo")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 6, resumen)
    pdf.ln(6)

    # — Desglose de Precio —
    _seccion(pdf, "Desglose de Inversión")
    _fila_tabla(pdf, f"Tarifa por hora ({tipo_servicio})", f"${precio['tarifa_hora']:,.2f}")
    _fila_tabla(pdf, f"Horas estimadas", f"{precio['horas']}")
    _fila_tabla(pdf, "Costo base", f"${precio['costo_base']:,.2f}")
    if precio["recargo"] > 0:
        _fila_tabla(pdf, "Recargo por urgencia (20 %)", f"${precio['recargo']:,.2f}")
    _fila_tabla(pdf, "Subtotal", f"${precio['subtotal']:,.2f}")
    _fila_tabla(pdf, "Margen operativo (30 %)", f"${precio['ganancia']:,.2f}")
    pdf.ln(2)
    _fila_tabla(pdf, "TOTAL A PAGAR", f"USD ${precio['precio_final']:,.2f}", bold=True)

    pdf.output(archivo)
    return os.path.abspath(archivo)


# ──────────────────────────────────────────────
# 4. Orquestador
# ──────────────────────────────────────────────

if __name__ == "__main__":
    # Datos de prueba
    nombre_cliente  = "Grupo Innova S.A."
    tipo_servicio   = "Premium"
    horas_estimadas = 40
    nivel_urgencia  = "Alto"

    # Paso 1 — Calcular precio
    print("▸ Calculando precio...")
    precio = calcular_precio(tipo_servicio, horas_estimadas, nivel_urgencia)
    print(f"  Precio final: USD ${precio['precio_final']:,.2f}")

    # Paso 2 — Generar resumen con IA
    print("▸ Generando resumen comercial con IA...")
    try:
        resumen = generar_resumen(nombre_cliente, tipo_servicio, precio)
    except Exception as e:
        print(f"  ⚠ Error al llamar a OpenAI: {e}")
        resumen = (
            f"Estimado equipo de {nombre_cliente}: nos complace presentarles nuestra "
            f"propuesta de servicios nivel {tipo_servicio}, diseñada para maximizar "
            f"el retorno de su inversión.\n\n"
            f"Con {horas_estimadas} horas de consultoría especializada y un equipo "
            f"comprometido con la excelencia, garantizamos resultados medibles que "
            f"justifican cada dólar invertido. Quedamos a su disposición para avanzar."
        )

    # Paso 3 — Generar PDF
    print("▸ Generando PDF...")
    ruta = generar_pdf(nombre_cliente, tipo_servicio, nivel_urgencia, precio, resumen)
    print(f"  ✔ PDF generado: {ruta}")

"""
setup_mock_data.py
Genera datos de prueba: CSV de clientes y PDFs simulados en /reportes_mensuales
"""

import csv
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
CSV_PATH = "clientes_reportes.csv"
REPORTES_DIR = Path("reportes_mensuales")

CLIENTES = [
    ("C001", "Andrés Martínez",    "andres.martinez@correo-demo.com",   "reporte_001.pdf"),
    ("C002", "Lucía Fernández",    "lucia.fernandez@correo-demo.com",   "reporte_002.pdf"),
    ("C003", "Carlos Herrera",     "carlos.herrera@correo-demo.com",    "reporte_003.pdf"),
    ("C004", "Sofía Ramírez",      "sofia.ramirez@correo-demo.com",     "reporte_004.pdf"),
    ("C005", "Miguel Torres",      "miguel.torres@correo-demo.com",     "reporte_005.pdf"),
    ("C006", "Valeria Gómez",      "valeria.gomez@correo-demo.com",     "reporte_006.pdf"),
    ("C007", "Ricardo López",      "ricardo.lopez@correo-demo.com",     "reporte_007.pdf"),
    ("C008", "Daniela Vargas",     "daniela.vargas@correo-demo.com",    "reporte_008.pdf"),
    ("C009", "Sebastián Castro",   "sebastian.castro@correo-demo.com",  "reporte_009.pdf"),
    ("C010", "Natalia Moreno",     "natalia.moreno@correo-demo.com",    "reporte_010.pdf"),
    ("C011", "Felipe Ruiz",        "felipe.ruiz@correo-demo.com",       "reporte_011.pdf"),
    ("C012", "Camila Díaz",        "camila.diaz@correo-demo.com",       "reporte_012.pdf"),
    ("C013", "Javier Mendoza",     "javier.mendoza@correo-demo.com",    "reporte_013.pdf"),
    ("C014", "Isabella Ríos",      "isabella.rios@correo-demo.com",     "reporte_014.pdf"),
    ("C015", "Tomás Aguirre",      "tomas.aguirre@correo-demo.com",     "reporte_015.pdf"),
    ("C016", "Mariana Salcedo",    "mariana.salcedo@correo-demo.com",   "reporte_016.pdf"),
    ("C017", "Diego Pizarro",      "diego.pizarro@correo-demo.com",     "reporte_017.pdf"),
    ("C018", "Laura Bustamante",   "laura.bustamante@correo-demo.com",  "reporte_018.pdf"),
    # Fila con correo inválido (para demostrar manejo de errores)
    ("C019", "Ernesto Blanco",     "correo-invalido-sin-arroba",        "reporte_019.pdf"),
    # Fila con PDF faltante (para demostrar manejo de errores)
    ("C020", "Patricia Mora",      "patricia.mora@correo-demo.com",     "reporte_999_FALTANTE.pdf"),
]


def crear_csv():
    """Escribe clientes_reportes.csv con los 20 registros de prueba."""
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id_cliente", "nombre", "correo", "nombre_archivo_pdf"])
        writer.writerows(CLIENTES)
    print(f"[OK] CSV creado: {CSV_PATH}  ({len(CLIENTES)} registros)")


def crear_pdfs_simulados():
    """
    Crea PDFs simulados en /reportes_mensuales.
    Son archivos de texto con extensión .pdf — suficiente para la demo.
    En producción estos serían PDFs reales generados por otro proceso.
    """
    REPORTES_DIR.mkdir(exist_ok=True)

    # Creamos los 19 primeros (el reporte_999 se omite a propósito → error demo)
    for cliente in CLIENTES[:-1]:
        id_c, nombre, _, archivo = cliente
        ruta = REPORTES_DIR / archivo
        ruta.write_text(
            f"REPORTE MENSUAL\n"
            f"================\n"
            f"Cliente  : {nombre}\n"
            f"ID       : {id_c}\n"
            f"Período  : Marzo 2026\n\n"
            f"[Contenido del estado de cuenta simulado]\n",
            encoding="utf-8",
        )

    creados = len(list(REPORTES_DIR.glob("*.pdf")))
    print(f"[OK] PDFs simulados creados en '{REPORTES_DIR}/'  ({creados} archivos)")
    print(f"[INFO] 'reporte_999_FALTANTE.pdf' NO fue creado → se usará para demostrar el manejo de errores.")


if __name__ == "__main__":
    crear_csv()
    crear_pdfs_simulados()
    print("\n[LISTO] Datos de prueba generados. Ejecuta ahora: python email_bot.py")

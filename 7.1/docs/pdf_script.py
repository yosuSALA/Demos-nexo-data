from pypdf import PdfReader
import sys

try:
    reader = PdfReader(r'c:\Users\Daly\OneDrive\Documentos\Demo#7\Demo7_RRHH_RolesConfianza.pdf')
    text = ''.join([page.extract_text() for page in reader.pages])
    with open("pdf_content.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("Success")
except Exception as e:
    print(f"Error: {e}")

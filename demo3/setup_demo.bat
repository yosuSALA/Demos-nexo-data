@echo off
REM ─── Setup Demo PDF Generator ─────────────────────────────────────────────
REM Instala dependencias en el venv existente del proyecto ETL-Supercias
REM Ejecutar desde la carpeta raíz del proyecto o desde demo2\

echo [1/3] Instalando matplotlib, jinja2...
..\\.venv\\Scripts\\pip install matplotlib jinja2 --quiet

echo [2/3] Instalando WeasyPrint...
echo NOTA: WeasyPrint en Windows requiere GTK3 runtime.
echo Si falla, instala GTK desde: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
..\\.venv\\Scripts\\pip install weasyprint --quiet

echo [3/3] Listo. Ejecutar con:
echo    ..\.venv\Scripts\python generador_pdfs.py
echo    ..\.venv\Scripts\python generador_pdfs.py --top 5
pause

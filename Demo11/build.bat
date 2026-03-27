@echo off
REM ═══════════════════════════════════════════════════════════════
REM  build.bat — Compilar Controlador ETL Super Cias a .exe
REM ═══════════════════════════════════════════════════════════════
REM
REM  Requisitos previos:
REM    1. Tener el venv activo o ejecutar desde la raiz del proyecto
REM    2. pip install pyinstaller  (ya instalado)
REM    3. Colocar el icono en:  assets\app_icon.ico
REM
REM  Uso:
REM    build.bat
REM
REM  Salida:
REM    dist\ETL_SuperCias.exe
REM ═══════════════════════════════════════════════════════════════

setlocal

REM --- Rutas del proyecto ---
set PROJECT_ROOT=%~dp0
set VENV_PYTHON=%PROJECT_ROOT%.venv\Scripts\python.exe
set SPEC_FILE=%PROJECT_ROOT%etl_supercias.spec

REM --- Verificar que el venv existe ---
if not exist "%VENV_PYTHON%" (
    echo [ERROR] No se encontro el venv en .venv\Scripts\python.exe
    echo         Ejecute: python -m venv .venv
    pause
    exit /b 1
)

REM --- Verificar PyInstaller ---
"%VENV_PYTHON%" -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [INFO] Instalando PyInstaller...
    "%VENV_PYTHON%" -m pip install pyinstaller
)

REM --- Verificar icono ---
if not exist "%PROJECT_ROOT%assets\app_icon.ico" (
    echo [AVISO] No se encontro assets\app_icon.ico
    echo         El ejecutable se generara sin icono personalizado.
    echo         Para agregar icono, coloque un archivo .ico en assets\app_icon.ico
    echo.
)

REM --- Compilar usando el archivo .spec ---
echo.
echo ══════════════════════════════════════════════════
echo  Compilando Controlador ETL Super Cias...
echo ══════════════════════════════════════════════════
echo.

"%VENV_PYTHON%" -m PyInstaller "%SPEC_FILE%" --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] La compilacion fallo. Revise los mensajes anteriores.
    pause
    exit /b 1
)

echo.
echo ══════════════════════════════════════════════════
echo  Compilacion exitosa!
echo  Ejecutable en: dist\ETL_SuperCias.exe
echo ══════════════════════════════════════════════════
echo.

pause

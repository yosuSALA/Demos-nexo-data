# Motor ETL de Alto Rendimiento — Estados Financieros (Super Cias Ecuador)

Sistema de ingenieria de datos con interfaz grafica que automatiza la **descarga, transformacion y carga** de estados financieros consolidados publicados por la Superintendencia de Companias, Valores y Seguros del Ecuador. Procesa mas de **15 millones de registros** con uso acotado de memoria RAM gracias a lectura por bloques y operaciones vectorizadas.

---

## Descripcion General

El pipeline descarga automaticamente el archivo ZIP de balances consolidados desde el portal de la Super Cias, detecta la codificacion del archivo (UTF-8 o Latin-1), transcodifica si es necesario, filtra por sector de interes, normaliza formatos numericos y de fechas ecuatorianos, y carga los datos limpios en una base de datos analitica DuckDB. Adicionalmente exporta un archivo Parquet con compresion ZSTD listo para conectar desde Power BI o Tableau.

---

## Stack Tecnologico

| Componente | Tecnologia | Rol |
|---|---|---|
| GUI | CustomTkinter 5.2+ | Interfaz moderna con barra de progreso en tiempo real |
| Motor ETL | Polars 0.20+ (vectorizado) | Transformacion de datos a alta velocidad sin bucles Python |
| Base de datos | DuckDB 0.10+ (columnar) | Almacenamiento analitico sin servidor, con deduplicacion por PK |
| Transferencia | Apache Arrow (PyArrow 15+) | Carga zero-copy desde Polars hacia DuckDB |
| Exportacion | Parquet + ZSTD | Salida directa para Power BI / Tableau |
| CLI | Typer 0.12+ | Interfaz de linea de comandos con opciones tipadas |
| Logging | Loguru 0.7+ | Registro rotativo con colores y compresion gz |
| Descarga | Requests 2.31+ | Descarga streaming con progreso (128 KB/chunk) |

---

## Arquitectura

```
Portal Super Cias (ZIP remoto)
      |
      v
  Descarga streaming (128 KB/chunk, con barra de progreso)
      |
      v
  Extraccion del ZIP a directorio temporal
      |
      v
  Deteccion de encoding (UTF-8 / Latin-1) + transcodificacion automatica
      |
      v
  Deteccion automatica de separador (TAB / ; / ,)
      |
      v
  Polars read_csv_batched (500K filas/bloque, memoria acotada)
      |
      v
  Filtrado por sector: "ADMINISTRADORA DE FONDOS Y FIDEICOMISOS"
      |
      v
  Transformacion vectorizada (dentro del motor Polars, sin bucles Python):
  - Normalizacion numerica: formato EC (1.188.854,66) -> Float64
  - Estandarizacion de fechas: multi-formato -> ISO 8601 (YYYY-MM-DD)
  - Limpieza de sector_code: quitar puntos de miles (15.036 -> 15036)
  - Validacion de RUC: exactamente 13 digitos numericos
  - Deduplicacion por clave primaria compuesta (ruc + account_code + date + period_type)
  - Eliminacion de filas con campos criticos nulos o vacios
      |
      v
  Arrow zero-copy -> DuckDB (INSERT OR REPLACE / INSERT OR IGNORE)
      |
      v
  Marts analiticos (SQL): resumenes anuales, rankings, KPIs, deteccion de anomalias
      |
      v
  Exportacion Parquet (COPY streaming con compresion ZSTD)
```

### Flujo de datos en modo GUI

1. El usuario selecciona la ruta de la base de datos destino y el modo (actualizar/crear).
2. Al presionar "Ejecutar", el backend inicia en un hilo secundario para no bloquear la interfaz.
3. El callback `on_progress(mensaje, porcentaje)` actualiza la barra de progreso en tiempo real.
4. Al finalizar, se muestra un resumen con filas leidas, cargadas, descartadas y duracion.

---

## Prerequisitos

- **Python 3.10+** (probado con 3.11 y 3.12)
- **Windows 10/11** (la GUI usa CustomTkinter con Segoe UI; el CLI funciona en cualquier OS)
- Conexion a internet (para descargar el ZIP desde el portal de la Super Cias)

---

## Instalacion

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd Demo11

# 2. Crear entorno virtual
python -m venv .venv

# 3. Activar el entorno virtual
# Windows (CMD):
.venv\Scripts\activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt
```

### Dependencias (requirements.txt)

```
polars>=0.20.0
duckdb>=0.10.0
typer>=0.12.0
loguru>=0.7.0
pyarrow>=15.0.0
customtkinter>=5.2.0
requests>=2.31.0
```

---

## Como Ejecutar

### Modo GUI (interfaz grafica)

```bash
python main_gui.py
```

La interfaz permite:
- Seleccionar la ruta de la base de datos DuckDB de destino
- Elegir entre **Actualizar** (carga incremental, sin duplicar) o **Crear** (elimina y recrea desde cero)
- Ejecutar con un clic y ver el progreso en tiempo real (descarga, procesamiento, carga)
- Programar ejecuciones automaticas mensuales via Windows Task Scheduler
- Cambiar el tema visual (dark / light / system)
- Guardar la configuracion del usuario en JSON persistente

### Modo automatico (sin GUI, para Task Scheduler)

```bash
python main_gui.py --auto
```

Ejecuta el ETL completo en modo headless usando la configuracion guardada. Ideal para programar con `schtasks` en Windows. Los resultados se registran en `etl_gui.log`.

### Modo CLI (pipeline con archivo local)

```bash
python run_pipeline.py --input datos.tsv --db output/supercias.duckdb
```

Opciones disponibles:

| Opcion | Valor por defecto | Descripcion |
|---|---|---|
| `--input` | (requerido) | Ruta al archivo CSV/TSV de origen |
| `--db` | `output/supercias.duckdb` | Ruta del archivo DuckDB de salida |
| `--sql-dir` | `sql` | Directorio con archivos SQL de marts analiticos |
| `--chunk-size` | `500000` | Filas por bloque de procesamiento |
| `--separator` | `\t` (TAB) | Separador de columnas |
| `--has-header` | `False` | Si el archivo tiene fila de cabecera |
| `--encoding` | `utf8` | Codificacion del archivo de origen |
| `--log-level` | `INFO` | Nivel de detalle del log (DEBUG/INFO/WARNING) |
| `--log-file` | `etl.log` | Ruta del archivo de log |

### Compilar a ejecutable (.exe)

```bash
build.bat
```

Genera `dist/ETL_SuperCias.exe` usando PyInstaller. Empaqueta el codigo, los archivos SQL y los assets en un unico ejecutable portable.

---

## Caracteristicas Principales

### Ingestion de datos
- Descarga automatica del ZIP de balances consolidados desde el portal oficial
- Deteccion automatica de codificacion (UTF-8, Latin-1, Windows-1252) con transcodificacion transparente
- Deteccion automatica de separador de columnas (TAB, punto y coma, coma)
- Lectura por bloques de 500K filas para mantener el uso de RAM acotado

### Transformacion
- Parseo de numeros en formato Ecuador (1.188.854,66 -> 1188854.66) completamente vectorizado
- Normalizacion de fechas multi-formato (dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd, yyyymmdd) a ISO 8601
- Validacion de RUC ecuatoriano (13 digitos exactos)
- Limpieza de codigos de sector con puntos de miles
- Deduplicacion por clave primaria compuesta antes de la carga
- Manejo de dos formatos de codigo contable: entero simple (101) y jerarquia con puntos (502.03.08)

### Carga y almacenamiento
- Insercion zero-copy via Apache Arrow (sin serializacion intermedia)
- `INSERT OR REPLACE` para actualizaciones incrementales (el balance corregido gana)
- `INSERT OR IGNORE` para cargas iniciales sin duplicados
- Indice unico sobre la clave primaria compuesta (ruc, account_code, date, period_type)
- Exportacion automatica a Parquet con compresion ZSTD via `COPY` nativo de DuckDB (cero impacto en RAM de Python)

### Marts analiticos (SQL)
- Resumen anual por empresa
- Activos vs. pasivos
- Categorias de cuentas contables
- Ranking de empresas
- Consultas listas para dashboards BI
- Indicadores financieros (KPIs)
- Deteccion de anomalias

### Esquemas alternativos
- Esquema normalizado
- Esquema estrella (star schema) con dimensiones y hechos
- Vistas BI preconstruidas

### Interfaz grafica
- Tema oscuro/claro/sistema con CustomTkinter
- Barra de progreso en tiempo real con detalle de MB descargados y filas procesadas
- Ejecucion en hilo secundario (la GUI nunca se congela)
- Configuracion persistente en JSON
- Boton para copiar el comando de Windows Task Scheduler al portapapeles
- Informacion en vivo: ultima carga, conteo de registros, ruta de la BD

### Operaciones
- Logging rotativo con compresion (50 MB por archivo, 7 dias de retencion)
- Limpieza automatica de archivos temporales (incluso si el proceso falla)
- Manejo de errores con mensajes descriptivos en espanol
- Modo `--auto` para ejecucion desatendida via Task Scheduler

---

## Estructura del Proyecto

```
Demo11/
|
|-- main_gui.py              Punto de entrada principal (GUI / --auto)
|-- run_pipeline.py          CLI alternativo con Typer (para archivos locales)
|-- requirements.txt         Dependencias del proyecto
|-- build.bat                Script de compilacion a .exe con PyInstaller
|-- etl_supercias.spec       Configuracion de PyInstaller
|-- pytest.ini               Configuracion de pytest
|-- .gitignore               Archivos excluidos del repositorio
|
|-- gui/
|   |-- app.py               Ventana principal (CustomTkinter, 900x680)
|   |-- backend.py           Orquestador ETL: descarga, filtrado, carga, exportacion Parquet
|   |-- config_manager.py    Persistencia de configuracion en JSON
|
|-- etl/
|   |-- __init__.py
|   |-- extract.py           Lector CSV/TSV por bloques (Polars read_csv_batched)
|   |-- transform.py         Limpieza y normalizacion vectorizada (numeros EC, fechas, RUC)
|   |-- load.py              Carga en DuckDB (init, load_chunk, build_marts, finalize)
|
|-- utils/
|   |-- __init__.py
|   |-- formatters.py        Parseo de numeros EC y normalizacion de fechas (funciones puras)
|   |-- logger.py            Configuracion de Loguru (rotacion, compresion, colores)
|
|-- sql/                     Marts analiticos y consultas BI
|   |-- 00_create_marts.sql
|   |-- 01_mart_yearly_summary.sql
|   |-- 02_mart_assets_vs_liabilities.sql
|   |-- 03_mart_account_categories.sql
|   |-- 04_mart_company_ranking.sql
|   |-- 05_bi_dashboard_queries.sql
|   |-- 06_kpi_financial_indicators.sql
|   |-- 07_anomaly_detection.sql
|
|-- schema/                  Esquemas de base de datos alternativos
|   |-- 00_build_schema.sql
|   |-- 01_normalized.sql
|   |-- 02_star_schema.sql
|   |-- 03_populate_dimensions.sql
|   |-- 04_bi_views.sql
|
|-- tests/                   Suite de pruebas (pytest)
|   |-- conftest.py
|   |-- test_extract.py
|   |-- test_transform.py
|   |-- test_load.py
|   |-- test_formatters.py
|   |-- test_data_quality.py
|   |-- test_integration.py
|   |-- test_nuevos_formatos.py
|
|-- docs/                    Documentacion tecnica
|   |-- guia_testing_etl.md
|   |-- indicadores_financieros_bi.md
|   |-- manual_de_usuario.md
|
|-- assets/                  Recursos (icono de la aplicacion)
|-- output/                  Directorio de salida (DuckDB + Parquet, excluido de git)
|-- config/                  Configuracion local del usuario (excluido de git)
|-- dist/                    Ejecutable compilado (excluido de git)
|-- build/                   Archivos temporales de compilacion (excluido de git)
```

---

## Tests

```bash
# Ejecutar toda la suite
pytest -v

# Ejecutar solo tests unitarios (rapidos)
pytest -v -m "not integration"

# Ejecutar tests de integracion (requieren I/O y DuckDB)
pytest -v -m integration
```

La suite cubre: extraccion por bloques, transformacion vectorizada, carga en DuckDB, calidad de datos, formatos especiales (numeros EC, fechas multi-formato, codigos contables con puntos) e integracion de punta a punta.

---

## Notas de Rendimiento

| Aspecto | Detalle |
|---|---|
| **Lectura** | Polars `read_csv_batched` procesa 500K filas por bloque sin cargar el archivo completo en RAM |
| **Transformacion** | Todas las operaciones (parseo numerico, fechas, dedup) son expresiones vectorizadas de Polars ejecutadas en Rust, no en Python |
| **Carga** | La transferencia Polars -> DuckDB usa Apache Arrow (zero-copy): los datos pasan directo sin serializacion |
| **Exportacion** | `COPY ... TO Parquet` de DuckDB es streaming interno, sin pasar los datos por el runtime de Python |
| **Compresion** | ZSTD ofrece mejor ratio que Snappy para datos financieros tabulares con alta repetitividad |
| **Concurrencia** | La GUI ejecuta el ETL en un hilo secundario; la interfaz permanece responsiva durante todo el proceso |
| **Memoria** | El consumo se mantiene proporcional al tamano de un bloque (~500K filas), no al tamano total del archivo |
| **Descarga** | Streaming en chunks de 128 KB con progreso, sin almacenar el ZIP completo en RAM |

---

## Fuente de Datos

Los datos provienen del portal abierto de la **Superintendencia de Companias, Valores y Seguros del Ecuador**:

- URL: `https://mercadodevalores.supercias.gob.ec/reportes/zip/balancesConsolidadosMv.zip`
- Formato: archivo ZIP con TSV/CSV sin cabecera, separado por tabulaciones
- Codificacion: Latin-1 (ISO 8859-1) o UTF-8 segun el periodo
- Contenido: balances consolidados de todas las empresas registradas

El pipeline filtra automaticamente por el sector **"Administradora de Fondos y Fideicomisos"**.

---

## Licencia

Proyecto de demostracion con fines educativos y de consultoria.

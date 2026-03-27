"""
backend.py — Motor ETL: Descarga, Transformación y Carga
=========================================================
Descarga el ZIP de balances consolidados de la Super Cías, extrae los
archivos, filtra únicamente el sector "ADMINISTRADORA DE FONDOS Y
FIDEICOMISOS" con Polars, y carga los resultados en DuckDB.

El GUI invoca `run_etl()` en un hilo secundario para no bloquear la interfaz.
El callback `on_progress(mensaje, porcentaje)` actualiza la barra de progreso.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import duckdb
import polars as pl
import requests

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────────────────
URL_BALANCES_ZIP = (
    "https://mercadodevalores.supercias.gob.ec/reportes/zip/balancesConsolidadosMv.zip"
)

# Filtro hardcodeado — único sector de interés del cliente
FILTRO_ENTITY_TYPE = "ADMINISTRADORA DE FONDOS Y FIDEICOMISOS"

# Tamaño de bloque para descarga con progreso (128 KB)
DOWNLOAD_CHUNK_SIZE = 131_072

# Tamaño de bloque para lectura CSV por lotes (filas)
CSV_CHUNK_SIZE = 500_000

# Esquema de la tabla destino en DuckDB
# La PRIMARY KEY compuesta previene duplicados a nivel de motor de BD.
# DuckDB usa esta PK para resolver INSERT OR REPLACE / INSERT OR IGNORE.
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS financial_statements (
    sector_code    VARCHAR,
    entity_type    VARCHAR,
    ruc            VARCHAR NOT NULL,
    company_name   VARCHAR,
    date           VARCHAR NOT NULL,
    period_type    VARCHAR NOT NULL,
    account_code   VARCHAR NOT NULL,
    account_name   VARCHAR,
    value          DOUBLE  NOT NULL,
    entity_subtype VARCHAR,
    loaded_at      TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (ruc, account_code, date, period_type)
);
"""

ProgressCallback = Callable[[str, float], None]


@dataclass
class ETLResult:
    """Resultado resumido de una ejecución ETL."""
    filas_leidas: int = 0
    filas_cargadas: int = 0
    filas_descartadas: int = 0
    duracion_seg: float = 0.0
    exitoso: bool = True
    mensaje_error: str = ""


# ──────────────────────────────────────────────────────────
# Consultas sobre la base de datos existente
# ──────────────────────────────────────────────────────────
def get_high_water_mark(db_path: Path) -> str | None:
    """Retorna la fecha más reciente cargada, o None si la tabla no existe o está vacía."""
    if not db_path.exists():
        return None
    try:
        conn = duckdb.connect(str(db_path), read_only=True)
        result = conn.execute("SELECT MAX(date) FROM financial_statements").fetchone()
        conn.close()
        return result[0] if result and result[0] else None
    except duckdb.CatalogException:
        return None
    except Exception:
        return None


def get_record_count(db_path: Path) -> int:
    """Retorna el conteo total de registros, o 0 si la tabla no existe."""
    if not db_path.exists():
        return 0
    try:
        conn = duckdb.connect(str(db_path), read_only=True)
        result = conn.execute("SELECT COUNT(*) FROM financial_statements").fetchone()
        conn.close()
        return result[0] if result else 0
    except duckdb.CatalogException:
        return 0
    except Exception:
        return 0


# ──────────────────────────────────────────────────────────
# Pipeline ETL principal
# ──────────────────────────────────────────────────────────
def run_etl(
    duckdb_path: Path,
    mode: str,
    on_progress: ProgressCallback | None = None,
) -> ETLResult:
    """
    Ejecuta el pipeline ETL completo.

    Parámetros:
        duckdb_path: Ruta al archivo DuckDB de destino.
        mode: 'create' (borra tabla y recrea) o 'update' (inserta sin duplicar).
        on_progress: Callback para actualizar la barra de progreso de la GUI.

    Etapas:
        1. Descarga el ZIP desde el portal de la Super Cías.
        2. Extrae el contenido a un directorio temporal.
        3. Lee cada archivo CSV/TSV con Polars en bloques.
        4. Filtra por entity_type = "ADMINISTRADORA DE FONDOS Y FIDEICOMISOS".
        5. Inserta los datos filtrados en DuckDB.
        6. Limpia los archivos temporales.
    """
    _progress = on_progress or (lambda msg, pct: None)
    t0 = time.perf_counter()
    tmp_dir = None

    try:
        # ── Paso 1: Descarga ──────────────────────
        _progress("Conectando con el portal de la Super Cías...", 0.02)

        tmp_dir = Path(tempfile.mkdtemp(prefix="etl_supercias_"))
        zip_path = tmp_dir / "balances.zip"

        _download_zip(zip_path, _progress)

        # ── Paso 2: Extracción del ZIP ────────────
        _progress("Extrayendo archivos del ZIP...", 0.30)
        data_files = _extract_zip(zip_path, tmp_dir)

        if not data_files:
            return ETLResult(
                exitoso=False,
                mensaje_error="El ZIP no contiene archivos CSV/TSV válidos.",
                duracion_seg=time.perf_counter() - t0,
            )

        _progress(f"Se encontraron {len(data_files)} archivo(s) de datos.", 0.35)

        # ── Paso 3: Inicializar DuckDB ────────────
        _progress("Inicializando base de datos DuckDB...", 0.37)
        duckdb_path.parent.mkdir(parents=True, exist_ok=True)
        conn = duckdb.connect(str(duckdb_path))

        if mode == "create":
            _progress("Modo CREAR: eliminando tabla anterior...", 0.38)
            conn.execute("DROP TABLE IF EXISTS financial_statements")

        conn.execute(CREATE_TABLE_SQL)

        # ── Paso 4: Lectura, filtrado y carga ─────
        total_leidas = 0
        total_cargadas = 0
        file_count = len(data_files)

        for file_idx, data_file in enumerate(data_files):
            base_pct = 0.40 + (file_idx / file_count) * 0.50  # 40%-90% del progreso

            _progress(
                f"Procesando archivo {file_idx + 1}/{file_count}: {data_file.name}...",
                base_pct,
            )

            leidas, cargadas = _process_file(
                data_file, conn, mode, _progress,
                base_pct=base_pct,
                pct_range=0.50 / file_count,
                tmp_dir=tmp_dir,
            )
            total_leidas += leidas
            total_cargadas += cargadas

        # ── Paso 5: Marts analíticos ──────────────
        _progress("Generando vistas analíticas (marts)...", 0.91)
        _build_marts(conn)

        # ── Paso 6: Exportar Parquet para Power BI ──
        parquet_path = duckdb_path.with_suffix(".parquet")
        export_to_powerbi_parquet(conn, parquet_path, progress=_progress)

        # ── Paso 7: Finalizar ─────────────────────
        final_count = conn.execute(
            "SELECT COUNT(*) FROM financial_statements"
        ).fetchone()[0]
        conn.close()

        _progress("Limpiando archivos temporales...", 0.97)

        duracion = time.perf_counter() - t0
        _progress("Proceso completado exitosamente.", 1.0)

        return ETLResult(
            filas_leidas=total_leidas,
            filas_cargadas=total_cargadas,
            filas_descartadas=total_leidas - total_cargadas,
            duracion_seg=duracion,
            exitoso=True,
        )

    except requests.ConnectionError:
        return ETLResult(
            exitoso=False,
            mensaje_error=(
                "No se pudo conectar al servidor de la Super Cías.\n"
                "Verifique su conexión a internet e intente nuevamente."
            ),
            duracion_seg=time.perf_counter() - t0,
        )
    except requests.Timeout:
        return ETLResult(
            exitoso=False,
            mensaje_error="La descarga excedió el tiempo de espera (timeout).",
            duracion_seg=time.perf_counter() - t0,
        )
    except Exception as e:
        return ETLResult(
            exitoso=False,
            mensaje_error=str(e),
            duracion_seg=time.perf_counter() - t0,
        )
    finally:
        # Limpieza de archivos temporales pase lo que pase
        if tmp_dir and tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ──────────────────────────────────────────────────────────
# Funciones internas
# ──────────────────────────────────────────────────────────
def _download_zip(dest: Path, progress: ProgressCallback) -> None:
    """Descarga el ZIP con progreso basado en Content-Length."""
    progress("Descargando balances consolidados de la Super Cías...", 0.03)

    resp = requests.get(URL_BALANCES_ZIP, stream=True, timeout=120)
    resp.raise_for_status()

    total_bytes = int(resp.headers.get("content-length", 0))
    downloaded = 0

    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
            f.write(chunk)
            downloaded += len(chunk)

            if total_bytes > 0:
                dl_pct = downloaded / total_bytes
                # La descarga ocupa del 3% al 28% de la barra total
                overall_pct = 0.03 + dl_pct * 0.25
                mb_dl = downloaded / (1024 * 1024)
                mb_total = total_bytes / (1024 * 1024)
                progress(
                    f"Descargando: {mb_dl:.1f} MB / {mb_total:.1f} MB ({dl_pct:.0%})",
                    overall_pct,
                )

    progress("Descarga completada.", 0.28)


def _extract_zip(zip_path: Path, dest_dir: Path) -> list[Path]:
    """Extrae el ZIP y retorna las rutas de archivos de datos encontrados."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)

    # Buscar archivos CSV/TSV/TXT dentro del directorio extraído
    extensions = {".csv", ".tsv", ".txt"}
    data_files = sorted(
        f for f in dest_dir.rglob("*")
        if f.suffix.lower() in extensions and f.stat().st_size > 0
    )
    return data_files


def _detect_encoding(file_path: Path) -> str:
    """
    Detecta la codificación del archivo leyendo los primeros bytes.

    Los archivos de la Super Cías típicamente usan Latin-1 (ISO 8859-1)
    o Windows-1252 para caracteres con tilde (á, é, í, ó, ú, ñ).
    Si el archivo es UTF-8 válido, se respeta esa codificación.
    """
    sample_size = 8192  # 8 KB es suficiente para detectar
    raw = file_path.read_bytes()[:sample_size]

    # Si empieza con BOM de UTF-8, es UTF-8
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8"

    # Intentar decodificar como UTF-8 estricto
    try:
        raw.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass

    # No es UTF-8 → asumir Latin-1 (estándar de archivos de la Super Cías)
    logger.info(f"Archivo {file_path.name}: codificacion detectada como Latin-1 (ISO 8859-1)")
    return "latin-1"


def _transcode_to_utf8(file_path: Path, encoding: str, tmp_dir: Path) -> Path:
    """
    Si el archivo no es UTF-8, crea una copia transcodificada a UTF-8
    en el directorio temporal. Polars solo soporta UTF-8 de forma nativa.

    Lee y escribe en bloques de 4 MB para no cargar el archivo completo en RAM.
    """
    if encoding.lower() in ("utf-8", "utf8"):
        return file_path  # Ya es UTF-8, no hace falta copiar

    utf8_path = tmp_dir / f"{file_path.stem}_utf8{file_path.suffix}"
    logger.info(f"Transcodificando {file_path.name} de {encoding} a UTF-8...")

    block_size = 4 * 1024 * 1024  # 4 MB
    with open(file_path, "r", encoding=encoding, errors="replace") as src, \
         open(utf8_path, "w", encoding="utf-8", newline="") as dst:
        while True:
            chunk = src.read(block_size)
            if not chunk:
                break
            dst.write(chunk)

    return utf8_path


def _detect_separator(file_path: Path, encoding: str = "utf-8") -> str:
    """Detecta el separador del archivo leyendo la primera línea."""
    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        first_line = f.readline()

    tab_count = first_line.count("\t")
    semicolon_count = first_line.count(";")
    comma_count = first_line.count(",")

    if tab_count >= semicolon_count and tab_count >= comma_count:
        return "\t"
    if semicolon_count >= comma_count:
        return ";"
    return ","


def _process_file(
    file_path: Path,
    conn: duckdb.DuckDBPyConnection,
    mode: str,
    progress: ProgressCallback,
    base_pct: float,
    pct_range: float,
    tmp_dir: Path | None = None,
) -> tuple[int, int]:
    """
    Lee un archivo CSV/TSV en bloques con Polars, filtra por el sector
    fiduciario y carga en DuckDB.

    Detecta automáticamente la codificación (UTF-8 o Latin-1) y transcodifica
    a UTF-8 si es necesario para que Polars procese tildes correctamente.

    Retorna (filas_leidas, filas_cargadas).
    """
    # Detectar codificación y transcodificar si no es UTF-8
    encoding = _detect_encoding(file_path)
    separator = _detect_separator(file_path, encoding)

    if encoding.lower() not in ("utf-8", "utf8") and tmp_dir:
        file_path = _transcode_to_utf8(file_path, encoding, tmp_dir)

    total_leidas = 0
    total_cargadas = 0

    # Polars BatchedCsvReader para lectura por bloques controlados en memoria
    reader = pl.read_csv_batched(
        file_path,
        separator=separator,
        has_header=False,
        encoding="utf8",             # Ahora el archivo siempre es UTF-8
        infer_schema_length=0,
        batch_size=CSV_CHUNK_SIZE,
        truncate_ragged_lines=True,
    )

    chunk_num = 0
    while True:
        batches = reader.next_batches(1)
        if not batches:
            break

        raw_df = batches[0]
        chunk_num += 1
        total_leidas += len(raw_df)

        # Asignar nombres de columna según el esquema conocido de la Super Cías
        col_names = [
            "sector_code", "entity_type", "ruc", "company_name",
            "date", "period_type", "account_code", "account_name",
            "value", "entity_subtype",
        ]
        # Tomar solo las columnas que existan (el archivo puede tener más o menos)
        actual_cols = min(len(raw_df.columns), len(col_names))
        rename_map = {raw_df.columns[i]: col_names[i] for i in range(actual_cols)}
        df = raw_df.select(list(rename_map.keys())).rename(rename_map)

        # ── Filtro hardcodeado: solo sector fiduciario ──
        if "entity_type" in df.columns:
            df = df.filter(
                pl.col("entity_type").str.to_uppercase().str.contains(FILTRO_ENTITY_TYPE)
            )

        if df.is_empty():
            progress(
                f"Bloque {chunk_num}: sin datos del sector fiduciario, omitiendo...",
                base_pct + (pct_range * 0.5),
            )
            continue

        # ── Deduplicación en Polars ANTES de enviar a DuckDB ──
        # El archivo crudo de la Super Cías contiene duplicados (balances corregidos).
        # keep="last" conserva la corrección más reciente dentro del bloque.
        pk_cols = ["ruc", "account_code", "date", "period_type"]
        cols_presentes = [c for c in pk_cols if c in df.columns]
        if len(cols_presentes) == len(pk_cols):
            antes = len(df)
            df = df.unique(subset=pk_cols, keep="last")
            dupes = antes - len(df)
            if dupes > 0:
                progress(
                    f"Bloque {chunk_num}: {dupes:,} duplicados eliminados en memoria",
                    base_pct + (pct_range * 0.3),
                )

        # ── Conversión del campo value a numérico ──
        if "value" in df.columns:
            df = df.with_columns(
                pl.col("value")
                .str.replace_all(r"\.", "", literal=False)   # Quitar puntos de miles
                .str.replace(",", ".", literal=True)          # Coma decimal → punto
                .cast(pl.Float64, strict=False)
                .alias("value")
            )
            # Descartar filas donde value no se pudo parsear
            df = df.filter(pl.col("value").is_not_null())

        if df.is_empty():
            continue

        # ── Inserción en DuckDB ──
        # mode="update" → INSERT OR REPLACE: si la PK ya existe, sobreescribe
        #                  con el dato nuevo (balance corregido gana).
        # mode="create" → INSERT OR IGNORE: la tabla está vacía pero el mismo
        #                  bloque podría tener duplicados residuales post-unique().
        arrow_table = df.to_arrow()  # noqa: F841 — DuckDB lo referencia por nombre
        target_cols = [c for c in col_names if c in df.columns]
        cols_sql = ", ".join(target_cols)

        insert_verb = "INSERT OR REPLACE" if mode == "update" else "INSERT OR IGNORE"
        conn.execute(f"""
            {insert_verb} INTO financial_statements ({cols_sql})
            SELECT {cols_sql} FROM arrow_table
        """)

        total_cargadas += len(df)

        # Actualizar progreso
        chunk_pct = base_pct + (pct_range * 0.9)
        progress(
            f"Bloque {chunk_num}: {total_cargadas:,} filas del sector fiduciario cargadas",
            min(chunk_pct, 0.90),
        )

    return total_leidas, total_cargadas


# ──────────────────────────────────────────────────────────
# Exportación Parquet único para Power BI
# ──────────────────────────────────────────────────────────
def export_to_powerbi_parquet(
    conn: duckdb.DuckDBPyConnection,
    output_path: Path,
    progress: ProgressCallback | None = None,
) -> None:
    """
    Exporta financial_statements a un archivo Parquet único con COPY de DuckDB.

    - Cero impacto en RAM: COPY es una operación de streaming interna de DuckDB,
      los datos fluyen directo de la tabla al disco sin pasar por Python.
    - Compresión ZSTD: mejor ratio que Snappy para datos financieros tabulares.
    - El archivo se genera junto al .duckdb (ej: sib_final.parquet) y se
      conecta directamente desde Power BI como fuente Parquet.

    Parámetros:
        conn: Conexión abierta a DuckDB con la tabla financial_statements.
        output_path: Ruta del archivo .parquet de salida.
        progress: Callback opcional para actualizar la GUI.
    """
    _progress = progress or (lambda msg, pct: None)

    count_result = conn.execute(
        "SELECT COUNT(*) FROM financial_statements"
    ).fetchone()
    total_rows = count_result[0] if count_result else 0

    if total_rows == 0:
        logger.warning("Exportacion Parquet omitida: la tabla financial_statements esta vacia.")
        _progress("Exportacion Parquet omitida (tabla vacia).", 0.95)
        return

    logger.info(f"Exportando {total_rows:,} filas a Parquet: {output_path}")
    _progress(f"Exportando {total_rows:,} filas a Parquet (ZSTD)...", 0.93)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Ruta con forward slashes para compatibilidad con DuckDB en Windows
    parquet_str = str(output_path).replace("\\", "/")

    copy_sql = (
        f"COPY financial_statements TO '{parquet_str}' "
        f"(FORMAT PARQUET, COMPRESSION 'ZSTD')"
    )

    logger.debug(f"SQL de exportacion: {copy_sql}")

    try:
        conn.execute(copy_sql)
    except duckdb.IOException as e:
        logger.error(f"Error de I/O al escribir Parquet: {e}")
        raise
    except duckdb.CatalogException as e:
        logger.error(f"Error de catalogo durante exportacion Parquet: {e}")
        raise

    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"Parquet exportado: {output_path.name} ({size_mb:.1f} MB, {total_rows:,} filas)")
    _progress(f"Parquet exportado: {output_path.name} ({size_mb:.1f} MB)", 0.96)


def _build_marts(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Ejecuta los archivos SQL de marts analíticos si existen.
    Busca en el directorio sql/ relativo a la raíz del proyecto.
    """
    from gui.config_manager import get_bundled_path

    sql_dir = get_bundled_path("sql")
    if not sql_dir.exists():
        return

    mart_files = sorted(f for f in sql_dir.glob("[0-9][0-9]_*.sql"))
    for path in mart_files:
        try:
            conn.execute(path.read_text(encoding="utf-8"))
        except Exception:
            pass  # Los marts son opcionales, no bloquean el proceso

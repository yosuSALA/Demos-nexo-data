import io
import itertools
from pathlib import Path
from typing import Iterator

import polars as pl
from loguru import logger

# Polars solo soporta UTF-8 de forma nativa en su lector CSV vectorizado.
# Para otras codificaciones se usa la ruta de lectura por Python IO.
_POLARS_UTF8_ENCODINGS = {"utf8", "utf-8", "utf8-lossy"}

# ---------------------------------------------------------------------------
# Nombres de columnas reales inferidos de los datos fuente (Superintendencia).
# El archivo no tiene fila de cabecera; las columnas están separadas por tabulación.
# ---------------------------------------------------------------------------
COLUMN_NAMES = [
    "sector_code",    # Código numérico del sector (ej. 22, 15.036 → se limpia a 15036)
    "entity_type",    # Etiqueta del sector (ej. ADMINISTRADORA DE FONDOS Y FIDEICOMISOS)
    "ruc",            # Identificación fiscal — cadena de 13 dígitos
    "company_name",   # Nombre legal completo
    "date",           # Fecha del reporte en formato dd/mm/yyyy
    "period_type",    # Tipo de periodo: ANUAL | MENSUAL | TRIMESTRAL…
    "account_code",   # Código contable: entero simple (1, 101) o jerarquía con puntos (502.03.08)
    "account_name",   # Nombre de la cuenta contable en español
    "value",          # Valor numérico en formato Ecuador (ej. 1.188.854,66 / -190.089,41)
    "entity_subtype", # Subtipo de entidad — vacío en ANUAL, ej. "FIDEICOMISO MERCANTIL" en MENSUAL
]


def iter_csv_chunks(
    path: str | Path,
    chunk_size: int,
    separator: str = "\t",
    encoding: str = "utf8",
    has_header: bool = False,
) -> Iterator[tuple[int, pl.DataFrame]]:
    """
    Genera bloques (chunks) sucesivos de DataFrames desde archivos TSV/CSV sin cargar
    todo el archivo en la memoria RAM simultáneamente.

    Utiliza el lector de CSV por bloques de Polars (read_csv_batched) para que el consumo
    de memoria esté limitado a aproximadamente el tamaño de cada bloque.

    Parámetros
    ----------
    path        : Ruta al archivo fuente.
    chunk_size  : Cantidad de filas por lote/bloque.
    separator   : Delimitador de columnas (por defecto TAB — usado en archivos de la Supercias).
    encoding    : Codificación del archivo.
    has_header  : True si la primera fila contiene los nombres de las columnas.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Archivo de entrada no encontrado: {path}")

    logger.info(
        f"Abriendo '{path.name}' | separador={repr(separator)} "
        f"cabecera={has_header} | tamaño bloque={chunk_size:,}"
    )

    # Polars solo soporta UTF-8. Para otras codificaciones (latin1, windows-1252, etc.)
    # se transcode cada bloque en Python antes de pasarlo al parser vectorizado de Polars.
    if encoding.lower() in _POLARS_UTF8_ENCODINGS:
        yield from _iter_chunks_polars(path, chunk_size, separator, encoding, has_header)
    else:
        yield from _iter_chunks_python_io(path, chunk_size, separator, encoding, has_header)


def _iter_chunks_polars(
    path: Path,
    chunk_size: int,
    separator: str,
    encoding: str,
    has_header: bool,
) -> Iterator[tuple[int, pl.DataFrame]]:
    """Ruta rápida: lector vectorizado nativo de Polars (solo UTF-8)."""
    reader = pl.read_csv_batched(
        path,
        separator=separator,
        encoding=encoding,
        has_header=has_header,
        infer_schema_length=0,
        ignore_errors=True,
        batch_size=chunk_size,
    )
    chunk_num = 0
    while True:
        batches = reader.next_batches(1)
        if not batches:
            break
        chunk_num += 1
        df = _assign_column_names(batches[0])
        logger.debug(f"Bloque {chunk_num}: {len(df):,} filas, {len(df.columns)} columnas")
        yield chunk_num, df
    logger.info(f"Extracción finalizada — se leyeron {chunk_num} bloque(s)")


def _iter_chunks_python_io(
    path: Path,
    chunk_size: int,
    separator: str,
    encoding: str,
    has_header: bool,
) -> Iterator[tuple[int, pl.DataFrame]]:
    """Ruta compatible: Python IO transcode → Polars parser (para latin1, cp1252, etc.)."""
    chunk_num = 0
    with open(path, encoding=encoding, errors="replace", newline="") as fh:
        if has_header:
            next(fh)
        while True:
            lines = list(itertools.islice(fh, chunk_size))
            if not lines:
                break
            chunk_num += 1
            df = pl.read_csv(
                io.StringIO("".join(lines)),
                separator=separator,
                has_header=False,
                infer_schema_length=0,
                ignore_errors=True,
            )
            df = _assign_column_names(df)
            logger.debug(f"Bloque {chunk_num}: {len(df):,} filas, {len(df.columns)} columnas")
            yield chunk_num, df
    logger.info(f"Extracción finalizada — se leyeron {chunk_num} bloque(s)")


def _assign_column_names(df: pl.DataFrame) -> pl.DataFrame:
    """
    Renombra las columnas auto-generadas por Polars (column_1 … column_N) a COLUMN_NAMES.
    Las columnas adicionales al final (vacías o desconocidas) se eliminan automáticamente.
    """
    n_esperadas = len(COLUMN_NAMES)
    if len(df.columns) < n_esperadas:
        raise ValueError(
            f"El archivo tiene {len(df.columns)} columnas, se esperaban al menos {n_esperadas}. "
            "Verifique el separador o la lista de columnas en extract.py."
        )
    # Renombrar las primeras N columnas; descartar cualquier columna extra más allá de ellas.
    rename_map = {old: new for old, new in zip(df.columns[:n_esperadas], COLUMN_NAMES)}
    df = df.rename(rename_map).select(COLUMN_NAMES)
    return df


def _detect_account_format(sample_code: str) -> str:
    """
    Detecta el formato del código de cuenta a partir de una muestra.
    Retorna 'dotted' (ej. 502.03.08) o 'plain' (ej. 10101).
    Solo informativo — el pipeline maneja ambos formatos transparentemente.
    """
    return "dotted" if "." in sample_code else "plain"

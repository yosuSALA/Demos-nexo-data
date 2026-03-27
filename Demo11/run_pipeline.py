"""
Pipeline de ETL — Estados Financieros
====================================
Procesa archivos CSV de gran tamaño (más de 15M de filas) en bloques de memoria acotados
usando Polars, y luego carga los datos limpios en DuckDB.

Uso:
    python run_pipeline.py --input data/statements.csv --db output/supercias.duckdb

Opciones:
    --input       Ruta al archivo CSV de origen
    --db          Ruta para el archivo de salida DuckDB (se crea si no existe)
    --chunk-size  Filas por lote de procesamiento     (por defecto: 500,000)
    --separator   Separador de columnas del CSV      (por defecto: ,)
    --log-level   Nivel de detalle del log           (por defecto: INFO)
    --log-file    Ruta del archivo de log            (por defecto: etl.log)
"""

import sys
import time
from pathlib import Path

import typer
from loguru import logger

from etl.extract import iter_csv_chunks
from etl.load import finalize, init_db, load_chunk
from etl.transform import transform_chunk
from utils.logger import setup_logger

app = typer.Typer(add_completion=False)


@app.command()
def main(
    input: Path = typer.Option(..., help="Ruta al archivo CSV o TSV de origen"),
    db: Path = typer.Option(Path("output/supercias.duckdb"), help="Ruta del archivo de base de datos DuckDB de salida"),
    sql_dir: Path = typer.Option(Path("sql"), help="Directorio que contiene los archivos SQL para crear las vistas analíticas (marts)"),
    chunk_size: int = typer.Option(500_000, help="Cantidad de filas a procesar por bloque (control de memoria)"),
    separator: str = typer.Option("\t", help="Carácter delimitador de columnas (por defecto: TAB para TSV)"),
    has_header: bool = typer.Option(False, help="Indicar si el archivo tiene una fila de cabecera (header)"),
    log_level: str = typer.Option("INFO", help="Nivel de detalle del registro (DEBUG/INFO/WARNING)"),
    log_file: str = typer.Option("etl.log", help="Ruta donde se guardará el archivo de registro (log)"),
    encoding: str = typer.Option("utf8", help="Codificación del archivo de origen (ej. utf8, latin1)"),
) -> None:
    """
    Función principal que orquesta el flujo ETL: Extracción, Transformación y Carga.
    """
    setup_logger(log_file=log_file, level=log_level)

    # Asegura que el directorio de salida exista antes de iniciar la base de datos
    db.parent.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("ETL de Estados Financieros Supercias — Inicio del Proceso")
    logger.info(f"  Archivo de entrada  : {input}")
    logger.info(f"  Base de datos       : {db}")
    logger.info(f"  Tamaño de bloque    : {chunk_size:,} filas")
    logger.info("=" * 60)

    t_start = time.perf_counter()
    # Inicialización de la conexión a DuckDB y creación de tablas
    conn = init_db(db)

    total_in = 0
    total_out = 0

    try:
        # Itera sobre el archivo de origen en bloques para manejar eficientemente la memoria RAM
        for chunk_num, raw_df in iter_csv_chunks(input, chunk_size, separator, encoding=encoding, has_header=has_header):
            total_in += len(raw_df)

            # Aplicación de reglas de limpieza y normalización
            clean_df = transform_chunk(raw_df, chunk_num)

            if clean_df.is_empty():
                logger.warning(f"Bloque {chunk_num}: Todas las filas fueron descartadas tras la limpieza")
                continue

            # Inserción de los datos transformados en DuckDB
            rows_written = load_chunk(conn, clean_df, chunk_num)
            total_out += rows_written

            # Cálculo de métricas de rendimiento en tiempo real
            elapsed = time.perf_counter() - t_start
            rate = total_in / elapsed if elapsed > 0 else 0
            logger.info(
                f"Bloque {chunk_num:>4} | Procesadas={total_in:>12,} | "
                f"Cargadas={total_out:>12,} | Velocidad={rate:,.0f} filas/s"
            )

    except KeyboardInterrupt:
        logger.warning("Pipeline interrumpido manualmente por el usuario")
        sys.exit(1)
    except Exception:
        logger.exception("Error crítico no controlado — El pipeline ha sido abortado")
        sys.exit(1)
    finally:
        # Cierre seguro de la conexión y ejecución de procesos post-carga (marts)
        finalize(conn, sql_dir=sql_dir)

    # Resumen ejecutivo del proceso realizado
    elapsed = time.perf_counter() - t_start
    logger.info("=" * 60)
    logger.info(f"Proceso finalizado exitosamente en {elapsed:.1f} segundos")
    logger.info(f"  Total filas leídas     : {total_in:,}")
    logger.info(f"  Total filas cargadas    : {total_out:,}")
    logger.info(f"  Total filas descartadas : {total_in - total_out:,}")
    logger.info("=" * 60)


if __name__ == "__main__":
    app()

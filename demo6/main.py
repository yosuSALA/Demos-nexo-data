"""
main.py — Orquestador del pipeline de generación del ATS.

Ejecuta el flujo completo:
    1. Genera datos de prueba (mock).
    2. Aplica validaciones del SRI.
    3. Imprime reporte de errores para el contador.
    4. Genera el XML del ATS con los registros válidos.
    5. Exporta los errores a Excel para revisión.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Asegurar que el directorio del script esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mock_data import generar_datos_compras
from validador_sri import validar_compras
from generador_xml import generar_xml_ats


# ---------------------------------------------------------------------------
# Utilidades de reporte
# ---------------------------------------------------------------------------

_ANCHO_LINEA = 70


def _separador(char: str = "=") -> str:
    return char * _ANCHO_LINEA


def _banner(titulo: str) -> None:
    print(f"\n{_separador()}")
    print(f"  {titulo}")
    print(f"{_separador()}\n")


def imprimir_resumen(
    total: int,
    validos: int,
    errores: int,
) -> None:
    """Imprime un resumen ejecutivo en consola."""
    _banner("REPORTE DE VALIDACION - ATS")

    print(f"  Registros procesados  : {total:>5d}")
    print(f"  [OK]  Validos         : {validos:>5d}")
    print(f"  [ERR] Con errores     : {errores:>5d}")
    tasa = (validos / total * 100) if total else 0
    print(f"  [%]   Tasa aprobacion : {tasa:>5.1f}%")
    print()


def imprimir_detalle_errores(df_errores: pd.DataFrame) -> None:
    """Imprime el detalle de cada registro con error."""
    if df_errores.empty:
        print("  No se encontraron errores. Todos los registros son validos.\n")
        return

    _banner("DETALLE DE ERRORES (para revision del contador)")

    for i, (_, row) in enumerate(df_errores.iterrows(), start=1):
        print(f"  [{i:02d}] Proveedor: {row['razon_social']}")
        print(f"       RUC      : {row['ruc_proveedor']}")
        print(f"       Base imp.: ${row['base_imponible']:,.2f}")
        print(f"       Motivo   : {row['motivo_error']}")
        print()


def exportar_errores_excel(
    df_errores: pd.DataFrame,
    directorio: str = ".",
) -> Path | None:
    """Exporta los errores a un archivo Excel para revisión fácil."""
    if df_errores.empty:
        return None

    ahora = datetime.now()
    nombre = f"errores_ats_{ahora.month:02d}_{ahora.year}.xlsx"
    ruta = Path(directorio) / nombre
    df_errores.to_excel(str(ruta), index=False, sheet_name="Errores ATS")
    return ruta


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def ejecutar_pipeline(
    n_registros: int = 20,
    mes: int | None = None,
    anio: int | None = None,
) -> None:
    """Ejecuta el pipeline completo de generación del ATS.

    Args:
        n_registros: Cantidad de registros mock a generar.
        mes: Mes del periodo fiscal.
        anio: Año del periodo fiscal.
    """
    directorio_base = os.path.dirname(os.path.abspath(__file__))
    directorio_salida = os.path.join(directorio_base, "output")
    os.makedirs(directorio_salida, exist_ok=True)

    # Paso 1 — Generar datos mock
    _banner("PASO 1 - Generacion de datos de prueba")
    df = generar_datos_compras(n_registros)
    print(f"  Se generaron {len(df)} registros de compras simulados.\n")

    # Paso 2 — Validar
    _banner("PASO 2 - Validacion segun reglas del SRI")
    validos, errores = validar_compras(df)
    imprimir_resumen(
        total=len(df),
        validos=len(validos),
        errores=len(errores),
    )
    imprimir_detalle_errores(errores)

    # Paso 3 — Generar XML del ATS
    _banner("PASO 3 - Generacion del XML del ATS")
    ruta_xml = generar_xml_ats(
        validos,
        mes=mes,
        anio=anio,
        directorio_salida=directorio_salida,
    )
    print(f"  [OK] XML generado exitosamente:")
    print(f"       {ruta_xml.resolve()}\n")
    print(f"  Registros incluidos en el XML: {len(validos)}")
    print()

    # Paso 4 — Exportar errores
    if not errores.empty:
        _banner("PASO 4 - Exportacion de errores a Excel")
        ruta_excel = exportar_errores_excel(errores, directorio_salida)
        if ruta_excel:
            print(f"  [OK] Archivo de errores exportado:")
            print(f"       {ruta_excel.resolve()}\n")
            print(
                "  Envie este archivo al contador para que corrija "
                "los registros y vuelva a procesar.\n"
            )

    # Resumen final
    _banner("PIPELINE COMPLETADO")
    print(f"  Archivos generados en: {Path(directorio_salida).resolve()}")
    print()


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ejecutar_pipeline()

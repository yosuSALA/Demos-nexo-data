"""
validador_sri.py — Motor de validación de registros de compras según reglas del SRI.

Aplica las reglas básicas de validación del Servicio de Rentas Internas (Ecuador)
sobre cada registro del reporte de compras y separa los datos en dos conjuntos:
    • registros_validos   → listos para generar el XML del ATS.
    • registros_con_errores → incluyen columna `motivo_error` para revisión contable.
"""

from __future__ import annotations

import re
from typing import Tuple

import pandas as pd

# Tolerancia para comparaciones de punto flotante (centavos)
TOLERANCIA_REDONDEO = 0.02


# ---------------------------------------------------------------------------
# Reglas individuales
# ---------------------------------------------------------------------------

def _validar_ruc(ruc: str) -> str | None:
    """Valida que el RUC sea numérico, tenga 13 dígitos y termine en '001'.

    Returns:
        Mensaje de error o None si es válido.
    """
    if not isinstance(ruc, str):
        ruc = str(ruc)

    if not re.fullmatch(r"\d{13}", ruc):
        return (
            f"RUC '{ruc}' inválido: debe contener exactamente 13 dígitos numéricos "
            f"(tiene {len(ruc)} caracteres)."
        )

    if not ruc.endswith("001"):
        return (
            f"RUC '{ruc}' inválido: los tres últimos dígitos deben ser '001' "
            f"(tiene '{ruc[-3:]}')."
        )

    return None


def _validar_retencion_iva(
    monto_iva: float,
    porcentaje_retencion: float,
    valor_retenido: float,
) -> str | None:
    """Valida que valor_retenido ≈ monto_iva × porcentaje_retencion.

    Returns:
        Mensaje de error o None si es válido.
    """
    esperado = round(monto_iva * porcentaje_retencion, 2)
    diferencia = abs(valor_retenido - esperado)

    if diferencia > TOLERANCIA_REDONDEO:
        return (
            f"Retención IVA no cuadra: esperado ${esperado:.2f} "
            f"(IVA ${monto_iva:.2f} × {porcentaje_retencion:.0%}), "
            f"registrado ${valor_retenido:.2f} "
            f"(diferencia ${diferencia:.2f})."
        )

    return None


# ---------------------------------------------------------------------------
# Función principal de validación
# ---------------------------------------------------------------------------

def validar_compras(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Aplica las reglas de validación del SRI al DataFrame de compras.

    Args:
        df: DataFrame con los registros del reporte de compras.

    Returns:
        Tupla (registros_validos, registros_con_errores).
        El DataFrame de errores incluye la columna ``motivo_error``.
    """
    errores: list[dict] = []
    indices_con_error: set[int] = set()

    for idx, row in df.iterrows():
        motivos: list[str] = []

        # Regla 1 — RUC
        error_ruc = _validar_ruc(row["ruc_proveedor"])
        if error_ruc:
            motivos.append(error_ruc)

        # Regla 2 — Retención IVA
        error_ret = _validar_retencion_iva(
            row["monto_iva"],
            row["porcentaje_retencion_iva"],
            row["valor_retenido_iva"],
        )
        if error_ret:
            motivos.append(error_ret)

        if motivos:
            indices_con_error.add(idx)
            errores.append(
                {**row.to_dict(), "motivo_error": " | ".join(motivos)}
            )

    registros_validos = df.drop(index=list(indices_con_error)).reset_index(drop=True)
    registros_con_errores = pd.DataFrame(errores)

    return registros_validos, registros_con_errores


# ---------------------------------------------------------------------------
# Ejecución directa para prueba rápida
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from mock_data import generar_datos_compras

    df = generar_datos_compras()
    validos, errores = validar_compras(df)

    print(f"Registros totales : {len(df)}")
    print(f"Registros válidos : {len(validos)}")
    print(f"Registros con error: {len(errores)}")
    print()

    if not errores.empty:
        print("=== DETALLE DE ERRORES ===")
        for _, row in errores.iterrows():
            print(f"  • {row['ruc_proveedor']} — {row['razon_social']}")
            print(f"    {row['motivo_error']}")
            print()

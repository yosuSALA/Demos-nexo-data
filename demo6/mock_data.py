"""
mock_data.py — Generador de datos de prueba para el ATS.

Crea un DataFrame con ~20 registros simulando el reporte de compras
exportado desde un sistema contable. Incluye registros válidos y
registros intencionalmente erróneos para probar el motor de validación.
"""

import pandas as pd
import random

random.seed(42)


def generar_datos_compras(n_registros: int = 20) -> pd.DataFrame:
    """Genera un DataFrame con registros de compras simulados.

    Aproximadamente el 70 % de los registros son válidos.
    El 30 % restante contiene errores deliberados:
      - RUC con longitud incorrecta o sin terminación '001'.
      - Valor retenido IVA que no coincide con el cálculo esperado.

    Args:
        n_registros: Cantidad de registros a generar.

    Returns:
        DataFrame con las columnas del reporte de compras.
    """

    # ------- Pools de datos -------
    rucs_validos = [
        "1790016919001",
        "1791714350001",
        "1792012457001",
        "0992397535001",
        "1791251237001",
        "1790567281001",
        "0190003647001",
        "1791395123001",
        "1792060346001",
        "1790843297001",
        "0992712554001",
        "1791408683001",
        "1792287456001",
        "1790010937001",
    ]

    rucs_invalidos = [
        "179001691900",     # 12 dígitos
        "17900169190010",   # 14 dígitos
        "1790016919002",    # no termina en 001
        "ABC0016919001",    # contiene letras
        "0000000000000",    # todo ceros
        "179001691",        # 9 dígitos
    ]

    codigos_sustento = ["01", "02", "03", "05"]
    tipos_comprobante = ["01", "02", "03", "04"]
    porcentajes_retencion = [0.00, 0.10, 0.20, 0.30, 0.70, 1.00]

    registros = []

    for i in range(n_registros):
        es_valido = random.random() < 0.70

        # ---------- RUC ----------
        if es_valido:
            ruc = random.choice(rucs_validos)
        else:
            ruc = random.choice(rucs_invalidos)

        # ---------- Montos ----------
        base_imponible = round(random.uniform(50.0, 15000.0), 2)
        porcentaje_iva = random.choice([0.12, 0.15])
        monto_iva = round(base_imponible * porcentaje_iva, 2)
        pct_ret_iva = random.choice(porcentajes_retencion)

        # ---------- Valor retenido ----------
        valor_retenido_correcto = round(monto_iva * pct_ret_iva, 2)

        if es_valido:
            valor_retenido_iva = valor_retenido_correcto
        else:
            # Introducir error aritmético deliberado
            valor_retenido_iva = round(
                valor_retenido_correcto + random.uniform(5.0, 50.0), 2
            )

        # ---------- Serie y autorización ----------
        establecimiento = f"{random.randint(1, 999):03d}"
        punto_emision = f"{random.randint(1, 999):03d}"
        secuencial = f"{random.randint(1, 999999999):09d}"
        autorizacion = f"{random.randint(10**9, 10**10 - 1)}"

        registros.append(
            {
                "ruc_proveedor": ruc,
                "razon_social": f"PROVEEDOR_{i + 1:03d} S.A.",
                "codigo_sustento": random.choice(codigos_sustento),
                "tipo_comprobante": random.choice(tipos_comprobante),
                "establecimiento": establecimiento,
                "punto_emision": punto_emision,
                "secuencial": secuencial,
                "autorizacion": autorizacion,
                "fecha_emision": f"15/{'01':0>2}/2026",
                "base_no_gravada": round(random.uniform(0, 500.0), 2),
                "base_imponible": base_imponible,
                "monto_iva": monto_iva,
                "porcentaje_retencion_iva": pct_ret_iva,
                "valor_retenido_iva": valor_retenido_iva,
                "porcentaje_retencion_renta": random.choice(
                    [0.00, 0.01, 0.02, 0.08, 0.10]
                ),
                "valor_retenido_renta": round(
                    base_imponible * random.choice([0.00, 0.01, 0.02, 0.08, 0.10]), 2
                ),
            }
        )

    return pd.DataFrame(registros)


# ---------------------------------------------------------------------------
# Ejecución directa para inspección rápida
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    df = generar_datos_compras()
    print(df.to_string(index=False))
    print(f"\nTotal registros generados: {len(df)}")

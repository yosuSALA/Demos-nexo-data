"""
Demo #4: Bot de Conciliación Bancaria Automática
Cruza extracto bancario vs libro mayor y genera reporte de diferencias.
"""

import random
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

fake = Faker("es_ES")
random.seed(42)
Faker.seed(42)

# ---------------------------------------------------------------------------
# 1. Generación de Datos de Prueba
# ---------------------------------------------------------------------------

DESCRIPCIONES_BANCO = [
    "Transferencia recibida", "Pago proveedor", "Depósito en ventanilla",
    "Débito automático", "Transferencia enviada", "Pago nómina",
    "Cobro factura", "Abono préstamo", "Pago servicio básico",
]

CONCEPTOS_CONTABLES = [
    "Cobro cliente", "Pago a proveedor", "Depósito caja",
    "Débito automático servicios", "Transferencia saliente", "Nómina mensual",
    "Ingreso por ventas", "Cuota préstamo", "Servicios públicos",
]


def generar_datos(n: int = 50) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Genera datos mock de banco y contabilidad con coincidencias parciales."""

    fecha_base = datetime(2026, 2, 1)
    registros_banco = []
    registros_contabilidad = []

    # --- Registros que coinciden (con desfase de 1-3 días) ---
    n_coincidentes = int(n * 0.76)  # ~38 de 50
    for i in range(n_coincidentes):
        monto = round(random.uniform(50, 15_000), 2)
        fecha_contab = fecha_base + timedelta(days=random.randint(0, 27))
        desfase = timedelta(days=random.randint(1, 3))
        fecha_banco = fecha_contab + desfase
        ref = f"REF-{1000 + i}"

        tipo_banco = random.choice(["Depósito", "Retiro"])
        tipo_contab = "Ingreso" if tipo_banco == "Depósito" else "Egreso"

        registros_banco.append({
            "fecha_transaccion": fecha_banco.date(),
            "descripcion": random.choice(DESCRIPCIONES_BANCO),
            "referencia": ref,
            "tipo": tipo_banco,
            "monto": monto,
        })
        registros_contabilidad.append({
            "fecha_registro": fecha_contab.date(),
            "comprobante": f"COMP-{2000 + i}",
            "concepto": random.choice(CONCEPTOS_CONTABLES),
            "referencia": ref,
            "tipo": tipo_contab,
            "monto": monto,
        })

    # --- Solo en banco (comisiones, cargos automáticos) ---
    solo_banco_desc = [
        "Comisión bancaria mensual", "Comisión transferencia intl.",
        "Cargo por chequera", "IVA servicios bancarios",
        "Comisión mantenimiento cuenta", "Seguro de desgravamen",
    ]
    n_solo_banco = int(n * 0.12)  # ~6
    for i in range(n_solo_banco):
        registros_banco.append({
            "fecha_transaccion": (fecha_base + timedelta(days=random.randint(0, 27))).date(),
            "descripcion": solo_banco_desc[i % len(solo_banco_desc)],
            "referencia": f"BK-{3000 + i}",
            "tipo": "Retiro",
            "monto": round(random.uniform(5, 120), 2),
        })

    # --- Solo en contabilidad (cheques en tránsito, ajustes) ---
    solo_contab_desc = [
        "Cheque en tránsito #4521", "Cheque en tránsito #4522",
        "Ajuste por diferencia cambiaria", "Provisión cuentas incobrables",
        "Depósito en tránsito", "Nota de crédito pendiente",
    ]
    n_solo_contab = n - n_coincidentes - n_solo_banco  # resto ~6
    for i in range(n_solo_contab):
        registros_contabilidad.append({
            "fecha_registro": (fecha_base + timedelta(days=random.randint(0, 27))).date(),
            "comprobante": f"COMP-{4000 + i}",
            "concepto": solo_contab_desc[i % len(solo_contab_desc)],
            "referencia": f"CT-{5000 + i}",
            "tipo": random.choice(["Ingreso", "Egreso"]),
            "monto": round(random.uniform(50, 5_000), 2),
        })

    df_banco = pd.DataFrame(registros_banco).sort_values("fecha_transaccion").reset_index(drop=True)
    df_contabilidad = pd.DataFrame(registros_contabilidad).sort_values("fecha_registro").reset_index(drop=True)

    return df_banco, df_contabilidad


# ---------------------------------------------------------------------------
# 2. Motor de Conciliación
# ---------------------------------------------------------------------------

def conciliar(df_banco: pd.DataFrame, df_contabilidad: pd.DataFrame) -> dict:
    """
    Cruza banco vs contabilidad por monto exacto + ventana de ±3 días.
    Retorna dict con DataFrames: conciliados, faltantes_banco, faltantes_contabilidad.
    """

    df_b = df_banco.copy()
    df_c = df_contabilidad.copy()
    df_b["fecha_transaccion"] = pd.to_datetime(df_b["fecha_transaccion"])
    df_c["fecha_registro"] = pd.to_datetime(df_c["fecha_registro"])

    usados_banco = set()
    usados_contab = set()
    conciliados = []

    tolerancia = pd.Timedelta(days=3)

    for idx_b, row_b in df_b.iterrows():
        if idx_b in usados_banco:
            continue
        candidatos = df_c[
            (~df_c.index.isin(usados_contab))
            & (df_c["monto"] == row_b["monto"])
            & ((df_c["fecha_registro"] - row_b["fecha_transaccion"]).abs() <= tolerancia)
        ]
        if not candidatos.empty:
            idx_c = candidatos.index[0]
            row_c = candidatos.iloc[0]
            conciliados.append({
                "referencia": row_b["referencia"],
                "monto": row_b["monto"],
                "fecha_banco": row_b["fecha_transaccion"].date(),
                "descripcion_banco": row_b["descripcion"],
                "fecha_contabilidad": row_c["fecha_registro"].date(),
                "concepto_contable": row_c["concepto"],
                "comprobante": row_c["comprobante"],
                "desfase_dias": abs((row_b["fecha_transaccion"] - row_c["fecha_registro"]).days),
                "estado": "Conciliado",
            })
            usados_banco.add(idx_b)
            usados_contab.add(idx_c)

    df_conciliados = pd.DataFrame(conciliados)
    df_faltantes_banco = df_c[~df_c.index.isin(usados_contab)].copy()
    df_faltantes_banco["estado"] = "Partida en tránsito (no está en banco)"
    df_faltantes_contab = df_b[~df_b.index.isin(usados_banco)].copy()
    df_faltantes_contab["estado"] = "No registrada en contabilidad"

    return {
        "conciliados": df_conciliados,
        "faltantes_banco": df_faltantes_banco,
        "faltantes_contabilidad": df_faltantes_contab,
    }


# ---------------------------------------------------------------------------
# 3. Reporte Excel
# ---------------------------------------------------------------------------

def exportar_excel(resultado: dict, archivo: str = "reporte_conciliacion.xlsx"):
    """Exporta resultado a Excel con 3 pestañas formateadas."""
    with pd.ExcelWriter(archivo, engine="openpyxl") as writer:
        if not resultado["conciliados"].empty:
            resultado["conciliados"].to_excel(writer, sheet_name="Conciliados", index=False)
        else:
            pd.DataFrame({"Mensaje": ["No hay partidas conciliadas"]}).to_excel(
                writer, sheet_name="Conciliados", index=False
            )

        resultado["faltantes_banco"].to_excel(
            writer, sheet_name="Faltantes_en_Banco", index=False
        )
        resultado["faltantes_contabilidad"].to_excel(
            writer, sheet_name="Faltantes_en_Contabilidad", index=False
        )

        # Autoajustar ancho de columnas
        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                header_len = len(str(col[0].value or ""))
                ws.column_dimensions[col[0].column_letter].width = max(max_len, header_len) + 3

    return archivo


# ---------------------------------------------------------------------------
# 4. Orquestador
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  Bot de Conciliación Bancaria Automática")
    print("=" * 60)

    print("\n[1/3] Generando datos de prueba...")
    df_banco, df_contabilidad = generar_datos(50)
    print(f"      Banco: {len(df_banco)} registros | Contabilidad: {len(df_contabilidad)} registros")

    print("[2/3] Ejecutando motor de conciliación...")
    resultado = conciliar(df_banco, df_contabilidad)

    n_conciliados = len(resultado["conciliados"])
    n_falt_banco = len(resultado["faltantes_banco"])
    n_falt_contab = len(resultado["faltantes_contabilidad"])
    total = n_conciliados + n_falt_banco + n_falt_contab

    print("[3/3] Exportando reporte Excel...")
    archivo = exportar_excel(resultado)

    print(f"\n{'-' * 60}")
    print(f"  RESUMEN DE CONCILIACION")
    print(f"{'-' * 60}")
    print(f"  Transacciones analizadas:         {total}")
    print(f"  [OK] Conciliadas:                 {n_conciliados}")
    print(f"  [!!] Faltantes en banco (transito): {n_falt_banco}")
    print(f"  [!!] No registradas en contabilidad: {n_falt_contab}")
    print(f"  Tasa de conciliacion:              {n_conciliados / total * 100:.1f}%")
    print(f"{'-' * 60}")
    print(f"  Reporte guardado en: {archivo}")
    print()

"""
ETL — Cartera Vencida (Aging Report)
Entrada : clientes.csv, facturas.csv
Salidas :
  - df_aging        → vista maestra con categoría de aging y flags
  - df_top_deudores → Top 10 clientes por saldo vencido
  - df_por_vencer   → Facturas por vencer en los próximos 7 días
"""

import pandas as pd
from datetime import date, timedelta

HOY     = date.today()
EN_7D   = HOY + timedelta(days=7)

# ─────────────────────────────────────────────
# 1. CARGA
# ─────────────────────────────────────────────
df_cli = pd.read_csv("clientes.csv", encoding="utf-8-sig")
df_fac = pd.read_csv(
    "facturas.csv",
    encoding="utf-8-sig",
    parse_dates=["fecha_emision", "fecha_vencimiento"],
)

# ─────────────────────────────────────────────
# 2. JOIN base
# ─────────────────────────────────────────────
df = df_fac.merge(df_cli, on="id_cliente", how="left")

# ─────────────────────────────────────────────
# 3. DÍAS DE VENCIMIENTO
#    Solo se calcula cuando hay saldo pendiente > 0
# ─────────────────────────────────────────────
hoy_ts = pd.Timestamp(HOY)

df["dias_vencido"] = (
    (hoy_ts - df["fecha_vencimiento"]).dt.days
    .where(df["saldo_pendiente"] > 0)          # NaN si saldo = 0
    .clip(lower=0)                             # facturas vigentes → 0 (no negativo)
)

# ─────────────────────────────────────────────
# 4. CATEGORÍA AGING
# ─────────────────────────────────────────────
def categorizar_aging(row) -> str:
    if row["saldo_pendiente"] == 0:
        return "Pagada"
    d = row["dias_vencido"]
    if pd.isna(d) or d == 0:
        return "Vigente"
    elif d <= 30:
        return "1-30 días"
    elif d <= 60:
        return "31-60 días"
    elif d <= 90:
        return "61-90 días"
    else:
        return "+90 días"

df["aging_bucket"] = df.apply(categorizar_aging, axis=1)

# Orden lógico para gráficos
AGING_ORDER = pd.CategoricalDtype(
    categories=["Pagada", "Vigente", "1-30 días", "31-60 días", "61-90 días", "+90 días"],
    ordered=True,
)
df["aging_bucket"] = df["aging_bucket"].astype(AGING_ORDER)

# ─────────────────────────────────────────────
# 5. FLAG — Por vencer en los próximos 7 días
#    (facturas con saldo > 0 Y vencimiento entre hoy y hoy+7)
# ─────────────────────────────────────────────
venc_ts = pd.Timestamp(EN_7D)

df["alerta_por_vencer"] = (
    (df["saldo_pendiente"] > 0)
    & (df["fecha_vencimiento"] >= hoy_ts)
    & (df["fecha_vencimiento"] <= venc_ts)
)

# ─────────────────────────────────────────────
# 6. VISTA MAESTRA — df_aging
# ─────────────────────────────────────────────
COLS_AGING = [
    "id_factura", "id_cliente", "nombre_comercial", "segmento",
    "fecha_emision", "fecha_vencimiento", "termino_dias",
    "monto_total", "saldo_pendiente", "estado",
    "dias_vencido", "aging_bucket", "alerta_por_vencer",
]
df_aging = df[COLS_AGING].copy()

# ─────────────────────────────────────────────
# 7. TOP 10 DEUDORES
#    Suma de saldo_pendiente donde aging indica mora real
# ─────────────────────────────────────────────
BUCKETS_VENCIDOS = {"1-30 días", "31-60 días", "61-90 días", "+90 días"}

df_top_deudores = (
    df_aging[df_aging["aging_bucket"].isin(BUCKETS_VENCIDOS)]
    .groupby(["id_cliente", "nombre_comercial", "segmento"], observed=True)
    .agg(
        saldo_vencido_total=("saldo_pendiente", "sum"),
        n_facturas_vencidas=("id_factura",       "count"),
    )
    .sort_values("saldo_vencido_total", ascending=False)
    .head(10)
    .reset_index()
)

# ─────────────────────────────────────────────
# 8. FACTURAS POR VENCER (próximos 7 días)
# ─────────────────────────────────────────────
df_por_vencer = (
    df_aging[df_aging["alerta_por_vencer"]]
    [["id_factura", "id_cliente", "nombre_comercial", "segmento",
      "fecha_vencimiento", "monto_total", "saldo_pendiente"]]
    .sort_values("fecha_vencimiento")
    .reset_index(drop=True)
)

# ─────────────────────────────────────────────
# 9. RESUMEN CONSOLA
# ─────────────────────────────────────────────
print("=" * 55)
print("  AGING REPORT — RESUMEN EJECUTIVO")
print("=" * 55)
print(f"  Fecha de corte : {HOY}")
print(f"  Total facturas : {len(df_aging):,}")
print()

resumen_aging = (
    df_aging.groupby("aging_bucket", observed=True)["saldo_pendiente"]
    .agg(["count", "sum"])
    .rename(columns={"count": "n_facturas", "sum": "saldo_total"})
)
resumen_aging["saldo_total"] = resumen_aging["saldo_total"].map("${:,.2f}".format)
print(resumen_aging.to_string())

print()
print("─" * 55)
print("  TOP 10 DEUDORES")
print("─" * 55)
print(
    df_top_deudores[["nombre_comercial", "segmento", "saldo_vencido_total", "n_facturas_vencidas"]]
    .to_string(index=False)
)

print()
print("─" * 55)
print(f"  ALERTAS — Por vencer en 7 días ({len(df_por_vencer)} facturas)")
print("─" * 55)
if not df_por_vencer.empty:
    print(df_por_vencer.to_string(index=False))
else:
    print("  Sin facturas próximas a vencer.")

print("=" * 55)

# ─────────────────────────────────────────────
# 10. EXPORTAR (opcional — útil para Power BI / Tableau)
# ─────────────────────────────────────────────
df_aging.to_csv("aging_report.csv",      index=False, encoding="utf-8-sig")
df_top_deudores.to_csv("top_deudores.csv", index=False, encoding="utf-8-sig")
df_por_vencer.to_csv("alertas_cobro.csv", index=False, encoding="utf-8-sig")

print("\n✔ Archivos exportados: aging_report.csv | top_deudores.csv | alertas_cobro.csv")

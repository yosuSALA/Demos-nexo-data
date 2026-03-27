"""
Generador de Datos Sintéticos — Cartera Vencida (Aging Report)
Genera: clientes.csv, facturas.csv
"""

import pandas as pd
import numpy as np
from faker import Faker
from datetime import date, timedelta

fake = Faker("es_MX")
rng = np.random.default_rng(seed=42)

# ─────────────────────────────────────────────
# 1. CLIENTES
# ─────────────────────────────────────────────
N_CLIENTES = 50

SEGMENTOS = ["Minorista", "Mayorista", "HORECA"]
SEG_WEIGHTS = [0.5, 0.3, 0.2]

LIMITES_POR_SEGMENTO = {
    "Minorista": (5_000,  30_000),
    "Mayorista": (50_000, 200_000),
    "HORECA":    (10_000, 80_000),
}

# ~20 % de clientes serán "morosos crónicos" (flag interno para usarse al generar facturas)
n_morosos = int(N_CLIENTES * 0.20)
moroso_ids = set(rng.choice(range(1, N_CLIENTES + 1), size=n_morosos, replace=False).tolist())

clientes_rows = []
for i in range(1, N_CLIENTES + 1):
    seg = rng.choice(SEGMENTOS, p=SEG_WEIGHTS)
    lo, hi = LIMITES_POR_SEGMENTO[seg]
    limite = int(rng.integers(lo, hi) // 1000 * 1000)   # redondea al millar
    clientes_rows.append({
        "id_cliente":       i,
        "nombre_comercial": fake.company(),
        "segmento":         seg,
        "limite_credito":   limite,
        "es_moroso":        i in moroso_ids,             # columna auxiliar, se descarta al final
    })

df_clientes = pd.DataFrame(clientes_rows)

# ─────────────────────────────────────────────
# 2. FACTURAS
# ─────────────────────────────────────────────
N_FACTURAS = 2_000
HOY         = date.today()
INICIO_PERIODO = HOY - timedelta(days=365)

TERMINOS = [30, 45]   # días de crédito

def fecha_aleatoria(inicio: date, fin: date) -> date:
    delta = (fin - inicio).days
    return inicio + timedelta(days=int(rng.integers(0, delta + 1)))

facturas_rows = []
for fac_id in range(1, N_FACTURAS + 1):
    # ── cliente ──
    cliente = clientes_rows[int(rng.integers(0, N_CLIENTES))]
    id_cli   = cliente["id_cliente"]
    es_moroso = cliente["es_moroso"]

    # ── fechas ──
    fecha_emision    = fecha_aleatoria(INICIO_PERIODO, HOY)
    termino_dias     = rng.choice(TERMINOS)
    fecha_vencimiento = fecha_emision + timedelta(days=int(termino_dias))

    # ── monto ──
    lo_monto = 500
    hi_monto = int(cliente["limite_credito"] * 0.40)
    hi_monto = max(hi_monto, 2_000)
    monto_total = round(float(rng.uniform(lo_monto, hi_monto)), 2)

    dias_desde_vencimiento = (HOY - fecha_vencimiento).days

    # ── estado y saldo ──
    # Lógica con "suciedad" realista:
    #   moroso   → 65 % Vencida, 20 % Vigente, 15 % Pagada
    #   normal   → 20 % Vencida, 40 % Vigente, 40 % Pagada
    if es_moroso:
        estado = rng.choice(["Vencida", "Vigente", "Pagada"], p=[0.65, 0.20, 0.15])
    else:
        estado = rng.choice(["Vencida", "Vigente", "Pagada"], p=[0.20, 0.40, 0.40])

    # Corregir incoherencias fecha/estado
    if fecha_vencimiento > HOY and estado == "Vencida":
        estado = "Vigente"
    if fecha_vencimiento <= HOY and estado == "Vigente":
        estado = "Vencida"

    # Calcular saldo pendiente según estado
    if estado == "Pagada":
        # 15 % pagadas parcialmente (saldo residual pequeño)
        if rng.random() < 0.15:
            pct_pendiente = rng.uniform(0.01, 0.25)
            saldo_pendiente = round(monto_total * pct_pendiente, 2)
            estado = "Vencida" if fecha_vencimiento <= HOY else "Vigente"
        else:
            saldo_pendiente = 0.0
    elif estado == "Vigente":
        # Algunas vigentes ya tienen pago parcial
        if rng.random() < 0.20:
            pct_pendiente = rng.uniform(0.50, 0.99)
            saldo_pendiente = round(monto_total * pct_pendiente, 2)
        else:
            saldo_pendiente = monto_total
    else:  # Vencida
        if rng.random() < 0.25:
            # pago parcial: saldo entre 10 % y 90 % del total
            pct_pendiente = rng.uniform(0.10, 0.90)
            saldo_pendiente = round(monto_total * pct_pendiente, 2)
        else:
            saldo_pendiente = monto_total

    facturas_rows.append({
        "id_factura":         fac_id,
        "id_cliente":         id_cli,
        "fecha_emision":      fecha_emision.isoformat(),
        "fecha_vencimiento":  fecha_vencimiento.isoformat(),
        "termino_dias":       int(termino_dias),
        "monto_total":        monto_total,
        "saldo_pendiente":    saldo_pendiente,
        "estado":             estado,
    })

df_facturas = pd.DataFrame(facturas_rows)

# ─────────────────────────────────────────────
# 3. EXPORTAR
# ─────────────────────────────────────────────
df_clientes.drop(columns=["es_moroso"]).to_csv("clientes.csv", index=False, encoding="utf-8-sig")
df_facturas.to_csv("facturas.csv", index=False, encoding="utf-8-sig")

print(f"✔ clientes.csv  → {len(df_clientes)} registros")
print(f"✔ facturas.csv  → {len(df_facturas)} registros")
print("\nDistribución de estados en facturas:")
print(df_facturas["estado"].value_counts())
print("\nClientes morosos generados:", n_morosos)

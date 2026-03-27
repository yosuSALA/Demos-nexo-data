"""
Monitor de Vencimiento de Contratos y Obligaciones
ETL Pipeline + Motor de Alertas Automáticas
"""

import sys
import pandas as pd
import numpy as np
from faker import Faker
from datetime import date, timedelta
import random

# UTF-8 en terminales Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

fake = Faker("es_MX")
random.seed(42)
np.random.seed(42)

# ─────────────────────────────────────────────
# 1. GENERACIÓN DE DATOS SINTÉTICOS
# ─────────────────────────────────────────────

TIPOS = [
    "Contrato de Arriendo",
    "Póliza de Seguro",
    "Garantía",
    "Permiso Municipal",
]

RESPONSABLES = [
    "Ana Torres", "Carlos Mendez", "Sofía Reyes",
    "Jorge Quispe", "Valentina Cruz", "Ricardo Morales",
    "Daniela Fuentes", "Andrés Salinas",
]

HOY = date.today()

def _fecha_vencimiento_variada() -> date:
    """Distribuye vencimientos para cubrir todos los tramos del semáforo."""
    bucket = random.choices(
        ["vencido", "7d", "15d", "30d", "largo_plazo"],
        weights=[15, 10, 10, 10, 55],
    )[0]
    offsets = {
        "vencido":      lambda: random.randint(-180, -1),
        "7d":           lambda: 7,
        "15d":          lambda: 15,
        "30d":          lambda: 30,
        "largo_plazo":  lambda: random.randint(31, 730),
    }
    return HOY + timedelta(days=offsets[bucket]())


def generar_datos(n: int = 100) -> pd.DataFrame:
    registros = []
    for i in range(1, n + 1):
        fecha_inicio = fake.date_between(start_date="-3y", end_date="today")
        fecha_vencimiento = _fecha_vencimiento_variada()

        registros.append({
            "id_obligacion":    f"OBL-{i:04d}",
            "tipo":             random.choice(TIPOS),
            "entidad_relacionada": fake.company(),
            "fecha_inicio":     fecha_inicio,
            "fecha_vencimiento": fecha_vencimiento,
            "valor_usd":        round(random.uniform(1_000, 500_000), 2),
            "responsable_interno": random.choice(RESPONSABLES),
        })

    df = pd.DataFrame(registros)
    df["fecha_inicio"] = pd.to_datetime(df["fecha_inicio"])
    df["fecha_vencimiento"] = pd.to_datetime(df["fecha_vencimiento"])
    return df


# ─────────────────────────────────────────────
# 2. TRANSFORMACIÓN ETL PARA EL DASHBOARD
# ─────────────────────────────────────────────

def _semaforo(dias: int) -> str:
    if dias < 15:
        return "Rojo"
    elif dias <= 30:
        return "Amarillo"
    return "Verde"


def transformar(df: pd.DataFrame) -> pd.DataFrame:
    hoy = pd.Timestamp(HOY)
    df = df.copy()

    df["dias_para_vencer"] = (df["fecha_vencimiento"] - hoy).dt.days
    df["estado_semaforo"]  = df["dias_para_vencer"].apply(_semaforo)

    # Orden de visualización en el dashboard
    orden_semaforo = {"Rojo": 0, "Amarillo": 1, "Verde": 2}
    df["_orden"] = df["estado_semaforo"].map(orden_semaforo)
    df = df.sort_values(["_orden", "dias_para_vencer"]).drop(columns="_orden")
    df = df.reset_index(drop=True)

    return df


def guardar_csv(df: pd.DataFrame, ruta: str = "datos_dashboard_contratos.csv") -> None:
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    print(f"[ETL] Dashboard CSV exportado -> {ruta}  ({len(df)} registros)")


# ─────────────────────────────────────────────
# 3. MOTOR DE ALERTAS AUTOMÁTICAS
# ─────────────────────────────────────────────

UMBRALES_ALERTA = {30, 15, 7}

PLANTILLA_EMAIL = """\
──────────────────────────────────────────────
ALERTA AUTOMÁTICA — VENCIMIENTO PRÓXIMO
──────────────────────────────────────────────
Para:     {responsable}
Asunto:   [{umbral} días] Vence "{tipo}" — {entidad}

Estimado/a {responsable},

Le informamos que la siguiente obligación está próxima a vencer:

  • ID de Obligación : {id_obligacion}
  • Tipo             : {tipo}
  • Entidad          : {entidad}
  • Fecha de Vencim. : {fecha_vencimiento}
  • Días Restantes   : {dias_para_vencer} días
  • Valor en Riesgo  : USD {valor:,.2f}

Por favor, tome las medidas necesarias antes del vencimiento.

Este es un mensaje generado automáticamente por el
Sistema Monitor de Contratos y Obligaciones.
──────────────────────────────────────────────
"""


def generar_alertas(df: pd.DataFrame) -> list[dict]:
    """
    Filtra registros a exactamente 7, 15 o 30 días de vencer
    y devuelve una lista de dicts con {registro, cuerpo_email}.
    """
    criticos = df[df["dias_para_vencer"].isin(UMBRALES_ALERTA)].copy()

    alertas = []
    for _, row in criticos.iterrows():
        cuerpo = PLANTILLA_EMAIL.format(
            responsable     = row["responsable_interno"],
            umbral          = row["dias_para_vencer"],
            tipo            = row["tipo"],
            entidad         = row["entidad_relacionada"],
            id_obligacion   = row["id_obligacion"],
            fecha_vencimiento = row["fecha_vencimiento"].date(),
            dias_para_vencer= row["dias_para_vencer"],
            valor           = row["valor_usd"],
        )
        alertas.append({"registro": row.to_dict(), "cuerpo_email": cuerpo})

    return alertas


def imprimir_alertas(alertas: list[dict]) -> None:
    if not alertas:
        print("[Alertas] No hay obligaciones en los umbrales de 7 / 15 / 30 días hoy.")
        return

    print(f"\n[Alertas] {len(alertas)} alerta(s) generada(s):\n")
    for alerta in alertas:
        print(alerta["cuerpo_email"])


# ─────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  Monitor de Vencimiento de Contratos y Obligaciones")
    print("=" * 55)

    # 1 · Generar datos
    df_raw = generar_datos(n=100)
    print(f"[ETL] Datos generados: {len(df_raw)} registros")

    # 2 · Transformar
    df = transformar(df_raw)

    # Resumen semáforo
    resumen = df["estado_semaforo"].value_counts()
    print(f"[ETL] Semaforo -> Rojo: {resumen.get('Rojo', 0)}  "
          f"Amarillo: {resumen.get('Amarillo', 0)}  "
          f"Verde: {resumen.get('Verde', 0)}")

    # 3 · Exportar CSV para el dashboard
    guardar_csv(df)

    # 4 · Motor de alertas
    alertas = generar_alertas(df)
    imprimir_alertas(alertas)


if __name__ == "__main__":
    main()

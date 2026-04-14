"""
generador_ventas.py — Demo #5: Dashboard de Ventas en Tiempo Real
=================================================================
Genera un flujo continuo de transacciones sintéticas simulando un sistema
de facturación en vivo de una empresa de retail/tecnología en Guayaquil.

Los datos se insertan en una base de datos SQLite (ventas_gye.db) y
opcionalmente se exportan a CSV para consumo directo en Power BI.

Modos de ejecución:
  python generador_ventas.py              -> Genera 500 facturas historicas + streaming continuo
  python generador_ventas.py --seed-only  -> Solo genera la carga historica (sin streaming)
  python generador_ventas.py --stream     -> Solo streaming (asume que ya hay datos)
  python generador_ventas.py --export-csv -> Exporta la BD actual a CSV y sale

Autor: Nexo Data Consulting
"""

import sqlite3
import argparse
import random
import time
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).parent / "ventas_gye.db"
CSV_PATH = Path(__file__).parent / "ventas_gye.csv"

fake = Faker("es_ES")
Faker.seed(42)
random.seed(42)

# ── Catálogo de productos (retail / tecnología) ──────────────────────────────

PRODUCTOS = [
    # (nombre, categoria, precio_base_min, precio_base_max)
    ("Laptop HP 15.6\"",           "Computadoras",     620.00,  980.00),
    ("Monitor Samsung 24\"",       "Monitores",        185.00,  320.00),
    ("Impresora Epson EcoTank",    "Impresoras",       210.00,  350.00),
    ("Teclado Logitech MK270",     "Accesorios",        28.00,   45.00),
    ("Mouse Inalámbrico Genius",   "Accesorios",        12.00,   22.00),
    ("Disco Duro Externo 1TB",     "Almacenamiento",    55.00,   85.00),
    ("Router TP-Link AC1200",      "Redes",             42.00,   68.00),
    ("Tablet Samsung Galaxy A9",   "Tablets",          280.00,  420.00),
    ("Parlante JBL Go 3",         "Audio",             35.00,   55.00),
    ("Cámara Web Logitech C920",   "Accesorios",        65.00,   95.00),
]

# Probabilidades de venta por producto (los accesorios se venden más)
PRODUCTO_PESOS = [0.08, 0.07, 0.06, 0.15, 0.18, 0.10, 0.09, 0.05, 0.12, 0.10]

# ── Vendedores ────────────────────────────────────────────────────────────────

VENDEDORES = [
    {"id": "V001", "nombre": "Carlos Herrera",    "zona_base": "Urdesa"},
    {"id": "V002", "nombre": "María Fernández",   "zona_base": "Samborondón"},
    {"id": "V003", "nombre": "Andrés Martínez",   "zona_base": "Centro"},
    {"id": "V004", "nombre": "Lucía Ramírez",     "zona_base": "Vía a la Costa"},
    {"id": "V005", "nombre": "Miguel Torres",     "zona_base": "Vía a Daule"},
]

# ── Zonas geográficas de Guayaquil ────────────────────────────────────────────

ZONAS = [
    {"nombre": "Urdesa",          "lat": -2.1500, "lon": -79.9100},
    {"nombre": "Samborondón",     "lat": -2.1447, "lon": -79.8839},
    {"nombre": "Centro",          "lat": -2.1894, "lon": -79.8831},
    {"nombre": "Vía a la Costa",  "lat": -2.1900, "lon": -79.9600},
    {"nombre": "Vía a Daule",     "lat": -2.1300, "lon": -79.9500},
    {"nombre": "Los Ceibos",      "lat": -2.1700, "lon": -79.9350},
    {"nombre": "Sauces",          "lat": -2.1350, "lon": -79.9050},
    {"nombre": "Alborada",        "lat": -2.1200, "lon": -79.9150},
]

# Cada vendedor vende más en su zona base pero puede vender en otras
ZONA_NOMBRES = [z["nombre"] for z in ZONAS]

# ── Metas diarias y mensuales ─────────────────────────────────────────────────

META_DIARIA_EMPRESA   = 8_500.00   # USD
META_MENSUAL_EMPRESA  = 220_000.00
META_DIARIA_VENDEDOR  = 1_700.00

# ── Métodos de pago ───────────────────────────────────────────────────────────

METODOS_PAGO = ["Efectivo", "Tarjeta Crédito", "Tarjeta Débito", "Transferencia"]
METODO_PESOS = [0.30, 0.35, 0.20, 0.15]


# ---------------------------------------------------------------------------
# FUNCIONES DE GENERACIÓN
# ---------------------------------------------------------------------------

def crear_tabla(conn: sqlite3.Connection):
    """Crea la tabla de ventas si no existe."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            factura_id      TEXT    NOT NULL,
            timestamp       TEXT    NOT NULL,
            fecha           TEXT    NOT NULL,
            hora            TEXT    NOT NULL,
            vendedor_id     TEXT    NOT NULL,
            vendedor_nombre TEXT    NOT NULL,
            zona            TEXT    NOT NULL,
            zona_lat        REAL    NOT NULL,
            zona_lon        REAL    NOT NULL,
            producto        TEXT    NOT NULL,
            categoria       TEXT    NOT NULL,
            cantidad        INTEGER NOT NULL,
            precio_unitario REAL    NOT NULL,
            subtotal        REAL    NOT NULL,
            iva             REAL    NOT NULL,
            total           REAL    NOT NULL,
            metodo_pago     TEXT    NOT NULL,
            cliente_nombre  TEXT    NOT NULL,
            cliente_ruc     TEXT    NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metas (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo            TEXT    NOT NULL,
            periodo         TEXT    NOT NULL,
            meta_usd        REAL    NOT NULL,
            vendedor_id     TEXT,
            descripcion     TEXT
        )
    """)
    conn.commit()


def poblar_metas(conn: sqlite3.Connection):
    """Inserta las metas si la tabla está vacía."""
    count = conn.execute("SELECT COUNT(*) FROM metas").fetchone()[0]
    if count > 0:
        return

    hoy = datetime.now()
    mes_actual = hoy.strftime("%Y-%m")

    # Meta empresa
    conn.execute(
        "INSERT INTO metas (tipo, periodo, meta_usd, descripcion) VALUES (?, ?, ?, ?)",
        ("diaria_empresa", hoy.strftime("%Y-%m-%d"), META_DIARIA_EMPRESA,
         "Meta diaria global de la empresa"),
    )
    conn.execute(
        "INSERT INTO metas (tipo, periodo, meta_usd, descripcion) VALUES (?, ?, ?, ?)",
        ("mensual_empresa", mes_actual, META_MENSUAL_EMPRESA,
         "Meta mensual global de la empresa"),
    )
    # Meta por vendedor
    for v in VENDEDORES:
        conn.execute(
            "INSERT INTO metas (tipo, periodo, meta_usd, vendedor_id, descripcion) VALUES (?, ?, ?, ?, ?)",
            ("diaria_vendedor", hoy.strftime("%Y-%m-%d"), META_DIARIA_VENDEDOR,
             v["id"], f"Meta diaria de {v['nombre']}"),
        )
    conn.commit()


def generar_factura_id(secuencia: int) -> str:
    """Genera un ID de factura tipo 001-001-000000123."""
    return f"001-001-{secuencia:09d}"


def peso_hora(hora: int) -> float:
    """
    Devuelve un peso de probabilidad según la hora del día.
    Simula patrón real de retail: picos a media mañana y tarde.
    """
    if hora < 8:
        return 0.02   # Antes de abrir
    elif hora < 10:
        return 0.08   # Apertura
    elif hora < 13:
        return 0.18   # Mañana fuerte
    elif hora < 14:
        return 0.10   # Almuerzo (baja)
    elif hora < 17:
        return 0.20   # Tarde fuerte
    elif hora < 19:
        return 0.15   # Cierre
    elif hora < 21:
        return 0.05   # Nocturno
    else:
        return 0.01   # Cerrado


def generar_transaccion(ts: datetime, secuencia: int) -> dict:
    """Genera una transacción de venta sintética."""
    # Seleccionar vendedor
    vendedor = random.choice(VENDEDORES)

    # Zona: 60% probabilidad de su zona base, 40% otra zona
    if random.random() < 0.60:
        zona = next(z for z in ZONAS if z["nombre"] == vendedor["zona_base"])
    else:
        zona = random.choice(ZONAS)

    # Producto con pesos
    idx = random.choices(range(len(PRODUCTOS)), weights=PRODUCTO_PESOS, k=1)[0]
    prod_nombre, prod_cat, precio_min, precio_max = PRODUCTOS[idx]
    precio = round(random.uniform(precio_min, precio_max), 2)

    # Cantidad (productos caros = menos unidades)
    if precio > 200:
        cantidad = random.choices([1, 2], weights=[0.85, 0.15], k=1)[0]
    else:
        cantidad = random.choices([1, 2, 3, 4, 5], weights=[0.40, 0.25, 0.15, 0.12, 0.08], k=1)[0]

    subtotal = round(precio * cantidad, 2)
    iva = round(subtotal * 0.15, 2)  # IVA Ecuador 15%
    total = round(subtotal + iva, 2)

    metodo = random.choices(METODOS_PAGO, weights=METODO_PESOS, k=1)[0]

    # Cliente
    cliente_nombre = fake.name()
    # RUC ecuatoriano simulado (13 dígitos)
    ruc_base = fake.numerify(text="09########")
    cliente_ruc = ruc_base + "001"

    return {
        "factura_id":      generar_factura_id(secuencia),
        "timestamp":       ts.isoformat(),
        "fecha":           ts.strftime("%Y-%m-%d"),
        "hora":            ts.strftime("%H:%M:%S"),
        "vendedor_id":     vendedor["id"],
        "vendedor_nombre": vendedor["nombre"],
        "zona":            zona["nombre"],
        "zona_lat":        zona["lat"],
        "zona_lon":        zona["lon"],
        "producto":        prod_nombre,
        "categoria":       prod_cat,
        "cantidad":        cantidad,
        "precio_unitario": precio,
        "subtotal":        subtotal,
        "iva":             iva,
        "total":           total,
        "metodo_pago":     metodo,
        "cliente_nombre":  cliente_nombre,
        "cliente_ruc":     cliente_ruc,
    }


def insertar_venta(conn: sqlite3.Connection, venta: dict):
    """Inserta una venta en la tabla."""
    conn.execute("""
        INSERT INTO ventas (
            factura_id, timestamp, fecha, hora,
            vendedor_id, vendedor_nombre, zona, zona_lat, zona_lon,
            producto, categoria, cantidad, precio_unitario,
            subtotal, iva, total, metodo_pago,
            cliente_nombre, cliente_ruc
        ) VALUES (
            :factura_id, :timestamp, :fecha, :hora,
            :vendedor_id, :vendedor_nombre, :zona, :zona_lat, :zona_lon,
            :producto, :categoria, :cantidad, :precio_unitario,
            :subtotal, :iva, :total, :metodo_pago,
            :cliente_nombre, :cliente_ruc
        )
    """, venta)
    conn.commit()


# ---------------------------------------------------------------------------
# MODOS DE EJECUCIÓN
# ---------------------------------------------------------------------------

def seed_historico(conn: sqlite3.Connection, dias: int = 30, facturas_por_dia: int = 40):
    """
    Genera datos históricos: N días de transacciones con distribución
    horaria realista. Útil para que el dashboard tenga contexto desde el día 1.
    """
    total = dias * facturas_por_dia
    print(f"\n{'='*60}")
    print(f"  SEED HISTORICO -- {total} facturas ({dias} dias x {facturas_por_dia}/dia)")
    print(f"{'='*60}\n")

    hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    secuencia = conn.execute("SELECT COALESCE(MAX(id), 0) FROM ventas").fetchone()[0] + 1

    for d in range(dias, 0, -1):
        dia = hoy - timedelta(days=d)
        # Generar timestamps según patrón horario
        horas_ponderadas = []
        for h in range(8, 21):
            peso = peso_hora(h)
            num_ventas = max(1, int(facturas_por_dia * peso))
            horas_ponderadas.extend([h] * num_ventas)

        random.shuffle(horas_ponderadas)
        horas_seleccionadas = horas_ponderadas[:facturas_por_dia]

        for h in sorted(horas_seleccionadas):
            ts = dia.replace(
                hour=h,
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
            )
            venta = generar_transaccion(ts, secuencia)
            insertar_venta(conn, venta)
            secuencia += 1

        fecha_str = dia.strftime("%Y-%m-%d")
        total_dia = conn.execute(
            "SELECT SUM(total) FROM ventas WHERE fecha = ?", (fecha_str,)
        ).fetchone()[0] or 0
        print(f"  [{fecha_str}]  {facturas_por_dia} facturas  ->  ${total_dia:,.2f}")

    total_global = conn.execute("SELECT SUM(total) FROM ventas").fetchone()[0] or 0
    print(f"\n  TOTAL HISTORICO: ${total_global:,.2f}  ({secuencia - 1} facturas)\n")


def streaming_continuo(conn: sqlite3.Connection, intervalo_min: float = 3.0, intervalo_max: float = 12.0):
    """
    Genera transacciones en tiempo real con intervalos aleatorios.
    Simula el flujo natural de un sistema de facturación activo.
    """
    print(f"\n{'='*60}")
    print(f"  STREAMING EN VIVO -- Simulando facturacion en tiempo real")
    print(f"  Intervalo: {intervalo_min}s - {intervalo_max}s entre facturas")
    print(f"  Presiona Ctrl+C para detener")
    print(f"{'='*60}\n")

    secuencia = conn.execute("SELECT COALESCE(MAX(id), 0) FROM ventas").fetchone()[0] + 1
    count = 0

    try:
        while True:
            ahora = datetime.now()
            hora_actual = ahora.hour

            # Fuera de horario comercial (21-07): generar esporádicamente
            if hora_actual < 7 or hora_actual >= 21:
                if random.random() > 0.05:  # 95% de las veces, espera
                    time.sleep(30)
                    continue

            venta = generar_transaccion(ahora, secuencia)
            insertar_venta(conn, venta)

            count += 1
            secuencia += 1

            # Log en consola con color
            zona_pad = f"{venta['zona']:<18}"
            prod_pad = f"{venta['producto']:<28}"
            total_fmt = f"${venta['total']:>8.2f}"
            vendedor_pad = f"{venta['vendedor_nombre']:<18}"

            print(
                f"  [{venta['hora']}]  "
                f"FAC {venta['factura_id']}  "
                f"{vendedor_pad}  {zona_pad}  {prod_pad}  {total_fmt}"
            )

            # Cada 10 ventas, mostrar resumen del día
            if count % 10 == 0:
                hoy_str = ahora.strftime("%Y-%m-%d")
                total_hoy = conn.execute(
                    "SELECT SUM(total) FROM ventas WHERE fecha = ?", (hoy_str,)
                ).fetchone()[0] or 0
                pct_meta = (total_hoy / META_DIARIA_EMPRESA) * 100
                print(f"\n  -- ACUMULADO HOY: ${total_hoy:,.2f}  ({pct_meta:.1f}% de meta) --\n")

            # Esperar intervalo aleatorio
            espera = random.uniform(intervalo_min, intervalo_max)
            time.sleep(espera)

    except KeyboardInterrupt:
        print(f"\n\n  Streaming detenido. {count} facturas generadas en esta sesión.\n")


def exportar_csv(conn: sqlite3.Connection):
    """Exporta toda la base de datos a CSV."""
    df = pd.read_sql_query("SELECT * FROM ventas ORDER BY timestamp", conn)
    df.to_csv(CSV_PATH, index=False, encoding="utf-8")
    print(f"\n  Exportado: {CSV_PATH}")
    print(f"  Registros: {len(df)}")
    total = df["total"].sum()
    print(f"  Venta total: ${total:,.2f}\n")

    # También exportar metas
    df_metas = pd.read_sql_query("SELECT * FROM metas", conn)
    metas_path = Path(__file__).parent / "metas.csv"
    df_metas.to_csv(metas_path, index=False, encoding="utf-8")
    print(f"  Metas exportadas: {metas_path}\n")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Demo #5 — Generador de Ventas en Tiempo Real (Guayaquil)",
    )
    parser.add_argument("--seed-only", action="store_true",
                        help="Solo genera datos históricos (30 días) y sale")
    parser.add_argument("--stream", action="store_true",
                        help="Solo inicia streaming en vivo (sin seed)")
    parser.add_argument("--export-csv", action="store_true",
                        help="Exporta la BD actual a CSV y sale")
    parser.add_argument("--dias", type=int, default=30,
                        help="Días de historia a generar en el seed (default: 30)")
    parser.add_argument("--facturas-dia", type=int, default=40,
                        help="Facturas por día en el seed (default: 40)")
    parser.add_argument("--intervalo-min", type=float, default=3.0,
                        help="Segundos mínimos entre facturas en streaming")
    parser.add_argument("--intervalo-max", type=float, default=12.0,
                        help="Segundos máximos entre facturas en streaming")
    args = parser.parse_args()

    conn = sqlite3.connect(str(DB_PATH))
    crear_tabla(conn)
    poblar_metas(conn)

    if args.export_csv:
        exportar_csv(conn)
        conn.close()
        return

    if args.stream:
        streaming_continuo(conn, args.intervalo_min, args.intervalo_max)
        conn.close()
        return

    if args.seed_only:
        seed_historico(conn, args.dias, args.facturas_dia)
        exportar_csv(conn)
        conn.close()
        return

    # Modo default: seed + streaming
    ya_tiene_datos = conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0] > 0
    if not ya_tiene_datos:
        seed_historico(conn, args.dias, args.facturas_dia)
        exportar_csv(conn)
    else:
        count = conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
        print(f"\n  BD existente con {count} registros. Saltando seed.")
        print(f"  (Elimina ventas_gye.db para regenerar datos históricos)\n")

    streaming_continuo(conn, args.intervalo_min, args.intervalo_max)
    conn.close()


if __name__ == "__main__":
    main()

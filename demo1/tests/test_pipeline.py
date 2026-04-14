"""Corre processor+exporter con fixtures. Valida flags + xlsx generado."""
import sys
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.processor import DataProcessor  # noqa: E402
from src.exporter import ExcelExporter  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

FIX = Path(__file__).resolve().parent / "fixtures"
OUT = ROOT / "output" / "test_cruce.xlsx"


def main():
    fact = FIX / "facturas_2026_03.txt"
    ret = FIX / "retenciones_2026_03.txt"
    assert fact.exists(), f"falta {fact} — correr make_fixtures.py"
    assert ret.exists(), f"falta {ret}"

    proc = DataProcessor(fact, ret)
    proc.cargar()
    df = proc.cruzar()

    print("\n=== resumen cruce ===")
    print(f"total filas: {len(df)}")
    print(f"sin retención: {df['__SIN_RETENCION'].sum()}")
    print(f"diff monto: {df['__DIFF_MONTO'].sum()}")
    print("\n=== flags por fila ===")
    print(df[["CLAVE_ACCESO", "VALOR_SIN_IMPUESTOS", "RET_BASE_IMPONIBLE",
              "__SIN_RETENCION", "__DIFF_MONTO"]].to_string())

    # expectativas fixtures:
    # fila 1 (PROV A): tiene ret, monto match → ambos False
    # fila 2 (PROV B): SIN retención → __SIN_RETENCION=True
    # fila 3 (PROV C): tiene ret PERO base=450 vs factura=500 → __DIFF_MONTO=True
    # fila 4 (PROV D): SIN retención → __SIN_RETENCION=True
    # fila 5 (PROV E): tiene ret, monto match → ambos False
    assert df["__SIN_RETENCION"].sum() == 2, "esperaba 2 sin retención"
    assert df["__DIFF_MONTO"].sum() == 1, "esperaba 1 diff monto"

    ExcelExporter(OUT).exportar(df)
    assert OUT.exists() and OUT.stat().st_size > 0
    print(f"\n[OK] xlsx generado -> {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

"""DataProcessor — carga TXT/CSV SRI, limpia, cruza facturas vs retenciones."""
from __future__ import annotations
import logging
from pathlib import Path
import pandas as pd

log = logging.getLogger(__name__)

# Columnas típicas reporte SRI (ajustar según archivo real)
COLS_FACTURA = ["RUC_EMISOR", "RAZON_SOCIAL", "CLAVE_ACCESO", "FECHA_EMISION",
                "TIPO_COMPROBANTE", "NUMERO", "VALOR_SIN_IMPUESTOS", "IVA", "IMPORTE_TOTAL"]
COLS_RETENCION = ["RUC_EMISOR", "RAZON_SOCIAL", "CLAVE_ACCESO", "FECHA_EMISION",
                  "NUMERO", "BASE_IMPONIBLE", "VALOR_RETENIDO", "DOC_SUSTENTO"]


class DataProcessor:
    def __init__(self, facturas_path: Path, retenciones_path: Path):
        self.facturas_path = facturas_path
        self.retenciones_path = retenciones_path
        self.df_fact: pd.DataFrame | None = None
        self.df_ret: pd.DataFrame | None = None

    @staticmethod
    def _leer(path: Path) -> pd.DataFrame:
        """Lee TXT SRI. Separador tab por defecto; fallback a ; y ,."""
        for sep in ("\t", ";", ","):
            try:
                df = pd.read_csv(path, sep=sep, dtype=str, encoding="utf-8", engine="python")
                if df.shape[1] > 1:
                    log.info(f"{path.name}: sep='{sep}' cols={df.shape[1]} rows={len(df)}")
                    return df
            except Exception as e:
                log.debug(f"sep={sep} fail: {e}")
        raise ValueError(f"no pude parsear {path}")

    def cargar(self) -> None:
        self.df_fact = self._leer(self.facturas_path)
        self.df_ret = self._leer(self.retenciones_path)
        self._limpiar()

    def _limpiar(self) -> None:
        for df in (self.df_fact, self.df_ret):
            df.columns = [c.strip().upper().replace(" ", "_") for c in df.columns]
        # convert montos a float
        for col in ("VALOR_SIN_IMPUESTOS", "IVA", "IMPORTE_TOTAL"):
            if col in self.df_fact.columns:
                self.df_fact[col] = pd.to_numeric(
                    self.df_fact[col].str.replace(",", ".", regex=False), errors="coerce"
                )
        for col in ("BASE_IMPONIBLE", "VALOR_RETENIDO"):
            if col in self.df_ret.columns:
                self.df_ret[col] = pd.to_numeric(
                    self.df_ret[col].str.replace(",", ".", regex=False), errors="coerce"
                )

    def cruzar(self) -> pd.DataFrame:
        """Merge por CLAVE_ACCESO o DOC_SUSTENTO. Marca discrepancias.

        Retorna DataFrame con cols: __SIN_RETENCION, __DIFF_MONTO (flags bool).
        """
        if self.df_fact is None or self.df_ret is None:
            raise RuntimeError("llama cargar() primero")

        key_fact = "CLAVE_ACCESO"
        key_ret = "DOC_SUSTENTO" if "DOC_SUSTENTO" in self.df_ret.columns else "CLAVE_ACCESO"

        merged = self.df_fact.merge(
            self.df_ret.add_prefix("RET_"),
            left_on=key_fact,
            right_on=f"RET_{key_ret}",
            how="left",
            indicator=True,
        )
        merged["__SIN_RETENCION"] = merged["_merge"] == "left_only"

        # diff monto: base retención vs valor sin impuestos factura (tolerancia 0.01)
        if {"VALOR_SIN_IMPUESTOS", "RET_BASE_IMPONIBLE"}.issubset(merged.columns):
            diff = (merged["VALOR_SIN_IMPUESTOS"].fillna(0) -
                    merged["RET_BASE_IMPONIBLE"].fillna(0)).abs()
            merged["__DIFF_MONTO"] = (diff > 0.01) & (~merged["__SIN_RETENCION"])
        else:
            merged["__DIFF_MONTO"] = False

        merged.drop(columns=["_merge"], inplace=True)
        log.info(f"cruce: total={len(merged)} sin_ret={merged['__SIN_RETENCION'].sum()} diff={merged['__DIFF_MONTO'].sum()}")
        return merged

"""
generador_xml.py — Generador del archivo XML del Anexo Transaccional Simplificado (ATS).

Toma el DataFrame de registros válidos y construye la estructura XML
requerida por el portal del SRI (Ecuador).

Estructura generada:
    <iva>
        <compras>
            <detalleCompras> ... </detalleCompras>
            <detalleCompras> ... </detalleCompras>
            ...
        </compras>
    </iva>
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import pandas as pd


def _add_text_element(parent: ET.Element, tag: str, text: str) -> ET.Element:
    """Agrega un sub-elemento con texto al nodo padre."""
    elem = ET.SubElement(parent, tag)
    elem.text = str(text)
    return elem


def generar_xml_ats(
    df_validos: pd.DataFrame,
    mes: int | None = None,
    anio: int | None = None,
    ruc_informante: str = "1790016919001",
    razon_social_informante: str = "EMPRESA DEMO S.A.",
    directorio_salida: str = ".",
) -> Path:
    """Construye el XML del ATS a partir de los registros válidos.

    Args:
        df_validos: DataFrame con los registros que pasaron validación.
        mes: Mes del periodo fiscal (por defecto el mes actual).
        anio: Año del periodo fiscal (por defecto el año actual).
        ruc_informante: RUC de la empresa declarante.
        razon_social_informante: Razón social de la empresa declarante.
        directorio_salida: Carpeta donde se guardará el XML generado.

    Returns:
        Path al archivo XML generado.
    """
    ahora = datetime.now()
    mes = mes or ahora.month
    anio = anio or ahora.year

    # ---- Nodo raíz ----
    root = ET.Element("iva")

    # ---- Información del periodo ----
    _add_text_element(root, "TipoIDInformante", "R")
    _add_text_element(root, "IdInformante", ruc_informante)
    _add_text_element(root, "razonSocial", razon_social_informante)
    _add_text_element(root, "Anio", str(anio))
    _add_text_element(root, "Mes", f"{mes:02d}")

    # ---- Nodo compras ----
    compras_node = ET.SubElement(root, "compras")

    for _, row in df_validos.iterrows():
        detalle = ET.SubElement(compras_node, "detalleCompras")

        _add_text_element(detalle, "codSustento", row["codigo_sustento"])
        _add_text_element(detalle, "tpIdProv", "01")  # RUC
        _add_text_element(detalle, "idProv", row["ruc_proveedor"])
        _add_text_element(detalle, "tipoComprobante", row["tipo_comprobante"])

        # Datos del comprobante
        _add_text_element(detalle, "fechaRegistro", row.get("fecha_emision", ""))
        _add_text_element(detalle, "establecimiento", row.get("establecimiento", ""))
        _add_text_element(detalle, "puntoEmision", row.get("punto_emision", ""))
        _add_text_element(detalle, "secuencial", row.get("secuencial", ""))
        _add_text_element(detalle, "autorizacion", row.get("autorizacion", ""))

        # Bases imponibles
        _add_text_element(
            detalle,
            "baseNoGraIva",
            f"{row.get('base_no_gravada', 0.0):.2f}",
        )
        _add_text_element(
            detalle,
            "baseImponible",
            f"{row['base_imponible']:.2f}",
        )
        _add_text_element(
            detalle,
            "baseImpGrav",
            f"{row['base_imponible']:.2f}",
        )
        _add_text_element(detalle, "montoIva", f"{row['monto_iva']:.2f}")

        # Retenciones
        _add_text_element(
            detalle,
            "valRetBien10",
            f"{row['valor_retenido_iva']:.2f}"
            if row["porcentaje_retencion_iva"] == 0.10
            else "0.00",
        )
        _add_text_element(
            detalle,
            "valRetServ20",
            f"{row['valor_retenido_iva']:.2f}"
            if row["porcentaje_retencion_iva"] == 0.20
            else "0.00",
        )
        _add_text_element(
            detalle,
            "valorRetBienes",
            f"{row['valor_retenido_iva']:.2f}"
            if row["porcentaje_retencion_iva"] == 0.30
            else "0.00",
        )
        _add_text_element(
            detalle,
            "valRetServ50",
            "0.00",
        )
        _add_text_element(
            detalle,
            "valorRetServicios",
            f"{row['valor_retenido_iva']:.2f}"
            if row["porcentaje_retencion_iva"] == 0.70
            else "0.00",
        )
        _add_text_element(
            detalle,
            "valRetServ100",
            f"{row['valor_retenido_iva']:.2f}"
            if row["porcentaje_retencion_iva"] == 1.00
            else "0.00",
        )

        # Retención en la fuente (renta)
        _add_text_element(
            detalle,
            "valorRetRenta",
            f"{row.get('valor_retenido_renta', 0.0):.2f}",
        )

    # ---- Indentar para lectura humana ----
    ET.indent(root, space="  ")

    # ---- Escribir archivo ----
    nombre_archivo = f"ats_generado_{mes:02d}_{anio}.xml"
    ruta_salida = Path(directorio_salida) / nombre_archivo

    tree = ET.ElementTree(root)
    tree.write(
        str(ruta_salida),
        encoding="utf-8",
        xml_declaration=True,
    )

    return ruta_salida


# ---------------------------------------------------------------------------
# Ejecución directa
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from mock_data import generar_datos_compras
    from validador_sri import validar_compras

    df = generar_datos_compras()
    validos, _ = validar_compras(df)
    ruta = generar_xml_ats(validos)
    print(f"XML generado en: {ruta.resolve()}")

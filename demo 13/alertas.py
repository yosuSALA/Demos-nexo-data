"""
alertas.py — Demo #13: Sistema de Alertas Automáticas de Precios
Detecta productos con precios no competitivos y genera notificaciones.
"""
import logging
import pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

UMBRAL_ALERTA_PCT  = 3.0   # % mínimo de diferencia para generar alerta
VOLUMEN_MENSUAL    = 50    # unidades/mes por SKU (para estimación de impacto)
NOMBRE_EMPRESA     = "Mi Empresa S.A."
NOMBRE_COMPETIDOR  = "Competidor A"


# ─── Detección de alertas ───────────────────────────────────────────────────

def detectar_alertas(
    df_comparacion: pd.DataFrame,
    umbral_pct: float = UMBRAL_ALERTA_PCT,
) -> pd.DataFrame:
    """
    Filtra los productos donde el competidor tiene un precio menor al nuestro
    por más de `umbral_pct` puntos porcentuales.

    Args:
        df_comparacion: DataFrame resultado de comparador.calcular_diferencias()
        umbral_pct:     Porcentaje mínimo de diferencia para considerar alerta

    Returns:
        DataFrame con solo los productos en situación de alerta, ordenados
        de mayor a menor diferencia.
    """
    if df_comparacion.empty:
        logger.warning("DataFrame de comparación vacío; no hay alertas que generar.")
        return df_comparacion

    df_alertas = (
        df_comparacion[df_comparacion["diff_porcentual"] > umbral_pct]
        .copy()
        .sort_values("diff_porcentual", ascending=False)
        .reset_index(drop=True)
    )

    logger.info(
        f"Alertas detectadas: {len(df_alertas)} productos "
        f"con diferencia > {umbral_pct:.0f}% respecto a {NOMBRE_COMPETIDOR}"
    )
    return df_alertas


# ─── Cálculo de impacto económico ───────────────────────────────────────────

def calcular_impacto_mensual(
    df_alertas:      pd.DataFrame,
    volumen_mensual: int = VOLUMEN_MENSUAL,
) -> dict:
    """
    Estima el impacto económico mensual de no ajustar precios.

    Returns:
        dict con métricas de impacto.
    """
    if df_alertas.empty:
        return {"perdida_total": 0.0, "perdida_por_producto": pd.Series(dtype=float)}

    perdida_por_producto = (df_alertas["diff_absoluta"] * volumen_mensual).round(2)
    return {
        "perdida_total":        round(perdida_por_producto.sum(), 2),
        "perdida_por_producto": perdida_por_producto,
        "mayor_perdida_sku":    df_alertas.loc[perdida_por_producto.idxmax(), "nombre"],
        "mayor_perdida_monto":  perdida_por_producto.max(),
    }


# ─── Formateo del mensaje de alerta ─────────────────────────────────────────

def formatear_alerta_email(
    df_alertas:      pd.DataFrame,
    volumen_mensual: int  = VOLUMEN_MENSUAL,
    umbral_pct:      float = UMBRAL_ALERTA_PCT,
) -> str:
    """
    Genera el cuerpo de un correo de alerta listo para enviar al gerente de ventas.

    Args:
        df_alertas:      DataFrame filtrado de productos en alerta
        volumen_mensual: Unidades vendidas por mes por SKU (para proyección)
        umbral_pct:      Umbral utilizado en la detección (para referencia en el texto)

    Returns:
        String con el mensaje completo formateado.
    """
    if df_alertas.empty:
        return (
            "✅  Sin alertas activas: todos los precios monitoreados "
            f"son competitivos (diferencia ≤ {umbral_pct:.0f}%)."
        )

    fecha   = datetime.now().strftime("%d/%m/%Y  %H:%M hs")
    impacto = calcular_impacto_mensual(df_alertas, volumen_mensual)

    # ── Tabla de productos (trunca nombres largos para que el email se vea limpio) ──
    MAX_NOMBRE = 52
    lineas = []
    for _, fila in df_alertas.iterrows():
        nombre_corto = (
            fila["nombre"][:MAX_NOMBRE] + "…"
            if len(fila["nombre"]) > MAX_NOMBRE
            else fila["nombre"]
        )
        perdida_sku = fila["diff_absoluta"] * volumen_mensual
        lineas.append(
            f"  {'▲' if fila['diff_porcentual'] >= 10 else '►'} "
            f"{nombre_corto:<54}"
            f"Nuestro: ${fila['precio_empresa']:>6.2f}  |  "
            f"Compet.: ${fila['precio_competidor']:>6.2f}  |  "
            f"Dif.: {fila['diff_porcentual']:>+5.1f}%  |  "
            f"Pérdida est.: ${perdida_sku:>8.2f}/mes"
        )

    tabla_productos = "\n".join(lineas)

    # ── Clasificación de urgencia ────────────────────────────────────────────
    criticos  = df_alertas[df_alertas["diff_porcentual"] >= 10]
    moderados = df_alertas[(df_alertas["diff_porcentual"] >= umbral_pct) & (df_alertas["diff_porcentual"] < 10)]
    nivel_alerta = "🔴 CRÍTICA" if len(criticos) >= 3 else ("🟠 MODERADA" if len(criticos) >= 1 else "🟡 BAJA")

    mensaje = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║          ALERTA DE INTELIGENCIA COMPETITIVA — PRECIOS                   ║
╚══════════════════════════════════════════════════════════════════════════╝

De:      Sistema de Monitoreo Automático <precios@miempresa.com>
Para:    Gerente de Ventas <gerente@miempresa.com>
CC:      Dirección Comercial <comercial@miempresa.com>
Fecha:   {fecha}
Asunto:  ⚠️  [{nivel_alerta}] {len(df_alertas)} producto(s) no competitivos — acción requerida

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Estimado/a Gerente de Ventas,

El sistema de monitoreo automático detectó {len(df_alertas)} producto(s) en los que
{NOMBRE_COMPETIDOR} ofrece un precio inferior al nuestro por más del {umbral_pct:.0f}%.

Si no se ajustan precios, estimamos una pérdida de ingresos de
${impacto['perdida_total']:,.2f} USD durante el próximo mes *.

━━━ RESUMEN EJECUTIVO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Nivel de alerta:               {nivel_alerta}
  Productos en alerta total:     {len(df_alertas)}
    · Críticos  (≥ 10%):         {len(criticos)}
    · Moderados ({umbral_pct:.0f}–9.9%):       {len(moderados)}
  Mayor diferencia detectada:    {df_alertas['diff_porcentual'].max():.1f}% → {df_alertas.iloc[0]['nombre'][:50]}
  Diferencia promedio:           {df_alertas['diff_porcentual'].mean():.1f}%
  Pérdida estimada mensual:      ${impacto['perdida_total']:,.2f} USD
  SKU con mayor impacto:         {impacto['mayor_perdida_sku'][:50]}
                                 (${impacto['mayor_perdida_monto']:,.2f}/mes)

━━━ DETALLE POR PRODUCTO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▲ = diferencia crítica (≥10%)   ► = diferencia moderada (3–9.9%)

{tabla_productos}

━━━ ACCIÓN RECOMENDADA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Revisar la lista de precios con el equipo comercial en las próximas
     48 horas hábiles.
  2. Priorizar los productos marcados con ▲ (diferencia crítica ≥ 10%).
  3. Actualizar el ERP / sistema de punto de venta con los nuevos precios.
  4. Considerar margen mínimo aceptable antes de igualar al competidor.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

* Estimación basada en un volumen de {volumen_mensual} unidades/mes por SKU.
  Ajustar según el histórico real de ventas de cada producto.

Fuente de datos:  {NOMBRE_COMPETIDOR} — scraping automatizado
Próxima revisión: mañana a las 08:00 hs (cron diario)

[Mensaje generado automáticamente — responder a precios@miempresa.com]
"""
    return mensaje


# ─── Ejecución directa (módulo independiente con datos de ejemplo) ──────────

if __name__ == "__main__":
    # Datos sintéticos para probar el módulo sin necesidad de ejecutar el scraper
    datos_ejemplo = {
        "nombre": [
            "Libro A: El Gran Clásico",
            "Libro B: Aventuras Modernas",
            "Libro C: Ciencia para Todos",
            "Libro D: Historia Universal",
            "Libro E: Poesía Selecta",
        ],
        "precio_empresa":    [55.00, 42.00, 28.00, 67.00, 19.00],
        "precio_competidor": [48.00, 41.50, 25.00, 70.00, 19.50],
        "disponibilidad":    ["In Stock", "In Stock", "In Stock", "Out of Stock", "In Stock"],
        "diff_absoluta":     [7.00,   0.50,  3.00,  -3.00,  -0.50],
        "diff_porcentual":   [12.73,  1.19, 10.71,  -4.48,  -2.63],
    }
    df_ejemplo = pd.DataFrame(datos_ejemplo)

    df_alertas_ejemplo = detectar_alertas(df_ejemplo, umbral_pct=UMBRAL_ALERTA_PCT)
    mensaje = formatear_alerta_email(df_alertas_ejemplo, volumen_mensual=VOLUMEN_MENSUAL)
    print(mensaje)

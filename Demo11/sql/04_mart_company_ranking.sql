-- =============================================================================
-- MART 4: Ranking de entidades por total de activos
--
-- Estrategia para total de activos (compatible con ambos formatos de account_code):
--   Si existe account_code = '1' (datos ANUAL): usar ese valor directamente.
--   Si no existe (datos MENSUAL): sumar todas las hojas cuyo primer dígito = '1'.
--   Una "hoja" es un account_code que no tiene ningún código hijo en el mismo
--   (ruc, date, period_type).
--
-- Grain: una fila por (ruc, fiscal_year, period_type)
-- =============================================================================

CREATE OR REPLACE VIEW mart_company_ranking AS
WITH
-- Detecta filas con cuenta raíz de activos (solo en datos ANUAL)
root_assets AS (
    SELECT ruc, date, period_type, value AS total_activos
    FROM financial_statements
    WHERE account_code = '1'
),
-- Hojas de activos para datos MENSUAL (sin cuenta raíz '1')
leaf_assets AS (
    SELECT fs.ruc, fs.date, fs.period_type, SUM(fs.value) AS total_activos
    FROM financial_statements fs
    WHERE LEFT(fs.account_code, 1) = '1'
      AND NOT EXISTS (
          SELECT 1 FROM financial_statements child
          WHERE child.ruc         = fs.ruc
            AND child.date        = fs.date
            AND child.period_type = fs.period_type
            AND child.account_code LIKE fs.account_code || '%'
            AND child.account_code <> fs.account_code
      )
      -- Solo aplica cuando NO existe ya una cuenta raíz '1' para ese registro
      AND NOT EXISTS (
          SELECT 1 FROM financial_statements root
          WHERE root.ruc         = fs.ruc
            AND root.date        = fs.date
            AND root.period_type = fs.period_type
            AND root.account_code = '1'
      )
    GROUP BY fs.ruc, fs.date, fs.period_type
),
-- Unión de ambas estrategias
asset_totals AS (
    SELECT
        ra.ruc,
        fs.company_name,
        fs.entity_type,
        fs.entity_subtype,
        ra.date,
        YEAR(CAST(ra.date AS DATE)) AS fiscal_year,
        ra.period_type,
        ra.total_activos
    FROM root_assets ra
    JOIN financial_statements fs
      ON fs.ruc = ra.ruc AND fs.date = ra.date AND fs.period_type = ra.period_type
      AND fs.account_code = '1'

    UNION ALL

    SELECT
        la.ruc,
        fs2.company_name,
        fs2.entity_type,
        fs2.entity_subtype,
        la.date,
        YEAR(CAST(la.date AS DATE)) AS fiscal_year,
        la.period_type,
        la.total_activos
    FROM leaf_assets la
    JOIN financial_statements fs2
      ON fs2.ruc = la.ruc AND fs2.date = la.date AND fs2.period_type = la.period_type
    GROUP BY la.ruc, fs2.company_name, fs2.entity_type, fs2.entity_subtype,
             la.date, YEAR(CAST(la.date AS DATE)), la.period_type, la.total_activos
),
ranked AS (
    SELECT
        ruc,
        company_name,
        entity_type,
        entity_subtype,
        fiscal_year,
        period_type,
        total_activos,

        RANK() OVER (
            PARTITION BY fiscal_year, period_type
            ORDER BY total_activos DESC
        ) AS ranking_global,

        RANK() OVER (
            PARTITION BY fiscal_year, period_type, entity_type
            ORDER BY total_activos DESC
        ) AS ranking_por_sector,

        ROUND(
            PERCENT_RANK() OVER (
                PARTITION BY fiscal_year, period_type
                ORDER BY total_activos
            ) * 100, 1
        ) AS percentil,

        LAG(total_activos) OVER (
            PARTITION BY ruc, period_type ORDER BY fiscal_year
        ) AS activos_anio_anterior
    FROM asset_totals
)
SELECT
    ruc,
    company_name,
    entity_type,
    entity_subtype,
    fiscal_year,
    period_type,
    ROUND(total_activos,          2) AS total_activos,
    ranking_global,
    ranking_por_sector,
    percentil,
    ROUND(activos_anio_anterior,  2) AS activos_anio_anterior,
    ROUND(total_activos - activos_anio_anterior, 2) AS variacion_absoluta,
    ROUND(
        (total_activos - activos_anio_anterior) /
        NULLIF(ABS(activos_anio_anterior), 0) * 100,
        2
    )                                AS variacion_pct_yoy
FROM ranked
ORDER BY fiscal_year DESC, period_type, ranking_global;

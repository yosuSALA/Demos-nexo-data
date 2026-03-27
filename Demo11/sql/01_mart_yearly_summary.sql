-- =============================================================================
-- MART 1: Yearly summary by company
-- Grain: one row per (ruc, fiscal_year, period_type)
-- =============================================================================

CREATE OR REPLACE VIEW mart_yearly_summary AS
SELECT
    sector_code,
    entity_type,
    ruc,
    company_name,
    YEAR(CAST(date AS DATE))          AS fiscal_year,
    period_type,
    COUNT(DISTINCT account_code)      AS accounts_reported,
    SUM(value)                        AS total_value,
    SUM(CASE WHEN value > 0 THEN value ELSE 0 END) AS total_positive,
    SUM(CASE WHEN value < 0 THEN value ELSE 0 END) AS total_negative,
    MIN(value)                        AS min_value,
    MAX(value)                        AS max_value
FROM financial_statements
WHERE date IS NOT NULL
GROUP BY
    sector_code,
    entity_type,
    ruc,
    company_name,
    YEAR(CAST(date AS DATE)),
    period_type
ORDER BY fiscal_year DESC, total_value DESC;

-- Preview
-- SELECT * FROM mart_yearly_summary WHERE period_type = 'ANUAL' LIMIT 10;

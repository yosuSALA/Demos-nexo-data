-- =============================================================================
-- BI VIEWS — ready-to-query surfaces for dashboards
-- Each view is self-contained: a BI tool can point directly at it.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- V1: Company balance sheet snapshot
-- One row per company per year — KPI cards and year-over-year comparisons.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_balance_sheet AS
SELECT
    dc.ruc,
    dc.company_name,
    dc.sector_name,
    dd.fiscal_year,
    ff.period_type,
    SUM(ff.total_assets)      AS total_assets,
    SUM(ff.total_liabilities) AS total_liabilities,
    SUM(ff.total_equity)      AS total_equity,
    SUM(ff.total_income)      AS total_income,
    SUM(ff.total_expenses)    AS total_expenses,
    SUM(ff.total_income)  - SUM(ff.total_expenses)   AS net_result,
    SUM(ff.total_assets)  - SUM(ff.total_liabilities) AS net_worth,
    ROUND(
        SUM(ff.total_liabilities) /
        NULLIF(SUM(ff.total_assets), 0), 4
    ) AS leverage_ratio
FROM financial_fact    ff
JOIN dim_company dc ON dc.company_key = ff.company_key
JOIN dim_date    dd ON dd.date_key    = ff.date_key
WHERE ff.total_assets IS NOT NULL
   OR ff.total_liabilities IS NOT NULL
GROUP BY dc.ruc, dc.company_name, dc.sector_name, dd.fiscal_year, ff.period_type;

-- ---------------------------------------------------------------------------
-- V2: Account drill-down
-- Full hierarchy expanded — for treemaps and drill-through reports.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_account_drilldown AS
SELECT
    dc.ruc,
    dc.company_name,
    dc.sector_name,
    dd.fiscal_year,
    ff.period_type,
    da.account_class,
    da.class_code,
    da.class_name,
    da.group_code,
    da.group_name,
    da.subgroup_code,
    da.subgroup_name,
    da.account_code,
    da.account_name,
    da.account_level,
    da.is_leaf,
    ff.value
FROM financial_fact   ff
JOIN dim_company dc ON dc.company_key = ff.company_key
JOIN dim_account da ON da.account_key = ff.account_key
JOIN dim_date    dd ON dd.date_key    = ff.date_key;

-- ---------------------------------------------------------------------------
-- V3: Sector aggregates
-- Sector-level totals — for industry benchmark dashboards.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_sector_aggregates AS
SELECT
    dc.sector_code,
    dc.sector_name,
    dd.fiscal_year,
    ff.period_type,
    COUNT(DISTINCT dc.ruc)    AS companies_count,
    SUM(ff.total_assets)      AS sector_assets,
    SUM(ff.total_liabilities) AS sector_liabilities,
    SUM(ff.total_equity)      AS sector_equity,
    SUM(ff.total_income)      AS sector_income,
    SUM(ff.total_expenses)    AS sector_expenses,
    AVG(
        SUM(ff.total_liabilities) /
        NULLIF(SUM(ff.total_assets), 0)
    ) OVER (PARTITION BY dc.sector_code, dd.fiscal_year, ff.period_type)
        AS avg_leverage_ratio
FROM financial_fact   ff
JOIN dim_company dc ON dc.company_key = ff.company_key
JOIN dim_date    dd ON dd.date_key    = ff.date_key
GROUP BY dc.sector_code, dc.sector_name, dd.fiscal_year, ff.period_type;

-- ---------------------------------------------------------------------------
-- V4: Company ranking by total assets
-- Includes YoY growth — for leaderboard and ranking widgets.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_company_ranking AS
WITH base AS (
    SELECT
        dc.ruc,
        dc.company_name,
        dc.sector_name,
        dd.fiscal_year,
        ff.period_type,
        SUM(ff.total_assets) AS total_assets
    FROM financial_fact   ff
    JOIN dim_company dc ON dc.company_key = ff.company_key
    JOIN dim_date    dd ON dd.date_key    = ff.date_key
    WHERE ff.total_assets IS NOT NULL
    GROUP BY dc.ruc, dc.company_name, dc.sector_name, dd.fiscal_year, ff.period_type
)
SELECT
    *,
    RANK() OVER (
        PARTITION BY fiscal_year, period_type
        ORDER BY total_assets DESC
    ) AS rank_global,
    RANK() OVER (
        PARTITION BY fiscal_year, period_type, sector_name
        ORDER BY total_assets DESC
    ) AS rank_in_sector,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY fiscal_year, period_type
        ORDER BY total_assets
    ) * 100, 1) AS percentile,
    LAG(total_assets) OVER (
        PARTITION BY ruc, period_type ORDER BY fiscal_year
    ) AS prev_year_assets,
    ROUND(
        (total_assets - LAG(total_assets) OVER (
            PARTITION BY ruc, period_type ORDER BY fiscal_year
        )) /
        NULLIF(ABS(LAG(total_assets) OVER (
            PARTITION BY ruc, period_type ORDER BY fiscal_year
        )), 0) * 100, 2
    ) AS yoy_growth_pct
FROM base
ORDER BY fiscal_year DESC, period_type, rank_global;

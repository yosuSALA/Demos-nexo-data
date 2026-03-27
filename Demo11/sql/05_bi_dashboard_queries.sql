-- =============================================================================
-- BI DASHBOARD QUERIES
-- Engine  : DuckDB
-- Source  : star schema (financial_fact + dim_* tables) and BI views
-- Sections:
--   A. Yearly asset totals
--   B. Liabilities vs assets comparison
--   C. Entity ranking by total assets
--   D. Growth trends over time
-- =============================================================================


-- =============================================================================
-- A. YEARLY ASSET TOTALS
-- =============================================================================

-- ---------------------------------------------------------------------------
-- A1. Total assets per year — system-wide (KPI card / area chart)
-- ---------------------------------------------------------------------------
SELECT
    dd.fiscal_year,
    ff.period_type,
    COUNT(DISTINCT dc.ruc)                 AS companies_reporting,
    ROUND(SUM(ff.total_assets), 2)         AS total_assets,
    ROUND(AVG(ff.total_assets), 2)         AS avg_assets_per_company,
    ROUND(MIN(ff.total_assets), 2)         AS min_company_assets,
    ROUND(MAX(ff.total_assets), 2)         AS max_company_assets
FROM financial_fact    ff
JOIN dim_date    dd ON dd.date_key    = ff.date_key
JOIN dim_company dc ON dc.company_key = ff.company_key
WHERE ff.total_assets IS NOT NULL
  AND ff.period_type  = 'ANUAL'
GROUP BY dd.fiscal_year, ff.period_type
ORDER BY dd.fiscal_year;


-- ---------------------------------------------------------------------------
-- A2. Total assets per year, broken down by sector (stacked bar chart)
-- ---------------------------------------------------------------------------
SELECT
    dd.fiscal_year,
    dc.sector_name,
    ROUND(SUM(ff.total_assets), 2)         AS sector_assets,
    COUNT(DISTINCT dc.ruc)                 AS companies_count,
    ROUND(
        SUM(ff.total_assets) * 100.0 /
        SUM(SUM(ff.total_assets)) OVER (PARTITION BY dd.fiscal_year),
        2
    )                                      AS pct_of_total
FROM financial_fact    ff
JOIN dim_date    dd ON dd.date_key    = ff.date_key
JOIN dim_company dc ON dc.company_key = ff.company_key
WHERE ff.total_assets IS NOT NULL
  AND ff.period_type  = 'ANUAL'
GROUP BY dd.fiscal_year, dc.sector_name
ORDER BY dd.fiscal_year, sector_assets DESC;


-- ---------------------------------------------------------------------------
-- A3. Total assets per year broken down by account group (treemap data)
-- Shows which account groups (101, 102…) drive asset totals.
-- ---------------------------------------------------------------------------
SELECT
    dd.fiscal_year,
    da.class_name,
    da.group_code,
    da.group_name,
    ROUND(SUM(ff.value), 2)                AS group_total,
    COUNT(DISTINCT dc.ruc)                 AS companies_count,
    ROUND(
        SUM(ff.value) * 100.0 /
        SUM(SUM(ff.value)) OVER (PARTITION BY dd.fiscal_year, da.class_name),
        2
    )                                      AS pct_within_class
FROM financial_fact    ff
JOIN dim_date    dd ON dd.date_key    = ff.date_key
JOIN dim_company dc ON dc.company_key = ff.company_key
JOIN dim_account da ON da.account_key = ff.account_key
WHERE da.account_class = 'Assets'
  AND da.account_level = 3                -- group level (3-digit codes e.g. 101)
  AND ff.period_type   = 'ANUAL'
GROUP BY dd.fiscal_year, da.class_name, da.group_code, da.group_name
ORDER BY dd.fiscal_year, group_total DESC;


-- =============================================================================
-- B. LIABILITIES VS ASSETS COMPARISON
-- =============================================================================

-- ---------------------------------------------------------------------------
-- B1. System-wide assets, liabilities, equity per year (grouped bar chart)
-- ---------------------------------------------------------------------------
SELECT
    dd.fiscal_year,
    ROUND(SUM(ff.total_assets),      2)    AS total_assets,
    ROUND(SUM(ff.total_liabilities), 2)    AS total_liabilities,
    ROUND(SUM(ff.total_equity),      2)    AS total_equity,
    ROUND(SUM(ff.total_assets) - SUM(ff.total_liabilities), 2) AS net_worth,
    ROUND(
        SUM(ff.total_liabilities) /
        NULLIF(SUM(ff.total_assets), 0),
        4
    )                                      AS system_leverage_ratio
FROM financial_fact    ff
JOIN dim_date    dd ON dd.date_key    = ff.date_key
WHERE ff.period_type = 'ANUAL'
  AND (ff.total_assets IS NOT NULL OR ff.total_liabilities IS NOT NULL)
GROUP BY dd.fiscal_year
ORDER BY dd.fiscal_year;


-- ---------------------------------------------------------------------------
-- B2. Liabilities vs assets by sector per year (heat map / bubble chart)
-- ---------------------------------------------------------------------------
SELECT
    dd.fiscal_year,
    dc.sector_name,
    ROUND(SUM(ff.total_assets),      2)    AS total_assets,
    ROUND(SUM(ff.total_liabilities), 2)    AS total_liabilities,
    ROUND(SUM(ff.total_equity),      2)    AS total_equity,
    ROUND(
        SUM(ff.total_liabilities) /
        NULLIF(SUM(ff.total_assets), 0),
        4
    )                                      AS leverage_ratio,
    -- Solvency flag: leverage > 0.90 signals stress
    CASE
        WHEN SUM(ff.total_liabilities) /
             NULLIF(SUM(ff.total_assets), 0) > 0.90 THEN 'High Risk'
        WHEN SUM(ff.total_liabilities) /
             NULLIF(SUM(ff.total_assets), 0) > 0.70 THEN 'Moderate'
        ELSE 'Healthy'
    END                                    AS solvency_flag
FROM financial_fact    ff
JOIN dim_date    dd ON dd.date_key    = ff.date_key
JOIN dim_company dc ON dc.company_key = ff.company_key
WHERE ff.period_type = 'ANUAL'
  AND (ff.total_assets IS NOT NULL OR ff.total_liabilities IS NOT NULL)
GROUP BY dd.fiscal_year, dc.sector_name
ORDER BY dd.fiscal_year, leverage_ratio DESC;


-- ---------------------------------------------------------------------------
-- B3. Per-company liabilities vs assets — latest available year
-- Use as the source for a scatter plot (X = assets, Y = liabilities)
-- ---------------------------------------------------------------------------
WITH latest_year AS (
    SELECT MAX(fiscal_year) AS yr FROM dim_date
    WHERE period_type = 'ANUAL'
)
SELECT
    dc.ruc,
    dc.company_name,
    dc.sector_name,
    dd.fiscal_year,
    ROUND(SUM(ff.total_assets),      2)    AS total_assets,
    ROUND(SUM(ff.total_liabilities), 2)    AS total_liabilities,
    ROUND(SUM(ff.total_equity),      2)    AS total_equity,
    ROUND(
        SUM(ff.total_liabilities) /
        NULLIF(SUM(ff.total_assets), 0),
        4
    )                                      AS leverage_ratio
FROM financial_fact    ff
JOIN dim_date    dd ON dd.date_key    = ff.date_key
JOIN dim_company dc ON dc.company_key = ff.company_key
JOIN latest_year ly ON dd.fiscal_year = ly.yr
WHERE ff.period_type = 'ANUAL'
  AND (ff.total_assets IS NOT NULL OR ff.total_liabilities IS NOT NULL)
GROUP BY dc.ruc, dc.company_name, dc.sector_name, dd.fiscal_year
ORDER BY total_assets DESC;


-- =============================================================================
-- C. ENTITY RANKING BY TOTAL ASSETS
-- =============================================================================

-- ---------------------------------------------------------------------------
-- C1. Global ranking — top N companies by assets, latest year (leaderboard)
-- ---------------------------------------------------------------------------
WITH latest_year AS (
    SELECT MAX(fiscal_year) AS yr FROM dim_date WHERE period_type = 'ANUAL'
)
SELECT
    RANK() OVER (ORDER BY SUM(ff.total_assets) DESC)  AS rank_global,
    dc.ruc,
    dc.company_name,
    dc.sector_name,
    dd.fiscal_year,
    ROUND(SUM(ff.total_assets),      2)                AS total_assets,
    ROUND(SUM(ff.total_liabilities), 2)                AS total_liabilities,
    ROUND(SUM(ff.total_equity),      2)                AS total_equity,
    ROUND(
        SUM(ff.total_assets) * 100.0 /
        SUM(SUM(ff.total_assets)) OVER (),
        2
    )                                                  AS pct_of_system,
    ROUND(
        SUM(SUM(ff.total_assets)) OVER (
            ORDER BY SUM(ff.total_assets) DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) * 100.0 /
        SUM(SUM(ff.total_assets)) OVER (),
        2
    )                                                  AS cumulative_pct  -- Pareto
FROM financial_fact    ff
JOIN dim_date    dd ON dd.date_key    = ff.date_key
JOIN dim_company dc ON dc.company_key = ff.company_key
JOIN latest_year ly ON dd.fiscal_year = ly.yr
WHERE ff.total_assets IS NOT NULL
  AND ff.period_type  = 'ANUAL'
GROUP BY dc.ruc, dc.company_name, dc.sector_name, dd.fiscal_year
ORDER BY rank_global
LIMIT 20;


-- ---------------------------------------------------------------------------
-- C2. Ranking per sector — top 5 companies within each sector
-- ---------------------------------------------------------------------------
WITH ranked AS (
    SELECT
        dc.ruc,
        dc.company_name,
        dc.sector_name,
        dd.fiscal_year,
        SUM(ff.total_assets) AS total_assets,
        RANK() OVER (
            PARTITION BY dc.sector_name, dd.fiscal_year
            ORDER BY SUM(ff.total_assets) DESC
        ) AS rank_in_sector
    FROM financial_fact    ff
    JOIN dim_date    dd ON dd.date_key    = ff.date_key
    JOIN dim_company dc ON dc.company_key = ff.company_key
    WHERE ff.total_assets IS NOT NULL
      AND ff.period_type  = 'ANUAL'
    GROUP BY dc.ruc, dc.company_name, dc.sector_name, dd.fiscal_year
)
SELECT
    fiscal_year,
    sector_name,
    rank_in_sector,
    ruc,
    company_name,
    ROUND(total_assets, 2) AS total_assets
FROM ranked
WHERE rank_in_sector <= 5
ORDER BY fiscal_year DESC, sector_name, rank_in_sector;


-- ---------------------------------------------------------------------------
-- C3. Ranking volatility — companies that moved ≥10 positions year-over-year
-- ---------------------------------------------------------------------------
WITH annual_rank AS (
    SELECT
        dc.ruc,
        dc.company_name,
        dc.sector_name,
        dd.fiscal_year,
        SUM(ff.total_assets) AS total_assets,
        RANK() OVER (
            PARTITION BY dd.fiscal_year
            ORDER BY SUM(ff.total_assets) DESC
        ) AS rank_global
    FROM financial_fact    ff
    JOIN dim_date    dd ON dd.date_key    = ff.date_key
    JOIN dim_company dc ON dc.company_key = ff.company_key
    WHERE ff.total_assets IS NOT NULL
      AND ff.period_type  = 'ANUAL'
    GROUP BY dc.ruc, dc.company_name, dc.sector_name, dd.fiscal_year
)
SELECT
    curr.fiscal_year,
    curr.ruc,
    curr.company_name,
    curr.sector_name,
    prev.rank_global                       AS rank_prev_year,
    curr.rank_global                       AS rank_curr_year,
    prev.rank_global - curr.rank_global    AS rank_change,   -- positive = moved up
    ROUND(curr.total_assets, 2)            AS total_assets,
    ROUND(prev.total_assets, 2)            AS prev_total_assets
FROM annual_rank curr
JOIN annual_rank prev
  ON prev.ruc         = curr.ruc
 AND prev.fiscal_year = curr.fiscal_year - 1
WHERE ABS(prev.rank_global - curr.rank_global) >= 10
ORDER BY curr.fiscal_year DESC, ABS(prev.rank_global - curr.rank_global) DESC;


-- =============================================================================
-- D. GROWTH TRENDS OVER TIME
-- =============================================================================

-- ---------------------------------------------------------------------------
-- D1. Year-over-year asset growth per company (line chart per company)
-- ---------------------------------------------------------------------------
WITH yearly AS (
    SELECT
        dc.ruc,
        dc.company_name,
        dc.sector_name,
        dd.fiscal_year,
        SUM(ff.total_assets) AS total_assets
    FROM financial_fact    ff
    JOIN dim_date    dd ON dd.date_key    = ff.date_key
    JOIN dim_company dc ON dc.company_key = ff.company_key
    WHERE ff.total_assets IS NOT NULL
      AND ff.period_type  = 'ANUAL'
    GROUP BY dc.ruc, dc.company_name, dc.sector_name, dd.fiscal_year
)
SELECT
    fiscal_year,
    ruc,
    company_name,
    sector_name,
    ROUND(total_assets, 2)                 AS total_assets,
    ROUND(LAG(total_assets) OVER w, 2)     AS prev_year_assets,
    ROUND(total_assets
          - LAG(total_assets) OVER w, 2)   AS yoy_change,
    ROUND(
        (total_assets - LAG(total_assets) OVER w) /
        NULLIF(ABS(LAG(total_assets) OVER w), 0) * 100,
        2
    )                                      AS yoy_growth_pct,
    -- 3-year moving average (smooths volatility for trend lines)
    ROUND(AVG(total_assets) OVER (
        WINDOW w ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2)                                  AS moving_avg_3yr
FROM yearly
WINDOW w AS (PARTITION BY ruc ORDER BY fiscal_year)
ORDER BY ruc, fiscal_year;


-- ---------------------------------------------------------------------------
-- D2. System-wide CAGR (Compound Annual Growth Rate) per sector
-- Compares first and last available year per sector.
-- ---------------------------------------------------------------------------
WITH endpoints AS (
    SELECT
        dc.sector_name,
        dd.fiscal_year,
        SUM(ff.total_assets)                     AS total_assets,
        MIN(dd.fiscal_year) OVER (PARTITION BY dc.sector_name) AS first_year,
        MAX(dd.fiscal_year) OVER (PARTITION BY dc.sector_name) AS last_year
    FROM financial_fact    ff
    JOIN dim_date    dd ON dd.date_key    = ff.date_key
    JOIN dim_company dc ON dc.company_key = ff.company_key
    WHERE ff.total_assets IS NOT NULL
      AND ff.period_type  = 'ANUAL'
    GROUP BY dc.sector_name, dd.fiscal_year
)
SELECT
    e_last.sector_name,
    e_last.first_year,
    e_last.last_year,
    e_last.last_year - e_last.first_year          AS years_span,
    ROUND(e_first.total_assets, 2)                AS assets_first_year,
    ROUND(e_last.total_assets,  2)                AS assets_last_year,
    ROUND(
        (POWER(
            e_last.total_assets / NULLIF(e_first.total_assets, 0),
            1.0 / NULLIF(e_last.last_year - e_last.first_year, 0)
        ) - 1) * 100,
        2
    )                                             AS cagr_pct
FROM endpoints e_last
JOIN endpoints e_first
  ON  e_first.sector_name = e_last.sector_name
  AND e_first.fiscal_year = e_last.first_year
WHERE e_last.fiscal_year  = e_last.last_year
ORDER BY cagr_pct DESC;


-- ---------------------------------------------------------------------------
-- D3. Quarter-by-quarter growth — for datasets that include TRIMESTRAL periods
-- Shows intra-year momentum (waterfall / sequential bar chart)
-- ---------------------------------------------------------------------------
WITH quarterly AS (
    SELECT
        dc.sector_name,
        dd.fiscal_year,
        dd.quarter,
        CONCAT(dd.fiscal_year, '-Q', dd.quarter) AS period_label,
        SUM(ff.total_assets)                      AS total_assets
    FROM financial_fact    ff
    JOIN dim_date    dd ON dd.date_key    = ff.date_key
    JOIN dim_company dc ON dc.company_key = ff.company_key
    WHERE ff.total_assets IS NOT NULL
      AND ff.period_type  = 'TRIMESTRAL'
    GROUP BY dc.sector_name, dd.fiscal_year, dd.quarter
)
SELECT
    sector_name,
    fiscal_year,
    quarter,
    period_label,
    ROUND(total_assets, 2)                 AS total_assets,
    ROUND(
        total_assets - LAG(total_assets) OVER w,
        2
    )                                      AS qoq_change,
    ROUND(
        (total_assets - LAG(total_assets) OVER w) /
        NULLIF(ABS(LAG(total_assets) OVER w), 0) * 100,
        2
    )                                      AS qoq_growth_pct,
    -- Same quarter prior year (seasonal comparison)
    ROUND(
        total_assets - LAG(total_assets, 4) OVER w,
        2
    )                                      AS yoy_same_quarter_change
FROM quarterly
WINDOW w AS (PARTITION BY sector_name ORDER BY fiscal_year, quarter)
ORDER BY sector_name, fiscal_year, quarter;


-- ---------------------------------------------------------------------------
-- D4. Net result trend (Income - Expenses) — profitability over time
-- ---------------------------------------------------------------------------
WITH yearly AS (
    SELECT
        dc.ruc,
        dc.company_name,
        dc.sector_name,
        dd.fiscal_year,
        SUM(ff.total_income)   AS total_income,
        SUM(ff.total_expenses) AS total_expenses,
        SUM(ff.total_income) - SUM(ff.total_expenses) AS net_result
    FROM financial_fact    ff
    JOIN dim_date    dd ON dd.date_key    = ff.date_key
    JOIN dim_company dc ON dc.company_key = ff.company_key
    WHERE ff.period_type = 'ANUAL'
      AND (ff.total_income IS NOT NULL OR ff.total_expenses IS NOT NULL)
    GROUP BY dc.ruc, dc.company_name, dc.sector_name, dd.fiscal_year
)
SELECT
    fiscal_year,
    ruc,
    company_name,
    sector_name,
    ROUND(total_income,   2)               AS total_income,
    ROUND(total_expenses, 2)               AS total_expenses,
    ROUND(net_result,     2)               AS net_result,
    CASE WHEN net_result > 0 THEN 'Profit' ELSE 'Loss' END AS result_flag,
    ROUND(
        net_result - LAG(net_result) OVER (PARTITION BY ruc ORDER BY fiscal_year),
        2
    )                                      AS net_result_change,
    ROUND(
        (net_result - LAG(net_result) OVER (PARTITION BY ruc ORDER BY fiscal_year)) /
        NULLIF(ABS(LAG(net_result) OVER (PARTITION BY ruc ORDER BY fiscal_year)), 0) * 100,
        2
    )                                      AS net_result_growth_pct
FROM yearly
ORDER BY ruc, fiscal_year;

-- =============================================================================
-- KPI QUERIES — Financial Indicators for BI Dashboards
-- Perspective: Financial manager reviewing entity health across the system.
-- Engine     : DuckDB  |  Source: star schema (financial_fact + dim_*)
--
-- Sections:
--   1. Solvency & Leverage
--   2. Liquidity
--   3. Profitability
--   4. Efficiency
--   5. Growth & Momentum
--   6. Market Concentration (system-level)
--   7. Early Warning — risk flags
-- =============================================================================


-- =============================================================================
-- 1. SOLVENCY & LEVERAGE
-- Question: Can entities meet their long-term obligations?
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1A. Debt-to-Equity ratio per company per year
-- Formula : Total Liabilities / Total Equity
-- Healthy range: < 2.0 for most financial entities
-- ---------------------------------------------------------------------------
SELECT
    dc.ruc,
    dc.company_name,
    dc.sector_name,
    dd.fiscal_year,
    ROUND(SUM(ff.total_assets),      2)  AS total_assets,
    ROUND(SUM(ff.total_liabilities), 2)  AS total_liabilities,
    ROUND(SUM(ff.total_equity),      2)  AS total_equity,

    -- Leverage ratio: Liabilities / Assets
    ROUND(
        SUM(ff.total_liabilities) / NULLIF(SUM(ff.total_assets), 0),
        4
    )                                    AS leverage_ratio,

    -- Debt-to-Equity
    ROUND(
        SUM(ff.total_liabilities) / NULLIF(SUM(ff.total_equity), 0),
        4
    )                                    AS debt_to_equity,

    -- Equity multiplier (Assets / Equity) — how leveraged the equity base is
    ROUND(
        SUM(ff.total_assets) / NULLIF(SUM(ff.total_equity), 0),
        4
    )                                    AS equity_multiplier,

    CASE
        WHEN SUM(ff.total_liabilities) / NULLIF(SUM(ff.total_assets), 0) > 0.90
            THEN 'Critical'
        WHEN SUM(ff.total_liabilities) / NULLIF(SUM(ff.total_assets), 0) > 0.75
            THEN 'High'
        WHEN SUM(ff.total_liabilities) / NULLIF(SUM(ff.total_assets), 0) > 0.50
            THEN 'Moderate'
        ELSE 'Healthy'
    END                                  AS solvency_band

FROM financial_fact    ff
JOIN dim_date    dd ON dd.date_key    = ff.date_key
JOIN dim_company dc ON dc.company_key = ff.company_key
WHERE ff.period_type = 'ANUAL'
  AND (ff.total_assets IS NOT NULL OR ff.total_liabilities IS NOT NULL)
GROUP BY dc.ruc, dc.company_name, dc.sector_name, dd.fiscal_year
ORDER BY dd.fiscal_year DESC, leverage_ratio DESC;


-- ---------------------------------------------------------------------------
-- 1B. System-wide solvency distribution per year (histogram buckets)
-- Shows what fraction of entities fall in each solvency band.
-- ---------------------------------------------------------------------------
WITH company_leverage AS (
    SELECT
        dd.fiscal_year,
        dc.ruc,
        SUM(ff.total_liabilities) / NULLIF(SUM(ff.total_assets), 0) AS leverage_ratio
    FROM financial_fact    ff
    JOIN dim_date    dd ON dd.date_key    = ff.date_key
    JOIN dim_company dc ON dc.company_key = ff.company_key
    WHERE ff.period_type = 'ANUAL'
      AND ff.total_assets IS NOT NULL
    GROUP BY dd.fiscal_year, dc.ruc
)
SELECT
    fiscal_year,
    CASE
        WHEN leverage_ratio > 0.90 THEN '4_Critical  (>90%)'
        WHEN leverage_ratio > 0.75 THEN '3_High      (75–90%)'
        WHEN leverage_ratio > 0.50 THEN '2_Moderate  (50–75%)'
        ELSE                            '1_Healthy   (<50%)'
    END                        AS solvency_band,
    COUNT(*)                   AS entity_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY fiscal_year), 1)
                               AS pct_of_total
FROM company_leverage
WHERE leverage_ratio IS NOT NULL
GROUP BY fiscal_year, solvency_band
ORDER BY fiscal_year DESC, solvency_band;


-- =============================================================================
-- 2. LIQUIDITY
-- Question: Can entities meet short-term obligations?
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 2A. Current ratio per company per year
-- Formula : Current Assets (101xx) / Current Liabilities (201xx)
-- Healthy range: > 1.0  (above 1 means short-term assets cover short-term debt)
-- ---------------------------------------------------------------------------
WITH liquidity_components AS (
    SELECT
        ff.company_key,
        ff.date_key,
        ff.period_type,
        -- Current Assets  = account group 101
        SUM(CASE WHEN da.group_code = '101' THEN ff.value ELSE 0 END)
            AS current_assets,
        -- Non-Current Assets = account group 102
        SUM(CASE WHEN da.group_code = '102' THEN ff.value ELSE 0 END)
            AS noncurrent_assets,
        -- Current Liabilities = account group 201
        SUM(CASE WHEN da.group_code = '201' THEN ff.value ELSE 0 END)
            AS current_liabilities,
        -- Non-Current Liabilities = account group 202
        SUM(CASE WHEN da.group_code = '202' THEN ff.value ELSE 0 END)
            AS noncurrent_liabilities,
        -- Cash & Equivalents = account group 10101
        SUM(CASE WHEN da.subgroup_code = '10101' THEN ff.value ELSE 0 END)
            AS cash_and_equivalents
    FROM financial_fact    ff
    JOIN dim_account da ON da.account_key = ff.account_key
    WHERE ff.period_type = 'ANUAL'
    GROUP BY ff.company_key, ff.date_key, ff.period_type
)
SELECT
    dc.ruc,
    dc.company_name,
    dc.sector_name,
    dd.fiscal_year,
    ROUND(lc.current_assets,       2)  AS current_assets,
    ROUND(lc.current_liabilities,  2)  AS current_liabilities,
    ROUND(lc.cash_and_equivalents, 2)  AS cash_and_equivalents,

    -- Current Ratio
    ROUND(lc.current_assets / NULLIF(lc.current_liabilities, 0), 4)
                                       AS current_ratio,

    -- Cash Ratio (most conservative liquidity measure)
    ROUND(lc.cash_and_equivalents / NULLIF(lc.current_liabilities, 0), 4)
                                       AS cash_ratio,

    CASE
        WHEN lc.current_assets / NULLIF(lc.current_liabilities, 0) < 1.0
            THEN 'Illiquid'
        WHEN lc.current_assets / NULLIF(lc.current_liabilities, 0) < 1.5
            THEN 'Adequate'
        ELSE 'Strong'
    END                                AS liquidity_flag

FROM liquidity_components lc
JOIN dim_company dc ON dc.company_key = lc.company_key
JOIN dim_date    dd ON dd.date_key    = lc.date_key
ORDER BY dd.fiscal_year DESC, current_ratio;


-- =============================================================================
-- 3. PROFITABILITY
-- Question: Are entities generating returns relative to their size?
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 3A. ROA, ROE, Net Margin per company per year
-- ROA    = Net Result / Total Assets
-- ROE    = Net Result / Total Equity
-- Margin = Net Result / Total Income
-- ---------------------------------------------------------------------------
WITH profitability_base AS (
    SELECT
        ff.company_key,
        ff.date_key,
        SUM(ff.total_assets)   AS total_assets,
        SUM(ff.total_equity)   AS total_equity,
        SUM(ff.total_income)   AS total_income,
        SUM(ff.total_expenses) AS total_expenses,
        SUM(ff.total_income) - SUM(ff.total_expenses) AS net_result
    FROM financial_fact ff
    WHERE ff.period_type = 'ANUAL'
      AND (ff.total_income IS NOT NULL OR ff.total_expenses IS NOT NULL)
    GROUP BY ff.company_key, ff.date_key
)
SELECT
    dc.ruc,
    dc.company_name,
    dc.sector_name,
    dd.fiscal_year,
    ROUND(pb.total_assets,   2)  AS total_assets,
    ROUND(pb.total_income,   2)  AS total_income,
    ROUND(pb.total_expenses, 2)  AS total_expenses,
    ROUND(pb.net_result,     2)  AS net_result,

    -- Return on Assets
    ROUND(pb.net_result / NULLIF(pb.total_assets, 0) * 100, 2)
                                 AS roa_pct,

    -- Return on Equity
    ROUND(pb.net_result / NULLIF(pb.total_equity, 0) * 100, 2)
                                 AS roe_pct,

    -- Net Profit Margin
    ROUND(pb.net_result / NULLIF(pb.total_income, 0) * 100, 2)
                                 AS net_margin_pct,

    -- Operating Expense Ratio
    ROUND(pb.total_expenses / NULLIF(pb.total_income, 0) * 100, 2)
                                 AS expense_ratio_pct,

    CASE
        WHEN pb.net_result > 0 THEN 'Profitable'
        WHEN pb.net_result = 0 THEN 'Break-even'
        ELSE 'Loss'
    END                          AS profitability_flag

FROM profitability_base pb
JOIN dim_company dc ON dc.company_key = pb.company_key
JOIN dim_date    dd ON dd.date_key    = pb.date_key
ORDER BY dd.fiscal_year DESC, roa_pct DESC;


-- ---------------------------------------------------------------------------
-- 3B. Profitability by sector — sector benchmark (box-plot data)
-- Returns P25, median, P75 across companies within each sector.
-- ---------------------------------------------------------------------------
WITH company_roa AS (
    SELECT
        dc.sector_name,
        dd.fiscal_year,
        (SUM(ff.total_income) - SUM(ff.total_expenses)) /
            NULLIF(SUM(ff.total_assets), 0) * 100 AS roa_pct
    FROM financial_fact    ff
    JOIN dim_date    dd ON dd.date_key    = ff.date_key
    JOIN dim_company dc ON dc.company_key = ff.company_key
    WHERE ff.period_type = 'ANUAL'
    GROUP BY dc.sector_name, dd.fiscal_year, dc.ruc
)
SELECT
    fiscal_year,
    sector_name,
    COUNT(*)                                          AS entity_count,
    ROUND(MIN(roa_pct), 2)                            AS roa_min,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY roa_pct), 2)
                                                      AS roa_p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY roa_pct), 2)
                                                      AS roa_median,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY roa_pct), 2)
                                                      AS roa_p75,
    ROUND(MAX(roa_pct), 2)                            AS roa_max,
    ROUND(AVG(roa_pct), 2)                            AS roa_avg
FROM company_roa
WHERE roa_pct IS NOT NULL
GROUP BY fiscal_year, sector_name
ORDER BY fiscal_year DESC, roa_median DESC;


-- =============================================================================
-- 4. EFFICIENCY
-- Question: How effectively are entities using their assets?
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 4A. Asset turnover per company per year
-- Formula : Total Income / Total Assets
-- Higher = more revenue generated per unit of assets
-- ---------------------------------------------------------------------------
SELECT
    dc.ruc,
    dc.company_name,
    dc.sector_name,
    dd.fiscal_year,
    ROUND(SUM(ff.total_income),  2)  AS total_income,
    ROUND(SUM(ff.total_assets),  2)  AS total_assets,
    ROUND(SUM(ff.total_expenses),2)  AS total_expenses,

    -- Asset Turnover
    ROUND(SUM(ff.total_income) / NULLIF(SUM(ff.total_assets), 0), 4)
                                     AS asset_turnover,

    -- Cost Efficiency (Expenses / Income) — lower is better
    ROUND(SUM(ff.total_expenses) / NULLIF(SUM(ff.total_income), 0) * 100, 2)
                                     AS cost_efficiency_pct,

    -- Income per unit of equity
    ROUND(SUM(ff.total_income) / NULLIF(SUM(ff.total_equity), 0), 4)
                                     AS income_on_equity

FROM financial_fact    ff
JOIN dim_date    dd ON dd.date_key    = ff.date_key
JOIN dim_company dc ON dc.company_key = ff.company_key
WHERE ff.period_type = 'ANUAL'
  AND ff.total_income IS NOT NULL
GROUP BY dc.ruc, dc.company_name, dc.sector_name, dd.fiscal_year
ORDER BY dd.fiscal_year DESC, asset_turnover DESC;


-- =============================================================================
-- 5. GROWTH & MOMENTUM
-- Question: Which entities and sectors are expanding or contracting?
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 5A. Multi-metric YoY growth dashboard (one row = one company-year)
-- Includes: asset growth, income growth, equity growth, net result delta
-- ---------------------------------------------------------------------------
WITH annual_snapshot AS (
    SELECT
        dc.ruc,
        dc.company_name,
        dc.sector_name,
        dd.fiscal_year,
        SUM(ff.total_assets)   AS assets,
        SUM(ff.total_equity)   AS equity,
        SUM(ff.total_income)   AS income,
        SUM(ff.total_income) - SUM(ff.total_expenses) AS net_result
    FROM financial_fact    ff
    JOIN dim_date    dd ON dd.date_key    = ff.date_key
    JOIN dim_company dc ON dc.company_key = ff.company_key
    WHERE ff.period_type = 'ANUAL'
    GROUP BY dc.ruc, dc.company_name, dc.sector_name, dd.fiscal_year
)
SELECT
    fiscal_year,
    ruc,
    company_name,
    sector_name,
    ROUND(assets,      2)  AS total_assets,
    ROUND(income,      2)  AS total_income,
    ROUND(net_result,  2)  AS net_result,

    -- YoY growth rates
    ROUND((assets  - LAG(assets)     OVER w) / NULLIF(ABS(LAG(assets)     OVER w), 0) * 100, 2)
                           AS asset_growth_pct,
    ROUND((income  - LAG(income)     OVER w) / NULLIF(ABS(LAG(income)     OVER w), 0) * 100, 2)
                           AS income_growth_pct,
    ROUND((equity  - LAG(equity)     OVER w) / NULLIF(ABS(LAG(equity)     OVER w), 0) * 100, 2)
                           AS equity_growth_pct,
    ROUND(net_result - LAG(net_result) OVER w, 2)
                           AS net_result_change,

    -- 3-year compound growth (smoothed signal)
    ROUND(
        (POWER(assets / NULLIF(LAG(assets, 3) OVER w, 0), 1.0/3) - 1) * 100,
        2
    )                      AS asset_cagr_3yr_pct

FROM annual_snapshot
WINDOW w AS (PARTITION BY ruc ORDER BY fiscal_year)
ORDER BY fiscal_year DESC, asset_growth_pct DESC;


-- ---------------------------------------------------------------------------
-- 5B. Fastest-growing entities — top 10 by 3-year asset CAGR, latest period
-- ---------------------------------------------------------------------------
WITH annual_assets AS (
    SELECT
        dc.ruc,
        dc.company_name,
        dc.sector_name,
        dd.fiscal_year,
        SUM(ff.total_assets) AS assets
    FROM financial_fact    ff
    JOIN dim_date    dd ON dd.date_key    = ff.date_key
    JOIN dim_company dc ON dc.company_key = ff.company_key
    WHERE ff.total_assets IS NOT NULL
      AND ff.period_type  = 'ANUAL'
    GROUP BY dc.ruc, dc.company_name, dc.sector_name, dd.fiscal_year
),
with_lag AS (
    SELECT *,
        LAG(assets, 3) OVER (PARTITION BY ruc ORDER BY fiscal_year) AS assets_3yr_ago
    FROM annual_assets
),
latest AS (
    SELECT MAX(fiscal_year) AS yr FROM annual_assets
)
SELECT
    w.ruc,
    w.company_name,
    w.sector_name,
    w.fiscal_year,
    ROUND(w.assets,          2)  AS current_assets,
    ROUND(w.assets_3yr_ago,  2)  AS assets_3yr_ago,
    ROUND(
        (POWER(w.assets / NULLIF(w.assets_3yr_ago, 0), 1.0/3) - 1) * 100,
        2
    )                            AS cagr_3yr_pct
FROM with_lag w
JOIN latest l ON w.fiscal_year = l.yr
WHERE w.assets_3yr_ago IS NOT NULL
  AND w.assets_3yr_ago > 0
ORDER BY cagr_3yr_pct DESC
LIMIT 10;


-- =============================================================================
-- 6. MARKET CONCENTRATION
-- Question: How concentrated is the sector? Are a few entities dominant?
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 6A. Herfindahl-Hirschman Index (HHI) per sector per year
-- Formula : SUM( (entity_share_pct)^2 )
-- HHI < 1500          → Competitive market
-- HHI 1500–2500       → Moderately concentrated
-- HHI > 2500          → Highly concentrated (potential regulatory concern)
-- ---------------------------------------------------------------------------
WITH market_shares AS (
    SELECT
        dc.sector_name,
        dd.fiscal_year,
        dc.ruc,
        SUM(ff.total_assets) AS entity_assets,
        SUM(SUM(ff.total_assets)) OVER (
            PARTITION BY dc.sector_name, dd.fiscal_year
        )                    AS sector_total_assets
    FROM financial_fact    ff
    JOIN dim_date    dd ON dd.date_key    = ff.date_key
    JOIN dim_company dc ON dc.company_key = ff.company_key
    WHERE ff.total_assets IS NOT NULL
      AND ff.period_type  = 'ANUAL'
    GROUP BY dc.sector_name, dd.fiscal_year, dc.ruc
)
SELECT
    fiscal_year,
    sector_name,
    COUNT(DISTINCT ruc)                                     AS entities,
    ROUND(SUM(sector_total_assets), 2)                      AS sector_assets,
    -- HHI = sum of squared market shares (in percentage points)
    ROUND(SUM(
        POWER(entity_assets / NULLIF(sector_total_assets, 0) * 100, 2)
    ), 0)                                                   AS hhi,
    CASE
        WHEN SUM(POWER(entity_assets / NULLIF(sector_total_assets,0)*100,2)) > 2500
            THEN 'Highly Concentrated'
        WHEN SUM(POWER(entity_assets / NULLIF(sector_total_assets,0)*100,2)) > 1500
            THEN 'Moderately Concentrated'
        ELSE 'Competitive'
    END                                                     AS concentration_level
FROM market_shares
GROUP BY fiscal_year, sector_name
ORDER BY fiscal_year DESC, hhi DESC;


-- ---------------------------------------------------------------------------
-- 6B. Top-5 concentration ratio (CR5) per sector per year
-- % of sector assets held by the 5 largest entities
-- CR5 > 60% signals oligopolistic structure
-- ---------------------------------------------------------------------------
WITH ranked_entities AS (
    SELECT
        dc.sector_name,
        dd.fiscal_year,
        dc.ruc,
        SUM(ff.total_assets) AS entity_assets,
        RANK() OVER (
            PARTITION BY dc.sector_name, dd.fiscal_year
            ORDER BY SUM(ff.total_assets) DESC
        ) AS rank_in_sector
    FROM financial_fact    ff
    JOIN dim_date    dd ON dd.date_key    = ff.date_key
    JOIN dim_company dc ON dc.company_key = ff.company_key
    WHERE ff.total_assets IS NOT NULL
      AND ff.period_type  = 'ANUAL'
    GROUP BY dc.sector_name, dd.fiscal_year, dc.ruc
),
sector_total AS (
    SELECT sector_name, fiscal_year, SUM(entity_assets) AS total
    FROM ranked_entities
    GROUP BY sector_name, fiscal_year
)
SELECT
    r.fiscal_year,
    r.sector_name,
    ROUND(SUM(r.entity_assets), 2)                         AS cr5_assets,
    ROUND(SUM(r.entity_assets) / NULLIF(st.total, 0) * 100, 2)
                                                           AS cr5_pct
FROM ranked_entities r
JOIN sector_total st ON st.sector_name = r.sector_name
                     AND st.fiscal_year = r.fiscal_year
WHERE r.rank_in_sector <= 5
GROUP BY r.fiscal_year, r.sector_name, st.total
ORDER BY r.fiscal_year DESC, cr5_pct DESC;


-- =============================================================================
-- 7. EARLY WARNING — RISK FLAGS
-- Question: Which entities show deteriorating financial health?
-- These are the first signals a financial supervisor looks for.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 7A. Multi-signal risk scorecard
-- Each flag contributes 1 point to a composite risk_score (0–5).
-- Entities with score >= 3 require immediate review.
-- ---------------------------------------------------------------------------
WITH metrics AS (
    SELECT
        dc.ruc,
        dc.company_name,
        dc.sector_name,
        dd.fiscal_year,
        SUM(ff.total_assets)      AS assets,
        SUM(ff.total_liabilities) AS liabilities,
        SUM(ff.total_equity)      AS equity,
        SUM(ff.total_income)      AS income,
        SUM(ff.total_expenses)    AS expenses,
        SUM(ff.total_income) - SUM(ff.total_expenses) AS net_result,
        -- Asset growth YoY
        SUM(ff.total_assets) - LAG(SUM(ff.total_assets)) OVER (
            PARTITION BY dc.ruc ORDER BY dd.fiscal_year
        ) AS asset_yoy_change
    FROM financial_fact    ff
    JOIN dim_date    dd ON dd.date_key    = ff.date_key
    JOIN dim_company dc ON dc.company_key = ff.company_key
    WHERE ff.period_type = 'ANUAL'
    GROUP BY dc.ruc, dc.company_name, dc.sector_name, dd.fiscal_year
)
SELECT
    fiscal_year,
    ruc,
    company_name,
    sector_name,
    ROUND(assets,      2)  AS total_assets,
    ROUND(liabilities, 2)  AS total_liabilities,
    ROUND(net_result,  2)  AS net_result,

    -- Individual risk flags (1 = triggered)
    (liabilities / NULLIF(assets, 0) > 0.90)::INT      AS flag_high_leverage,
    (net_result < 0)::INT                              AS flag_loss,
    (equity < 0)::INT                                  AS flag_negative_equity,
    (income < expenses * 0.80)::INT                    AS flag_cost_overrun,
    (asset_yoy_change < 0 AND asset_yoy_change IS NOT NULL)::INT
                                                       AS flag_asset_decline,

    -- Composite risk score
    (liabilities / NULLIF(assets, 0) > 0.90)::INT
    + (net_result < 0)::INT
    + (equity < 0)::INT
    + (income < expenses * 0.80)::INT
    + (asset_yoy_change < 0 AND asset_yoy_change IS NOT NULL)::INT
                                                       AS risk_score,

    CASE
        (liabilities / NULLIF(assets, 0) > 0.90)::INT
        + (net_result < 0)::INT
        + (equity < 0)::INT
        + (income < expenses * 0.80)::INT
        + (asset_yoy_change < 0 AND asset_yoy_change IS NOT NULL)::INT
        WHEN 0      THEN 'Low'
        WHEN 1      THEN 'Watch'
        WHEN 2      THEN 'Elevated'
        ELSE             'Critical'
    END                                                AS risk_level

FROM metrics
ORDER BY fiscal_year DESC, risk_score DESC, assets DESC;

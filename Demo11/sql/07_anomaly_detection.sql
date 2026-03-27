-- Engine  : DuckDB  |  Source: financial_statements (flat ETL table) — Supercias
--
-- Detection strategies used:
--   1. Impossible values       — structural impossibilities (negative assets, etc.)
--   2. Statistical outliers    — Z-score and IQR methods
--   3. Sudden spikes/drops     — YoY change beyond sector thresholds
--   4. Hierarchy violations    — child account value exceeds parent
--   5. Reporting gaps          — companies that vanished or appeared unexpectedly
--   6. Suspicious patterns     — round numbers, zeroed-out periods, sign flips
--   7. Cross-entity anomalies  — a company diverges sharply from sector peers
--   8. Composite risk score    — unified anomaly score per company-year
-- =============================================================================


-- =============================================================================
-- 1. IMPOSSIBLE VALUES
-- Hard constraints that should never be violated in valid financial data.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1A. Negative total assets
-- Assets (account 1) must always be >= 0.
-- ---------------------------------------------------------------------------
SELECT
    ruc,
    company_name,
    entity_type,
    date,
    period_type,
    value                           AS total_assets,
    'Negative total assets'         AS anomaly_type,
    'CRITICAL'                      AS severity
FROM financial_statements
WHERE account_code = '1'
  AND value < 0
ORDER BY value;


-- ---------------------------------------------------------------------------
-- 1B. Liabilities exceed assets by more than 20 %
-- Leverage ratio > 1.20 is structurally impossible for a solvent entity.
-- ---------------------------------------------------------------------------
WITH balance AS (
    SELECT
        ruc,
        company_name,
        entity_type,
        date,
        period_type,
        SUM(CASE WHEN account_code = '1' THEN value END) AS assets,
        SUM(CASE WHEN account_code = '2' THEN value END) AS liabilities
    FROM financial_statements
    WHERE account_code IN ('1', '2')
    GROUP BY ruc, company_name, entity_type, date, period_type
)
SELECT
    ruc,
    company_name,
    entity_type,
    date,
    period_type,
    ROUND(assets,      2) AS total_assets,
    ROUND(liabilities, 2) AS total_liabilities,
    ROUND(liabilities / NULLIF(assets, 0), 4) AS leverage_ratio,
    'Liabilities > 120% of assets'            AS anomaly_type,
    'CRITICAL'                                 AS severity
FROM balance
WHERE liabilities / NULLIF(assets, 0) > 1.20
ORDER BY leverage_ratio DESC;


-- ---------------------------------------------------------------------------
-- 1C. Negative equity
-- Equity (account 3) < 0 signals technical insolvency.
-- ---------------------------------------------------------------------------
SELECT
    ruc,
    company_name,
    entity_type,
    date,
    period_type,
    ROUND(value, 2)             AS total_equity,
    'Negative equity'           AS anomaly_type,
    'HIGH'                      AS severity
FROM financial_statements
WHERE account_code = '3'
  AND value < 0
ORDER BY value;


-- ---------------------------------------------------------------------------
-- 1D. Income = 0 but expenses > 0 (or vice versa)
-- An entity with no income but real expenses, or phantom income with no costs,
-- is almost certainly a data entry error or a missing report.
-- ---------------------------------------------------------------------------
WITH income_expense AS (
    SELECT
        ruc,
        company_name,
        entity_type,
        date,
        period_type,
        SUM(CASE WHEN account_code = '4' THEN value ELSE 0 END) AS income,
        SUM(CASE WHEN account_code = '5' THEN value ELSE 0 END) AS expenses
    FROM financial_statements
    WHERE account_code IN ('4', '5')
    GROUP BY ruc, company_name, entity_type, date, period_type
)
SELECT
    ruc,
    company_name,
    entity_type,
    date,
    period_type,
    ROUND(income,   2) AS income,
    ROUND(expenses, 2) AS expenses,
    CASE
        WHEN income = 0 AND expenses > 0 THEN 'Zero income with real expenses'
        WHEN expenses = 0 AND income > 0 THEN 'Real income with zero expenses'
    END                AS anomaly_type,
    'MEDIUM'           AS severity
FROM income_expense
WHERE (income = 0 AND expenses > 0)
   OR (expenses = 0 AND income > 0)
ORDER BY date DESC;


-- =============================================================================
-- 2. STATISTICAL OUTLIERS
-- Values that deviate significantly from the peer distribution.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 2A. Z-score outliers by account code per year
-- |Z| > 3  → value is more than 3 standard deviations from the peer mean.
-- Applied per (account_code, fiscal_year) so comparison is apples-to-apples.
-- ---------------------------------------------------------------------------
WITH stats AS (
    SELECT
        account_code,
        account_name,
        YEAR(CAST(date AS DATE))    AS fiscal_year,
        period_type,
        AVG(value)                  AS mean_val,
        STDDEV_SAMP(value)          AS std_val,
        COUNT(*)                    AS peer_count
    FROM financial_statements
    WHERE date IS NOT NULL
    GROUP BY account_code, account_name, YEAR(CAST(date AS DATE)), period_type
    HAVING COUNT(*) >= 5           -- need at least 5 peers for Z-score to be meaningful
),
scored AS (
    SELECT
        fs.ruc,
        fs.company_name,
        fs.entity_type,
        fs.date,
        fs.period_type,
        fs.account_code,
        fs.account_name,
        ROUND(fs.value, 2)                                               AS value,
        ROUND(st.mean_val, 2)                                            AS peer_mean,
        ROUND(st.std_val, 2)                                             AS peer_std,
        ROUND((fs.value - st.mean_val) / NULLIF(st.std_val, 0), 2)      AS z_score,
        st.peer_count
    FROM financial_statements fs
    JOIN stats st
      ON  st.account_code  = fs.account_code
      AND st.fiscal_year   = YEAR(CAST(fs.date AS DATE))
      AND st.period_type   = fs.period_type
    WHERE fs.date IS NOT NULL
)
SELECT
    *,
    'Z-score outlier'   AS anomaly_type,
    CASE
        WHEN ABS(z_score) > 5 THEN 'CRITICAL'
        WHEN ABS(z_score) > 4 THEN 'HIGH'
        ELSE                       'MEDIUM'
    END                 AS severity
FROM scored
WHERE ABS(z_score) > 3
ORDER BY ABS(z_score) DESC;


-- ---------------------------------------------------------------------------
-- 2B. IQR (Interquartile Range) outliers — total assets per sector per year
-- More robust than Z-score when distributions are skewed (common in finance).
-- Outlier : value < Q1 - 3*IQR  or  value > Q3 + 3*IQR  (extreme fence)
-- ---------------------------------------------------------------------------
WITH iqr AS (
    SELECT
        entity_type,
        YEAR(CAST(date AS DATE))                              AS fiscal_year,
        period_type,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY value)  AS q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY value)  AS q3
    FROM financial_statements
    WHERE account_code = '1'
      AND date IS NOT NULL
    GROUP BY entity_type, YEAR(CAST(date AS DATE)), period_type
    HAVING COUNT(*) >= 5
),
fenced AS (
    SELECT
        fs.ruc,
        fs.company_name,
        fs.entity_type,
        fs.date,
        fs.period_type,
        ROUND(fs.value, 2)                AS total_assets,
        ROUND(iq.q1, 2)                   AS q1,
        ROUND(iq.q3, 2)                   AS q3,
        ROUND(iq.q3 - iq.q1, 2)          AS iqr,
        ROUND(iq.q1 - 3 * (iq.q3-iq.q1), 2) AS lower_fence,
        ROUND(iq.q3 + 3 * (iq.q3-iq.q1), 2) AS upper_fence
    FROM financial_statements fs
    JOIN iqr iq
      ON  iq.entity_type  = fs.entity_type
      AND iq.fiscal_year  = YEAR(CAST(fs.date AS DATE))
      AND iq.period_type  = fs.period_type
    WHERE fs.account_code = '1'
      AND fs.date IS NOT NULL
)
SELECT
    *,
    CASE
        WHEN total_assets < lower_fence THEN 'IQR outlier — unusually small'
        WHEN total_assets > upper_fence THEN 'IQR outlier — unusually large'
    END AS anomaly_type,
    'HIGH' AS severity
FROM fenced
WHERE total_assets < lower_fence
   OR total_assets > upper_fence
ORDER BY entity_type, date;


-- =============================================================================
-- 3. SUDDEN SPIKES AND DROPS
-- Large year-over-year changes that exceed sector norms.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 3A. YoY change beyond sector threshold (assets)
-- Flag entities whose asset growth deviates more than 3× the sector's
-- median absolute YoY change.
-- ---------------------------------------------------------------------------
WITH annual_assets AS (
    SELECT
        ruc,
        company_name,
        entity_type,
        YEAR(CAST(date AS DATE))  AS fiscal_year,
        period_type,
        SUM(value)                AS total_assets
    FROM financial_statements
    WHERE account_code = '1'
      AND date IS NOT NULL
    GROUP BY ruc, company_name, entity_type, YEAR(CAST(date AS DATE)), period_type
),
with_yoy AS (
    SELECT
        *,
        LAG(total_assets) OVER (PARTITION BY ruc, period_type ORDER BY fiscal_year)
            AS prev_assets,
        total_assets - LAG(total_assets) OVER (PARTITION BY ruc, period_type ORDER BY fiscal_year)
            AS yoy_change
    FROM annual_assets
),
sector_median_change AS (
    SELECT
        entity_type,
        fiscal_year,
        period_type,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY ABS(yoy_change)) AS median_abs_change
    FROM with_yoy
    WHERE yoy_change IS NOT NULL
    GROUP BY entity_type, fiscal_year, period_type
)
SELECT
    w.ruc,
    w.company_name,
    w.entity_type,
    w.fiscal_year,
    w.period_type,
    ROUND(w.prev_assets,  2)  AS prev_year_assets,
    ROUND(w.total_assets, 2)  AS current_assets,
    ROUND(w.yoy_change,   2)  AS yoy_change,
    ROUND(w.yoy_change / NULLIF(w.prev_assets, 0) * 100, 2) AS yoy_pct,
    ROUND(s.median_abs_change, 2)                            AS sector_median_abs_change,
    CASE
        WHEN w.yoy_change > 0 THEN 'Abnormal spike'
        ELSE                       'Abnormal drop'
    END                       AS anomaly_type,
    CASE
        WHEN ABS(w.yoy_change) > s.median_abs_change * 5 THEN 'CRITICAL'
        ELSE 'HIGH'
    END                       AS severity
FROM with_yoy w
JOIN sector_median_change s
  ON  s.entity_type  = w.entity_type
  AND s.fiscal_year  = w.fiscal_year
  AND s.period_type  = w.period_type
WHERE w.yoy_change IS NOT NULL
  AND ABS(w.yoy_change) > s.median_abs_change * 3
ORDER BY ABS(w.yoy_change / NULLIF(w.prev_assets, 0)) DESC;


-- ---------------------------------------------------------------------------
-- 3B. Sign flip — account that changed from positive to negative (or vice versa)
-- A sudden sign reversal in a major account is almost always an error.
-- ---------------------------------------------------------------------------
WITH annual_class AS (
    SELECT
        ruc,
        company_name,
        entity_type,
        account_code,
        account_name,
        YEAR(CAST(date AS DATE)) AS fiscal_year,
        period_type,
        SUM(value)               AS total_value
    FROM financial_statements
    WHERE account_code IN ('1','2','3','4','5')
      AND date IS NOT NULL
    GROUP BY ruc, company_name, entity_type, account_code, account_name,
             YEAR(CAST(date AS DATE)), period_type
)
SELECT
    curr.ruc,
    curr.company_name,
    curr.entity_type,
    curr.account_code,
    curr.account_name,
    curr.fiscal_year,
    curr.period_type,
    ROUND(prev.total_value, 2) AS prev_value,
    ROUND(curr.total_value, 2) AS curr_value,
    'Sign flip on class account'  AS anomaly_type,
    'HIGH'                        AS severity
FROM annual_class curr
JOIN annual_class prev
  ON  prev.ruc          = curr.ruc
  AND prev.account_code = curr.account_code
  AND prev.period_type  = curr.period_type
  AND prev.fiscal_year  = curr.fiscal_year - 1
WHERE SIGN(curr.total_value) != SIGN(prev.total_value)
  AND prev.total_value IS NOT NULL
ORDER BY curr.ruc, curr.fiscal_year, curr.account_code;


-- =============================================================================
-- 4. HIERARCHY VIOLATIONS
-- A child account value must not exceed its parent in absolute terms.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 4A. Group-level account (3 digits) exceeds its class-level parent (1 digit)
-- Example: account 101 (ACTIVO CORRIENTE) > account 1 (ACTIVO)
-- ---------------------------------------------------------------------------
SELECT
    child.ruc,
    child.company_name,
    child.entity_type,
    child.date,
    child.period_type,
    parent.account_code                   AS parent_code,
    parent.account_name                   AS parent_name,
    ROUND(parent.value, 2)                AS parent_value,
    child.account_code                    AS child_code,
    child.account_name                    AS child_name,
    ROUND(child.value, 2)                 AS child_value,
    ROUND(child.value - parent.value, 2)  AS excess,
    'Child > parent (group vs class)'     AS anomaly_type,
    'HIGH'                                AS severity
FROM financial_statements child
JOIN financial_statements parent
  ON  parent.ruc         = child.ruc
  AND parent.date        = child.date
  AND parent.period_type = child.period_type
  AND parent.account_code = LEFT(child.account_code, 1)
WHERE LENGTH(child.account_code)  = 3
  AND LENGTH(parent.account_code) = 1
  AND child.value  > 0
  AND parent.value > 0
  AND child.value  > parent.value
ORDER BY excess DESC;


-- ---------------------------------------------------------------------------
-- 4B. Subgroup-level (5 digits) exceeds its group-level parent (3 digits)
-- ---------------------------------------------------------------------------
SELECT
    child.ruc,
    child.company_name,
    child.entity_type,
    child.date,
    child.period_type,
    parent.account_code                   AS parent_code,
    parent.account_name                   AS parent_name,
    ROUND(parent.value, 2)                AS parent_value,
    child.account_code                    AS child_code,
    child.account_name                    AS child_name,
    ROUND(child.value, 2)                 AS child_value,
    ROUND(child.value - parent.value, 2)  AS excess,
    'Child > parent (subgroup vs group)'  AS anomaly_type,
    'MEDIUM'                              AS severity
FROM financial_statements child
JOIN financial_statements parent
  ON  parent.ruc         = child.ruc
  AND parent.date        = child.date
  AND parent.period_type = child.period_type
  AND parent.account_code = LEFT(child.account_code, 3)
WHERE LENGTH(child.account_code)  = 5
  AND LENGTH(parent.account_code) = 3
  AND child.value  > 0
  AND parent.value > 0
  AND child.value  > parent.value
ORDER BY excess DESC;


-- =============================================================================
-- 5. REPORTING GAPS
-- Entities that stopped reporting or appeared without history.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 5A. Companies with missing years in the reporting sequence
-- Detects gaps like: 2018, 2019, [gap], 2021 — year 2020 is missing.
-- ---------------------------------------------------------------------------
WITH all_years AS (
    SELECT DISTINCT YEAR(CAST(date AS DATE)) AS fiscal_year
    FROM financial_statements
    WHERE date IS NOT NULL AND period_type = 'ANUAL'
),
company_years AS (
    SELECT DISTINCT
        ruc,
        company_name,
        entity_type,
        YEAR(CAST(date AS DATE)) AS fiscal_year
    FROM financial_statements
    WHERE date IS NOT NULL AND period_type = 'ANUAL'
),
expected AS (
    SELECT cy.ruc, cy.company_name, cy.entity_type, ay.fiscal_year
    FROM (SELECT DISTINCT ruc, company_name, entity_type FROM company_years) cy
    CROSS JOIN all_years ay
    WHERE ay.fiscal_year BETWEEN
        (SELECT MIN(fiscal_year) FROM company_years cy2 WHERE cy2.ruc = cy.ruc)
        AND
        (SELECT MAX(fiscal_year) FROM company_years cy3 WHERE cy3.ruc = cy.ruc)
)
SELECT
    e.ruc,
    e.company_name,
    e.entity_type,
    e.fiscal_year          AS missing_year,
    'Missing annual report' AS anomaly_type,
    'HIGH'                  AS severity
FROM expected e
LEFT JOIN company_years cy
  ON cy.ruc = e.ruc AND cy.fiscal_year = e.fiscal_year
WHERE cy.ruc IS NULL
ORDER BY e.ruc, e.fiscal_year;


-- ---------------------------------------------------------------------------
-- 5B. Entities that reported only once (no time series available)
-- Single-year reporters cannot be trended — flag for completeness review.
-- ---------------------------------------------------------------------------
SELECT
    ruc,
    company_name,
    entity_type,
    COUNT(DISTINCT YEAR(CAST(date AS DATE))) AS years_reported,
    MIN(date)                                AS first_report,
    MAX(date)                                AS last_report,
    'Single year only — no trend possible'   AS anomaly_type,
    'LOW'                                    AS severity
FROM financial_statements
WHERE date IS NOT NULL
  AND period_type = 'ANUAL'
GROUP BY ruc, company_name, entity_type
HAVING COUNT(DISTINCT YEAR(CAST(date AS DATE))) = 1
ORDER BY ruc;


-- =============================================================================
-- 6. SUSPICIOUS PATTERNS
-- Values that may indicate manual entry errors or data integrity issues.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 6A. Suspiciously round numbers
-- Values that are exact multiples of 1,000,000 on non-class-level accounts
-- suggest manual aggregation rather than real accounting data.
-- ---------------------------------------------------------------------------
SELECT
    ruc,
    company_name,
    entity_type,
    date,
    period_type,
    account_code,
    account_name,
    ROUND(value, 2)                AS value,
    'Suspiciously round value'     AS anomaly_type,
    'LOW'                          AS severity
FROM financial_statements
WHERE LENGTH(account_code) >= 3                 -- only sub-class accounts
  AND ABS(value) >= 1_000_000
  AND MOD(value, 1_000_000) = 0
  AND value != 0
ORDER BY ABS(value) DESC;


-- ---------------------------------------------------------------------------
-- 6B. Identical value across all accounts in a period
-- When every account has the same value, it almost certainly indicates
-- a copy-paste or batch-fill error.
-- ---------------------------------------------------------------------------
WITH period_stats AS (
    SELECT
        ruc,
        company_name,
        entity_type,
        date,
        period_type,
        COUNT(DISTINCT value)    AS distinct_values,
        COUNT(*)                 AS total_accounts,
        MIN(value)               AS min_val,
        MAX(value)               AS max_val
    FROM financial_statements
    GROUP BY ruc, company_name, entity_type, date, period_type
    HAVING COUNT(*) >= 3
)
SELECT
    ruc,
    company_name,
    entity_type,
    date,
    period_type,
    total_accounts,
    ROUND(min_val, 2)              AS repeated_value,
    'All accounts share same value' AS anomaly_type,
    'HIGH'                          AS severity
FROM period_stats
WHERE distinct_values = 1
ORDER BY date DESC;


-- ---------------------------------------------------------------------------
-- 6C. Future dates — report date is after today
-- ---------------------------------------------------------------------------
SELECT
    ruc,
    company_name,
    entity_type,
    date,
    period_type,
    account_code,
    ROUND(value, 2)         AS value,
    'Future report date'    AS anomaly_type,
    'HIGH'                  AS severity
FROM financial_statements
WHERE CAST(date AS DATE) > CURRENT_DATE
ORDER BY date DESC;


-- ---------------------------------------------------------------------------
-- 6D. Implausibly old dates — before year 2000
-- ---------------------------------------------------------------------------
SELECT
    ruc,
    company_name,
    entity_type,
    date,
    period_type,
    account_code,
    ROUND(value, 2)               AS value,
    'Date before year 2000'       AS anomaly_type,
    'MEDIUM'                      AS severity
FROM financial_statements
WHERE date IS NOT NULL
  AND YEAR(CAST(date AS DATE)) < 2000
ORDER BY date;


-- =============================================================================
-- 7. CROSS-ENTITY ANOMALIES
-- A company whose ratios diverge sharply from its sector peers.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 7A. Leverage ratio more than 2 standard deviations above sector mean
-- Detects entities that are far more leveraged than their peers.
-- ---------------------------------------------------------------------------
WITH entity_leverage AS (
    SELECT
        ruc,
        company_name,
        entity_type,
        YEAR(CAST(date AS DATE))  AS fiscal_year,
        period_type,
        SUM(CASE WHEN account_code = '2' THEN value ELSE 0 END) /
            NULLIF(SUM(CASE WHEN account_code = '1' THEN value ELSE 0 END), 0)
                                  AS leverage_ratio
    FROM financial_statements
    WHERE account_code IN ('1','2')
      AND date IS NOT NULL
    GROUP BY ruc, company_name, entity_type, YEAR(CAST(date AS DATE)), period_type
),
sector_stats AS (
    SELECT
        entity_type,
        fiscal_year,
        period_type,
        AVG(leverage_ratio)      AS mean_leverage,
        STDDEV_SAMP(leverage_ratio) AS std_leverage
    FROM entity_leverage
    WHERE leverage_ratio IS NOT NULL
    GROUP BY entity_type, fiscal_year, period_type
    HAVING COUNT(*) >= 3
)
SELECT
    el.ruc,
    el.company_name,
    el.entity_type,
    el.fiscal_year,
    el.period_type,
    ROUND(el.leverage_ratio, 4)   AS entity_leverage,
    ROUND(ss.mean_leverage, 4)    AS sector_mean_leverage,
    ROUND(ss.std_leverage, 4)     AS sector_std_leverage,
    ROUND(
        (el.leverage_ratio - ss.mean_leverage) / NULLIF(ss.std_leverage, 0),
        2
    )                             AS leverage_z_score,
    'Leverage far above sector peers' AS anomaly_type,
    CASE
        WHEN (el.leverage_ratio - ss.mean_leverage) / NULLIF(ss.std_leverage,0) > 4
            THEN 'CRITICAL'
        ELSE 'HIGH'
    END                           AS severity
FROM entity_leverage el
JOIN sector_stats ss
  ON  ss.entity_type = el.entity_type
  AND ss.fiscal_year = el.fiscal_year
  AND ss.period_type = el.period_type
WHERE (el.leverage_ratio - ss.mean_leverage) / NULLIF(ss.std_leverage, 0) > 2
ORDER BY leverage_z_score DESC;


-- =============================================================================
-- 8. COMPOSITE ANOMALY SCORE
-- Unified view — one row per (company, year) with all anomaly flags
-- and a total score. Use as the main alert table for supervision.
-- =============================================================================

WITH base AS (
    SELECT
        ruc,
        company_name,
        entity_type,
        YEAR(CAST(date AS DATE))  AS fiscal_year,
        period_type,
        SUM(CASE WHEN account_code = '1' THEN value END) AS assets,
        SUM(CASE WHEN account_code = '2' THEN value END) AS liabilities,
        SUM(CASE WHEN account_code = '3' THEN value END) AS equity,
        SUM(CASE WHEN account_code = '4' THEN value END) AS income,
        SUM(CASE WHEN account_code = '5' THEN value END) AS expenses
    FROM financial_statements
    WHERE date IS NOT NULL
      AND account_code IN ('1','2','3','4','5')
    GROUP BY ruc, company_name, entity_type,
             YEAR(CAST(date AS DATE)), period_type
),
with_yoy AS (
    SELECT
        *,
        LAG(assets) OVER (PARTITION BY ruc, period_type ORDER BY fiscal_year)
            AS prev_assets,
        LAG(income) OVER (PARTITION BY ruc, period_type ORDER BY fiscal_year)
            AS prev_income
    FROM base
),
sector_avg_change AS (
    SELECT
        entity_type,
        fiscal_year,
        period_type,
        AVG(ABS(assets - LAG(assets) OVER (PARTITION BY ruc ORDER BY fiscal_year)))
            AS avg_abs_asset_change
    FROM base
    GROUP BY entity_type, fiscal_year, period_type
)
SELECT
    b.ruc,
    b.company_name,
    b.entity_type,
    b.fiscal_year,
    b.period_type,
    ROUND(b.assets,      2) AS total_assets,
    ROUND(b.liabilities, 2) AS total_liabilities,
    ROUND(b.equity,      2) AS total_equity,
    ROUND(b.income,      2) AS total_income,
    ROUND(b.expenses,    2) AS total_expenses,

    -- Individual anomaly flags (1 = triggered)
    (b.assets < 0)::INT
        AS flag_negative_assets,
    (b.liabilities / NULLIF(b.assets, 0) > 1.20)::INT
        AS flag_extreme_leverage,
    (b.equity < 0)::INT
        AS flag_negative_equity,
    (b.income = 0 AND b.expenses > 0)::INT
        AS flag_zero_income_with_costs,
    (b.income  < b.income    * 0.50 AND b.prev_income  > 0)::INT
        AS flag_income_halved,
    (ABS(b.assets - b.prev_assets) > s.avg_abs_asset_change * 3
        AND b.prev_assets IS NOT NULL)::INT
        AS flag_abnormal_asset_change,
    (b.income > 0 AND b.expenses = 0)::INT
        AS flag_zero_expenses_with_income,

    -- Composite score (0–7)
    (b.assets < 0)::INT
    + (b.liabilities / NULLIF(b.assets, 0) > 1.20)::INT
    + (b.equity < 0)::INT
    + (b.income = 0 AND b.expenses > 0)::INT
    + (b.income < b.income * 0.50 AND b.prev_income > 0)::INT
    + (ABS(b.assets - b.prev_assets) > s.avg_abs_asset_change * 3
        AND b.prev_assets IS NOT NULL)::INT
    + (b.income > 0 AND b.expenses = 0)::INT
        AS anomaly_score,

    CASE
        (b.assets < 0)::INT
        + (b.liabilities / NULLIF(b.assets, 0) > 1.20)::INT
        + (b.equity < 0)::INT
        + (b.income = 0 AND b.expenses > 0)::INT
        + (b.income < b.income * 0.50 AND b.prev_income > 0)::INT
        + (ABS(b.assets - b.prev_assets) > s.avg_abs_asset_change * 3
            AND b.prev_assets IS NOT NULL)::INT
        + (b.income > 0 AND b.expenses = 0)::INT
        WHEN 0 THEN 'Normal'
        WHEN 1 THEN 'Watch'
        WHEN 2 THEN 'Suspicious'
        ELSE        'Critical'
    END AS anomaly_level

FROM with_yoy b
JOIN sector_avg_change s
  ON  s.entity_type = b.entity_type
  AND s.fiscal_year = b.fiscal_year
  AND s.period_type = b.period_type
ORDER BY anomaly_score DESC, b.fiscal_year DESC;

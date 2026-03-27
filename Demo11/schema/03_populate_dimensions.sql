-- =============================================================================
-- POPULATE DIMENSIONS from the normalized financial_statements table
-- Run once after the ETL pipeline loads raw data, then re-run incrementally.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- dim_date — generate one row per distinct reporting date in the dataset
-- ---------------------------------------------------------------------------
INSERT OR IGNORE INTO dim_date
SELECT
    CAST(strftime(full_date, '%Y%m%d') AS INTEGER)   AS date_key,
    full_date,
    EXTRACT('day'   FROM full_date)::TINYINT          AS day_of_month,
    EXTRACT('dow'   FROM full_date)::TINYINT          AS day_of_week,  -- 0=Sun DuckDB
    strftime(full_date, '%A')                         AS day_name,
    EXTRACT('week'  FROM full_date)::TINYINT          AS week_of_year,
    EXTRACT('month' FROM full_date)::TINYINT          AS month_num,
    strftime(full_date, '%B')                         AS month_name,
    EXTRACT('quarter' FROM full_date)::TINYINT        AS quarter,
    CASE WHEN EXTRACT('month' FROM full_date) <= 6
         THEN 1 ELSE 2 END::TINYINT                   AS semester,
    EXTRACT('year'  FROM full_date)::SMALLINT         AS fiscal_year,
    (full_date = last_day(full_date))                 AS is_month_end,
    (EXTRACT('month' FROM full_date) = 12
     AND EXTRACT('day' FROM full_date) = 31)          AS is_year_end,
    period_type
FROM (
    SELECT DISTINCT
        CAST(date AS DATE) AS full_date,
        period_type
    FROM financial_statements
    WHERE date IS NOT NULL
);

-- ---------------------------------------------------------------------------
-- dim_sector
-- ---------------------------------------------------------------------------
INSERT OR IGNORE INTO dim_sector (sector_key, sector_code, sector_name)
SELECT
    ROW_NUMBER() OVER (ORDER BY sector_code)::SMALLINT,
    sector_code,
    entity_type
FROM (
    SELECT DISTINCT sector_code, entity_type
    FROM financial_statements
    WHERE sector_code IS NOT NULL
) s;

-- ---------------------------------------------------------------------------
-- dim_company
-- ---------------------------------------------------------------------------
INSERT OR IGNORE INTO dim_company
    (company_key, ruc, company_name, sector_key, sector_code, sector_name)
SELECT
    ROW_NUMBER() OVER (ORDER BY c.ruc)::INTEGER,
    c.ruc,
    c.company_name,
    s.sector_key,
    s.sector_code,
    s.sector_name
FROM (
    SELECT DISTINCT ruc, company_name, sector_code
    FROM financial_statements
    WHERE ruc IS NOT NULL
) c
JOIN dim_sector s ON s.sector_code = c.sector_code;

-- ---------------------------------------------------------------------------
-- dim_account  — derive hierarchy from account_code length
-- ---------------------------------------------------------------------------
INSERT OR IGNORE INTO dim_account (
    account_key,
    account_code,
    account_name,
    account_level,
    class_code,
    class_name,
    group_code,
    group_name,
    subgroup_code,
    subgroup_name,
    account_class,
    is_leaf
)
WITH codes AS (
    SELECT DISTINCT account_code, account_name
    FROM financial_statements
    WHERE account_code IS NOT NULL
),
classified AS (
    SELECT
        account_code,
        account_name,
        LENGTH(account_code)::TINYINT AS account_level,

        LEFT(account_code, 1)  AS class_code,
        LEFT(account_code, 3)  AS group_code,
        LEFT(account_code, 5)  AS subgroup_code,

        CASE LEFT(account_code, 1)
            WHEN '1' THEN 'Assets'
            WHEN '2' THEN 'Liabilities'
            WHEN '3' THEN 'Equity'
            WHEN '4' THEN 'Income'
            WHEN '5' THEN 'Expenses'
            ELSE          'Other'
        END AS account_class
    FROM codes
)
SELECT
    ROW_NUMBER() OVER (ORDER BY c.account_code)::INTEGER AS account_key,
    c.account_code,
    c.account_name,
    c.account_level,

    c.class_code,
    cls.account_name                                     AS class_name,

    CASE WHEN c.account_level >= 3 THEN c.group_code    END AS group_code,
    grp.account_name                                     AS group_name,

    CASE WHEN c.account_level >= 5 THEN c.subgroup_code END AS subgroup_code,
    sub.account_name                                     AS subgroup_name,

    c.account_class,

    -- is_leaf = no other code starts with this code as prefix (excluding itself)
    NOT EXISTS (
        SELECT 1 FROM codes child
        WHERE child.account_code LIKE c.account_code || '%'
          AND child.account_code <> c.account_code
    ) AS is_leaf

FROM classified c
LEFT JOIN codes cls ON cls.account_code = c.class_code
LEFT JOIN codes grp ON grp.account_code = c.group_code AND c.account_level >= 3
LEFT JOIN codes sub ON sub.account_code = c.subgroup_code AND c.account_level >= 5;

-- ---------------------------------------------------------------------------
-- financial_fact — load from flat financial_statements table
-- ---------------------------------------------------------------------------
INSERT OR IGNORE INTO financial_fact (
    fact_id,
    company_key,
    account_key,
    date_key,
    period_type,
    value,
    total_assets,
    total_liabilities,
    total_equity,
    total_income,
    total_expenses
)
SELECT
    ROW_NUMBER() OVER ()::BIGINT                          AS fact_id,
    dc.company_key,
    da.account_key,
    dd.date_key,
    fs.period_type,
    fs.value,

    -- Snapshot class-level values onto every row of that company+period
    -- (NULL for rows that are not the class-level code themselves)
    CASE WHEN da.account_class = 'Assets'      AND da.account_level = 1
         THEN fs.value END                                AS total_assets,
    CASE WHEN da.account_class = 'Liabilities' AND da.account_level = 1
         THEN fs.value END                                AS total_liabilities,
    CASE WHEN da.account_class = 'Equity'      AND da.account_level = 1
         THEN fs.value END                                AS total_equity,
    CASE WHEN da.account_class = 'Income'      AND da.account_level = 1
         THEN fs.value END                                AS total_income,
    CASE WHEN da.account_class = 'Expenses'    AND da.account_level = 1
         THEN fs.value END                                AS total_expenses

FROM financial_statements  fs
JOIN dim_company dc  ON dc.ruc          = fs.ruc
JOIN dim_account da  ON da.account_code = fs.account_code
JOIN dim_date    dd  ON dd.full_date    = CAST(fs.date AS DATE)
                    AND dd.period_type  = fs.period_type
WHERE fs.date IS NOT NULL;

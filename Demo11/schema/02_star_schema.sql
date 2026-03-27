-- =============================================================================
-- STAR SCHEMA — optimized for BI dashboards
-- Purpose : analytical layer on top of the normalized schema.
--           Denormalized for fast aggregations; avoids multi-join queries
--           from BI tools (Metabase, Superset, Power BI, Grafana).
-- Engine  : DuckDB
--
-- Layout:
--
--                    ┌──────────────┐
--                    │  dim_date    │
--                    └──────┬───────┘
--                           │
--   ┌──────────────┐        │        ┌──────────────────┐
--   │  dim_company │────────┼────────│  dim_account     │
--   └──────┬───────┘        │        └────────┬─────────┘
--           │               ▼                 │
--           └──────► fact_financial ◄─────────┘
--                           │
--                    ┌──────┴───────┐
--                    │  dim_sector  │
--                    └──────────────┘
-- =============================================================================

-- ---------------------------------------------------------------------------
-- DIMENSION: DATE
-- Pre-expanded calendar — one row per day for the reporting range.
-- BI tools can filter/group by any time grain without runtime YEAR()/MONTH().
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_date (
    date_key      INTEGER      PRIMARY KEY,   -- surrogate: YYYYMMDD integer
    full_date     DATE         NOT NULL UNIQUE,
    day_of_month  TINYINT      NOT NULL,
    day_of_week   TINYINT      NOT NULL,      -- 1=Monday … 7=Sunday
    day_name      VARCHAR(10)  NOT NULL,
    week_of_year  TINYINT      NOT NULL,
    month_num     TINYINT      NOT NULL,
    month_name    VARCHAR(10)  NOT NULL,
    quarter       TINYINT      NOT NULL,      -- 1–4
    semester      TINYINT      NOT NULL,      -- 1–2
    fiscal_year   SMALLINT     NOT NULL,
    is_month_end  BOOLEAN      NOT NULL,
    is_year_end   BOOLEAN      NOT NULL,
    period_type   VARCHAR(20)  NOT NULL       -- ANUAL | MENSUAL | TRIMESTRAL
);

-- ---------------------------------------------------------------------------
-- DIMENSION: SECTOR
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_sector (
    sector_key    SMALLINT     PRIMARY KEY,   -- surrogate
    sector_code   VARCHAR(10)  NOT NULL UNIQUE,
    sector_name   VARCHAR(255) NOT NULL
);

-- ---------------------------------------------------------------------------
-- DIMENSION: COMPANY
-- Denormalized — sector fields copied in to avoid joins in BI queries.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_company (
    company_key   INTEGER      PRIMARY KEY,   -- surrogate
    ruc           VARCHAR(13)  NOT NULL UNIQUE,
    company_name  VARCHAR(500) NOT NULL,
    sector_key    SMALLINT     NOT NULL REFERENCES dim_sector(sector_key),
    -- Denormalized sector fields for filter convenience
    sector_code   VARCHAR(10)  NOT NULL,
    sector_name   VARCHAR(255) NOT NULL
);

-- ---------------------------------------------------------------------------
-- DIMENSION: ACCOUNT
-- Denormalized hierarchy — all ancestor labels stored on each row so
-- BI tools can drill from class → group → subgroup without recursive CTEs.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_account (
    account_key       INTEGER      PRIMARY KEY,   -- surrogate
    account_code      VARCHAR(20)  NOT NULL UNIQUE,
    account_name      VARCHAR(500) NOT NULL,
    account_level     TINYINT      NOT NULL,       -- 1 / 3 / 5 / 7

    -- Hierarchy breadcrumbs (denormalized)
    class_code        VARCHAR(5)   NOT NULL,       -- e.g. "1"
    class_name        VARCHAR(255),                -- e.g. "ACTIVO"
    group_code        VARCHAR(5),                  -- e.g. "101"
    group_name        VARCHAR(255),                -- e.g. "ACTIVO CORRIENTE"
    subgroup_code     VARCHAR(10),                 -- e.g. "10101"
    subgroup_name     VARCHAR(255),                -- e.g. "EFECTIVO Y EQUIVALENTES"

    -- Semantic classification (for cross-company BI filters)
    account_class     VARCHAR(20)  NOT NULL        -- Assets | Liabilities | Equity | Income | Expenses
        CHECK (account_class IN ('Assets','Liabilities','Equity','Income','Expenses','Other')),
    is_leaf           BOOLEAN      NOT NULL        -- true = no child accounts below
);

-- ---------------------------------------------------------------------------
-- FACT TABLE: financial_fact
-- Grain: one row per (company, account, reporting date, period type)
-- All foreign keys are integer surrogates — joins stay fast.
-- Pre-computed derived metrics avoid runtime calculation in dashboards.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS financial_fact (
    fact_id          BIGINT    PRIMARY KEY,
    -- Foreign keys to dimensions
    company_key      INTEGER   NOT NULL REFERENCES dim_company(company_key),
    account_key      INTEGER   NOT NULL REFERENCES dim_account(account_key),
    date_key         INTEGER   NOT NULL REFERENCES dim_date(date_key),

    -- Degenerate dimensions (low-cardinality flags stored directly in fact)
    period_type      VARCHAR(20) NOT NULL,

    -- Measures
    value            DOUBLE    NOT NULL,           -- reported account value

    -- Pre-aggregated measures at class level (populated via ETL)
    -- Avoids scanning millions of rows for top-level KPIs.
    -- NULL for non-class-level rows.
    total_assets     DOUBLE,    -- value when account_class = 'Assets'    and level = 1
    total_liabilities DOUBLE,   -- value when account_class = 'Liabilities' and level = 1
    total_equity     DOUBLE,    -- value when account_class = 'Equity'    and level = 1
    total_income     DOUBLE,    -- value when account_class = 'Income'    and level = 1
    total_expenses   DOUBLE,    -- value when account_class = 'Expenses'  and level = 1

    -- Audit
    loaded_at        TIMESTAMP DEFAULT current_timestamp,

    UNIQUE (company_key, account_key, date_key, period_type)
);

-- =============================================================================
-- INDEXES — star schema
-- =============================================================================

-- Fact table: cover the most common BI query patterns
CREATE INDEX IF NOT EXISTS idx_fact_company    ON financial_fact(company_key);
CREATE INDEX IF NOT EXISTS idx_fact_date       ON financial_fact(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_account    ON financial_fact(account_key);
CREATE INDEX IF NOT EXISTS idx_fact_period     ON financial_fact(period_type);

-- Composite: company + year slice (used by time-series dashboards)
CREATE INDEX IF NOT EXISTS idx_fact_co_date    ON financial_fact(company_key, date_key);

-- Composite: account_class filter + year (used by asset/liability dashboards)
CREATE INDEX IF NOT EXISTS idx_fact_acct_date  ON financial_fact(account_key, date_key);

-- dim_date: BI filters almost always slice by fiscal_year and period_type
CREATE INDEX IF NOT EXISTS idx_date_year       ON dim_date(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_date_period     ON dim_date(fiscal_year, period_type);

-- dim_account: drill-down by class hierarchy
CREATE INDEX IF NOT EXISTS idx_acct_class      ON dim_account(account_class);
CREATE INDEX IF NOT EXISTS idx_acct_level      ON dim_account(account_level);
CREATE INDEX IF NOT EXISTS idx_acct_class_code ON dim_account(class_code);

-- dim_company: filter by sector
CREATE INDEX IF NOT EXISTS idx_co_sector       ON dim_company(sector_key);

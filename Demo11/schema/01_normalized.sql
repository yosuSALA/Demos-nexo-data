-- =============================================================================
-- NORMALIZED SCHEMA (3NF)
-- Purpose : operational store — the canonical, deduplicated source of truth.
--           Feed from the ETL pipeline; power the star schema via views/CTAS.
-- Engine  : DuckDB (syntax-compatible with PostgreSQL for migration)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. SECTORS  (entity-type taxonomy)
-- ---------------------------------------------------------------------------
-- Maps the numeric sector_code to its sector label.
-- Example: 22 → 'ADMINISTRADORA DE FONDOS Y FIDEICOMISOS'
CREATE TABLE IF NOT EXISTS sector (
    sector_code   VARCHAR(10)  PRIMARY KEY,   -- source code (22, 522, …)
    sector_name   VARCHAR(255) NOT NULL
);

-- ---------------------------------------------------------------------------
-- 2. COMPANIES  (one row per legal entity)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS company (
    ruc           VARCHAR(13)  PRIMARY KEY,   -- Ecuador 13-digit tax ID
    company_name  VARCHAR(500) NOT NULL,
    sector_code   VARCHAR(10)  REFERENCES sector(sector_code)
);

-- ---------------------------------------------------------------------------
-- 3. ACCOUNTS  (chart of accounts — hierarchical)
-- ---------------------------------------------------------------------------
-- Hierarchy is encoded in the code length:
--   1 digit  = class      e.g. "1"     ACTIVO
--   3 digits = group      e.g. "101"   ACTIVO CORRIENTE
--   5 digits = subgroup   e.g. "10101" EFECTIVO Y EQUIVALENTES
--   7+       = detail lines
CREATE TABLE IF NOT EXISTS account (
    account_code    VARCHAR(20)  PRIMARY KEY,
    account_name    VARCHAR(500) NOT NULL,
    account_level   TINYINT      NOT NULL      -- 1 / 3 / 5 / 7 = hierarchy depth
        CHECK (account_level IN (1, 3, 5, 7, 9)),
    parent_code     VARCHAR(20)  REFERENCES account(account_code),
    account_class   VARCHAR(20)  NOT NULL      -- Assets / Liabilities / Equity / Income / Expenses
        CHECK (account_class IN ('Assets','Liabilities','Equity','Income','Expenses','Other'))
);

-- ---------------------------------------------------------------------------
-- 4. REPORTING PERIODS
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reporting_period (
    period_id     SMALLINT     PRIMARY KEY,
    period_date   DATE         NOT NULL,
    period_type   VARCHAR(20)  NOT NULL        -- ANUAL | MENSUAL | TRIMESTRAL
        CHECK (period_type IN ('ANUAL','MENSUAL','TRIMESTRAL','SEMESTRAL')),
    fiscal_year   SMALLINT     NOT NULL,
    fiscal_month  TINYINT,                     -- NULL for ANUAL
    fiscal_quarter TINYINT,                    -- NULL unless TRIMESTRAL
    UNIQUE (period_date, period_type)
);

-- ---------------------------------------------------------------------------
-- 5. FINANCIAL STATEMENTS  (fact — atomic grain)
-- ---------------------------------------------------------------------------
-- One row = one account value for one company in one reporting period.
CREATE TABLE IF NOT EXISTS financial_statement (
    id            BIGINT       PRIMARY KEY,    -- surrogate key
    ruc           VARCHAR(13)  NOT NULL REFERENCES company(ruc),
    account_code  VARCHAR(20)  NOT NULL REFERENCES account(account_code),
    period_id     SMALLINT     NOT NULL REFERENCES reporting_period(period_id),
    value         DOUBLE       NOT NULL,
    loaded_at     TIMESTAMP    DEFAULT current_timestamp,

    UNIQUE (ruc, account_code, period_id)     -- natural deduplication key
);

-- =============================================================================
-- INDEXES — normalized schema
-- =============================================================================

-- Most queries filter by company + period
CREATE INDEX IF NOT EXISTS idx_stmt_ruc        ON financial_statement(ruc);
CREATE INDEX IF NOT EXISTS idx_stmt_period     ON financial_statement(period_id);
CREATE INDEX IF NOT EXISTS idx_stmt_account    ON financial_statement(account_code);

-- Hierarchical account lookups (parent rollups)
CREATE INDEX IF NOT EXISTS idx_acct_parent     ON account(parent_code);
CREATE INDEX IF NOT EXISTS idx_acct_class      ON account(account_class);

-- Period lookups by year
CREATE INDEX IF NOT EXISTS idx_period_year     ON reporting_period(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_period_type     ON reporting_period(period_type);

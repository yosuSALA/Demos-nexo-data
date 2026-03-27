-- =============================================================================
-- Master script: creates all analytical views in the correct order.
-- Run this once after the ETL pipeline loads data into financial_statements.
--
-- Usage (DuckDB CLI):
--   duckdb output/supercias.duckdb < sql/00_create_marts.sql
--
-- Usage (Python):
--   conn.execute(open("sql/00_create_marts.sql").read())
-- =============================================================================

.read sql/01_mart_yearly_summary.sql
.read sql/02_mart_assets_vs_liabilities.sql
.read sql/03_mart_account_categories.sql
.read sql/04_mart_company_ranking.sql

-- Verify all views exist
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'main'
ORDER BY table_name;

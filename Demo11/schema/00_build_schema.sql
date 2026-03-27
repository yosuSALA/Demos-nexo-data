-- =============================================================================
-- MASTER BUILD SCRIPT
-- Runs all schema files in order.
--
-- Usage (DuckDB CLI — run AFTER ETL pipeline has loaded financial_statements):
--   duckdb output/supercias.duckdb < schema/00_build_schema.sql
-- =============================================================================

.read schema/01_normalized.sql
.read schema/02_star_schema.sql
.read schema/03_populate_dimensions.sql
.read schema/04_bi_views.sql

-- Verify
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'main'
ORDER BY table_type DESC, table_name;

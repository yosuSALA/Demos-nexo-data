-- =============================================================================
-- MART 2: Activos vs Pasivos
--
-- Clasificación por primer dígito del account_code (funciona para ambos formatos):
--   1x → Activos      (ACTIVO)
--   2x → Pasivos      (PASIVO)
--   3x → Patrimonio
--   4x → Ingresos
--   5x → Gastos
--   6–9 → Especiales / Fuera de balance (ej. cuenta 98: CAMBIOS EN ACTIVOS Y PASIVOS)
--
-- Estrategia para evitar doble conteo según formato:
--   ANUAL    : usa account_code de 1 solo dígito ('1','2','3','4','5') → totales ya consolidados
--   MENSUAL  : no existe cuenta raíz de 1 dígito → se suman las HOJAS (SPLIT_PART tiene > 1 segmento)
--              Las hojas se detectan con: NOT EXISTS cuenta hija con el mismo prefijo
--
-- Para simplicidad operativa, el mart filtra por el nivel más alto disponible por periodo:
--   - Si existe account_code = '1' para ese (ruc, date, period_type) → usar ese valor
--   - Si no existe → sumar todos los account_code cuyo primer dígito = '1'
--     que NO tengan un código hijo en el mismo dataset (hojas del árbol)
--
-- Grain: una fila por (ruc, fiscal_year, period_type)
-- =============================================================================

CREATE OR REPLACE VIEW mart_assets_vs_liabilities AS
WITH
-- Detecta si para cada (ruc, date, period_type) existe un código raíz de 1 dígito
has_root AS (
    SELECT DISTINCT ruc, date, period_type
    FROM financial_statements
    WHERE LENGTH(account_code) = 1
      AND LEFT(account_code, 1) IN ('1','2','3','4','5')
),
-- Hojas del árbol: account_codes que no son prefijo de ningún otro código del mismo registro
leaves AS (
    SELECT fs.ruc, fs.date, fs.period_type, fs.account_code,
           fs.value, LEFT(fs.account_code, 1) AS class_digit
    FROM financial_statements fs
    -- No tiene ningún registro hijo (con el mismo prefijo + más caracteres)
    WHERE NOT EXISTS (
        SELECT 1 FROM financial_statements child
        WHERE child.ruc         = fs.ruc
          AND child.date        = fs.date
          AND child.period_type = fs.period_type
          AND child.account_code LIKE fs.account_code || '%'
          AND child.account_code <> fs.account_code
    )
      AND LEFT(fs.account_code, 1) IN ('1','2','3','4','5')
),
-- Totales por clase: usa el código raíz cuando existe, hojas cuando no
class_totals AS (
    -- Datos ANUAL: existe la cuenta raíz → usar directamente
    SELECT
        fs.ruc, fs.company_name, fs.entity_type, fs.entity_subtype,
        fs.date, fs.period_type,
        LEFT(fs.account_code, 1) AS class_digit,
        fs.value
    FROM financial_statements fs
    JOIN has_root hr
      ON hr.ruc = fs.ruc AND hr.date = fs.date AND hr.period_type = fs.period_type
    WHERE LENGTH(fs.account_code) = 1
      AND LEFT(fs.account_code, 1) IN ('1','2','3','4','5')

    UNION ALL

    -- Datos MENSUAL: no existe cuenta raíz → sumar hojas
    SELECT
        lf.ruc,
        fs2.company_name, fs2.entity_type, fs2.entity_subtype,
        lf.date, lf.period_type,
        lf.class_digit,
        SUM(lf.value) AS value
    FROM leaves lf
    JOIN financial_statements fs2
      ON fs2.ruc = lf.ruc AND fs2.date = lf.date AND fs2.period_type = lf.period_type
      AND fs2.account_code = lf.account_code
    LEFT JOIN has_root hr2
      ON hr2.ruc = lf.ruc AND hr2.date = lf.date AND hr2.period_type = lf.period_type
    WHERE hr2.ruc IS NULL   -- solo procesa registros sin cuenta raíz
    GROUP BY lf.ruc, fs2.company_name, fs2.entity_type, fs2.entity_subtype,
             lf.date, lf.period_type, lf.class_digit
)
SELECT
    ruc,
    company_name,
    entity_type,
    entity_subtype,
    YEAR(CAST(date AS DATE))                                         AS fiscal_year,
    period_type,

    SUM(CASE WHEN class_digit = '1' THEN value ELSE 0 END)           AS total_activos,
    SUM(CASE WHEN class_digit = '2' THEN value ELSE 0 END)           AS total_pasivos,
    SUM(CASE WHEN class_digit = '3' THEN value ELSE 0 END)           AS total_patrimonio,
    SUM(CASE WHEN class_digit = '4' THEN value ELSE 0 END)           AS total_ingresos,
    SUM(CASE WHEN class_digit = '5' THEN value ELSE 0 END)           AS total_gastos,

    -- Indicadores derivados
    SUM(CASE WHEN class_digit = '1' THEN value ELSE 0 END) -
    SUM(CASE WHEN class_digit = '2' THEN value ELSE 0 END)           AS patrimonio_neto,

    ROUND(
        SUM(CASE WHEN class_digit = '2' THEN value ELSE 0 END) /
        NULLIF(SUM(CASE WHEN class_digit = '1' THEN value ELSE 0 END), 0),
        4
    )                                                                 AS razon_apalancamiento,

    SUM(CASE WHEN class_digit = '4' THEN value ELSE 0 END) -
    SUM(CASE WHEN class_digit = '5' THEN value ELSE 0 END)           AS resultado_neto

FROM class_totals
GROUP BY ruc, company_name, entity_type, entity_subtype,
         YEAR(CAST(date AS DATE)), period_type
ORDER BY fiscal_year DESC, period_type, total_activos DESC;

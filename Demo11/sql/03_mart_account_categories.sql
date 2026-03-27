-- =============================================================================
-- MART 3: Resumen por categoría de cuenta
--
-- Jerarquía de account_code — DOS formatos coexisten:
--
--   Formato ANUAL (entero simple):
--     1 dígito  → clase    ej. "1"     ACTIVO
--     3 dígitos → grupo    ej. "101"   ACTIVO CORRIENTE
--     5 dígitos → subgrupo ej. "10101" EFECTIVO Y EQUIVALENTES
--
--   Formato MENSUAL (jerarquía con puntos):
--     1 segmento  → "502"         (clase/grupo raíz)
--     2 segmentos → "502.03"      (subgrupo)
--     3 segmentos → "502.03.08"   (cuenta detalle)
--     N segmentos → "101.02.02.02.08" (cuenta hoja profunda)
--
-- Clasificación por primer dígito (válido en AMBOS formatos):
--   1 → Activos | 2 → Pasivos | 3 → Patrimonio | 4 → Ingresos | 5 → Gastos
--   6–9 → Especiales (ej. 98 = Cambios en activos y pasivos, flujo de caja)
--
-- Grain: una fila por (fiscal_year, period_type, clase, grupo_raiz)
-- =============================================================================

CREATE OR REPLACE VIEW mart_account_categories AS
WITH parsed AS (
    SELECT
        YEAR(CAST(date AS DATE))   AS fiscal_year,
        period_type,
        entity_type,
        entity_subtype,
        account_code,
        account_name,
        value,

        -- Primer dígito → clase (igual para entero y formato con puntos)
        LEFT(account_code, 1)      AS class_digit,

        -- Etiqueta semántica de la clase
        CASE LEFT(account_code, 1)
            WHEN '1' THEN 'Activos'
            WHEN '2' THEN 'Pasivos'
            WHEN '3' THEN 'Patrimonio'
            WHEN '4' THEN 'Ingresos'
            WHEN '5' THEN 'Gastos'
            ELSE          'Especiales'
        END                        AS account_class,

        -- Grupo raíz: primer segmento antes del primer punto (o el código completo si no hay puntos)
        -- "502.03.08" → "502" | "101.02.02.02.08" → "101" | "10101" → "10101" | "1" → "1"
        SPLIT_PART(account_code, '.', 1) AS root_segment,

        -- Nivel de profundidad en la jerarquía
        -- Formato con puntos: contar puntos + 1
        -- Formato entero: usar longitud (1→clase, 3→grupo, 5→subgrupo, 7+→detalle)
        CASE
            WHEN account_code LIKE '%.%'
                THEN LENGTH(account_code) - LENGTH(REPLACE(account_code, '.', '')) + 1
            WHEN LENGTH(account_code) = 1 THEN 1
            WHEN LENGTH(account_code) = 3 THEN 2
            WHEN LENGTH(account_code) = 5 THEN 3
            ELSE 4
        END                        AS depth_level,

        -- Etiqueta de nivel
        CASE
            WHEN account_code LIKE '%.%' THEN
                CASE LENGTH(account_code) - LENGTH(REPLACE(account_code, '.', ''))
                    WHEN 0 THEN 'raiz'
                    WHEN 1 THEN 'grupo'
                    WHEN 2 THEN 'subgrupo'
                    ELSE        'detalle'
                END
            ELSE
                CASE LENGTH(account_code)
                    WHEN 1 THEN 'clase'
                    WHEN 3 THEN 'grupo'
                    WHEN 5 THEN 'subgrupo'
                    ELSE        'detalle'
                END
        END                        AS account_level_label

    FROM financial_statements
    WHERE date IS NOT NULL
),
aggregated AS (
    SELECT
        fiscal_year,
        period_type,
        entity_type,
        entity_subtype,
        account_class,
        root_segment,
        -- Nombre del grupo raíz: tomar el de la cuenta con menor profundidad del segmento
        FIRST(account_name ORDER BY depth_level, account_code) AS root_name,
        COUNT(DISTINCT account_code)   AS cuentas_distintas,
        COUNT(*)                       AS filas,
        SUM(value)                     AS total_valor,
        AVG(value)                     AS promedio_valor,
        MIN(value)                     AS valor_minimo,
        MAX(value)                     AS valor_maximo
    FROM parsed
    GROUP BY fiscal_year, period_type, entity_type, entity_subtype,
             account_class, root_segment
)
SELECT
    *,
    ROUND(
        total_valor * 100.0 /
        NULLIF(SUM(total_valor) OVER (
            PARTITION BY fiscal_year, period_type, account_class
        ), 0),
        2
    ) AS pct_dentro_de_clase
FROM aggregated
ORDER BY fiscal_year DESC, period_type, account_class, total_valor DESC;

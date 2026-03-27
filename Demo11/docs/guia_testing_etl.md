# Guía de Testing — Pipeline ETL de Estados Financieros Supercias
**Rol:** Especialista en QA de Ingeniería de Datos
**Dataset:** Estados financieros — 15 millones de filas
**Stack:** Python · Polars · DuckDB · pytest

---

## Tabla de Contenidos

1. [Objetivos del Testing](#1-objetivos-del-testing)
2. [Tipos de Tests](#2-tipos-de-tests)
3. [Estructura del Proyecto de Tests](#3-estructura-del-proyecto-de-tests)
4. [Configuración del Entorno](#4-configuración-del-entorno)
5. [Procedimiento Paso a Paso](#5-procedimiento-paso-a-paso)
6. [Casos de Prueba Detallados](#6-casos-de-prueba-detallados)
7. [Consultas de Validación en DuckDB](#7-consultas-de-validación-en-duckdb)
8. [Resultados Esperados](#8-resultados-esperados)
9. [Criterios de Aceptación y Rechazo](#9-criterios-de-aceptación-y-rechazo)
10. [Registro de Resultados](#10-registro-de-resultados)

---

## 1. Objetivos del Testing

### 1.1 Objetivo General

Verificar que el pipeline ETL transforma, valida y carga correctamente los
estados financieros del sistema Supercias, garantizando la integridad y confiabilidad
de los datos que alimentan los dashboards de BI.

### 1.2 Objetivos Específicos

| # | Objetivo | Capa |
|---|---|---|
| O1 | Confirmar que la extracción del TSV asigna los 9 nombres de columna correctos y descarta la columna vacía trailing | Extracción |
| O2 | Verificar que los números en formato Ecuador (`1.188.854,66`) se convierten correctamente a `Float64` | Transformación |
| O3 | Confirmar que las fechas `dd/mm/yyyy` se normalizan a ISO 8601 (`YYYY-MM-DD`) | Transformación |
| O4 | Comprobar que las filas duplicadas (mismo RUC + cuenta + fecha + período) se eliminan | Transformación |
| O5 | Asegurar que las filas con campos críticos nulos (`ruc`, `account_code`, `value`) se descartan | Transformación |
| O6 | Validar que el esquema de DuckDB contiene las columnas y el índice único correctos | Carga |
| O7 | Confirmar que la ejecución repetida del pipeline es idempotente (no duplica filas) | Carga |
| O8 | Verificar que las vistas analíticas (marts) producen resultados coherentes con el negocio | Analítica |
| O9 | Detectar valores financieros imposibles o anómalos en los datos cargados | Calidad |

### 1.3 Alcance

```
IN SCOPE                                    OUT OF SCOPE
────────────────────────────────────────    ────────────────────────────────
Extracción desde TSV sin cabecera           Autenticación / acceso a archivos
Transformación: números, fechas, dedup      Rendimiento en producción (> 15M)
Carga en DuckDB con índice único            Dashboards de BI (Metabase/Superset)
Vistas: mart_yearly_summary, etc.           Despliegue en infraestructura cloud
Detección de anomalías financieras          Integración con sistemas externos
```

---

## 2. Tipos de Tests

### 2.1 Pirámide de tests adoptada

```
                    ▲
                   /E2E\          test_integration.py
                  /─────\         (lentos — I/O real + DuckDB)
                 / Integ \
                /──────────\
               / Calidad de \     test_data_quality.py
              /   Datos       \   (reglas de negocio sobre DuckDB)
             /─────────────────\
            /    Unitarios       \  test_extract.py
           /─────────────────────\ test_transform.py
          /     (rápidos, en RAM)  \ test_load.py
         /───────────────────────────\ test_formatters.py
```

### 2.2 Descripción de cada tipo

#### Tests Unitarios
- **Qué prueban:** Una función o método en aislamiento.
- **Ventaja:** Milisegundos por test — retroalimentación inmediata.
- **Archivos:** `test_formatters.py`, `test_extract.py`, `test_transform.py`, `test_load.py`

#### Tests de Calidad de Datos
- **Qué prueban:** Reglas de negocio aplicadas sobre datos ya cargados en DuckDB en memoria.
- **Ventaja:** Detectan problemas de dominio que los tests unitarios no pueden ver (jerarquía de cuentas, RUC de 13 dígitos, fechas en rango válido).
- **Archivo:** `test_data_quality.py`

#### Tests de Integración (End-to-End)
- **Qué prueban:** El pipeline completo desde un archivo TSV real hasta DuckDB.
- **Ventaja:** Garantizan que todos los módulos cooperan correctamente.
- **Archivo:** `test_integration.py`

---

## 3. Estructura del Proyecto de Tests

```
script-data-SIB/
├── pytest.ini                      ← Configuración global de pytest
├── tests/
│   ├── conftest.py                 ← Fixtures compartidos (datos de muestra, DB en memoria)
│   ├── test_formatters.py          ← Parser de números EC y normalizador de fechas
│   ├── test_extract.py             ← Lectura del TSV, asignación de columnas
│   ├── test_transform.py           ← Limpieza, dedup, manejo de nulos
│   ├── test_load.py                ← Esquema DuckDB, INSERT OR IGNORE
│   ├── test_data_quality.py        ← Reglas de negocio: RUC, jerarquía, rangos
│   └── test_integration.py        ← Pipeline completo E2E
└── sql/
    └── 07_anomaly_detection.sql    ← Consultas de detección de anomalías
```

### Fila de referencia para todos los tests

```python
# En conftest.py — fila válida real del sistema Supercias:
VALID_ROW = {
    "sector_code": "22",
    "entity_type":  "ADMINISTRADORA DE FONDOS Y FIDEICOMISOS",
    "ruc":          "0991290915001",
    "company_name": "FUTURFID S.A.",
    "date":         "31/12/2023",
    "period_type":  "ANUAL",
    "account_code": "1",
    "account_name": "ACTIVO",
    "value":        "1.188.854,66",
}
```

---

## 4. Configuración del Entorno

### 4.1 Requisitos previos

```bash
# Python 3.11+
python --version

# Dependencias del proyecto
pip install -r requirements.txt

# Dependencias exclusivas de testing (si no están en requirements.txt)
pip install pytest pytest-cov
```

### 4.2 Verificar instalación

```bash
cd /home/yosusala/Proyectos/script-data-SIB
python -c "import polars, duckdb, pytest; print('OK')"
```

### 4.3 Estructura de `pytest.ini`

```ini
[pytest]
testpaths = tests
addopts   = -v --tb=short
markers   =
    integration: tests E2E lentos que requieren I/O de archivo y DuckDB real
```

---

## 5. Procedimiento Paso a Paso

### PASO 1 — Verificar que el entorno funciona

```bash
# Debe mostrar la lista de tests recolectados sin errores
pytest --collect-only
```

**Resultado esperado:**
```
collected 47 items
tests/test_formatters.py::test_parse_ec_number[...]
tests/test_extract.py::TestAssignColumnNames::test_renames_to_expected_names
...
```
Si aparece `ERROR` en lugar de `collected`, revisar imports y rutas en `conftest.py`.

---

### PASO 2 — Ejecutar tests unitarios (rápidos)

```bash
pytest -m "not integration" -v
```

**Tiempo esperado:** < 5 segundos
**Resultado esperado:** Todos en verde (`PASSED`)

---

### PASO 3 — Ejecutar tests de calidad de datos

```bash
pytest tests/test_data_quality.py -v
```

Estos tests validan reglas de negocio (RUC, jerarquía de cuentas, fechas) sobre
un DuckDB en memoria. Son independientes de archivos externos.

---

### PASO 4 — Ejecutar tests de integración (E2E)

```bash
pytest -m integration -v
```

**Tiempo esperado:** 5–30 segundos (crea archivos temporales reales)

---

### PASO 5 — Ejecutar la suite completa con cobertura

```bash
pytest --cov=etl --cov=utils --cov-report=term-missing
```

**Umbral mínimo de cobertura aceptable:** 80 %

---

### PASO 6 — Validar datos reales en DuckDB

Después de correr el pipeline con datos reales:

```bash
python run_pipeline.py \
  --input data/estados_financieros.tsv \
  --db output/sib.duckdb \
  --chunk-size 500000

# Abrir DuckDB y ejecutar consultas de validación
duckdb output/sib.duckdb
```

Luego ejecutar las consultas de la sección 7 de esta guía.

---

### PASO 7 — Ejecutar detección de anomalías

```bash
duckdb output/sib.duckdb < sql/07_anomaly_detection.sql
```

Revisar el resultado de la **Sección 8 (Puntaje compuesto)** y filtrar
por `anomaly_level = 'Critical'`.

---

## 6. Casos de Prueba Detallados

### Módulo: `utils/formatters.py`

#### CP-F01 — Conversión de número en formato Ecuador

| Campo | Detalle |
|---|---|
| **ID** | CP-F01 |
| **Descripción** | El parser convierte `1.188.854,66` (formato Ecuador) a `1188854.66` (float Python) |
| **Precondición** | Función `parse_ec_number` importada |
| **Entrada** | `"1.188.854,66"` |
| **Pasos** | `result = parse_ec_number("1.188.854,66")` |
| **Resultado esperado** | `1188854.66` (tolerancia: `±0.001`) |
| **Archivo** | `test_formatters.py::test_parse_ec_number` |

#### CP-F02 — Número inválido retorna `None`

| Campo | Detalle |
|---|---|
| **ID** | CP-F02 |
| **Entradas** | `"N/A"`, `"#REF!"`, `""`, `None` |
| **Resultado esperado** | `None` en todos los casos |
| **Por qué importa** | Un `None` en `value` descartará la fila en transform — no debe producir excepción |

#### CP-F03 — Normalización de fecha `dd/mm/yyyy` → ISO 8601

| Campo | Detalle |
|---|---|
| **ID** | CP-F03 |
| **Entrada** | `"31/12/2014"` |
| **Resultado esperado** | `"2014-12-31"` |
| **Formatos adicionales probados** | `dd-mm-yyyy`, `yyyy-mm-dd`, `yyyymmdd` |

---

### Módulo: `etl/extract.py`

#### CP-E01 — Asignación correcta de nombres de columna

| Campo | Detalle |
|---|---|
| **ID** | CP-E01 |
| **Descripción** | El TSV no tiene cabecera. Polars genera `column_1…column_10`. La función `_assign_column_names` debe renombrar a los 9 nombres reales y descartar la columna trailing vacía. |
| **Entrada** | DataFrame con 10 columnas genéricas |
| **Resultado esperado** | `df.columns == ["sector_code", "entity_type", "ruc", "company_name", "date", "period_type", "account_code", "account_name", "value"]` |

#### CP-E02 — Error por columnas insuficientes

| Campo | Detalle |
|---|---|
| **ID** | CP-E02 |
| **Entrada** | DataFrame con 8 columnas (< 9 requeridas) |
| **Resultado esperado** | `ValueError` con mensaje `"expected at least"` |
| **Por qué importa** | Detecta un archivo con separador incorrecto antes de corromper la DB |

#### CP-E03 — Archivo inexistente

| Campo | Detalle |
|---|---|
| **ID** | CP-E03 |
| **Entrada** | Ruta a archivo que no existe |
| **Resultado esperado** | `FileNotFoundError` |

#### CP-E04 — Todas las columnas son `Utf8` al salir de la extracción

| Campo | Detalle |
|---|---|
| **ID** | CP-E04 |
| **Por qué importa** | `infer_schema_length=0` garantiza lectura como texto. Si alguna columna es inferida como número, el pipeline de transformación puede fallar silenciosamente. |
| **Resultado esperado** | `df[col].dtype == pl.Utf8` para todas las columnas |

---

### Módulo: `etl/transform.py`

#### CP-T01 — Limpieza de número EC en columna `value`

| Campo | Detalle |
|---|---|
| **ID** | CP-T01 |
| **Entrada** | Fila con `value = "1.188.854,66"` |
| **Resultado esperado** | `df["value"][0] == 1188854.66` y `dtype == Float64` |

#### CP-T02 — Fila con `value` inválido es descartada

| Campo | Detalle |
|---|---|
| **ID** | CP-T02 |
| **Entrada** | Fila con `value = "N/A"` |
| **Resultado esperado** | `len(df) == 0` — la fila fue eliminada porque `value` es columna crítica |

#### CP-T03 — El cero (`0,00`) es un valor válido y se conserva

| Campo | Detalle |
|---|---|
| **ID** | CP-T03 |
| **Justificación** | Los estados financieros pueden reportar cero legítimamente (cuenta sin movimiento). No debe confundirse con un valor nulo. |
| **Entrada** | `value = "0,00"` |
| **Resultado esperado** | `len(df) == 1` y `df["value"][0] == 0.0` |

#### CP-T04 — Deduplicación intra-chunk

| Campo | Detalle |
|---|---|
| **ID** | CP-T04 |
| **Entrada** | 2 filas idénticas en `(ruc, account_code, date, period_type)` con valores distintos |
| **Resultado esperado** | `len(df) == 1` — solo se conserva la primera ocurrencia |

#### CP-T05 — ANUAL y MENSUAL del mismo período no son duplicados

| Campo | Detalle |
|---|---|
| **ID** | CP-T05 |
| **Justificación** | El campo `period_type` forma parte de la clave única. Una empresa puede reportar el mismo mes tanto en un informe mensual como en el anual. |
| **Entrada** | 2 filas con mismo `ruc + account_code + date` pero `period_type = ANUAL` y `MENSUAL` respectivamente |
| **Resultado esperado** | `len(df) == 2` |

#### CP-T06 — Espacios en blanco son eliminados

| Campo | Detalle |
|---|---|
| **ID** | CP-T06 |
| **Entrada** | `ruc = "  0991290915001  "` |
| **Resultado esperado** | `df["ruc"][0] == "0991290915001"` |

#### CP-T07 — Columnas no críticas nulas no eliminan la fila

| Campo | Detalle |
|---|---|
| **ID** | CP-T07 |
| **Entrada** | Fila con `company_name = ""` y `account_name = ""` |
| **Resultado esperado** | `len(df) == 1` — solo `ruc`, `account_code` y `value` son críticos |

---

### Módulo: `etl/load.py`

#### CP-L01 — Esquema de la tabla en DuckDB

| Campo | Detalle |
|---|---|
| **ID** | CP-L01 |
| **Descripción** | Después de `init_db()`, la tabla debe tener exactamente las columnas declaradas |
| **Columnas requeridas** | `sector_code`, `entity_type`, `ruc`, `company_name`, `date`, `period_type`, `account_code`, `account_name`, `value`, `loaded_at` |
| **Resultado esperado** | Todas las columnas presentes en `information_schema.columns` |

#### CP-L02 — Índice único `uix_stmt` existe

| Campo | Detalle |
|---|---|
| **ID** | CP-L02 |
| **Clave del índice** | `(ruc, account_code, date, period_type)` |
| **Resultado esperado** | `"uix_stmt"` aparece en `duckdb_indexes()` |

#### CP-L03 — `INSERT OR IGNORE` previene duplicados entre chunks

| Campo | Detalle |
|---|---|
| **ID** | CP-L03 |
| **Pasos** | 1. Cargar chunk con 1 fila. 2. Cargar el mismo chunk nuevamente. |
| **Resultado esperado** | `SELECT COUNT(*) == 1` — el segundo insert fue ignorado |

#### CP-L04 — `init_db` es idempotente

| Campo | Detalle |
|---|---|
| **ID** | CP-L04 |
| **Pasos** | Llamar `init_db(mismo_path)` dos veces seguidas |
| **Resultado esperado** | Sin excepciones, tabla existente no es alterada |

---

### Módulo: Calidad de Datos (reglas de negocio)

#### CP-D01 — RUC tiene exactamente 13 dígitos numéricos

| Campo | Detalle |
|---|---|
| **ID** | CP-D01 |
| **RUC inválidos de prueba** | `"123"` (muy corto), `"12345678901234"` (muy largo), `"ABC4567890123"` (no numérico) |
| **Resultado esperado** | Ninguno de esos RUC aparece en la tabla cargada |

#### CP-D02 — Código de cuenta comienza con `1`–`5`

| Campo | Detalle |
|---|---|
| **ID** | CP-D02 |
| **Justificación** | Plan de cuentas SIB: 1=Activo, 2=Pasivo, 3=Patrimonio, 4=Ingresos, 5=Gastos |
| **Consulta de validación** | `SELECT COUNT(*) FROM financial_statements WHERE LEFT(account_code,1) NOT IN ('1','2','3','4','5')` |
| **Resultado esperado** | `0` |

#### CP-D03 — Fecha almacenada en formato `YYYY-MM-DD`

| Campo | Detalle |
|---|---|
| **ID** | CP-D03 |
| **Consulta** | `SELECT date FROM financial_statements LIMIT 1` |
| **Resultado esperado** | Cadena de longitud 10 con guiones en posición 4 y 7 |

#### CP-D04 — Cuenta hijo no supera a su cuenta padre

| Campo | Detalle |
|---|---|
| **ID** | CP-D04 |
| **Ejemplo** | `account_code = "101"` (ACTIVO CORRIENTE) no puede tener un valor mayor que `account_code = "1"` (ACTIVO) para el mismo RUC y fecha |
| **Resultado esperado** | La consulta de jerarquía retorna `0` violaciones |

---

### Tests de Integración (E2E)

#### CP-I01 — Pipeline completo carga el conteo correcto de filas

| Campo | Detalle |
|---|---|
| **ID** | CP-I01 |
| **Archivo de entrada** | TSV de 3 filas de muestra (fixture `sample_tsv`) |
| **Resultado esperado** | `SELECT COUNT(*) FROM financial_statements == 3` |

#### CP-I02 — Pipeline es idempotente

| Campo | Detalle |
|---|---|
| **ID** | CP-I02 |
| **Pasos** | 1. Ejecutar pipeline. 2. Ejecutar pipeline nuevamente con el mismo archivo y DB. |
| **Resultado esperado** | El conteo de filas no cambia en la segunda ejecución |

#### CP-I03 — Valores numéricos correctamente almacenados end-to-end

| Campo | Detalle |
|---|---|
| **ID** | CP-I03 |
| **Entrada en TSV** | `"1.188.854,66"` |
| **Consulta** | `SELECT value FROM financial_statements WHERE account_code = '1'` |
| **Resultado esperado** | `1188854.66` (tolerancia `±0.01`) |

---

## 7. Consultas de Validación en DuckDB

Ejecutar estas consultas manualmente después del pipeline sobre datos reales.

### 7.1 Conteo y completitud

```sql
-- Total de filas cargadas
SELECT COUNT(*) AS total_filas FROM financial_statements;

-- Distribución por tipo de período
SELECT period_type, COUNT(*) AS filas
FROM financial_statements
GROUP BY period_type
ORDER BY filas DESC;

-- Distribución por año fiscal
SELECT YEAR(CAST(date AS DATE)) AS anio, COUNT(*) AS filas
FROM financial_statements
WHERE date IS NOT NULL
GROUP BY anio ORDER BY anio;

-- Empresas únicas por sector
SELECT entity_type, COUNT(DISTINCT ruc) AS empresas
FROM financial_statements
GROUP BY entity_type
ORDER BY empresas DESC;
```

### 7.2 Integridad de columnas críticas

```sql
-- Ningún RUC debe ser nulo o vacío
SELECT COUNT(*) AS ruc_nulos
FROM financial_statements
WHERE ruc IS NULL OR ruc = '';

-- Ningún valor debe ser nulo
SELECT COUNT(*) AS values_nulos
FROM financial_statements
WHERE value IS NULL;

-- Ningún account_code debe ser nulo
SELECT COUNT(*) AS codes_nulos
FROM financial_statements
WHERE account_code IS NULL OR account_code = '';

-- RUC con longitud distinta a 13
SELECT ruc, LENGTH(ruc) AS longitud, COUNT(*) AS ocurrencias
FROM financial_statements
WHERE LENGTH(ruc) != 13
GROUP BY ruc, LENGTH(ruc);
```

### 7.3 Formato de fechas

```sql
-- Todas las fechas deben tener formato YYYY-MM-DD (longitud 10)
SELECT COUNT(*) AS fechas_mal_formateadas
FROM financial_statements
WHERE date IS NOT NULL
  AND (LENGTH(date) != 10 OR SUBSTR(date, 5, 1) != '-' OR SUBSTR(date, 8, 1) != '-');

-- Fechas fuera del rango válido (2000–2030)
SELECT date, COUNT(*) AS filas
FROM financial_statements
WHERE date IS NOT NULL
  AND (YEAR(CAST(date AS DATE)) < 2000 OR YEAR(CAST(date AS DATE)) > 2030)
GROUP BY date;
```

### 7.4 Integridad del plan de cuentas

```sql
-- Códigos de cuenta con primer dígito fuera de 1-5
SELECT account_code, account_name, COUNT(*) AS filas
FROM financial_statements
WHERE LEFT(account_code, 1) NOT IN ('1','2','3','4','5')
GROUP BY account_code, account_name;

-- Verificar los 5 niveles de clase presentes
SELECT LEFT(account_code, 1) AS clase, COUNT(DISTINCT account_code) AS cuentas_distintas
FROM financial_statements
GROUP BY clase ORDER BY clase;
```

### 7.5 Violaciones de jerarquía

```sql
-- Cuenta de grupo (3 dígitos) mayor que su cuenta padre (1 dígito)
SELECT
    hijo.ruc,
    hijo.company_name,
    hijo.date,
    padre.account_code AS cod_padre,
    ROUND(padre.value, 2) AS valor_padre,
    hijo.account_code  AS cod_hijo,
    ROUND(hijo.value, 2)  AS valor_hijo,
    ROUND(hijo.value - padre.value, 2) AS exceso
FROM financial_statements hijo
JOIN financial_statements padre
  ON  padre.ruc         = hijo.ruc
  AND padre.date        = hijo.date
  AND padre.period_type = hijo.period_type
  AND padre.account_code = LEFT(hijo.account_code, 1)
WHERE LENGTH(hijo.account_code)  = 3
  AND LENGTH(padre.account_code) = 1
  AND hijo.value > padre.value
  AND hijo.value > 0 AND padre.value > 0
ORDER BY exceso DESC
LIMIT 20;
```

### 7.6 Detección de duplicados residuales

```sql
-- No debe haber duplicados en la clave natural
SELECT ruc, account_code, date, period_type, COUNT(*) AS ocurrencias
FROM financial_statements
GROUP BY ruc, account_code, date, period_type
HAVING COUNT(*) > 1
LIMIT 20;
```

### 7.7 Validación de vistas analíticas (marts)

```sql
-- mart_yearly_summary debe tener datos
SELECT COUNT(*) FROM mart_yearly_summary;

-- Verificar que total_assets siempre es positivo en el mart
SELECT COUNT(*) AS activos_negativos
FROM mart_assets_vs_liabilities
WHERE total_assets < 0;

-- Ranking: verificar que rank_global inicia en 1 por año
SELECT fiscal_year, MIN(rank_global) AS min_rank, MAX(rank_global) AS max_rank
FROM mart_company_ranking
WHERE period_type = 'ANUAL'
GROUP BY fiscal_year
ORDER BY fiscal_year DESC;
```

### 7.8 Detección de anomalías — resumen ejecutivo

```sql
-- Puntaje compuesto de anomalías: ver entidades críticas
-- (Ejecutar la sección 8 de sql/07_anomaly_detection.sql)
-- Filtrar solo críticos:
SELECT ruc, company_name, entity_type, fiscal_year, anomaly_score, anomaly_level
FROM (
    -- pegar aquí el CTE de la sección 8
)
WHERE anomaly_level IN ('Critical', 'Suspicious')
ORDER BY anomaly_score DESC;
```

---

## 8. Resultados Esperados

### 8.1 Suite de tests automatizados

| Archivo | Tests | Resultado esperado | Tiempo estimado |
|---|---|---|---|
| `test_formatters.py` | 15 | 15 PASSED | < 1 s |
| `test_extract.py` | 9 | 9 PASSED | < 1 s |
| `test_transform.py` | 18 | 18 PASSED | < 2 s |
| `test_load.py` | 9 | 9 PASSED | < 2 s |
| `test_data_quality.py` | 16 | 16 PASSED | < 5 s |
| `test_integration.py` | 12 | 12 PASSED | < 30 s |
| **TOTAL** | **79** | **79 PASSED** | **< 45 s** |

### 8.2 Resultados de consultas de validación sobre datos reales

| Consulta | Resultado esperado | Resultado crítico |
|---|---|---|
| RUC nulos | `0` | > 0 → fallo crítico |
| Values nulos | `0` | > 0 → fallo crítico |
| Duplicados residuales | `0` | > 0 → revisar índice único |
| Fechas mal formateadas | `0` | > 0 → revisar `normalize_date()` |
| RUC con longitud ≠ 13 | `0` | > 0 → revisar datos fuente |
| Violaciones de jerarquía | `0` | > 0 → anomalía en datos Supercias |
| Códigos fuera de `1–5` | `0` | > 0 → revisar plan de cuentas |

### 8.3 Resultados de anomalías financieras

| Nivel | Porcentaje aceptable | Acción si supera |
|---|---|---|
| Normal | > 90 % de entidades | — |
| Watch | < 8 % | Monitorear |
| Suspicious | < 2 % | Revisar manualmente |
| Critical | < 0.5 % | Investigar antes de publicar |

---

## 9. Criterios de Aceptación y Rechazo

### ✅ ACEPTADO — El pipeline puede pasar a producción si:

- [ ] Los 79 tests automatizados pasan sin ningún `FAILED`
- [ ] Cobertura de código ≥ 80 % en módulos `etl/` y `utils/`
- [ ] Todas las consultas de validación de la sección 7 retornan `0` en errores críticos
- [ ] Entidades con `anomaly_level = 'Critical'` son < 0.5 % del total
- [ ] El pipeline es idempotente (segunda ejecución no cambia el conteo)
- [ ] El tiempo de procesamiento es < 30 minutos para 15M de filas

### ❌ RECHAZADO — Detener y corregir si:

- [ ] Algún test de `test_data_quality.py` falla (indica violación de regla de negocio)
- [ ] `SELECT COUNT(*) WHERE ruc IS NULL` retorna > 0
- [ ] Se detectan duplicados residuales (`HAVING COUNT(*) > 1`)
- [ ] Hay fechas fuera del rango 2000–2030
- [ ] El índice `uix_stmt` no existe en DuckDB

---

## 10. Registro de Resultados

Completar esta tabla después de cada ejecución del plan de pruebas.

| Fecha | Ejecutor | Versión pipeline | Tests pasados | Tests fallidos | Anomalías críticas | Decisión |
|---|---|---|---|---|---|---|
| `YYYY-MM-DD` | Nombre | `git rev` | `/79` | `` | `%` | ✅ / ❌ |

### Comandos rápidos de referencia

```bash
# Ejecutar todo y guardar resultado
pytest --tb=short -q 2>&1 | tee resultados_$(date +%Y%m%d).txt

# Solo tests unitarios (durante desarrollo)
pytest -m "not integration" -q

# Ver cobertura por módulo
pytest --cov=etl --cov=utils --cov-report=term-missing -q

# Test específico con salida detallada
pytest tests/test_data_quality.py::TestRucFormat -v

# Ejecutar anomalías sobre DB real
duckdb output/sib.duckdb < sql/07_anomaly_detection.sql
```

---

*Guía elaborada para el proyecto ETL Supercias — Estados Financieros*
*Stack: Python 3.11 · Polars ≥ 0.20 · DuckDB ≥ 0.10 · pytest*

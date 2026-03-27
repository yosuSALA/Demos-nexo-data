# Indicadores Financieros para Dashboards BI
## Perspectiva: Gerente Financiero — Sistema de Estados Financieros Supercias

---

## Las 7 preguntas clave que hace un gerente financiero

```
1. ¿Las entidades son solventes?      → Apalancamiento, Deuda/Patrimonio
2. ¿Tienen liquidez?                  → Razón Corriente, Razón de Efectivo
3. ¿Son rentables?                    → ROA, ROE, Margen Neto, Ratio de Gastos
4. ¿Son eficientes?                   → Rotación de Activos, Eficiencia de Costos
5. ¿Están creciendo?                  → CAGR de Activos, Crecimiento de Ingresos
6. ¿El mercado es saludable?          → HHI, CR5 — concentración de mercado
7. ¿Quién está en riesgo?             → Semáforo de alertas tempranas
```

---

## 1. Solvencia y Apalancamiento

**Pregunta:** ¿Puede la entidad cumplir sus obligaciones a largo plazo?

| Indicador | Fórmula | Rango Saludable |
|---|---|---|
| Razón de Apalancamiento | Pasivo Total / Activo Total | < 0.75 |
| Deuda sobre Patrimonio | Pasivo Total / Patrimonio | < 2.0 |
| Multiplicador de Patrimonio | Activo Total / Patrimonio | < 3.0 |

**Semáforo de solvencia:**

| Nivel | Rango de Apalancamiento | Acción |
|---|---|---|
| Saludable | < 50% | Monitoreo rutinario |
| Moderado | 50% – 75% | Revisión trimestral |
| Alto | 75% – 90% | Revisión mensual |
| Crítico | > 90% | Intervención inmediata |

**Visualización recomendada:** Gráfico de barras agrupadas (Activo / Pasivo / Patrimonio por año),
histograma de distribución de entidades por banda de solvencia.

---

## 2. Liquidez

**Pregunta:** ¿Puede la entidad cubrir sus obligaciones de corto plazo?

| Indicador | Fórmula | Rango Saludable |
|---|---|---|
| Razón Corriente | Activo Corriente / Pasivo Corriente | > 1.0 |
| Razón de Efectivo | Efectivo y Equivalentes / Pasivo Corriente | > 0.20 |

**Nota:** La Razón Corriente menor a 1.0 indica que la entidad no puede
cubrir sus deudas de corto plazo con sus activos disponibles.

**Visualización recomendada:** Mapa de calor de liquidez por entidad y año,
gráfico de dispersión Razón Corriente vs Apalancamiento.

---

## 3. Rentabilidad

**Pregunta:** ¿Genera la entidad retornos adecuados en relación a su tamaño?

| Indicador | Fórmula | Interpretación |
|---|---|---|
| ROA (Retorno sobre Activos) | Resultado Neto / Activo Total × 100 | Mayor = más eficiente |
| ROE (Retorno sobre Patrimonio) | Resultado Neto / Patrimonio × 100 | Mayor = mejor retorno al accionista |
| Margen Neto | Resultado Neto / Ingresos Totales × 100 | Debe ser positivo |
| Ratio de Gastos | Gastos Totales / Ingresos Totales × 100 | < 85% |

**Resultado Neto** = Ingresos Totales − Gastos Totales

**Visualización recomendada:** Diagrama de caja (box-plot) de ROA por sector,
tabla de ranking con semáforo de Rentable / Punto de Equilibrio / Pérdida.

---

## 4. Eficiencia Operativa

**Pregunta:** ¿Qué tan bien utiliza la entidad sus activos para generar ingresos?

| Indicador | Fórmula | Interpretación |
|---|---|---|
| Rotación de Activos | Ingresos Totales / Activo Total | Mayor = más productivo |
| Eficiencia de Costos | Gastos / Ingresos × 100 | Menor = más eficiente |
| Ingresos sobre Patrimonio | Ingresos Totales / Patrimonio | Capacidad generadora |

**Visualización recomendada:** Gráfico de dispersión Rotación de Activos vs ROA
(cuadrante de eficiencia), serie de tiempo de Eficiencia de Costos por sector.

---

## 5. Crecimiento y Tendencias

**Pregunta:** ¿Las entidades y sectores están expandiéndose o contrayéndose?

| Indicador | Fórmula | Interpretación |
|---|---|---|
| Crecimiento de Activos YoY | (Activos_t − Activos_{t-1}) / |Activos_{t-1}| × 100 | Positivo = expansión |
| Crecimiento de Ingresos YoY | (Ingresos_t − Ingresos_{t-1}) / |Ingresos_{t-1}| × 100 | Positivo = expansión |
| CAGR 3 años (Activos) | (Activos_t / Activos_{t-3})^(1/3) − 1 | Tasa compuesta de crecimiento |
| Promedio Móvil 3 años | Promedio de Activos de los últimos 3 años | Suaviza la volatilidad |

**Visualización recomendada:** Gráfico de líneas múltiples por entidad,
gráfico de barras de CAGR por sector (top 10 de mayor crecimiento).

---

## 6. Concentración de Mercado

**Pregunta:** ¿Está el mercado dominado por pocas entidades? ¿Hay riesgo sistémico?

### Índice Herfindahl-Hirschman (HHI)

```
HHI = Σ (participación_de_mercado_i²)
```

Donde `participación_de_mercado_i = Activos_entidad_i / Activos_totales_sector × 100`

| Valor HHI | Nivel de Concentración | Señal |
|---|---|---|
| < 1.500 | Competitivo | Normal |
| 1.500 – 2.500 | Moderadamente concentrado | Vigilancia |
| > 2.500 | Altamente concentrado | Riesgo regulatorio |

### Ratio de Concentración CR5

Porcentaje de activos del sector en manos de las 5 entidades más grandes.

| CR5 | Interpretación |
|---|---|
| < 40% | Mercado distribuido |
| 40% – 60% | Concentración moderada |
| > 60% | Estructura oligopólica |

**Visualización recomendada:** Serie de tiempo del HHI por sector,
gráfico de torta de participación de mercado (top 5 + resto).

---

## 7. Semáforo de Alertas Tempranas (Risk Scorecard)

**Pregunta:** ¿Qué entidades muestran deterioro financiero y requieren atención?

Cada entidad recibe una puntuación de 0 a 5 según señales de alerta activas:

| Señal | Condición | Descripción |
|---|---|---|
| Apalancamiento alto | Pasivo / Activo > 90% | Riesgo de insolvencia |
| Pérdida operativa | Resultado Neto < 0 | Opera en rojo |
| Patrimonio negativo | Patrimonio < 0 | Técnicamente en quiebra |
| Desbordamiento de costos | Ingresos < Gastos × 80% | Gastos fuera de control |
| Contracción de activos | Activos menores al año anterior | Balance encogiendo |

| Puntuación | Nivel de Riesgo | Acción Recomendada |
|---|---|---|
| 0 | Bajo | Monitoreo rutinario |
| 1 | Vigilancia | Revisión trimestral |
| 2 | Elevado | Revisión mensual con alertas |
| 3 – 5 | Crítico | Intervención regulatoria inmediata |

---

## Diseño del Dashboard Recomendado

```
┌──────────────────────────────────────────────────────────────────┐
│  FILA 1 — TARJETAS KPI (año actual vs año anterior)              │
│  [Activos Totales]  [Apalancamiento]  [ROA Promedio]  [En Riesgo]│
├──────────────────────────────────────────────────────────────────┤
│  FILA 2 — SERIES DE TIEMPO                                       │
│  [Activos por sector — área apilada]  [Tendencia Apalancamiento] │
├──────────────────────────────────────────────────────────────────┤
│  FILA 3 — DISTRIBUCIÓN Y RANKING                                 │
│  [Histograma de solvencia]  [Top empresas + curva de Pareto]     │
├──────────────────────────────────────────────────────────────────┤
│  FILA 4 — RENTABILIDAD                                           │
│  [Box-plot ROA por sector]  [Dispersión ROA vs Apalancamiento]   │
├──────────────────────────────────────────────────────────────────┤
│  FILA 5 — PANEL DE RIESGO                                        │
│  [Tabla semáforo de riesgo]  [HHI por sector]  [CR5 tendencia]  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Glosario de Cuentas (Plan de Cuentas Supercias Ecuador)

| Código | Nombre | Clase |
|---|---|---|
| 1 | ACTIVO | Activos |
| 101 | ACTIVO CORRIENTE | Activos |
| 10101 | EFECTIVO Y EQUIVALENTES DE EFECTIVO | Activos |
| 102 | ACTIVO NO CORRIENTE | Activos |
| 2 | PASIVO | Pasivos |
| 201 | PASIVO CORRIENTE | Pasivos |
| 202 | PASIVO NO CORRIENTE | Pasivos |
| 3 | PATRIMONIO | Patrimonio |
| 4 | INGRESOS | Ingresos |
| 5 | GASTOS | Gastos |

---

## Archivos SQL Relacionados

| Archivo | Contenido |
|---|---|
| `sql/05_bi_dashboard_queries.sql` | Consultas base: activos, pasivos, ranking, tendencias |
| `sql/06_kpi_financial_indicators.sql` | KPIs: ROA, ROE, HHI, CR5, semáforo de riesgo |
| `sql/01_mart_yearly_summary.sql` | Vista resumen anual por empresa |
| `sql/02_mart_assets_vs_liabilities.sql` | Activos vs pasivos por empresa y año |
| `sql/03_mart_account_categories.sql` | Resumen por categoría de cuenta |
| `sql/04_mart_company_ranking.sql` | Ranking y crecimiento YoY |
| `schema/04_bi_views.sql` | Vistas BI listas para conectar con Metabase / Superset |

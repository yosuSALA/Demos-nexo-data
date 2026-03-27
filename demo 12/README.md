# Demo 12 — ETL de Cartera Vencida (Aging Report)

Pipeline ETL que genera datos sintéticos de clientes y facturas, los transforma
para calcular la antigüedad de saldos vencidos y presenta los resultados en un
dashboard interactivo construido con Streamlit y Plotly.

## Estructura del proyecto

| Archivo | Descripcion |
|---|---|
| `generate_data.py` | Genera datos sinteticos de clientes y facturas (`clientes.csv`, `facturas.csv`) usando Faker. |
| `etl_transform.py` | Carga los CSV, calcula dias de vencimiento, asigna categorias de aging y produce reportes (`aging_report.csv`, `top_deudores.csv`, `alertas_cobro.csv`). |
| `app.py` | Dashboard interactivo en Streamlit que integra la generacion de datos y el ETL con visualizaciones en Plotly. |
| `requirements.txt` | Dependencias de Python necesarias para ejecutar el proyecto. |

## Requisitos

- Python 3.10 o superior

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Uso

### Opcion 1 — Dashboard interactivo (recomendado)

```bash
streamlit run app.py
```

Desde el panel lateral del dashboard puedes:

1. **Generar datos sinteticos** — crea `clientes.csv` y `facturas.csv` con datos aleatorios realistas.
2. **Ejecutar ETL** — transforma los datos crudos y genera el reporte de aging.
3. **Explorar resultados** — tablas con codigo de color por antiguedad, graficos de barras y dona, metricas resumidas y alertas de cobranza.

### Opcion 2 — Ejecucion por scripts independientes

```bash
# Paso 1: generar datos sinteticos
python generate_data.py

# Paso 2: ejecutar el ETL
python etl_transform.py
```

Los archivos CSV resultantes se pueden abrir en Excel, Power BI o Tableau.

## Categorias de aging

| Categoria | Descripcion |
|---|---|
| Pagada | Factura sin saldo pendiente |
| Vigente | Factura con saldo pendiente pero aun no vencida |
| 1-30 dias | Vencida entre 1 y 30 dias |
| 31-60 dias | Vencida entre 31 y 60 dias |
| 61-90 dias | Vencida entre 61 y 90 dias |
| +90 dias | Vencida con mas de 90 dias |

## Datos generados

- **50 clientes** distribuidos en tres segmentos: Minorista (50%), Mayorista (30%), HORECA (20%).
- **2,000 facturas** con montos, plazos y estados realistas. Aproximadamente el 20% de los clientes se marcan como morosos cronicos, lo que sesga la distribucion de facturas vencidas.

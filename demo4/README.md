# Demo #4: Bot de Conciliación Bancaria Automática

Sistema que cruza automáticamente un extracto bancario contra el libro mayor contable, identifica coincidencias y genera un reporte de diferencias.

## Descripcion

El bot toma dos fuentes de datos (banco y contabilidad), aplica reglas de cruce por monto exacto y ventana de fechas, y clasifica cada transacción en:

- **Conciliadas**: monto idéntico con desfase máximo de 3 días
- **Faltantes en banco** (partidas en tránsito): existen en contabilidad pero no en el extracto
- **No registradas en contabilidad**: aparecen en el banco pero no tienen comprobante

## Arquitectura

```
┌─────────────────┐     ┌─────────────────┐
│  Extracto Banco │     │   Libro Mayor   │
│   (df_banco)    │     │ (df_contabilidad)│
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
          ┌──────────▼──────────┐
          │  Motor Conciliación │
          │  (cruce por monto   │
          │   + ventana ±3 días)│
          └──────────┬──────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
  Conciliados   Faltantes    No Registradas
                en Banco     en Contabilidad
        │            │            │
        └────────────┼────────────┘
                     ▼
          ┌─────────────────────┐
          │  reporte_conciliacion│
          │       .xlsx         │
          └─────────────────────┘
```

## Requisitos

- Python 3.10+
- pip

## Instalacion

```bash
cd demo4
pip install -r requirements.txt
```

## Como ejecutar

### Modo consola (script directo)

```bash
python conciliacion.py
```

Genera datos mock, ejecuta la conciliación e imprime resumen en consola. Exporta `reporte_conciliacion.xlsx`.

### Modo dashboard (Streamlit)

```bash
streamlit run app.py
```

Abre una interfaz web interactiva con:
- Configuración de cantidad de registros
- Métricas de resumen (total, conciliadas, diferencias, tasa)
- Gráfico de dona con distribución de resultados
- Histograma de desfase de días
- Gráfico de montos por categoría
- Tablas de detalle por pestaña (conciliados, faltantes, datos originales)
- Botón de descarga del reporte Excel

## Estructura de archivos

| Archivo | Descripcion |
|---------|-------------|
| `conciliacion.py` | Script principal: generación de datos, motor de cruce y exportación Excel |
| `app.py` | Dashboard Streamlit con visualizaciones interactivas |
| `requirements.txt` | Dependencias del proyecto |
| `reporte_conciliacion.xlsx` | Reporte generado (3 pestañas) |

## Reglas de negocio

| Regla | Detalle |
|-------|---------|
| Cruce por monto | Coincidencia exacta (centavos incluidos) |
| Tolerancia de fecha | ±3 días entre fecha banco y fecha contabilidad |
| Partidas en tránsito | Registros en contabilidad sin match en banco (ej. cheques girados) |
| Partidas no registradas | Registros en banco sin match en contabilidad (ej. comisiones bancarias) |

## Datos de prueba

El generador crea datos realistas:
- ~76% de registros coinciden entre ambas fuentes (con desfase de 1-3 días)
- ~12% solo aparecen en banco (comisiones, cargos automáticos)
- ~12% solo aparecen en contabilidad (cheques en tránsito, ajustes)

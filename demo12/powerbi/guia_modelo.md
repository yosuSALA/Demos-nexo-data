# Guia de Configuracion - Power BI: Aging Report

## 1. Origen de datos

Importar el archivo **aging_report.csv** generado por `etl_transform.py`.

1. En Power BI Desktop: **Inicio > Obtener datos > Texto/CSV**.
2. Seleccionar `aging_report.csv` (codificacion UTF-8 con BOM).
3. Verificar que las columnas se detecten correctamente en la vista previa.

## 2. Tipos de dato en Power Query

Antes de cargar, ajustar los tipos en el Editor de Power Query:

| Columna | Tipo |
|---|---|
| id_factura | Numero entero |
| id_cliente | Numero entero |
| nombre_comercial | Texto |
| segmento | Texto |
| fecha_emision | Fecha |
| fecha_vencimiento | Fecha |
| termino_dias | Numero entero |
| monto_total | Numero decimal |
| saldo_pendiente | Numero decimal |
| estado | Texto |
| dias_vencido | Numero decimal |
| aging_bucket | Texto |
| alerta_por_vencer | Verdadero/Falso |

## 3. Columnas calculadas

Despues de cargar la tabla, crear estas columnas calculadas en la vista de datos (copiar desde `medidas_dax.dax`, seccion 14):

- **Rango Monto**: clasifica el monto total en rangos para segmentacion visual.
- **Mes Emision**: formato YYYY-MM para ejes temporales.
- **Trimestre**: formato "T1 2026" para agrupaciones trimestrales.

## 4. Orden de aging_bucket

Para que los graficos respeten el orden logico de los buckets:

1. Crear una tabla auxiliar (Introducir datos) con dos columnas:

| aging_bucket | Orden |
|---|---|
| Pagada | 1 |
| Vigente | 2 |
| 1-30 dias | 3 |
| 31-60 dias | 4 |
| 61-90 dias | 5 |
| +90 dias | 6 |

2. Crear relacion entre `aging_report[aging_bucket]` y la tabla auxiliar.
3. En el visual, ordenar por la columna `Orden`.

Alternativa rapida: seleccionar la columna `aging_bucket` en la vista de datos, ir a **Herramientas de columna > Ordenar por columna** y asignar una columna numerica de orden.

## 5. Medidas DAX

Todas las medidas estan en el archivo `medidas_dax.dax`. Para cargarlas:

1. En la vista de informe, seleccionar la tabla `aging_report`.
2. Ir a **Modelado > Nueva medida**.
3. Copiar y pegar cada medida del archivo `.dax`.

Se recomienda organizar las medidas en una carpeta de visualizacion:
- Seleccionar la medida en el panel de campos.
- En Propiedades, asignar **Carpeta para mostrar** (ej. "Conteos", "Saldos", "KPIs").

## 6. Formato de medidas

| Medida | Formato sugerido |
|---|---|
| Saldo Total, Saldo Vencido, etc. | $ #,##0.00 |
| % Morosidad, Indice de Recuperacion | 0.0% |
| Dias Promedio de Mora | #,##0.0 |
| Provision Estimada | $ #,##0.00 |
| Total Facturas, Facturas Vencidas, etc. | #,##0 |

## 7. Visuales sugeridos

| Visual | Campos |
|---|---|
| Tarjetas KPI | Saldo Total, Saldo Vencido, % Morosidad, KPI Semaforo |
| Barra apilada horizontal | Eje: aging_bucket / Valor: saldo_pendiente |
| Barra agrupada | Eje: segmento / Valor: Saldo por Segmento |
| Tabla Top Deudores | nombre_comercial, segmento, Saldo Vencido |
| Linea temporal | Eje: Mes Emision / Valor: Emision por Mes - Monto |
| Indicador (gauge) | Valor: % Morosidad / Objetivo: 0.10 |
| Tabla de alertas | Filtrar alerta_por_vencer = TRUE / Mostrar: id_factura, nombre_comercial, fecha_vencimiento, saldo_pendiente |

## 8. Formato condicional para el semaforo

Para el KPI Semaforo Cartera:

1. Usar la medida `KPI Semaforo Cartera Valor` (1=Verde, 2=Amarillo, 3=Rojo).
2. En la tarjeta o tabla, ir a **Formato > Formato condicional > Color de fondo**.
3. Configurar reglas:
   - Si el valor es 1: verde (#2ECC71)
   - Si el valor es 2: amarillo (#F1C40F)
   - Si el valor es 3: rojo (#E74C3C)

## 9. Filtros recomendados

Agregar segmentadores (slicers) para:

- **segmento**: Minorista, Mayorista, HORECA
- **aging_bucket**: para aislar rangos especificos
- **Rango Monto**: para analizar por tamano de factura
- **Trimestre**: para analisis temporal

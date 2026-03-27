# Guia de configuracion del modelo en Power BI

## 1. Importar los datos

1. Abrir Power BI Desktop.
2. **Obtener datos** > **Texto/CSV**.
3. Seleccionar el archivo `datos_dashboard_contratos.csv` ubicado en la carpeta `demo8/`.
4. En la vista previa, verificar que la codificacion sea **UTF-8** y el delimitador sea **coma**.
5. Hacer clic en **Transformar datos** para abrir Power Query.

## 2. Transformaciones en Power Query

En el Editor de Power Query, aplicar los siguientes pasos:

| Columna | Tipo de dato | Accion |
|---|---|---|
| `id_obligacion` | Texto | Sin cambios |
| `tipo` | Texto | Sin cambios |
| `entidad_relacionada` | Texto | Sin cambios |
| `fecha_inicio` | Fecha | Cambiar tipo a **Fecha** |
| `fecha_vencimiento` | Fecha | Cambiar tipo a **Fecha** |
| `valor_usd` | Numero decimal | Cambiar tipo a **Numero decimal** |
| `responsable_interno` | Texto | Sin cambios |
| `dias_para_vencer` | Numero entero | Cambiar tipo a **Numero entero** |
| `estado_semaforo` | Texto | Sin cambios |

Hacer clic en **Cerrar y aplicar**.

## 3. Renombrar la tabla

En la vista de **Modelo**, renombrar la tabla importada a **Contratos**. Esto es necesario porque todas las medidas DAX del archivo `medidas_dax.dax` hacen referencia a la tabla con ese nombre.

## 4. Crear las columnas calculadas

En la vista de **Datos**, seleccionar la tabla **Contratos** y agregar las siguientes columnas calculadas (copiar desde `medidas_dax.dax`):

1. **Estado Semaforo Calc** -- clasifica dinamicamente por dias restantes.
2. **Mes Vencimiento** -- formato YYYY-MM para ejes temporales.
3. **Trimestre** -- formato T1 2026, T2 2026, etc.

## 5. Crear las medidas

Ir a **Inicio** > **Nueva medida** y copiar cada medida del archivo `medidas_dax.dax`. Se recomienda organizarlas en carpetas de visualizacion:

| Carpeta | Medidas |
|---|---|
| **Conteos** | Total Contratos, Contratos Activos, Contratos Vencidos |
| **Semaforo** | Contratos Rojo, Contratos Amarillo, Contratos Verde, Pct Contratos en Riesgo |
| **Montos** | Monto Total Comprometido, Monto en Riesgo, Monto Alerta, Monto Rojo y Amarillo |
| **Temporales** | Contratos que Vencen Esta Semana, Contratos que Vencen Este Mes |
| **KPI** | KPI Semaforo General, KPI Semaforo Color, Dias Promedio para Vencimiento |
| **Por Dimension** | Contratos por Tipo, Contratos por Responsable, Monto por Responsable, Riesgo por Responsable |
| **Tendencia** | Vencimientos por Mes, Vencimientos Futuros por Mes, Monto Vencimientos por Mes |
| **Acumulados** | Acumulado Contratos Vencidos, Acumulado Monto Vencido |

Para crear carpetas de visualizacion: en la vista de **Modelo**, seleccionar las medidas, y en el panel de propiedades asignar el valor de **Carpeta para mostrar**.

## 6. Formato de medidas

Aplicar los siguientes formatos a cada medida:

- **Porcentajes** (Pct Contratos en Riesgo): formato porcentaje, 1 decimal.
- **Montos** (todas las medidas con "Monto"): formato moneda USD, sin decimales.
- **Conteos**: formato numero entero, sin decimales.
- **Dias Promedio**: formato numero decimal, 1 decimal.

## 7. Diseno sugerido del reporte

### Pagina 1: Resumen ejecutivo

- **Fila superior**: 5 tarjetas KPI
  - Total Contratos | Contratos Rojo | Contratos Amarillo | Contratos Verde | Monto Rojo y Amarillo
- **Fila central**:
  - Grafico de dona: estado_semaforo con Contratos por Tipo
  - Grafico de barras horizontales: tipo vs conteo, apilado por semaforo
  - Grafico de barras verticales: Mes Vencimiento vs Vencimientos Futuros por Mes
- **Fila inferior**:
  - Indicador (gauge): Pct Contratos en Riesgo (objetivo: 20%)
  - Tabla: Top 5 contratos criticos ordenados por valor_usd descendente

### Pagina 2: Detalle operativo

- **Segmentadores**: estado_semaforo, tipo, responsable_interno
- **Tabla detallada**: todas las columnas con formato condicional por semaforo
- **Tarjetas**: Contratos que Vencen Esta Semana, Contratos que Vencen Este Mes
- **Grafico de lineas**: Acumulado Contratos Vencidos por Mes Vencimiento

### Pagina 3: Analisis por responsable

- **Matriz**: responsable_interno en filas, estado_semaforo en columnas, Contratos por Responsable como valores
- **Grafico de barras**: Monto por Responsable
- **Tarjeta**: KPI Semaforo General (texto)

## 8. Formato condicional por semaforo

Para aplicar colores de semaforo en tablas y matrices:

1. Seleccionar la columna `estado_semaforo` o la medida correspondiente.
2. Ir a **Formato** > **Formato condicional** > **Color de fondo**.
3. Configurar reglas:
   - Si el valor es "Rojo": fondo `#FDECEA`
   - Si el valor es "Amarillo": fondo `#FEF9E7`
   - Si el valor es "Verde": fondo `#EAFAF1`

## 9. Actualizacion de datos

El CSV se regenera ejecutando el script `etl_contratos.py`. Para mantener el dashboard actualizado:

1. Configurar la ruta del CSV como parametro en Power Query.
2. Usar **Actualizar** en Power BI para recargar los datos.
3. Opcionalmente, programar actualizacion automatica si se publica en Power BI Service.

## 10. Logica del semaforo

La clasificacion sigue esta regla (coherente con `etl_contratos.py`):

| Estado | Condicion | Color |
|---|---|---|
| Rojo | dias_para_vencer < 15 | `#E74C3C` |
| Amarillo | 15 <= dias_para_vencer <= 30 | `#F39C12` |
| Verde | dias_para_vencer > 30 | `#27AE60` |

Nota: los contratos vencidos (dias negativos) tambien se clasifican como **Rojo**.

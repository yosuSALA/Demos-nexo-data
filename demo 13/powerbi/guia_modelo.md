# Guia de Configuracion del Modelo en Power BI

## Demo #13 -- Monitoreo Competitivo de Precios

---

## 1. Importar datos

1. Abrir Power BI Desktop.
2. **Obtener datos** > **Texto/CSV**.
3. Importar los dos archivos generados por el sistema Python:
   - `comparacion_precios.csv` -- tabla principal con todos los productos comparados.
   - `alertas_precios.csv` -- subconjunto filtrado (productos con diferencia > 3%).
4. En el editor de Power Query, verificar que los tipos de columna sean correctos:

| Columna              | Tipo esperado     |
|----------------------|-------------------|
| `nombre`             | Texto             |
| `precio_empresa`     | Numero decimal    |
| `precio_competidor`  | Numero decimal    |
| `disponibilidad`     | Texto             |
| `diff_absoluta`      | Numero decimal    |
| `diff_porcentual`    | Numero decimal    |

5. Hacer clic en **Cerrar y aplicar**.

---

## 2. Crear columnas calculadas

En la tabla `comparacion_precios`, agregar tres columnas calculadas desde la pestaña **Modelado > Nueva columna**. Copiar las formulas del archivo `medidas_dax.dax`:

- **Clasificacion** -- Asigna "Ventaja", "Desventaja" o "Neutral" segun el signo de la diferencia.
- **Rango Diferencia** -- Agrupa la diferencia porcentual en bandas descriptivas.
- **Urgencia** -- Clasifica la prioridad de accion: Alta, Media, Baja o Sin accion.

---

## 3. Crear medidas DAX

Ir a **Modelado > Nueva medida** y pegar cada medida del archivo `medidas_dax.dax`. Las medidas estan organizadas en estos grupos:

### KPIs principales
| Medida                              | Formato sugerido  |
|-------------------------------------|-------------------|
| Total Productos Monitoreados        | Numero entero     |
| Productos Mas Caros que Competencia | Numero entero     |
| Productos Mas Baratos que Competencia | Numero entero   |
| Diferencia Promedio USD             | Moneda ($0.00)    |
| Diferencia Promedio Porcentual      | Porcentaje (0.0%) |
| Impacto Economico Mensual           | Moneda ($0.00)    |
| Productos en Alerta Critica         | Numero entero     |
| Porcentaje Competitividad           | Porcentaje (0.0%) |
| Ahorro Potencial si Iguala Precios  | Moneda ($0.00)    |
| Precio Promedio Propio              | Moneda ($0.00)    |
| Precio Promedio Competidor          | Moneda ($0.00)    |

### Extremos y distribucion
| Medida                         | Formato sugerido  |
|--------------------------------|-------------------|
| Mayor Diferencia Positiva      | Porcentaje (0.0%) |
| Mayor Diferencia Negativa      | Porcentaje (0.0%) |
| Producto Mayor Sobrecoste      | Texto             |
| Producto Mayor Ventaja         | Texto             |
| Productos Rango Critico        | Numero entero     |
| Productos Rango Moderado       | Numero entero     |
| Productos Rango Aceptable      | Numero entero     |
| Productos con Ventaja          | Numero entero     |

### Semaforo y alertas
| Medida                         | Formato sugerido  |
|--------------------------------|-------------------|
| KPI Semaforo Competitividad    | Texto             |
| KPI Semaforo Valor             | Numero entero     |
| Total Alertas Activas          | Numero entero     |
| Perdida Estimada Mensual       | Moneda ($0.00)    |
| Perdida Promedio por Producto  | Moneda ($0.00)    |
| Nivel Alerta General           | Texto             |

---

## 4. Diseno sugerido del dashboard

### Pagina 1 -- Resumen Ejecutivo

- **Tarjetas KPI** (fila superior):
  - Total Productos Monitoreados
  - Porcentaje Competitividad (con formato condicional usando KPI Semaforo Valor)
  - Impacto Economico Mensual
  - Total Alertas Activas

- **Grafico de dona**: Clasificacion (Ventaja / Desventaja / Neutral).
  - Colores: Verde = Ventaja, Rojo = Desventaja, Gris = Neutral.

- **Grafico de barras horizontales**: Diferencia porcentual por producto, ordenado de mayor a menor.
  - Formato condicional: rojo si > 3%, verde si < 0%.

- **Tabla detallada**: nombre, precio_empresa, precio_competidor, diff_absoluta, diff_porcentual, Clasificacion, Urgencia.

### Pagina 2 -- Analisis de Alertas

- **Tarjetas KPI**:
  - Nivel Alerta General
  - Perdida Estimada Mensual
  - Perdida Promedio por Producto

- **Grafico de barras apiladas**: Productos por Rango Diferencia.

- **Tabla de alertas**: Solo productos de `alertas_precios` con columna de perdida estimada.

- **Grafico de dispersion**: precio_empresa (eje X) vs precio_competidor (eje Y) con linea diagonal de referencia (precio igual).

---

## 5. Formato condicional del semaforo

Para la tarjeta de Porcentaje Competitividad:

1. Seleccionar la tarjeta.
2. Ir a **Formato > Color de fondo > Formato condicional > Reglas**.
3. Configurar usando la medida `KPI Semaforo Valor`:
   - Valor = 1 --> Rojo (#FF4444)
   - Valor = 2 --> Amarillo (#FFAA00)
   - Valor = 3 --> Verde (#44BB44)

---

## 6. Actualizacion de datos

Para actualizar los precios del competidor y regenerar los CSV:

```bash
cd "ruta/a/demo 13"
python main.py
```

Luego en Power BI: **Inicio > Actualizar** para recargar los CSV.

---

## 7. Parametros del modelo

Estos valores estan definidos como constantes en las medidas DAX y en el codigo Python (`alertas.py`):

| Parametro          | Valor | Descripcion                                  |
|--------------------|-------|----------------------------------------------|
| UMBRAL_ALERTA_PCT  | 3.0%  | Diferencia minima para generar alerta        |
| VOLUMEN_MENSUAL    | 50    | Unidades vendidas por mes por SKU (estimado) |

Si se requiere cambiar estos valores, modificar tanto en `alertas.py` como en las medidas DAX correspondientes (Impacto Economico Mensual, Ahorro Potencial, Perdida Estimada Mensual).

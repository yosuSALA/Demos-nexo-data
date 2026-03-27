# Guia de Modelo Power BI - Conciliacion Bancaria

## 1. Como importar el Excel en Power BI

1. Abrir Power BI Desktop.
2. Ir a **Inicio > Obtener datos > Excel**.
3. Seleccionar el archivo `reporte_conciliacion.xlsx`.
4. En el navegador, marcar las tres hojas:
   - `Conciliados`
   - `Faltantes_en_Banco`
   - `Faltantes_en_Contabilidad`
5. Hacer clic en **Transformar datos** para revisar los tipos de columna en Power Query:
   - Verificar que las columnas de fecha (`fecha_banco`, `fecha_contabilidad`, `fecha_registro`, `fecha_transaccion`) sean de tipo **Fecha**.
   - Verificar que `monto` sea de tipo **Numero decimal**.
   - Verificar que `desfase_dias` sea de tipo **Numero entero**.
6. Hacer clic en **Cerrar y aplicar**.

## 2. Relaciones entre tablas

Las tres tablas son **independientes** (no comparten claves foraneas directas), por lo que no se crean relaciones entre ellas. Esto es correcto para este modelo.

**Opcional - Tabla Calendario:**
Si se desea analizar las tres tablas en un mismo eje temporal, se recomienda crear una tabla calendario:

1. Ir a **Modelado > Nueva tabla**.
2. Escribir:
   ```
   Calendario = CALENDAR(DATE(2026,2,1), DATE(2026,3,31))
   ```
3. Crear relaciones:
   - `Calendario[Date]` -> `Conciliados[fecha_banco]`
   - `Calendario[Date]` -> `Faltantes_en_Banco[fecha_registro]`
   - `Calendario[Date]` -> `Faltantes_en_Contabilidad[fecha_transaccion]`
4. Marcar las relaciones de Faltantes como **inactivas** si Power BI no permite multiples relaciones activas, y activarlas con `USERELATIONSHIP()` en las medidas que lo requieran.

## 3. Como usar las medidas DAX

1. Ir a **Modelado > Nueva medida** (o hacer clic derecho sobre la tabla Conciliados > Nueva medida).
2. Copiar cada medida del archivo `medidas_dax.dax` y pegarla en la barra de formulas.
3. Para la **columna calculada** "Rango de Monto":
   - Hacer clic derecho sobre la tabla `Conciliados` > **Nueva columna**.
   - Pegar la formula de `Rango de Monto`.
   - Repetir para `Faltantes_en_Banco` y `Faltantes_en_Contabilidad` usando las formulas comentadas en el archivo DAX.
4. Las medidas quedaran disponibles en el panel de campos para arrastrar a los visuales.

## 4. Visuales sugeridos

### Pagina 1: Resumen Ejecutivo

| Visual | Contenido | Notas |
|--------|-----------|-------|
| **Tarjeta (Card)** | `Total Transacciones` | Colocar arriba como KPI principal |
| **Tarjeta (Card)** | `Total Conciliadas` | Color verde |
| **Tarjeta (Card)** | `Total Faltantes Banco` | Color amarillo |
| **Tarjeta (Card)** | `Total Faltantes Contabilidad` | Color rojo |
| **Tarjeta (Card)** | `% Tasa de Conciliacion` | Formato porcentaje |
| **Tarjeta (Card)** | `Semaforo Conciliacion` | Usar formato condicional para color de fondo |
| **Grafico de dona** | Distribucion: Conciliadas vs Faltantes Banco vs Faltantes Contabilidad | Usar las tres medidas de conteo |
| **Grafico de dona** | Distribucion de montos: Monto Conciliado, Monto Faltante Banco, Monto Faltante Contabilidad | Segundo dona para montos |

### Pagina 2: Analisis Detallado

| Visual | Contenido | Notas |
|--------|-----------|-------|
| **Grafico de barras agrupadas** | Eje: `Rango de Monto`, Valor: conteo de filas | Para ver distribucion por rango de monto |
| **Grafico de lineas** | Eje: `fecha_banco`, Valor: `Running Total Conciliaciones` | Muestra el acumulado de conciliaciones |
| **Grafico de barras** | Eje: `desfase_dias`, Valor: conteo | Histograma de desfases |
| **Tarjeta** | `Promedio Desfase Dias` | KPI de eficiencia |
| **Tarjeta** | `Partidas con Desfase Mayor a 2 Dias` | Alerta de partidas lentas |
| **Tarjeta** | `Monto en Riesgo` | Formato moneda, color rojo |

### Pagina 3: Detalle de Partidas

| Visual | Contenido | Notas |
|--------|-----------|-------|
| **Tabla** | Todas las columnas de `Conciliados` | Con formato condicional en `desfase_dias` |
| **Tabla** | Todas las columnas de `Faltantes_en_Banco` | Resaltar montos altos |
| **Tabla** | Todas las columnas de `Faltantes_en_Contabilidad` | Resaltar montos altos |

### Formato condicional recomendado

- **Semaforo Conciliacion**: Usar reglas en la tarjeta para cambiar el color de fondo:
  - "Optimo" -> verde (#27AE60)
  - "Aceptable" -> amarillo (#F39C12)
  - "Critico" -> rojo (#E74C3C)
- **desfase_dias**: Escala de color de verde (0 dias) a rojo (3 dias).
- **monto**: Barras de datos en las tablas de detalle para facilitar la comparacion visual.

### Segmentadores (Slicers) recomendados

- Segmentador por **fecha** (rango de fechas).
- Segmentador por **Rango de Monto**.
- Segmentador por **tipo** (en las tablas de faltantes).
- Segmentador por **estado**.

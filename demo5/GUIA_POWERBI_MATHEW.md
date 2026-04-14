# 📊 Guía Técnica Power BI — Dashboard de Ventas en Tiempo Real
## Para: Mathew (Modelado Visual + DAX)
## Proyecto: Demo #5 — Nexo Data Consulting

---

## 1. Fuente de Datos

El script de Python (`generador_ventas.py`) genera una base de datos **SQLite** (`ventas_gye.db`) con dos tablas:

| Tabla | Descripción |
|-------|-------------|
| `ventas` | Cada fila = 1 línea de factura con timestamp, vendedor, zona, producto, totales |
| `metas` | Metas diarias/mensuales por empresa y por vendedor |

### Conexión desde Power BI Desktop

1. **Obtener datos** → **Base de datos ODBC** o instalar el conector SQLite:
   - Descargar el driver ODBC de SQLite: https://www.ch-werner.de/sqliteodbc/
   - O alternativamente: usar el **CSV exportado** (`ventas_gye.csv` + `metas.csv`)
2. **Para CSV**: Obtener datos → Texto/CSV → seleccionar `ventas_gye.csv`

> ⚠️ Para la demo en vivo usaremos **Actualización Automática de Página** (ver sección 5).

---

## 2. Modelo de Datos — Star Schema

Construir un esquema de estrella con la tabla de hechos `Ventas` y tres dimensiones:

```
                    ┌───────────────┐
                    │  DIM_Fecha    │
                    │───────────────│
                    │ Fecha         │
                    │ Año           │
                    │ Mes           │
                    │ MesNombre     │
                    │ Semana        │
                    │ DiaSemana     │
                    │ EsHoy         │
                    │ EsEstaSemana  │
                    └───────┬───────┘
                            │ 1:N
    ┌───────────────┐       │       ┌───────────────┐
    │ DIM_Vendedor  │       │       │ DIM_Producto  │
    │───────────────│       │       │───────────────│
    │ VendedorID    │       │       │ Producto      │
    │ Nombre        │       │       │ Categoria     │
    │ ZonaBase      │  ┌────┴────┐  │ PrecioPromedio│
    │ MetaDiaria    │──│  FACT   │──│               │
    └───────────────┘  │ Ventas  │  └───────────────┘
                       │─────────│
                       │ ID      │
                       │ FacturaID│
                       │ Fecha    │──→ DIM_Fecha
                       │ Hora     │
                       │ Vendedor │──→ DIM_Vendedor
                       │ Zona     │
                       │ ZonaLat  │
                       │ ZonaLon  │
                       │ Producto │──→ DIM_Producto
                       │ Cantidad │
                       │ PrecioU  │
                       │ Subtotal │
                       │ IVA      │
                       │ Total    │
                       │ MetodoPago│
                       │ Cliente  │
                       └──────────┘
```

### Crear las Dimensiones en Power Query (Editor)

#### DIM_Fecha (Tabla Calculada DAX)

```dax
DIM_Fecha = 
ADDCOLUMNS(
    CALENDARAUTO(),
    "Año",           YEAR([Date]),
    "Mes",           MONTH([Date]),
    "MesNombre",     FORMAT([Date], "MMMM"),
    "Semana",        WEEKNUM([Date]),
    "DiaSemana",     FORMAT([Date], "dddd"),
    "DiaSemanaNum",  WEEKDAY([Date], 2),
    "EsHoy",         IF([Date] = TODAY(), TRUE(), FALSE()),
    "EsEstaSemana",  IF(
                        WEEKNUM([Date]) = WEEKNUM(TODAY()) && YEAR([Date]) = YEAR(TODAY()),
                        TRUE(), FALSE()
                     )
)
```

#### DIM_Vendedor (Referencia desde ventas)

En Power Query: **Referencia** desde la tabla ventas → Eliminar duplicados por `vendedor_id`:

| Columna | Fuente |
|---------|--------|
| VendedorID | `vendedor_id` |
| Nombre | `vendedor_nombre` |
| ZonaBase | (asignar manualmente o con lógica) |

#### DIM_Producto (Referencia desde ventas)

Referencia → Eliminar duplicados por `producto`:

| Columna | Fuente |
|---------|--------|
| Producto | `producto` |
| Categoria | `categoria` |

### Relaciones

| Desde (Hecho) | Hacia (Dimensión) | Tipo | Columna |
|---|---|---|---|
| `Ventas[fecha]` | `DIM_Fecha[Date]` | Muchos a Uno | fecha |
| `Ventas[vendedor_id]` | `DIM_Vendedor[VendedorID]` | Muchos a Uno | vendedor_id |
| `Ventas[producto]` | `DIM_Producto[Producto]` | Muchos a Uno | producto |

---

## 3. Medidas DAX Críticas

Crear estas medidas en una **tabla de medidas** (Nueva tabla → `Medidas = ROW("x", BLANK())`).

### 3.1. Ventas Totales

```dax
Venta Total = SUM(ventas[total])
```

### 3.2. Ventas de Hoy

```dax
Ventas Hoy = 
CALCULATE(
    SUM(ventas[total]),
    ventas[fecha] = FORMAT(TODAY(), "yyyy-MM-dd")
)
```

### 3.3. Ventas de Esta Semana

```dax
Ventas Semana = 
CALCULATE(
    SUM(ventas[total]),
    FILTER(
        ventas,
        WEEKNUM(DATEVALUE(ventas[fecha])) = WEEKNUM(TODAY())
        && YEAR(DATEVALUE(ventas[fecha])) = YEAR(TODAY())
    )
)
```

### 3.4. Ventas del Mes Actual

```dax
Ventas Mes = 
CALCULATE(
    SUM(ventas[total]),
    YEAR(DATEVALUE(ventas[fecha])) = YEAR(TODAY()),
    MONTH(DATEVALUE(ventas[fecha])) = MONTH(TODAY())
)
```

### 3.5. Meta Diaria y Porcentaje de Avance

```dax
Meta Diaria = 8500
```

```dax
% Avance Diario = 
DIVIDE(
    [Ventas Hoy],
    [Meta Diaria],
    0
)
```

### 3.6. Meta Mensual y Porcentaje de Avance

```dax
Meta Mensual = 220000
```

```dax
% Avance Mensual = 
DIVIDE(
    [Ventas Mes],
    [Meta Mensual],
    0
)
```

### 3.7. Ranking de Vendedores Hoy

```dax
Ranking Vendedor Hoy = 
RANKX(
    ALL(ventas[vendedor_nombre]),
    [Ventas Hoy],
    ,
    DESC,
    Dense
)
```

### 3.8. Facturas del Día

```dax
Facturas Hoy = 
CALCULATE(
    DISTINCTCOUNT(ventas[factura_id]),
    ventas[fecha] = FORMAT(TODAY(), "yyyy-MM-dd")
)
```

### 3.9. Ticket Promedio

```dax
Ticket Promedio Hoy = 
DIVIDE(
    [Ventas Hoy],
    [Facturas Hoy],
    0
)
```

### 3.10. Variación vs Ayer

```dax
Ventas Ayer = 
CALCULATE(
    SUM(ventas[total]),
    ventas[fecha] = FORMAT(TODAY() - 1, "yyyy-MM-dd")
)
```

```dax
Variación vs Ayer = 
DIVIDE(
    [Ventas Hoy] - [Ventas Ayer],
    [Ventas Ayer],
    0
)
```

---

## 4. Diseño Visual del Dashboard (4 paneles principales)

### Panel 1: KPIs de Cabecera (Tarjetas)

| KPI | Medida DAX | Formato |
|-----|-----------|---------|
| Ventas Hoy | `[Ventas Hoy]` | $ #,##0.00 |
| % Meta Diaria | `[% Avance Diario]` | 0.0% con formato condicional (rojo <70%, amarillo 70-100%, verde >100%) |
| Facturas Hoy | `[Facturas Hoy]` | #,##0 |
| Ticket Promedio | `[Ticket Promedio Hoy]` | $ #,##0.00 |
| Variación vs Ayer | `[Variación vs Ayer]` | +0.0% / -0.0% con icono ▲▼ |

### Panel 2: Ranking de Vendedores en Vivo

- **Visual:** Gráfico de barras horizontales o tabla con formato condicional
- **Eje:** `vendedor_nombre`
- **Valor:** `[Ventas Hoy]`
- **Color:** Barra de datos condicional (verde para líder, rojo para último)
- **Agregar columna:** `[Ranking Vendedor Hoy]` como indicador visual

### Panel 3: Mapa de Calor por Zonas

- **Visual:** `Mapa de Azure Maps` o `Mapa de burbujas` nativo de Power BI
- **Latitud:** `zona_lat`
- **Longitud:** `zona_lon`
- **Tamaño de burbuja:** `SUM(ventas[total])`
- **Color:** Escala de calor (azul frío → rojo caliente basado en ventas)
- **Tooltip:** Zona, Total de ventas, # de facturas

### Panel 4: Top/Bottom Productos

| Sección | Visual | Configuración |
|---------|--------|---------------|
| Top 5 Productos | Gráfico de barras | TopN = 5, ordenado por `SUM(total)` DESC |
| Bottom 5 Productos | Gráfico de barras | TopN = 5, ordenado por `SUM(total)` ASC |
| Categorías | Gráfico de dona | `categoria` como leyenda, `SUM(total)` como valor |

### Panel Extra: Línea de Tiempo (Tendencia)

- **Visual:** Gráfico de líneas
- **Eje X:** `fecha` (o `hora` para vista intradía)
- **Valor:** `SUM(ventas[total])`
- **Línea de referencia:** Meta diaria (`8500 USD`)

---

## 5. Configuración de Actualización en Tiempo Real

### Opción A: Actualización Automática de Página (Recomendada para Demo)

Esta opción funciona con **Import Mode** y refresca los datos cada N segundos.

1. En Power BI Desktop:
   - Ir a **Archivo → Opciones → Vista previa de características**
   - Activar **"Actualización automática de la página"**
   - Reiniciar Power BI Desktop

2. En el lienzo del reporte:
   - Ir a **Formato → Página → Actualización de página**
   - Establecer: **"Detección de cambios"** o **"Intervalo fijo"**
   - Intervalo: **5 segundos** (para la demo en vivo)

3. El script de Python debe estar corriendo en paralelo (`python generador_ventas.py --stream`) para que la BD se llene.

4. Configurar la **fuente de datos para que re-lea** el CSV o la BD cada vez que refresque:
   - En Power Query: Click derecho en la consulta → **Propiedades** → "Incluir en la actualización del informe"

### Opción B: DirectQuery con SQLite (Avanzado)

> ⚠️ Requiere un driver ODBC de SQLite instalado en Windows.

1. Instalar [SQLite ODBC Driver](http://www.ch-werner.de/sqliteodbc/)
2. Crear un DSN en Windows:
   - Panel de Control → Herramientas administrativas → Orígenes de datos ODBC
   - Agregar → SQLite3 ODBC Driver → Apuntar a `ventas_gye.db`
3. En Power BI: Obtener datos → ODBC → Seleccionar el DSN
4. Elegir **DirectQuery** (no Import)
5. Cada visual consultará la BD directamente cada vez que se refresque

### Opción C: CSV + Actualización Manual por Script (Lo más simple)

Si las opciones anteriores dan problemas:

1. El script de Python genera `ventas_gye.csv` automáticamente
2. Power BI lee ese CSV (Import Mode)
3. Agregar un botón **"Actualizar"** en la barra de Power BI
4. O usar un script PowerShell que ejecute la exportación periódicamente

---

## 6. Paleta de Colores Sugerida

| Uso | Color | Hex |
|-----|-------|-----|
| Primario (headers, títulos) | Azul corporativo | `#1A3C6E` |
| Secundario (acentos, botones) | Azul eléctrico | `#2563EB` |
| Positivo (meta cumplida, ▲) | Verde | `#22C55E` |
| Neutro (en progreso) | Amarillo | `#F59E0B` |
| Negativo (debajo de meta, ▼) | Rojo | `#EF4444` |
| Fondo | Gris suave | `#F8FAFC` |

---

## 7. Checklist de Entrega de la Demo

- [ ] Conectar Power BI al CSV o SQLite
- [ ] Crear las 3 dimensiones (Fecha, Vendedor, Producto)
- [ ] Configurar relaciones del Star Schema
- [ ] Crear las 10 medidas DAX
- [ ] Diseñar los 4 paneles principales
- [ ] Configurar actualización automática de página (5s)
- [ ] Probar con el script de streaming corriendo
- [ ] Verificar que el ranking de vendedores cambia en vivo
- [ ] Verificar que el mapa de calor se actualiza
- [ ] Ajustar formato condicional (verde/amarillo/rojo)

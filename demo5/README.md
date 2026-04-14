# Demo 5 — Dashboard de Ventas en Tiempo Real

## Descripción

Sistema de generación de datos transaccionales simulando un punto de venta en vivo para una empresa de retail/tecnología en Guayaquil, Ecuador. Los datos alimentan un dashboard de Power BI que muestra métricas comerciales actualizadas cada pocos segundos.

**Problema que resuelve:** Los gerentes comerciales dependen de Excels consolidados manualmente y no tienen visibilidad hasta el día siguiente. Este sistema les da acceso en tiempo real a ventas del día, ranking de vendedores, mapa de calor por zonas y performance de productos.

## Arquitectura

```
demo5/
├── generador_ventas.py         # Script principal (Python)
├── requirements.txt            # Dependencias
├── GUIA_POWERBI_MATHEW.md      # Guía técnica para Power BI (DAX + modelo)
├── ventas_gye.db               # (generado) Base de datos SQLite
├── ventas_gye.csv              # (generado) Exportación para Power BI
├── metas.csv                   # (generado) Metas diarias/mensuales
└── README.md                   # Este archivo
```

### Flujo de datos

```
generador_ventas.py  →  ventas_gye.db (SQLite)  →  Power BI Desktop
                     →  ventas_gye.csv (export)  →  (refresh automático)
```

## Datos Generados

- **Zonas:** Urdesa, Samborondón, Centro, Vía a la Costa, Vía a Daule, Los Ceibos, Sauces, Alborada
- **Vendedores:** 5 vendedores con zonas base asignadas
- **Productos:** 10 productos de retail/tecnología con precios ecuatorianos
- **IVA:** 15% (Ecuador)
- **Patrón horario:** Distribución realista (pico mañana y tarde, baja al almuerzo)

## Cómo ejecutar

### Requisitos previos

- Python 3.9+
- pip

### Instalación

```bash
pip install -r requirements.txt
```

### Modo 1: Carga histórica + Streaming (recomendado)

```bash
python generador_ventas.py
```

Genera 30 días de historia (1200 facturas) y luego entra en modo streaming continuo.

### Modo 2: Solo carga histórica

```bash
python generador_ventas.py --seed-only
```

### Modo 3: Solo streaming

```bash
python generador_ventas.py --stream
```

### Modo 4: Exportar a CSV

```bash
python generador_ventas.py --export-csv
```

### Opciones avanzadas

```bash
python generador_ventas.py --dias 60 --facturas-dia 80 --intervalo-min 2 --intervalo-max 8
```

## Para Power BI

Ver el archivo `GUIA_POWERBI_MATHEW.md` con instrucciones completas de:
- Modelo de datos (Star Schema)
- 10 fórmulas DAX (ventas hoy, % avance meta, ranking, ticket promedio, etc.)
- Configuración de actualización en tiempo real
- Diseño visual sugerido

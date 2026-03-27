# Demo #13 — Monitor de Precios de Competencia

Sistema automatizado de inteligencia competitiva que extrae precios de un competidor, los compara con los propios y genera alertas cuando se detectan diferencias significativas.

## Arquitectura

```
scraper.py      Extrae precios de books.toscrape.com (Playwright + BeautifulSoup)
comparador.py   Cruza precios propios vs. competidor y calcula diferencias
alertas.py      Detecta productos no competitivos y genera notificaciones
main.py         Orquesta el pipeline completo (CLI)
app.py          Dashboard interactivo (Streamlit + Plotly)
```

## Requisitos

- Python 3.10+
- Dependencias listadas en `requirements.txt`

## Instalacion

```bash
pip install -r requirements.txt
```

Para el scraping real (opcional), instalar tambien el navegador de Playwright:

```bash
playwright install chromium
```

## Uso por linea de comandos

```bash
# Pipeline completo (scraping real + comparacion + alertas)
python main.py

# Sin scraping, usando CSV existente (modo demo)
python main.py --sin-scraping

# Parametros opcionales
python main.py --paginas 5 --umbral 5 --volumen 100
```

### Parametros CLI

| Parametro        | Descripcion                                      | Default |
|------------------|--------------------------------------------------|---------|
| `--sin-scraping` | Omite el scraping y usa `precios_competidor_A.csv` | `False` |
| `--paginas N`    | Numero de paginas a scrapear                     | `3`     |
| `--umbral PCT`   | Umbral de diferencia % para generar alerta       | `3.0`   |
| `--volumen N`    | Unidades mensuales por SKU (estimacion impacto)  | `50`    |

## Dashboard (Streamlit)

```bash
streamlit run app.py
```

El dashboard ofrece:

- **Metricas resumen** en la parte superior (productos analizados, alertas, perdida estimada)
- **Barra lateral** para configurar umbral, volumen y paginas
- **Tabla de comparacion** con resaltado por color segun la diferencia
- **Tabla de alertas** con los productos donde el competidor es mas barato
- **Graficos interactivos**: distribucion de diferencias de precio e impacto economico por producto

El modo recomendado para demostraciones es cargar datos CSV existentes, lo que no requiere tener Playwright instalado.

## Archivos generados

| Archivo                       | Contenido                                    |
|-------------------------------|----------------------------------------------|
| `precios_competidor_A.csv`    | Precios extraidos del competidor             |
| `comparacion_precios.csv`     | Cruce de precios con diferencias calculadas  |
| `alertas_precios.csv`         | Productos en situacion de alerta             |

## Fuente de datos

El scraper utiliza [books.toscrape.com](http://books.toscrape.com), un sitio disenado para practicar web scraping de forma legal y segura.

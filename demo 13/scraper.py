"""
scraper.py — Demo #13: Scraper de Precios de Competencia
Objetivo: Extraer nombre, precio y disponibilidad de books.toscrape.com
          usando Playwright (renderizado) + BeautifulSoup (parsing).
"""
import asyncio
import logging
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

BASE_URL    = "http://books.toscrape.com"
OUTPUT_FILE = "precios_competidor_A.csv"
MAX_PAGES   = 3   # Cambia a 50 para raspar el catálogo completo


# ─── Helpers de limpieza ────────────────────────────────────────────────────

def limpiar_precio(texto: str) -> float:
    """Convierte '£51.77' → 51.77 (float, sin símbolo de moneda)."""
    limpio = texto.replace("£", "").replace("$", "").replace(",", "").strip()
    return float(limpio)


def normalizar_disponibilidad(texto: str) -> str:
    """Mapea variantes de texto a valores canónicos."""
    texto = texto.strip()
    if "In stock" in texto:
        return "In Stock"
    if "Out of stock" in texto:
        return "Out of Stock"
    return texto


# ─── Lógica de scraping ─────────────────────────────────────────────────────

async def extraer_productos_pagina(page, url: str) -> list[dict]:
    """Navega a `url` y extrae todos los productos de esa página."""
    productos = []

    try:
        await page.goto(url, timeout=30_000)
        await page.wait_for_selector("article.product_pod", timeout=15_000)
    except PlaywrightTimeoutError:
        logger.error(f"Timeout cargando: {url}")
        return productos
    except Exception as exc:
        logger.error(f"Error inesperado al navegar a {url}: {exc}")
        return productos

    html  = await page.content()
    soup  = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("article", class_="product_pod")

    for card in cards:
        try:
            nombre       = card.find("h3").find("a")["title"]
            precio       = limpiar_precio(card.find("p", class_="price_color").text)
            disponib     = normalizar_disponibilidad(card.find("p", class_="availability").text)
            productos.append({
                "nombre":             nombre,
                "precio_competidor":  precio,
                "disponibilidad":     disponib,
            })
        except (AttributeError, ValueError, KeyError) as exc:
            logger.warning(f"  Producto omitido por error de parseo: {exc}")
            continue

    return productos


async def scrape_competitor(max_pages: int = MAX_PAGES) -> pd.DataFrame:
    """
    Punto de entrada del scraper.
    Recorre `max_pages` páginas del catálogo y consolida resultados en un DataFrame.
    """
    todos_los_productos = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        for num_pagina in range(1, max_pages + 1):
            url = (
                BASE_URL
                if num_pagina == 1
                else f"{BASE_URL}/catalogue/page-{num_pagina}.html"
            )
            logger.info(f"Scrapeando página {num_pagina}/{max_pages} → {url}")
            productos = await extraer_productos_pagina(page, url)
            todos_los_productos.extend(productos)
            logger.info(f"  ↳ {len(productos)} productos extraídos (total acumulado: {len(todos_los_productos)})")

        await browser.close()

    df = pd.DataFrame(todos_los_productos)

    if df.empty:
        logger.warning("No se extrajeron productos. Verifica la conectividad o la URL.")
        return df

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    logger.info(f"CSV guardado → '{OUTPUT_FILE}'  ({len(df)} filas)")
    return df


# ─── Ejecución directa ──────────────────────────────────────────────────────

if __name__ == "__main__":
    df = asyncio.run(scrape_competitor())
    print(f"\n{'─'*60}")
    print(f"Muestra de los primeros 10 productos extraídos:")
    print(f"{'─'*60}")
    print(df.head(10).to_string(index=False))

# Bot SRI — Descarga + Cruce Facturas/Retenciones

Automatiza descarga comprobantes portal SRI Ecuador + cruce facturas vs retenciones. Output xlsx con discrepancias resaltadas rojo.

## Stack
- Python 3.10+
- Playwright (Chromium)
- pandas / openpyxl
- Fedora / Linux (rutas `pathlib` agnósticas)

## Estructura

```
demo1/
├── main.py              # orquestador
├── config.py            # paths, creds, URLs
├── requirements.txt
├── .env.example
├── src/
│   ├── scraper.py       # SRIScraper: Playwright + login + descargas
│   ├── processor.py     # DataProcessor: pandas load + merge
│   └── exporter.py      # ExcelExporter: openpyxl + celdas rojas
├── downloads/           # TXT/CSV temporales SRI
└── output/              # xlsx final
```

## Instalar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
# Fedora: deps sistema para Chromium
sudo dnf install -y nss atk at-spi2-atk cups-libs libdrm libxkbcommon mesa-libgbm alsa-lib
```

## Config

```bash
cp .env.example .env
# edita .env con RUC + clave
```

## Correr

```bash
# headless (prod)
python main.py --anio 2026 --mes 3

# visible (debug selectores)
python main.py --anio 2026 --mes 3 --debug
```

## Descargas Playwright — cómo funciona

1. `browser.new_context(accept_downloads=True)` → contexto captura descargas.
2. `page.expect_download()` context manager → espera evento `download`.
3. Dentro, click en link/botón que dispara descarga.
4. `download.save_as(path)` → mueve archivo tmp Playwright → `downloads/`.

Playwright guarda primero en tmp OS; `save_as` copia a ruta final. Con `pathlib.Path` funciona igual en Linux/Windows/Mac.

## Ajustar selectores SRI

SRI cambia selectores sin aviso. Editar `src/scraper.py` → dict `SELECTORS`. Correr con `--debug` + DevTools para inspeccionar IDs reales. Pattern frecuente: `frmPrincipal:campo` (escape `\\:` en CSS).

## Notas
- Login SRI puede requerir captcha en algunos casos → revisar, puede necesitar 2captcha o pausa manual.
- Reportes SRI vienen TXT tab-separado generalmente; processor prueba `\t`, `;`, `,`.
- Cruce usa `CLAVE_ACCESO` (factura) vs `DOC_SUSTENTO` (retención). Tolerancia monto 0.01.

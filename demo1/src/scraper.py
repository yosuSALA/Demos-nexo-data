"""SRIScraper — login + navegación + descargas via Playwright.

NOTA: selectores SRI cambian seguido. Ajustar SELECTORS dict tras inspeccionar DOM real.
"""
from __future__ import annotations
import logging
from pathlib import Path
from contextlib import contextmanager
from playwright.sync_api import sync_playwright, Page, Download, TimeoutError as PwTimeout

log = logging.getLogger(__name__)

SELECTORS = {
    # login
    "ruc_input": "input#usuario",
    "clave_input": "input#password",
    "login_btn": "button#kc-login",
    # consulta comprobantes
    "anio_select": "select#frmPrincipal\\:ano",
    "mes_select": "select#frmPrincipal\\:mes",
    "dia_select": "select#frmPrincipal\\:dia",
    "tipo_comp_select": "select#frmPrincipal\\:cmbTipoComprobante",
    "consultar_btn": "button#frmPrincipal\\:btnRecaptcha",
    "descargar_listado_btn": "a#frmPrincipal\\:lnkTxtlistado",
}

# Valores tipo comprobante SRI
TIPO_FACTURA = "1"
TIPO_RETENCION = "7"


class SRIScraper:
    def __init__(self, ruc: str, clave: str, download_dir: Path, headless: bool = True, timeout_ms: int = 60_000):
        self.ruc = ruc
        self.clave = clave
        self.download_dir = download_dir
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._pw = None
        self._browser = None
        self._ctx = None
        self.page: Page | None = None

    def __enter__(self):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        # accept_downloads=True → Playwright intercepta descargas, no escribe disco hasta save_as
        self._ctx = self._browser.new_context(accept_downloads=True)
        self._ctx.set_default_timeout(self.timeout_ms)
        self.page = self._ctx.new_page()
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if self._ctx: self._ctx.close()
            if self._browser: self._browser.close()
            if self._pw: self._pw.stop()
        except Exception as e:
            log.warning(f"cleanup fail: {e}")

    def login(self) -> None:
        """Login portal SRI. Raises on fail."""
        log.info("login SRI...")
        try:
            self.page.goto("https://srienlinea.sri.gob.ec/auth/login", wait_until="domcontentloaded")
            self.page.fill(SELECTORS["ruc_input"], self.ruc)
            self.page.fill(SELECTORS["clave_input"], self.clave)
            self.page.click(SELECTORS["login_btn"])
            self.page.wait_for_load_state("networkidle")
            # TODO: verificar elemento post-login (ej. menú usuario) para confirmar éxito
            log.info("login ok")
        except PwTimeout as e:
            raise RuntimeError(f"login timeout: {e}")

    def _descargar_archivo(self, trigger_selector: str, dest_name: str) -> Path:
        """Click trigger → intercept download → save en download_dir."""
        with self.page.expect_download(timeout=self.timeout_ms) as dl_info:
            self.page.click(trigger_selector)
        download: Download = dl_info.value
        dest = self.download_dir / dest_name
        download.save_as(str(dest))
        log.info(f"archivo guardado: {dest}")
        return dest

    def descargar_comprobantes(self, anio: int, mes: int, tipo: str, nombre_salida: str) -> Path:
        """Navega consulta recibidos + filtra + descarga listado TXT.

        tipo: '1' factura, '7' retención (ver TIPO_* consts).
        """
        from config import SRI_COMPROBANTES_URL
        try:
            self.page.goto(SRI_COMPROBANTES_URL, wait_until="domcontentloaded")
            self.page.select_option(SELECTORS["anio_select"], str(anio))
            self.page.select_option(SELECTORS["mes_select"], str(mes))
            self.page.select_option(SELECTORS["dia_select"], "00")  # todo el mes
            self.page.select_option(SELECTORS["tipo_comp_select"], tipo)
            self.page.click(SELECTORS["consultar_btn"])
            self.page.wait_for_load_state("networkidle")
            return self._descargar_archivo(SELECTORS["descargar_listado_btn"], nombre_salida)
        except PwTimeout as e:
            raise RuntimeError(f"descarga timeout tipo={tipo}: {e}")

    def descargar_facturas(self, anio: int, mes: int) -> Path:
        return self.descargar_comprobantes(anio, mes, TIPO_FACTURA, f"facturas_{anio}_{mes:02d}.txt")

    def descargar_retenciones(self, anio: int, mes: int) -> Path:
        return self.descargar_comprobantes(anio, mes, TIPO_RETENCION, f"retenciones_{anio}_{mes:02d}.txt")

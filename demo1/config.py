"""Config central. Paths + creds + URLs SRI."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
OUTPUT_DIR = BASE_DIR / "output"
DOWNLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

RUC = os.getenv("SRI_RUC", "")
CLAVE = os.getenv("SRI_CLAVE", "")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

# URLs SRI — ajustar si cambian
SRI_LOGIN_URL = "https://srienlinea.sri.gob.ec/sri-en-linea/SriRucWeb/ConsultaRuc/Consultas/consultaRuc"
SRI_COMPROBANTES_URL = "https://srienlinea.sri.gob.ec/comprobantes-electronicos-internet/pages/consultas/recibidos/consultaRecibidos.jsf"
SRI_RETENCIONES_URL = "https://srienlinea.sri.gob.ec/comprobantes-electronicos-internet/pages/consultas/recibidos/consultaRecibidos.jsf"

TIMEOUT_MS = 60_000  # 60s default

from dotenv import load_dotenv
import os

load_dotenv()

HEADLESS = True

TIMEOUT = 30000

BASE_URL = "https://listado.mercadolibre.com.mx"
# Mercado Libre API
ML_API_BASE_URL = "https://api.mercadolibre.com"
ML_SITE_ID = "MLM"
ML_ACCESS_TOKEN = os.getenv("ML_ACCESS_TOKEN")

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/138.0 Safari/537.36"
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
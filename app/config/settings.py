import os

from dotenv import load_dotenv


# Carga las variables del archivo .env
load_dotenv()


# Configuración del navegador
HEADLESS = True
TIMEOUT = 30_000

BASE_URL = "https://listado.mercadolibre.com.mx"

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/138.0 Safari/537.36"
)





# Mercado Libre API
ML_API_BASE_URL = "https://api.mercadolibre.com"
ML_SITE_ID = "MLM"


# Credenciales OAuth de Mercado Libre
ML_CLIENT_ID = os.getenv("ML_CLIENT_ID", "").strip()
ML_CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET", "").strip()
ML_REDIRECT_URI = os.getenv("ML_REDIRECT_URI", "").strip()


# URLs OAuth
ML_AUTH_URL = "https://auth.mercadolibre.com.mx/authorization"
ML_TOKEN_URL = f"{ML_API_BASE_URL}/oauth/token"


# Tokens OAuth
ML_ACCESS_TOKEN = os.getenv("ML_ACCESS_TOKEN", "").strip()
ML_REFRESH_TOKEN = os.getenv("ML_REFRESH_TOKEN", "").strip()


# Base de datos
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./data/perfume_deals.db",
).strip()

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

TELEGRAM_API_BASE_URL = "https://api.telegram.org"

TELEGRAM_DISABLE_NOTIFICATION = (
    os.getenv(
        "TELEGRAM_DISABLE_NOTIFICATION",
        "false",
    )
    .strip()
    .lower()
    in {
        "1",
        "true",
        "yes",
        "on",
    }
)
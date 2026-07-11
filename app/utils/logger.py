from loguru import logger
import sys

# Elimina la configuración por defecto
logger.remove()

# Mostrar logs en la consola
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level}</level> | "
           "{message}"
)

# Guardar logs en archivo
logger.add(
    "logs/perfumebot.log",
    rotation="10 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)
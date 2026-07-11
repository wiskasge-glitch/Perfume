from app.utils.logger import logger
from app.models.perfume import Perfume


def main():
    logger.info("=================================")
    logger.info("Perfume Deals Bot iniciado")
    logger.info("=================================")

    perfume = Perfume(
        ml_id="MLM123456",
        title="Versace Eros EDT 100ml",
        brand="Versace",
        price=1299,
        original_price=1699,
        discount=23.5,
        seller="Amora Beauty Market",
        trusted_seller=True,
        mercado_lider=True,
        full=True,
        url="https://mercadolibre.com.mx",
    )

    logger.info(perfume)


if __name__ == "__main__":
    main()
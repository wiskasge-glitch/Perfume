import asyncio

from app.services.catalog_service import CatalogService
from app.sources.fixture import FixturePerfumeSource
from app.utils.logger import logger


async def main() -> None:
    logger.info("=================================")
    logger.info("Perfume Deals Bot iniciado")
    logger.info("=================================")

    source = FixturePerfumeSource()

    catalog = CatalogService(
        source=source,
    )

    perfumes = await catalog.get_valid_perfumes()

    logger.info(
        f"Perfumes preparados: {len(perfumes)}"
    )

    for perfume in perfumes:
        logger.info(
            f"{perfume.ml_id} | "
            f"{perfume.title} | "
            f"${perfume.price:,.2f} | "
            f"{perfume.seller}"
        )


if __name__ == "__main__":
    asyncio.run(main())
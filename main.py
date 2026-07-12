import asyncio

from app.database.session import DatabaseManager
from app.engine.offer_scorer import OfferScorer
from app.services.catalog_service import CatalogService
from app.services.offer_pipeline_service import (
    OfferPipelineService,
)
from app.sources.fixture import FixturePerfumeSource
from app.utils.logger import logger


async def main() -> None:
    logger.info("=================================")
    logger.info("Perfume Deals Bot iniciado")
    logger.info("=================================")

    database = DatabaseManager()

    try:
        await database.create_tables()

        source = FixturePerfumeSource()

        catalog = CatalogService(
            source=source,
        )

        pipeline = OfferPipelineService(
            catalog=catalog,
            database=database,
            scorer=OfferScorer(),
        )

        result = await pipeline.run()

        logger.info(
            f"Publicaciones procesadas: "
            f"{result.processed_count}"
        )

        logger.info(
            f"Alertas preparadas: "
            f"{result.alert_count}"
        )

        for offer in result.alert_candidates:
            perfume = offer.perfume
            score = offer.score

            logger.info(
                "---------------------------------"
            )
            logger.info(
                f"OFERTA | {perfume.title}"
            )
            logger.info(
                f"Precio: ${perfume.price:,.2f}"
            )
            logger.info(
                f"Vendedor: {perfume.seller}"
            )
            logger.info(
                f"Score: {score.total:.2f}/100"
            )
            logger.info(
                f"Nivel: {score.level}"
            )

            for reason in score.reasons:
                logger.info(
                    f"  - {reason}"
                )

    finally:
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
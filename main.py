import asyncio

from app.engine.offer_scorer import OfferScorer
from app.services.catalog_service import CatalogService
from app.sources.fixture import FixturePerfumeSource
from app.utils.logger import logger


async def main() -> None:
    logger.info("=================================")
    logger.info("Perfume Deals Bot iniciado")
    logger.info("=================================")

    source = FixturePerfumeSource()
    catalog = CatalogService(source=source)
    scorer = OfferScorer()

    perfumes = await catalog.get_valid_perfumes()

    scored_perfumes = scorer.score_many(perfumes)

    scored_perfumes.sort(
        key=lambda item: item[1].total,
        reverse=True,
    )

    logger.info("Ranking de ofertas:")

    for perfume, result in scored_perfumes:
        logger.info(
            f"{result.total:05.2f}/100 | "
            f"{result.level} | "
            f"{perfume.title} | "
            f"${perfume.price:,.2f}"
        )

        for reason in result.reasons:
            logger.info(f"  - {reason}")


if __name__ == "__main__":
    asyncio.run(main())
import asyncio

from app.engine.offer_scorer import OfferScorer
from app.models.price_history import HistoricalPriceStats
from app.services.catalog_service import CatalogService
from app.sources.fixture import FixturePerfumeSource
from app.utils.logger import logger


async def main() -> None:
    source = FixturePerfumeSource()
    catalog = CatalogService(source=source)
    scorer = OfferScorer()

    perfumes = await catalog.get_valid_perfumes()

    results = scorer.score_many(perfumes)

    scores = {
        perfume.ml_id: result.total
        for perfume, result in results
    }

    assert scores["TEST001"] == 62.0, (
        f"TEST001 obtuvo {scores['TEST001']}"
    )

    assert scores["TEST002"] == 58.0, (
        f"TEST002 obtuvo {scores['TEST002']}"
    )

    first_perfume = perfumes[0]

    historical_result = scorer.apply(
        perfume=first_perfume,
        history=HistoricalPriceStats(
            lowest_price=1300.0,
            average_price=1550.0,
            observations=10,
        ),
    )

    assert historical_result.total == 92.0, (
        f"Con historial se esperaban 92 puntos, "
        f"pero se obtuvieron {historical_result.total}"
    )

    assert historical_result.eligible_for_alert

    logger.info(
        "Prueba del motor de puntuación "
        "completada correctamente."
    )


if __name__ == "__main__":
    asyncio.run(main())
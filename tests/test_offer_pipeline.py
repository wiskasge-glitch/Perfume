import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from app.database.repository import PerfumeRepository
from app.database.session import DatabaseManager
from app.engine.offer_scorer import OfferScorer
from app.services.catalog_service import CatalogService
from app.services.offer_pipeline_service import (
    OfferPipelineService,
)
from app.sources.fixture import FixturePerfumeSource
from app.utils.logger import logger


async def run_test(database_url: str) -> None:
    database = DatabaseManager(
        database_url=database_url,
    )

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

        # Primera ejecución.
        first_result = await pipeline.run()

        assert first_result.processed_count == 2

        processed_ids = [
            offer.perfume.ml_id
            for offer in first_result.processed_offers
        ]

        assert processed_ids == [
            "TEST001",
            "TEST002",
        ]

        # TEST001 obtiene 62 puntos.
        # TEST002 obtiene 58 puntos.
        first_alert_ids = [
            offer.perfume.ml_id
            for offer in first_result.alert_candidates
        ]

        assert first_alert_ids == [
            "TEST001",
        ]

        first_scores = {
            offer.perfume.ml_id: offer.score.total
            for offer in first_result.processed_offers
        }

        assert first_scores["TEST001"] == 62.0
        assert first_scores["TEST002"] == 58.0

        assert all(
            offer.new_price_observation
            for offer in first_result.processed_offers
        )

        logger.info(
            f"Primera ejecución: "
            f"{first_result.alert_count} alerta nueva."
        )

        # Segunda ejecución con los mismos precios.
        second_result = await pipeline.run()

        assert second_result.processed_count == 2
        assert second_result.alert_count == 0

        assert all(
            not offer.new_price_observation
            for offer in second_result.processed_offers
        )

        logger.info(
            "Segunda ejecución: no se generaron "
            "alertas duplicadas."
        )

        # El mismo precio no debe duplicarse
        # en el historial.
        async with database.session() as session:
            repository = PerfumeRepository(session)

            test001_stats = (
                await repository.get_history_stats(
                    "TEST001"
                )
            )

            test002_stats = (
                await repository.get_history_stats(
                    "TEST002"
                )
            )

            assert test001_stats.observations == 1
            assert test002_stats.observations == 1

        logger.info(
            "Prueba de OfferPipelineService "
            "completada correctamente."
        )

    finally:
        await database.close()


async def main() -> None:
    with TemporaryDirectory() as temporary_directory:
        database_path = (
            Path(temporary_directory)
            / "test_pipeline.db"
        )

        database_url = (
            "sqlite+aiosqlite:///"
            + database_path.as_posix()
        )

        await run_test(database_url)


if __name__ == "__main__":
    asyncio.run(main())
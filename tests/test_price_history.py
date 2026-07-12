import asyncio
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from app.database.repository import PerfumeRepository
from app.database.session import DatabaseManager
from app.engine.offer_scorer import OfferScorer
from app.services.catalog_service import CatalogService
from app.sources.fixture import FixturePerfumeSource
from app.utils.logger import logger


async def run_test(database_url: str) -> None:
    database = DatabaseManager(
        database_url=database_url,
    )

    try:
        await database.create_tables()

        catalog = CatalogService(
            source=FixturePerfumeSource(),
        )

        perfumes = await catalog.get_valid_perfumes()
        current_perfume = perfumes[0]

        # Precios históricos anteriores al precio actual.
        historical_price_1 = replace(
            current_perfume,
            price=1500.0,
            original_price=None,
            discount=None,
        )

        historical_price_2 = replace(
            current_perfume,
            price=1400.0,
            original_price=None,
            discount=None,
        )

        historical_price_3 = replace(
            current_perfume,
            price=1350.0,
            original_price=None,
            discount=None,
        )

        async with database.session() as session:
            repository = PerfumeRepository(session)

            # Primera observación: $1,500.
            _, first_changed = (
                await repository.save_observation(
                    historical_price_1
                )
            )

            assert first_changed
            await session.commit()

            # Segunda observación: $1,400.
            _, second_changed = (
                await repository.save_observation(
                    historical_price_2
                )
            )

            assert second_changed
            await session.commit()

            # Tercera observación: $1,350.
            _, third_changed = (
                await repository.save_observation(
                    historical_price_3
                )
            )

            assert third_changed
            await session.commit()

            # Repetimos $1,350.
            # No debe crear otra observación.
            _, repeated_changed = (
                await repository.save_observation(
                    historical_price_3
                )
            )

            assert not repeated_changed
            await session.commit()

            # Consultamos el historial anterior.
            stats = await repository.get_history_stats(
                current_perfume.ml_id
            )

            assert stats.observations == 3
            assert stats.lowest_price == 1350.0

            assert stats.average_price is not None
            assert round(stats.average_price, 2) == 1416.67

            # Calculamos el score del precio actual usando
            # únicamente el historial anterior.
            scorer = OfferScorer()

            score_result = scorer.apply(
                perfume=current_perfume,
                history=stats,
            )

            logger.info(
                "Score antes de guardar el precio actual: "
                f"{score_result.total:.2f}"
            )

            assert score_result.total == 92.0
            assert score_result.eligible_for_alert

            # Guardamos el precio actual: $1,299.
            _, current_changed = (
                await repository.save_observation(
                    current_perfume
                )
            )

            assert current_changed
            await session.commit()

            updated_stats = (
                await repository.get_history_stats(
                    current_perfume.ml_id
                )
            )

            assert updated_stats.observations == 4
            assert updated_stats.lowest_price == 1299.0

            logger.info(
                "Historial guardado correctamente."
            )

            logger.info(
                f"Observaciones: "
                f"{updated_stats.observations}"
            )

            logger.info(
                f"Precio mínimo: "
                f"${updated_stats.lowest_price:,.2f}"
            )

            logger.info(
                f"Score calculado: "
                f"{score_result.total:.2f}/100"
            )

    finally:
        await database.close()


async def main() -> None:
    with TemporaryDirectory() as temporary_directory:
        database_path = (
            Path(temporary_directory)
            / "test_perfumes.db"
        )

        database_url = (
            "sqlite+aiosqlite:///"
            + database_path.as_posix()
        )

        await run_test(database_url)


if __name__ == "__main__":
    asyncio.run(main())
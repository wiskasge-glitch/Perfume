import argparse
import asyncio

from app.config.settings import (
    BOT_RUN_INTERVAL_SECONDS,
)
from app.database.session import DatabaseManager
from app.engine.offer_scorer import OfferScorer
from app.notifier.telegram import (
    TelegramClient,
    TelegramClientError,
)
from app.scheduler.runner import BotScheduler
from app.services.application_service import (
    ApplicationService,
)
from app.services.catalog_service import CatalogService
from app.services.notification_dispatcher_service import (
    NotificationDispatcherService,
)
from app.services.offer_pipeline_service import (
    OfferPipelineService,
)
from app.sources.fixture import FixturePerfumeSource
from app.utils.logger import logger


def parse_arguments() -> argparse.Namespace:
    """
    Lee los argumentos recibidos desde la terminal.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Detector y publicador de ofertas "
            "de perfumes."
        )
    )

    execution_mode = (
        parser.add_mutually_exclusive_group()
    )

    execution_mode.add_argument(
        "--once",
        action="store_true",
        help="Ejecuta un solo ciclo y termina.",
    )

    execution_mode.add_argument(
        "--watch",
        action="store_true",
        help="Ejecuta el bot continuamente.",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=BOT_RUN_INTERVAL_SECONDS,
        help=(
            "Intervalo entre ciclos, en segundos. "
            "Solo se utiliza con --watch."
        ),
    )

    return parser.parse_args()


async def run_application(
    watch: bool,
    interval_seconds: int,
) -> None:
    """
    Construye e inicia todos los servicios.
    """

    logger.info(
        "================================="
    )
    logger.info(
        "Perfume Deals Bot iniciado"
    )
    logger.info(
        "================================="
    )

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

        async with TelegramClient() as telegram:
            dispatcher = (
                NotificationDispatcherService(
                    database=database,
                    telegram=telegram,
                )
            )

            application = ApplicationService(
                pipeline=pipeline,
                dispatcher=dispatcher,
            )

            scheduler = BotScheduler(
                application=application,
                interval_seconds=interval_seconds,
            )

            if watch:
                await scheduler.run_forever()
            else:
                await scheduler.run_once()

    except TelegramClientError as error:
        logger.error(
            f"Error de Telegram: {error}"
        )

    finally:
        await database.close()

        logger.info(
            "Perfume Deals Bot detenido."
        )


def main() -> None:
    arguments = parse_arguments()

    try:
        asyncio.run(
            run_application(
                watch=arguments.watch,
                interval_seconds=arguments.interval,
            )
        )

    except KeyboardInterrupt:
        logger.info(
            "Ejecución detenida por el usuario."
        )


if __name__ == "__main__":
    main()
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from app.database.session import DatabaseManager
from app.engine.offer_scorer import OfferScorer
from app.notifier.telegram import TelegramSendResult
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


class FakeTelegramClient:
    """
    Cliente de Telegram falso para pruebas.
    """

    def __init__(self) -> None:
        self.sent_messages = 0

    async def send_offer(
        self,
        message,
    ) -> TelegramSendResult:
        assert message.text

        self.sent_messages += 1

        return TelegramSendResult(
            message_id=2000 + self.sent_messages,
            method="sendMessage",
        )


async def run_test(
    database_url: str,
) -> None:
    database = DatabaseManager(
        database_url=database_url
    )

    try:
        await database.create_tables()

        catalog = CatalogService(
            source=FixturePerfumeSource()
        )

        pipeline = OfferPipelineService(
            catalog=catalog,
            database=database,
            scorer=OfferScorer(),
        )

        fake_telegram = FakeTelegramClient()

        dispatcher = (
            NotificationDispatcherService(
                database=database,
                telegram=fake_telegram,
            )
        )

        application = ApplicationService(
            pipeline=pipeline,
            dispatcher=dispatcher,
        )

        first_cycle = await application.run_cycle()

        assert (
            first_cycle.pipeline.processed_count
            == 2
        )

        assert (
            first_cycle.pipeline.alert_count
            == 1
        )

        assert first_cycle.dispatch.sent == 1
        assert first_cycle.dispatch.failed == 0

        second_cycle = await application.run_cycle()

        assert (
            second_cycle.pipeline.processed_count
            == 2
        )

        assert (
            second_cycle.pipeline.alert_count
            == 0
        )

        assert second_cycle.dispatch.sent == 0
        assert second_cycle.dispatch.failed == 0

        assert fake_telegram.sent_messages == 1

        logger.info(
            "Prueba de ApplicationService "
            "completada correctamente."
        )

    finally:
        await database.close()


async def main() -> None:
    with TemporaryDirectory() as temporary_directory:
        database_path = (
            Path(temporary_directory)
            / "test_application.db"
        )

        database_url = (
            "sqlite+aiosqlite:///"
            + database_path.as_posix()
        )

        await run_test(database_url)


if __name__ == "__main__":
    asyncio.run(main())
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from app.database.outbox_repository import (
    NotificationOutboxRepository,
)
from app.database.session import DatabaseManager
from app.engine.offer_scorer import OfferScorer
from app.notifier.telegram import TelegramSendResult
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
    Cliente falso que no se conecta a Telegram.
    """

    def __init__(self) -> None:
        self.messages_sent = 0

    async def send_offer(
        self,
        message,
    ) -> TelegramSendResult:
        assert message.text

        self.messages_sent += 1

        return TelegramSendResult(
            message_id=1000 + self.messages_sent,
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

        pipeline_result = await pipeline.run()

        assert pipeline_result.processed_count == 2
        assert pipeline_result.alert_count == 1

        async with database.session() as session:
            repository = (
                NotificationOutboxRepository(
                    session
                )
            )

            assert (
                await repository.count_by_status(
                    "pending"
                )
                == 1
            )

            assert (
                await repository.count_by_status(
                    "sent"
                )
                == 0
            )

        fake_telegram = FakeTelegramClient()

        dispatcher = NotificationDispatcherService(
            database=database,
            telegram=fake_telegram,
        )

        dispatch_result = await dispatcher.run()

        assert dispatch_result.pending_found == 1
        assert dispatch_result.sent == 1
        assert dispatch_result.failed == 0

        async with database.session() as session:
            repository = (
                NotificationOutboxRepository(
                    session
                )
            )

            assert (
                await repository.count_by_status(
                    "pending"
                )
                == 0
            )

            assert (
                await repository.count_by_status(
                    "sent"
                )
                == 1
            )

        # No debe reenviar algo ya marcado como enviado.
        second_dispatch = await dispatcher.run()

        assert second_dispatch.pending_found == 0
        assert second_dispatch.sent == 0

        logger.info(
            "Prueba de la outbox completada correctamente."
        )

    finally:
        await database.close()


async def main() -> None:
    with TemporaryDirectory() as temporary_directory:
        database_path = (
            Path(temporary_directory)
            / "test_outbox.db"
        )

        database_url = (
            "sqlite+aiosqlite:///"
            + database_path.as_posix()
        )

        await run_test(database_url)


if __name__ == "__main__":
    asyncio.run(main())
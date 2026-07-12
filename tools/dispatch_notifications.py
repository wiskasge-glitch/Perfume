import asyncio

from app.database.session import DatabaseManager
from app.notifier.telegram import (
    TelegramClient,
    TelegramClientError,
)
from app.services.notification_dispatcher_service import (
    NotificationDispatcherService,
)
from app.utils.logger import logger


async def main() -> None:
    database = DatabaseManager()

    try:
        await database.create_tables()

        async with TelegramClient() as telegram:
            dispatcher = NotificationDispatcherService(
                database=database,
                telegram=telegram,
            )

            result = await dispatcher.run(
                limit=20
            )

            logger.info(
                f"Pendientes encontradas: "
                f"{result.pending_found}"
            )

            logger.info(
                f"Enviadas: {result.sent}"
            )

            logger.info(
                f"Fallidas: {result.failed}"
            )

    except TelegramClientError as error:
        logger.error(str(error))

    finally:
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
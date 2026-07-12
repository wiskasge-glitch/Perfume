from dataclasses import dataclass
from typing import Protocol

from app.database.outbox_repository import (
    NotificationOutboxRepository,
    payload_to_telegram_message,
)
from app.database.session import DatabaseManager
from app.notifier.formatter import TelegramOfferMessage
from app.notifier.telegram import (
    TelegramClientError,
    TelegramSendResult,
)
from app.utils.logger import logger


class TelegramSender(Protocol):
    """
    Contrato necesario para enviar mensajes a Telegram.
    """

    async def send_offer(
        self,
        message: TelegramOfferMessage,
    ) -> TelegramSendResult:
        ...


@dataclass(slots=True, frozen=True)
class NotificationDispatchResult:
    """
    Resumen del procesamiento de la cola.
    """

    pending_found: int
    sent: int
    failed: int


class NotificationDispatcherService:
    """
    Envía las notificaciones pendientes de la outbox.
    """

    def __init__(
        self,
        database: DatabaseManager,
        telegram: TelegramSender,
    ) -> None:
        self.database = database
        self.telegram = telegram

    async def run(
        self,
        limit: int = 20,
    ) -> NotificationDispatchResult:
        """
        Envía hasta `limit` notificaciones pendientes.
        """

        async with self.database.session() as session:
            repository = NotificationOutboxRepository(
                session
            )

            pending_ids = (
                await repository.get_pending_ids(
                    limit=limit
                )
            )

        sent_count = 0
        failed_count = 0

        for notification_id in pending_ids:
            async with self.database.session() as session:
                repository = (
                    NotificationOutboxRepository(
                        session
                    )
                )

                record = await repository.get_by_id(
                    notification_id
                )

                if (
                    record is None
                    or record.status != "pending"
                ):
                    continue

                try:
                    message = (
                        payload_to_telegram_message(
                            record.payload
                        )
                    )

                    result = await self.telegram.send_offer(
                        message
                    )

                    await repository.mark_sent(
                        record=record,
                        telegram_message_id=(
                            result.message_id
                        ),
                    )

                    await session.commit()

                    sent_count += 1

                    logger.info(
                        f"NOTIFICACIÓN ENVIADA | "
                        f"Outbox ID: {record.id} | "
                        f"Telegram ID: "
                        f"{result.message_id}"
                    )

                except (
                    TelegramClientError,
                    ValueError,
                ) as error:
                    await repository.mark_failed(
                        record=record,
                        error=str(error),
                    )

                    await session.commit()

                    failed_count += 1

                    logger.error(
                        f"NOTIFICACIÓN FALLIDA | "
                        f"Outbox ID: {record.id} | "
                        f"{error}"
                    )

        logger.info(
            f"Despacho terminado: "
            f"{sent_count} enviadas, "
            f"{failed_count} fallidas."
        )

        return NotificationDispatchResult(
            pending_found=len(pending_ids),
            sent=sent_count,
            failed=failed_count,
        )
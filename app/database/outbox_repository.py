from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import NotificationOutboxRecord
from app.notifier.formatter import TelegramOfferMessage


def telegram_message_to_payload(
    message: TelegramOfferMessage,
) -> dict[str, Any]:
    """
    Convierte un mensaje de Telegram en datos JSON.
    """

    return {
        "text": message.text,
        "button_text": message.button_text,
        "button_url": message.button_url,
        "image_url": message.image_url,
    }


def payload_to_telegram_message(
    payload: dict[str, Any],
) -> TelegramOfferMessage:
    """
    Reconstruye un mensaje de Telegram desde la base de datos.
    """

    text = payload.get("text")

    if not isinstance(text, str) or not text.strip():
        raise ValueError(
            "La notificación no contiene un texto válido."
        )

    button_text = payload.get(
        "button_text",
        "🛒 Ver oferta",
    )

    button_url = payload.get("button_url")
    image_url = payload.get("image_url")

    return TelegramOfferMessage(
        text=text,
        button_text=(
            button_text
            if isinstance(button_text, str)
            else "🛒 Ver oferta"
        ),
        button_url=(
            button_url
            if isinstance(button_url, str)
            else None
        ),
        image_url=(
            image_url
            if isinstance(image_url, str)
            else None
        ),
    )


class NotificationOutboxRepository:
    """
    Administra la cola persistente de notificaciones.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_by_event_key(
        self,
        event_key: str,
    ) -> NotificationOutboxRecord | None:
        statement = select(
            NotificationOutboxRecord
        ).where(
            NotificationOutboxRecord.event_key
            == event_key
        )

        return await self.session.scalar(statement)

    async def enqueue_telegram(
        self,
        event_key: str,
        message: TelegramOfferMessage,
    ) -> tuple[NotificationOutboxRecord, bool]:
        """
        Guarda una notificación pendiente.

        Devuelve False cuando el evento ya estaba registrado.
        """

        existing_record = await self.get_by_event_key(
            event_key
        )

        if existing_record is not None:
            return existing_record, False

        record = NotificationOutboxRecord(
            event_key=event_key,
            channel="telegram",
            status="pending",
            payload=telegram_message_to_payload(
                message
            ),
        )

        self.session.add(record)
        await self.session.flush()

        return record, True

    async def get_pending_ids(
        self,
        limit: int = 20,
    ) -> list[int]:
        """
        Obtiene los IDs de las notificaciones pendientes.
        """

        if limit <= 0:
            raise ValueError(
                "El límite debe ser mayor que cero."
            )

        statement = (
            select(NotificationOutboxRecord.id)
            .where(
                NotificationOutboxRecord.status
                == "pending"
            )
            .order_by(
                NotificationOutboxRecord.created_at,
                NotificationOutboxRecord.id,
            )
            .limit(limit)
        )

        result = await self.session.scalars(statement)

        return list(result)

    async def get_by_id(
        self,
        notification_id: int,
    ) -> NotificationOutboxRecord | None:
        return await self.session.get(
            NotificationOutboxRecord,
            notification_id,
        )

    async def mark_sent(
        self,
        record: NotificationOutboxRecord,
        telegram_message_id: int,
    ) -> None:
        """
        Marca una notificación como enviada.
        """

        now = datetime.now(timezone.utc)

        record.status = "sent"
        record.attempts += 1
        record.last_error = None
        record.telegram_message_id = (
            telegram_message_id
        )
        record.sent_at = now
        record.updated_at = now

        await self.session.flush()

    async def mark_failed(
        self,
        record: NotificationOutboxRecord,
        error: str,
        maximum_attempts: int = 5,
    ) -> None:
        """
        Registra un intento fallido.

        Mientras no alcance el límite, permanece pendiente.
        """

        record.attempts += 1
        record.last_error = error[:1000]
        record.updated_at = datetime.now(timezone.utc)

        if record.attempts >= maximum_attempts:
            record.status = "failed"
        else:
            record.status = "pending"

        await self.session.flush()

    async def count_by_status(
        self,
        status: str,
    ) -> int:
        statement = select(
            func.count(NotificationOutboxRecord.id)
        ).where(
            NotificationOutboxRecord.status == status
        )

        value = await self.session.scalar(statement)

        return int(value or 0)
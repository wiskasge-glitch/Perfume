from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now() -> datetime:
    """
    Devuelve la fecha y hora actual en UTC.
    """

    return datetime.now(timezone.utc)


class PerfumeRecord(Base):
    """
    Representa un perfume conocido por el sistema.
    """

    __tablename__ = "perfumes"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    external_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    brand: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    current_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    original_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    discount: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )

    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    image: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    seller: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
        default="",
        index=True,
    )

    trusted_seller: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    mercado_lider: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    full: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    condition: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Nuevo",
    )

    score: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    price_history: Mapped[list[PriceHistoryRecord]] = relationship(
        back_populates="perfume",
        cascade="all, delete-orphan",
    )


class PriceHistoryRecord(Base):
    """
    Representa un cambio de precio observado.
    """

    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    perfume_id: Mapped[int] = mapped_column(
        ForeignKey(
            "perfumes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    original_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    discount: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )

    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    perfume: Mapped[PerfumeRecord] = relationship(
        back_populates="price_history",
    )


Index(
    "ix_price_history_perfume_observed",
    PriceHistoryRecord.perfume_id,
    PriceHistoryRecord.observed_at,
)

class NotificationOutboxRecord(Base):
    """
    Representa una notificación pendiente, enviada o fallida.

    El mensaje se guarda antes de intentar enviarlo a Telegram,
    evitando perderlo por problemas temporales de conexión.
    """

    __tablename__ = "notification_outbox"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    event_key: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        nullable=False,
        index=True,
    )

    channel: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="telegram",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    telegram_message_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
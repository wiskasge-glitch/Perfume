from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    PerfumeRecord,
    PriceHistoryRecord,
)
from app.models.perfume import Perfume
from app.models.price_history import HistoricalPriceStats


MONEY_PRECISION = Decimal("0.01")


def as_decimal(value: float) -> Decimal:
    """
    Convierte un número a Decimal con dos posiciones.
    """

    return Decimal(str(value)).quantize(
        MONEY_PRECISION
    )


def as_optional_decimal(
    value: float | None,
) -> Decimal | None:
    """
    Convierte un número opcional a Decimal.
    """

    if value is None:
        return None

    return as_decimal(value)


class PerfumeRepository:
    """
    Guarda perfumes y consulta sus precios históricos.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_by_external_id(
        self,
        external_id: str,
    ) -> PerfumeRecord | None:
        """
        Busca un perfume por su identificador externo.
        """

        statement = select(
            PerfumeRecord
        ).where(
            PerfumeRecord.external_id == external_id
        )

        return await self.session.scalar(statement)

    async def save_observation(
        self,
        perfume: Perfume,
    ) -> tuple[PerfumeRecord, bool]:
        """
        Crea o actualiza un perfume.

        Devuelve:
        - El registro guardado.
        - True cuando el precio cambió.
        """

        current_price = as_decimal(
            perfume.price
        )

        record = await self.get_by_external_id(
            perfume.ml_id
        )

        now = datetime.now(timezone.utc)

        if record is None:
            record = PerfumeRecord(
                external_id=perfume.ml_id,
                title=perfume.title,
                brand=perfume.brand,
                current_price=current_price,
                original_price=as_optional_decimal(
                    perfume.original_price
                ),
                discount=as_optional_decimal(
                    perfume.discount
                ),
                url=perfume.url,
                image=perfume.image,
                seller=perfume.seller,
                trusted_seller=perfume.trusted_seller,
                mercado_lider=perfume.mercado_lider,
                full=perfume.full,
                condition=perfume.condition,
                score=as_decimal(perfume.score),
                first_seen_at=now,
                last_seen_at=now,
            )

            self.session.add(record)
            await self.session.flush()

        else:
            record.title = perfume.title
            record.brand = perfume.brand
            record.current_price = current_price
            record.original_price = as_optional_decimal(
                perfume.original_price
            )
            record.discount = as_optional_decimal(
                perfume.discount
            )
            record.url = perfume.url
            record.image = perfume.image
            record.seller = perfume.seller
            record.trusted_seller = (
                perfume.trusted_seller
            )
            record.mercado_lider = (
                perfume.mercado_lider
            )
            record.full = perfume.full
            record.condition = perfume.condition
            record.score = as_decimal(perfume.score)
            record.last_seen_at = now

        latest_price_statement = (
            select(PriceHistoryRecord.price)
            .where(
                PriceHistoryRecord.perfume_id
                == record.id
            )
            .order_by(
                desc(PriceHistoryRecord.observed_at),
                desc(PriceHistoryRecord.id),
            )
            .limit(1)
        )

        latest_price = await self.session.scalar(
            latest_price_statement
        )

        price_changed = (
            latest_price is None
            or as_decimal(float(latest_price))
            != current_price
        )

        if price_changed:
            observation = PriceHistoryRecord(
                perfume_id=record.id,
                price=current_price,
                original_price=as_optional_decimal(
                    perfume.original_price
                ),
                discount=as_optional_decimal(
                    perfume.discount
                ),
                observed_at=now,
            )

            self.session.add(observation)

        await self.session.flush()

        return record, price_changed

    async def get_history_stats(
        self,
        external_id: str,
    ) -> HistoricalPriceStats:
        """
        Calcula mínimo, promedio y número de precios
        registrados para un producto.
        """

        statement = (
            select(
                func.min(PriceHistoryRecord.price),
                func.avg(PriceHistoryRecord.price),
                func.count(PriceHistoryRecord.id),
            )
            .join(
                PerfumeRecord,
                PriceHistoryRecord.perfume_id
                == PerfumeRecord.id,
            )
            .where(
                PerfumeRecord.external_id
                == external_id
            )
        )

        result = await self.session.execute(
            statement
        )

        lowest_price, average_price, observations = (
            result.one()
        )

        return HistoricalPriceStats(
            lowest_price=(
                float(lowest_price)
                if lowest_price is not None
                else None
            ),
            average_price=(
                float(average_price)
                if average_price is not None
                else None
            ),
            observations=int(observations or 0),
        )
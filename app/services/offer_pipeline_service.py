from dataclasses import dataclass

from app.database.outbox_repository import (
    NotificationOutboxRepository,
)
from app.database.repository import PerfumeRepository
from app.database.session import DatabaseManager
from app.engine.offer_scorer import OfferScore, OfferScorer
from app.models.perfume import Perfume
from app.notifier.formatter import TelegramOfferFormatter
from app.services.catalog_service import CatalogService
from app.utils.logger import logger


@dataclass(slots=True, frozen=True)
class ProcessedOffer:
    """
    Representa una publicación procesada.
    """

    perfume: Perfume
    score: OfferScore
    new_price_observation: bool


@dataclass(slots=True, frozen=True)
class PipelineResult:
    """
    Resultado completo del pipeline.
    """

    processed_offers: tuple[ProcessedOffer, ...]
    alert_candidates: tuple[ProcessedOffer, ...]

    @property
    def processed_count(self) -> int:
        return len(self.processed_offers)

    @property
    def alert_count(self) -> int:
        return len(self.alert_candidates)


class OfferPipelineService:
    """
    Obtiene, filtra, puntúa y guarda ofertas.

    Las alertas se guardan en la outbox dentro de la
    misma transacción que el nuevo precio.
    """

    def __init__(
        self,
        catalog: CatalogService,
        database: DatabaseManager,
        scorer: OfferScorer | None = None,
        formatter: TelegramOfferFormatter | None = None,
    ) -> None:
        self.catalog = catalog
        self.database = database
        self.scorer = scorer or OfferScorer()
        self.formatter = (
            formatter or TelegramOfferFormatter()
        )

    async def run(self) -> PipelineResult:
        logger.info(
            "================================="
        )
        logger.info(
            "Iniciando pipeline de ofertas."
        )
        logger.info(
            "================================="
        )

        perfumes = await self.catalog.get_valid_perfumes()

        processed_offers: list[ProcessedOffer] = []
        alert_candidates: list[ProcessedOffer] = []

        async with self.database.session() as session:
            perfume_repository = PerfumeRepository(
                session
            )

            outbox_repository = (
                NotificationOutboxRepository(
                    session
                )
            )

            try:
                for perfume in perfumes:
                    # Consultamos el historial antes de
                    # guardar el precio actual.
                    history = (
                        await perfume_repository
                        .get_history_stats(
                            perfume.ml_id
                        )
                    )

                    score_result = self.scorer.apply(
                        perfume=perfume,
                        history=history,
                    )

                    _, new_price_observation = (
                        await perfume_repository
                        .save_observation(
                            perfume
                        )
                    )

                    processed_offer = ProcessedOffer(
                        perfume=perfume,
                        score=score_result,
                        new_price_observation=(
                            new_price_observation
                        ),
                    )

                    processed_offers.append(
                        processed_offer
                    )

                    logger.info(
                        f"PROCESADO | {perfume.ml_id} | "
                        f"{score_result.total:.2f}/100 | "
                        f"Precio nuevo: "
                        f"{'sí' if new_price_observation else 'no'}"
                    )

                    if not (
                        score_result.eligible_for_alert
                        and new_price_observation
                    ):
                        continue

                    message = self.formatter.format(
                        perfume=perfume,
                        score=score_result,
                    )

                    # El número de observaciones permite
                    # distinguir cada cambio de precio.
                    event_sequence = (
                        history.observations + 1
                    )

                    event_key = (
                        f"telegram:{perfume.ml_id}:"
                        f"{event_sequence}:"
                        f"{perfume.price:.2f}"
                    )

                    _, notification_created = (
                        await outbox_repository
                        .enqueue_telegram(
                            event_key=event_key,
                            message=message,
                        )
                    )

                    if notification_created:
                        alert_candidates.append(
                            processed_offer
                        )

                        logger.info(
                            f"ALERTA ENCOLADA | "
                            f"{perfume.ml_id} | "
                            f"{perfume.title}"
                        )

                # Precio y notificación se confirman juntos.
                await session.commit()

            except Exception:
                await session.rollback()

                logger.exception(
                    "Error durante el pipeline. "
                    "La transacción fue revertida."
                )

                raise

        alert_candidates.sort(
            key=lambda offer: offer.score.total,
            reverse=True,
        )

        logger.info(
            f"Pipeline terminado: "
            f"{len(processed_offers)} procesadas, "
            f"{len(alert_candidates)} alertas encoladas."
        )

        return PipelineResult(
            processed_offers=tuple(processed_offers),
            alert_candidates=tuple(alert_candidates),
        ) 
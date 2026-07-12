from dataclasses import dataclass

from app.database.repository import PerfumeRepository
from app.database.session import DatabaseManager
from app.engine.offer_scorer import OfferScore, OfferScorer
from app.models.perfume import Perfume
from app.services.catalog_service import CatalogService
from app.utils.logger import logger


@dataclass(slots=True, frozen=True)
class ProcessedOffer:
    """
    Representa una publicación procesada por el pipeline.
    """

    perfume: Perfume
    score: OfferScore
    new_price_observation: bool


@dataclass(slots=True, frozen=True)
class PipelineResult:
    """
    Resultado completo de una ejecución del pipeline.
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
    Coordina el procesamiento completo de las ofertas.

    Flujo:

    1. Obtiene perfumes válidos.
    2. Consulta su historial anterior.
    3. Calcula el score.
    4. Guarda el precio actual.
    5. Selecciona las alertas nuevas.
    """

    def __init__(
        self,
        catalog: CatalogService,
        database: DatabaseManager,
        scorer: OfferScorer | None = None,
    ) -> None:
        self.catalog = catalog
        self.database = database
        self.scorer = scorer or OfferScorer()

    async def run(self) -> PipelineResult:
        """
        Ejecuta una actualización completa del catálogo.
        """

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
            repository = PerfumeRepository(session)

            try:
                for perfume in perfumes:
                    # El historial se consulta antes de guardar
                    # el precio actual.
                    history = await repository.get_history_stats(
                        perfume.ml_id
                    )

                    score_result = self.scorer.apply(
                        perfume=perfume,
                        history=history,
                    )

                    _, new_price_observation = (
                        await repository.save_observation(
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

                    # Evitamos publicar repetidamente una oferta
                    # cuyo precio no cambió.
                    if (
                        score_result.eligible_for_alert
                        and new_price_observation
                    ):
                        alert_candidates.append(
                            processed_offer
                        )

                        logger.info(
                            f"ALERTA ELEGIBLE | "
                            f"{perfume.ml_id} | "
                            f"{perfume.title}"
                        )

                await session.commit()

            except Exception:
                await session.rollback()

                logger.exception(
                    "Ocurrió un error durante el pipeline. "
                    "La transacción fue revertida."
                )

                raise

        # Las mejores ofertas aparecen primero.
        alert_candidates.sort(
            key=lambda offer: offer.score.total,
            reverse=True,
        )

        logger.info(
            f"Pipeline terminado: "
            f"{len(processed_offers)} procesadas, "
            f"{len(alert_candidates)} alertas nuevas."
        )

        return PipelineResult(
            processed_offers=tuple(processed_offers),
            alert_candidates=tuple(alert_candidates),
        )
from dataclasses import dataclass

from app.config.settings import OUTBOX_BATCH_SIZE
from app.services.notification_dispatcher_service import (
    NotificationDispatcherService,
    NotificationDispatchResult,
)
from app.services.offer_pipeline_service import (
    OfferPipelineService,
    PipelineResult,
)
from app.utils.logger import logger


@dataclass(slots=True, frozen=True)
class ApplicationCycleResult:
    """
    Resultado completo de un ciclo del bot.
    """

    pipeline: PipelineResult
    dispatch: NotificationDispatchResult


class ApplicationService:
    """
    Coordina un ciclo completo del bot.

    1. Busca y procesa ofertas.
    2. Guarda las alertas en la outbox.
    3. Envía las notificaciones pendientes.
    """

    def __init__(
        self,
        pipeline: OfferPipelineService,
        dispatcher: NotificationDispatcherService,
        outbox_batch_size: int = OUTBOX_BATCH_SIZE,
    ) -> None:
        if outbox_batch_size <= 0:
            raise ValueError(
                "El tamaño del lote debe ser positivo."
            )

        self.pipeline = pipeline
        self.dispatcher = dispatcher
        self.outbox_batch_size = outbox_batch_size

    async def run_cycle(
        self,
    ) -> ApplicationCycleResult:
        """
        Ejecuta un ciclo completo de la aplicación.
        """

        logger.info(
            "#################################"
        )
        logger.info(
            "Iniciando ciclo de Perfume Deals Bot."
        )
        logger.info(
            "#################################"
        )

        pipeline_result = await self.pipeline.run()

        dispatch_result = await self.dispatcher.run(
            limit=self.outbox_batch_size
        )

        logger.info(
            "Ciclo terminado: "
            f"{pipeline_result.processed_count} procesadas, "
            f"{pipeline_result.alert_count} encoladas, "
            f"{dispatch_result.sent} enviadas, "
            f"{dispatch_result.failed} fallidas."
        )

        return ApplicationCycleResult(
            pipeline=pipeline_result,
            dispatch=dispatch_result,
        )
import asyncio
from time import monotonic

from app.config.settings import (
    BOT_RUN_INTERVAL_SECONDS,
)
from app.services.application_service import (
    ApplicationService,
)
from app.utils.logger import logger


class BotScheduler:
    """
    Ejecuta la aplicación repetidamente
    utilizando asyncio.
    """

    def __init__(
        self,
        application: ApplicationService,
        interval_seconds: int = (
            BOT_RUN_INTERVAL_SECONDS
        ),
    ) -> None:
        if interval_seconds < 30:
            raise ValueError(
                "El intervalo mínimo permitido "
                "es de 30 segundos."
            )

        self.application = application
        self.interval_seconds = interval_seconds

    async def run_once(self) -> None:
        """
        Ejecuta solamente un ciclo.
        """

        await self.application.run_cycle()

    async def run_forever(self) -> None:
        """
        Ejecuta ciclos hasta que el programa sea detenido.
        """

        logger.info(
            "Bot iniciado en modo continuo."
        )

        logger.info(
            f"Intervalo: "
            f"{self.interval_seconds} segundos."
        )

        while True:
            started_at = monotonic()

            try:
                await self.application.run_cycle()

            except asyncio.CancelledError:
                logger.info(
                    "El scheduler fue cancelado."
                )
                raise

            except Exception:
                logger.exception(
                    "El ciclo terminó con un error. "
                    "El bot continuará ejecutándose."
                )

            elapsed_seconds = (
                monotonic() - started_at
            )

            sleep_seconds = max(
                0,
                self.interval_seconds
                - elapsed_seconds,
            )

            logger.info(
                f"Próximo ciclo en "
                f"{sleep_seconds:.0f} segundos."
            )

            await asyncio.sleep(
                sleep_seconds
            )
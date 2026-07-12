from app.engine.perfume_filter import PerfumeFilter
from app.models.perfume import Perfume
from app.sources.base import PerfumeSource
from app.utils.logger import logger


class CatalogService:
    """
    Coordina la obtención y filtrado de perfumes.

    Esta clase no sabe de dónde vienen los productos.
    Solo necesita una fuente que cumpla el contrato
    definido por PerfumeSource.
    """

    def __init__(
        self,
        source: PerfumeSource,
        perfume_filter: PerfumeFilter | None = None,
    ) -> None:
        self.source = source
        self.perfume_filter = (
            perfume_filter or PerfumeFilter()
        )

    async def get_valid_perfumes(
        self,
    ) -> list[Perfume]:
        """
        Obtiene los perfumes desde la fuente configurada
        y devuelve únicamente los que cumplen las reglas.
        """

        logger.info(
            "Iniciando actualización del catálogo."
        )

        perfumes = await self.source.get_perfumes()

        logger.info(
            f"La fuente entregó "
            f"{len(perfumes)} publicaciones."
        )

        valid_perfumes = (
            self.perfume_filter.filter_many(perfumes)
        )

        logger.info(
            f"Catálogo actualizado: "
            f"{len(valid_perfumes)} perfumes válidos."
        )

        return valid_perfumes
import asyncio

from app.services.catalog_service import CatalogService
from app.sources.fixture import FixturePerfumeSource
from app.utils.logger import logger


async def main() -> None:
    source = FixturePerfumeSource()

    catalog = CatalogService(
        source=source,
    )

    perfumes = await catalog.get_valid_perfumes()

    perfume_ids = [
        perfume.ml_id
        for perfume in perfumes
    ]

    expected_ids = [
        "TEST001",
        "TEST002",
    ]

    assert perfume_ids == expected_ids, (
        f"Se esperaban {expected_ids}, "
        f"pero se recibieron {perfume_ids}"
    )

    assert all(
        perfume.trusted_seller
        for perfume in perfumes
    ), "Todos los perfumes aceptados deben tener vendedor confiable."

    logger.info(
        f"Catálogo válido: {perfume_ids}"
    )

    logger.info(
        "Prueba de CatalogService completada correctamente."
    )


if __name__ == "__main__":
    asyncio.run(main())
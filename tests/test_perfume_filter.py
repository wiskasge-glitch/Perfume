import asyncio

from app.engine.perfume_filter import PerfumeFilter
from app.sources.fixture import FixturePerfumeSource
from app.utils.logger import logger


async def main() -> None:
    source = FixturePerfumeSource()
    perfume_filter = PerfumeFilter()

    perfumes = await source.get_perfumes()

    accepted_perfumes = (
        perfume_filter.filter_many(perfumes)
    )

    accepted_ids = [
        perfume.ml_id
        for perfume in accepted_perfumes
    ]

    logger.info(
        f"IDs aceptados: {accepted_ids}"
    )

    expected_ids = [
        "TEST001",
        "TEST002",
    ]

    assert accepted_ids == expected_ids, (
        f"Se esperaban {expected_ids}, "
        f"pero se obtuvieron {accepted_ids}"
    )

    logger.info(
        "Prueba del filtro completada correctamente."
    )


if __name__ == "__main__":
    asyncio.run(main())
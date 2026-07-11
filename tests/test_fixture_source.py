import asyncio

from app.sources.fixture import FixturePerfumeSource
from app.utils.logger import logger


async def main() -> None:
    source = FixturePerfumeSource()

    perfumes = await source.get_perfumes()

    logger.info(
        f"Total de perfumes recibidos: {len(perfumes)}"
    )

    for perfume in perfumes:
        logger.info(
            f"{perfume.ml_id} | "
            f"{perfume.title} | "
            f"${perfume.price:,.2f} | "
            f"{perfume.seller}"
        )


if __name__ == "__main__":
    asyncio.run(main())
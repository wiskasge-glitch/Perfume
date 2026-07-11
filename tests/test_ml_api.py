import asyncio

from app.clients.mercadolibre import MercadoLibreClient
from app.utils.logger import logger


async def main() -> None:
    async with MercadoLibreClient() as client:
        products = await client.search_items(
            keyword="versace eros",
            limit=5,
        )

        for product in products:
            logger.info(
                f"{product.get('id')} | "
                f"{product.get('title')} | "
                f"${product.get('price')}"
            )


if __name__ == "__main__":
    asyncio.run(main())
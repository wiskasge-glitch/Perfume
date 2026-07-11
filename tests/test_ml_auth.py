import asyncio

from app.clients.mercadolibre import (
    MercadoLibreAPIError,
    MercadoLibreClient,
)
from app.utils.logger import logger


async def main() -> None:
    try:
        async with MercadoLibreClient() as client:
            user = await client.get_current_user()

            logger.info("Token válido.")
            logger.info(
                f"Usuario ID: {user.get('id')}"
            )
            logger.info(
                f"Nickname: {user.get('nickname')}"
            )

    except MercadoLibreAPIError as error:
        logger.error(str(error))


if __name__ == "__main__":
    asyncio.run(main())
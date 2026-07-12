import asyncio

from app.notifier.telegram import (
    TelegramClient,
    TelegramClientError,
)
from app.utils.logger import logger


async def main() -> None:
    try:
        async with TelegramClient() as telegram:
            bot = await telegram.get_me()

            logger.info(
                "Bot de Telegram autenticado."
            )

            logger.info(
                f"Nombre: {bot.get('first_name')}"
            )

            logger.info(
                f"Usuario: @{bot.get('username')}"
            )

            result = await telegram.send_text(
                "✅ <b>Perfume Deals Bot</b>\n\n"
                "La conexión con el canal funciona "
                "correctamente."
            )

            logger.info(
                f"Mensaje enviado correctamente. "
                f"ID: {result.message_id}"
            )

    except TelegramClientError as error:
        logger.error(str(error))


if __name__ == "__main__":
    asyncio.run(main())
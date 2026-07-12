import asyncio

from app.database.session import DatabaseManager
from app.utils.logger import logger


async def main() -> None:
    database = DatabaseManager()

    try:
        await database.create_tables()

        logger.info(
            "Base de datos inicializada correctamente."
        )

    finally:
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
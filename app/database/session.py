from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import DATABASE_URL
from app.database.base import Base

# Importar los modelos registra sus tablas en Base.metadata.
from app.database import models as database_models


class DatabaseManager:
    """
    Administra el motor y las sesiones de la base de datos.
    """

    def __init__(
        self,
        database_url: str = DATABASE_URL,
        echo: bool = False,
    ) -> None:
        if not database_url:
            raise ValueError(
                "La URL de la base de datos está vacía."
            )

        # Evita que el import sea considerado accidentalmente
        # innecesario por herramientas de análisis.
        self._models = database_models

        self.engine = create_async_engine(
            database_url,
            echo=echo,
        )

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def create_tables(self) -> None:
        """
        Crea las tablas que todavía no existan.
        """

        async with self.engine.begin() as connection:
            await connection.run_sync(
                Base.metadata.create_all
            )

    def session(self) -> AsyncSession:
        """
        Devuelve una nueva sesión asíncrona.
        """

        return self.session_factory()

    async def close(self) -> None:
        """
        Cierra todas las conexiones del motor.
        """

        await self.engine.dispose()
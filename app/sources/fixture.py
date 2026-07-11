import json
from pathlib import Path
from typing import Any

from app.models.perfume import Perfume
from app.utils.logger import logger


class FixtureSourceError(RuntimeError):
    """
    Error al cargar los datos locales de prueba.
    """


class FixturePerfumeSource:
    """
    Fuente local utilizada durante el desarrollo.

    Lee publicaciones ficticias desde un archivo JSON
    y las convierte en objetos Perfume.
    """

    def __init__(
        self,
        file_path: str | Path = "data/fixtures/perfumes.json",
    ) -> None:
        self.file_path = Path(file_path)

    async def get_perfumes(self) -> list[Perfume]:
        logger.info(
            f"Cargando perfumes desde: {self.file_path}"
        )

        if not self.file_path.exists():
            raise FixtureSourceError(
                f"No se encontró el archivo: {self.file_path}"
            )

        try:
            content = self.file_path.read_text(
                encoding="utf-8"
            )

            payload: Any = json.loads(content)

        except json.JSONDecodeError as error:
            raise FixtureSourceError(
                "El archivo de perfumes contiene JSON inválido."
            ) from error

        if not isinstance(payload, list):
            raise FixtureSourceError(
                "El contenido principal del JSON debe ser una lista."
            )

        perfumes: list[Perfume] = []

        for index, item in enumerate(payload, start=1):
            if not isinstance(item, dict):
                raise FixtureSourceError(
                    f"El elemento {index} no es un objeto JSON."
                )

            try:
                perfume = Perfume(**item)
            except TypeError as error:
                raise FixtureSourceError(
                    f"El elemento {index} contiene campos "
                    "faltantes o no reconocidos."
                ) from error

            perfumes.append(perfume)

        logger.info(
            f"Se cargaron {len(perfumes)} perfumes de prueba."
        )

        return perfumes
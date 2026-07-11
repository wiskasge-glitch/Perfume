from typing import Any

import httpx

from app.config.settings import (
    ML_ACCESS_TOKEN,
    ML_API_BASE_URL,
    ML_SITE_ID,
)
from app.utils.logger import logger


class MercadoLibreAPIError(RuntimeError):
    """
    Error producido durante una solicitud a Mercado Libre API.
    """


class MercadoLibreClient:
    """
    Cliente asíncrono para comunicarse con Mercado Libre API.
    """

    def __init__(
        self,
        access_token: str | None = ML_ACCESS_TOKEN,
        site_id: str = ML_SITE_ID,
    ) -> None:
        self.access_token = access_token
        self.site_id = site_id

        headers = {
            "Accept": "application/json",
            "User-Agent": "PerfumeDealsBot/0.1",
        }

        if self.access_token:
            headers["Authorization"] = (
                f"Bearer {self.access_token}"
            )

        self.client = httpx.AsyncClient(
            base_url=ML_API_BASE_URL,
            headers=headers,
            timeout=20.0,
        )

    async def __aenter__(self) -> "MercadoLibreClient":
        return self

    async def __aexit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self.client.aclose()

    async def search_items(
        self,
        keyword: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Prueba la búsqueda pública de publicaciones por palabra clave.

        La disponibilidad de este recurso puede depender de los
        permisos concedidos a la aplicación de Mercado Libre.
        """

        keyword = keyword.strip()

        if not keyword:
            raise ValueError(
                "La palabra clave no puede estar vacía."
            )

        if not self.access_token:
            raise MercadoLibreAPIError(
                "Falta ML_ACCESS_TOKEN en el archivo .env."
            )

        if not 1 <= limit <= 50:
            raise ValueError(
                "El límite debe estar entre 1 y 50."
            )

        logger.info(
            f"Consultando Mercado Libre API: {keyword}"
        )

        response = await self.client.get(
            f"/sites/{self.site_id}/search",
            params={
                "q": keyword,
                "limit": limit,
                "offset": offset,
            },
        )

        if response.status_code == 401:
            raise MercadoLibreAPIError(
                "El access token no es válido o ya expiró."
            )

        if response.status_code == 403:
            raise MercadoLibreAPIError(
                "Mercado Libre rechazó esta búsqueda con HTTP 403. "
                "El recurso puede no estar habilitado para la aplicación."
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise MercadoLibreAPIError(
                "Error al consultar Mercado Libre API: "
                f"HTTP {response.status_code}."
            ) from error

        data = response.json()
        results = data.get("results", [])

        logger.info(
            f"Mercado Libre API devolvió "
            f"{len(results)} publicaciones."
        )

        return results
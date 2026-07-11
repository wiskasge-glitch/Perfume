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
    Cliente asíncrono para Mercado Libre API.
    """

    def __init__(
        self,
        access_token: str | None = ML_ACCESS_TOKEN,
        site_id: str = ML_SITE_ID,
    ) -> None:
        self.access_token = access_token
        self.site_id = site_id

        if not self.access_token:
            raise MercadoLibreAPIError(
                "Falta ML_ACCESS_TOKEN en el archivo .env."
            )

        self.client = httpx.AsyncClient(
            base_url=ML_API_BASE_URL,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.access_token}",
                "User-Agent": "PerfumeDealsBot/0.1",
            },
            timeout=30.0,
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

    @staticmethod
    def _get_error_details(response: httpx.Response) -> str:
        """
        Extrae información segura del error devuelto por Mercado Libre.
        Nunca muestra el access token.
        """

        request_id = (
            response.headers.get("x-request-id")
            or response.headers.get("x-correlation-id")
            or "no disponible"
        )

        try:
            payload = response.json()

            if isinstance(payload, dict):
                error = payload.get("error", "sin código")
                message = payload.get("message", "sin mensaje")
                cause = payload.get("cause")

                details = (
                    f"error={error}; "
                    f"message={message}; "
                    f"request_id={request_id}"
                )

                if cause:
                    details += f"; cause={str(cause)[:300]}"

                return details

        except ValueError:
            pass

        body = response.text.strip()[:300]

        return (
            f"request_id={request_id}; "
            f"respuesta={body or 'vacía'}"
        )

    async def _get_json(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Realiza una solicitud GET y devuelve la respuesta JSON.
        """

        response = await self.client.get(
            path,
            params=params,
        )

        if response.status_code >= 400:
            details = self._get_error_details(response)

            raise MercadoLibreAPIError(
                f"Mercado Libre rechazó {path} "
                f"con HTTP {response.status_code}. "
                f"{details}"
            )

        try:
            return response.json()

        except ValueError as error:
            raise MercadoLibreAPIError(
                f"Mercado Libre respondió a {path}, "
                "pero el contenido no es JSON válido."
            ) from error

    async def get_current_user(self) -> dict[str, Any]:
        """
        Comprueba el token consultando al usuario autorizado.
        """

        logger.info(
            "Comprobando el usuario autorizado en Mercado Libre..."
        )

        data = await self._get_json("/users/me")

        if not isinstance(data, dict):
            raise MercadoLibreAPIError(
                "La respuesta de /users/me no tiene "
                "el formato esperado."
            )

        return data

    async def get_user(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        """
        Obtiene información básica de un usuario o vendedor.
        """

        data = await self._get_json(
            f"/users/{user_id}"
        )

        if not isinstance(data, dict):
            raise MercadoLibreAPIError(
                "La información del vendedor no tiene "
                "el formato esperado."
            )

        return data

    async def get_item(
        self,
        item_id: str,
    ) -> dict[str, Any]:
        """
        Obtiene los detalles de una publicación concreta.
        """

        normalized_id = (
            item_id.strip()
            .upper()
            .replace("-", "")
            .replace("_", "")
        )

        if not normalized_id.startswith("MLM"):
            raise ValueError(
                "El identificador debe comenzar con MLM."
            )

        logger.info(
            f"Consultando publicación: {normalized_id}"
        )

        data = await self._get_json(
            f"/items/{normalized_id}"
        )

        if not isinstance(data, dict):
            raise MercadoLibreAPIError(
                "La publicación no tiene el formato esperado."
            )

        return data

    async def get_seller_item_ids(
        self,
        seller_id: int,
        limit: int = 50,
        offset: int = 0,
        status: str = "active",
    ) -> list[str]:
        """
        Obtiene los identificadores de las publicaciones
        pertenecientes a un vendedor.
        """

        if not 1 <= limit <= 50:
            raise ValueError(
                "El límite debe estar entre 1 y 50."
            )

        if offset < 0:
            raise ValueError(
                "El offset no puede ser negativo."
            )

        logger.info(
            f"Consultando publicaciones del vendedor "
            f"{seller_id}..."
        )

        data = await self._get_json(
            f"/users/{seller_id}/items/search",
            params={
                "status": status,
                "limit": limit,
                "offset": offset,
            },
        )

        if not isinstance(data, dict):
            raise MercadoLibreAPIError(
                "La búsqueda por vendedor no tiene "
                "el formato esperado."
            )

        results = data.get("results", [])

        if not isinstance(results, list):
            raise MercadoLibreAPIError(
                "El campo results no es una lista."
            )

        item_ids = [
            str(item_id)
            for item_id in results
        ]

        logger.info(
            f"Se encontraron {len(item_ids)} "
            "publicaciones del vendedor."
        )

        return item_ids

    async def search_items(
        self,
        keyword: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Búsqueda general.

        Actualmente este recurso devuelve HTTP 403
        para nuestra aplicación, por lo que no será
        la fuente principal del bot.
        """

        keyword = keyword.strip()

        if not keyword:
            raise ValueError(
                "La palabra clave no puede estar vacía."
            )

        data = await self._get_json(
            f"/sites/{self.site_id}/search",
            params={
                "q": keyword,
                "limit": limit,
                "offset": offset,
            },
        )

        if not isinstance(data, dict):
            raise MercadoLibreAPIError(
                "La búsqueda no tiene el formato esperado."
            )

        results = data.get("results", [])

        return (
            results
            if isinstance(results, list)
            else []
        )
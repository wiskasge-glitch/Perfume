from dataclasses import dataclass
from typing import Any

import httpx

from app.config.settings import (
    TELEGRAM_API_BASE_URL,
    TELEGRAM_CHAT_ID,
    TELEGRAM_DISABLE_NOTIFICATION,
    TELEGRAM_TOKEN,
)
from app.notifier.formatter import TelegramOfferMessage
from app.utils.logger import logger


class TelegramClientError(RuntimeError):
    """
    Error producido durante una solicitud a Telegram.
    """

    def __init__(
        self,
        message: str,
        error_code: int | None = None,
    ) -> None:
        super().__init__(message)

        self.error_code = error_code


@dataclass(slots=True, frozen=True)
class TelegramSendResult:
    """
    Resultado de un mensaje enviado correctamente.
    """

    message_id: int
    method: str


class TelegramClient:
    """
    Cliente asíncrono para Telegram Bot API.
    """

    def __init__(
        self,
        token: str = TELEGRAM_TOKEN,
        chat_id: str = TELEGRAM_CHAT_ID,
        api_base_url: str = TELEGRAM_API_BASE_URL,
        disable_notification: bool = (
            TELEGRAM_DISABLE_NOTIFICATION
        ),
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.token = token.strip()
        self.chat_id = chat_id.strip()
        self.disable_notification = (
            disable_notification
        )

        if not self.token:
            raise TelegramClientError(
                "Falta TELEGRAM_TOKEN en el archivo .env."
            )

        if not self.chat_id:
            raise TelegramClientError(
                "Falta TELEGRAM_CHAT_ID en el archivo .env."
            )

        self._api_root = (
            f"{api_base_url.rstrip('/')}"
            f"/bot{self.token}"
        )

        self._owns_client = http_client is None

        self.client = (
            http_client
            or httpx.AsyncClient(
                timeout=30.0,
            )
        )

    async def __aenter__(
        self,
    ) -> "TelegramClient":
        return self

    async def __aexit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """
        Cierra el cliente HTTP si fue creado
        por esta instancia.
        """

        if self._owns_client:
            await self.client.aclose()

    async def _call(
        self,
        method: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Ejecuta un método de Telegram Bot API.
        """

        try:
            response = await self.client.post(
                f"{self._api_root}/{method}",
                json=payload,
            )

        except httpx.RequestError as error:
            raise TelegramClientError(
                "No fue posible conectarse con Telegram."
            ) from error

        try:
            response_data = response.json()

        except ValueError as error:
            raise TelegramClientError(
                "Telegram devolvió una respuesta "
                "que no contiene JSON válido."
            ) from error

        if not isinstance(response_data, dict):
            raise TelegramClientError(
                "Telegram devolvió un formato inesperado."
            )

        telegram_ok = response_data.get(
            "ok",
            False,
        )

        if response.is_error or not telegram_ok:
            error_code_value = response_data.get(
                "error_code",
                response.status_code,
            )

            try:
                error_code = int(error_code_value)

            except (TypeError, ValueError):
                error_code = response.status_code

            description = str(
                response_data.get(
                    "description",
                    "Error desconocido.",
                )
            )

            raise TelegramClientError(
                f"Telegram rechazó {method}: "
                f"{description}",
                error_code=error_code,
            )

        result = response_data.get("result")

        if not isinstance(result, dict):
            raise TelegramClientError(
                f"Telegram respondió correctamente a "
                f"{method}, pero falta el resultado."
            )

        return result

    @staticmethod
    def _create_reply_markup(
        button_text: str | None,
        button_url: str | None,
    ) -> dict[str, Any] | None:
        """
        Crea un botón que abre la publicación.
        """

        if not button_text or not button_url:
            return None

        return {
            "inline_keyboard": [
                [
                    {
                        "text": button_text,
                        "url": button_url,
                    }
                ]
            ]
        }

    @staticmethod
    def _extract_message_id(
        result: dict[str, Any],
    ) -> int:
        """
        Extrae y valida el ID del mensaje enviado.
        """

        message_id = result.get("message_id")

        if not isinstance(message_id, int):
            raise TelegramClientError(
                "Telegram no devolvió un message_id válido."
            )

        return message_id

    async def get_me(self) -> dict[str, Any]:
        """
        Comprueba el token y devuelve información del bot.
        """

        return await self._call(
            method="getMe",
            payload={},
        )

    async def send_text(
        self,
        text: str,
        button_text: str | None = None,
        button_url: str | None = None,
    ) -> TelegramSendResult:
        """
        Envía un mensaje de texto al canal.
        """

        if not text.strip():
            raise ValueError(
                "El mensaje de Telegram está vacío."
            )

        payload: dict[str, Any] = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_notification": (
                self.disable_notification
            ),
        }

        reply_markup = self._create_reply_markup(
            button_text=button_text,
            button_url=button_url,
        )

        if reply_markup:
            payload["reply_markup"] = reply_markup

        result = await self._call(
            method="sendMessage",
            payload=payload,
        )

        return TelegramSendResult(
            message_id=self._extract_message_id(
                result
            ),
            method="sendMessage",
        )

    async def send_offer(
        self,
        message: TelegramOfferMessage,
    ) -> TelegramSendResult:
        """
        Envía una oferta con fotografía cuando exista.

        Si Telegram no puede procesar la fotografía,
        reintenta enviando únicamente texto.
        """

        reply_markup = self._create_reply_markup(
            button_text=message.button_text,
            button_url=message.button_url,
        )

        if message.image_url:
            payload: dict[str, Any] = {
                "chat_id": self.chat_id,
                "photo": message.image_url,
                "caption": message.text,
                "parse_mode": "HTML",
                "disable_notification": (
                    self.disable_notification
                ),
            }

            if reply_markup:
                payload["reply_markup"] = (
                    reply_markup
                )

            try:
                result = await self._call(
                    method="sendPhoto",
                    payload=payload,
                )

                return TelegramSendResult(
                    message_id=(
                        self._extract_message_id(
                            result
                        )
                    ),
                    method="sendPhoto",
                )

            except TelegramClientError as error:
                # Una imagen inválida suele producir HTTP 400.
                # En ese caso conservamos la alerta enviándola
                # como mensaje de texto.
                if error.error_code != 400:
                    raise

                logger.warning(
                    "Telegram no pudo procesar la imagen. "
                    "La oferta se enviará como texto."
                )

        return await self.send_text(
            text=message.text,
            button_text=message.button_text,
            button_url=message.button_url,
        )
import asyncio
import json

import httpx

from app.notifier.formatter import (
    TelegramOfferMessage,
)
from app.notifier.telegram import TelegramClient
from app.utils.logger import logger


async def main() -> None:
    captured_requests: list[
        dict[str, object]
    ] = []

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        payload = json.loads(
            request.content.decode("utf-8")
        )

        captured_requests.append(
            {
                "path": request.url.path,
                "payload": payload,
            }
        )

        return httpx.Response(
            status_code=200,
            json={
                "ok": True,
                "result": {
                    "message_id": 321,
                },
            },
            request=request,
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
    ) as http_client:
        client = TelegramClient(
            token="123456:token_de_prueba",
            chat_id="@canal_de_prueba",
            http_client=http_client,
        )

        message = TelegramOfferMessage(
            text=(
                "🔥 <b>OFERTA DE PRUEBA</b>\n"
                "Versace Eros"
            ),
            button_text="🛒 Ver oferta",
            button_url=(
                "https://example.com/perfume"
            ),
            image_url=None,
        )

        result = await client.send_offer(
            message
        )

    assert result.message_id == 321
    assert result.method == "sendMessage"

    assert len(captured_requests) == 1

    captured = captured_requests[0]

    assert captured["path"].endswith(
        "/sendMessage"
    )

    payload = captured["payload"]

    assert isinstance(payload, dict)
    assert payload["chat_id"] == (
        "@canal_de_prueba"
    )

    assert payload["parse_mode"] == "HTML"

    assert payload["reply_markup"] == {
        "inline_keyboard": [
            [
                {
                    "text": "🛒 Ver oferta",
                    "url": (
                        "https://example.com/perfume"
                    ),
                }
            ]
        ]
    }

    logger.info(
        "Prueba del cliente de Telegram "
        "completada correctamente."
    )


if __name__ == "__main__":
    asyncio.run(main())
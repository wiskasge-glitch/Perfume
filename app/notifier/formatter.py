from dataclasses import dataclass
from html import escape
from urllib.parse import urlparse

from app.engine.offer_scorer import OfferScore
from app.models.perfume import Perfume


# Telegram permite hasta 1024 caracteres en el texto
# que acompaña una fotografía. Dejamos un margen.
MAX_CAPTION_LENGTH = 950


@dataclass(slots=True, frozen=True)
class TelegramOfferMessage:
    """
    Representa un mensaje listo para enviarse a Telegram.
    """

    text: str
    button_text: str
    button_url: str | None
    image_url: str | None


def truncate_text(
    value: str,
    maximum_length: int,
) -> str:
    """
    Recorta un texto sin superar la longitud indicada.
    """

    clean_value = " ".join(value.split())

    if len(clean_value) <= maximum_length:
        return clean_value

    return clean_value[: maximum_length - 1].rstrip() + "…"


def is_http_url(value: str) -> bool:
    """
    Comprueba que una URL utilice HTTP o HTTPS.
    """

    if not value:
        return False

    parsed_url = urlparse(value)

    return (
        parsed_url.scheme in {"http", "https"}
        and bool(parsed_url.netloc)
    )


class TelegramOfferFormatter:
    """
    Convierte un Perfume y su puntuación
    en un mensaje HTML para Telegram.
    """

    def format(
        self,
        perfume: Perfume,
        score: OfferScore,
    ) -> TelegramOfferMessage:
        """
        Construye el mensaje completo de una oferta.
        """

        title = escape(
            truncate_text(
                perfume.title,
                maximum_length=180,
            )
        )

        brand = escape(
            truncate_text(
                perfume.brand or "No identificada",
                maximum_length=60,
            )
        )

        seller = escape(
            truncate_text(
                perfume.seller or "No disponible",
                maximum_length=100,
            )
        )

        score_level = escape(score.level)

        price_line = (
            f"💵 <b>Precio:</b> "
            f"<b>${perfume.price:,.2f} MXN</b>"
        )

        savings_line: str | None = None

        if (
            perfume.original_price is not None
            and perfume.original_price > perfume.price
        ):
            savings = (
                perfume.original_price
                - perfume.price
            )

            price_line = (
                f"💵 <b>Precio:</b> "
                f"<s>${perfume.original_price:,.2f}</s> "
                f"→ <b>${perfume.price:,.2f} MXN</b>"
            )

            savings_line = (
                f"💰 <b>Ahorras:</b> "
                f"${savings:,.2f} MXN"
            )

        lines = [
            "🔥 <b>OFERTA DE PERFUME</b>",
            "",
            f"🧴 <b>{title}</b>",
            f"🏷 <b>Marca:</b> {brand}",
            price_line,
        ]

        if score.effective_discount > 0:
            lines.append(
                f"📉 <b>Descuento:</b> "
                f"{score.effective_discount:.2f}%"
            )

        if savings_line:
            lines.append(savings_line)

        lines.extend(
            [
                f"🏪 <b>Vendedor:</b> {seller}",
                (
                    f"⭐ <b>Score:</b> "
                    f"{score.total:.2f}/100 · "
                    f"{score_level}"
                ),
            ]
        )

        badges: list[str] = []

        if perfume.trusted_seller:
            badges.append("✅ Vendedor confiable")

        if perfume.mercado_lider:
            badges.append("🏅 MercadoLíder")

        if perfume.full:
            badges.append("🚚 FULL")

        if badges:
            lines.extend(
                [
                    "",
                    " • ".join(badges),
                ]
            )

        text = "\n".join(lines)

        if len(text) > MAX_CAPTION_LENGTH:
            raise ValueError(
                "El mensaje generado supera el límite "
                "establecido para Telegram."
            )

        button_url = (
            perfume.url
            if is_http_url(perfume.url)
            else None
        )

        image_url = (
            perfume.image
            if is_http_url(perfume.image)
            else None
        )

        return TelegramOfferMessage(
            text=text,
            button_text="🛒 Ver oferta",
            button_url=button_url,
            image_url=image_url,
        )
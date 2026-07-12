from app.engine.offer_scorer import OfferScorer
from app.models.perfume import Perfume
from app.notifier.formatter import (
    MAX_CAPTION_LENGTH,
    TelegramOfferFormatter,
)
from app.utils.logger import logger


def main() -> None:
    perfume = Perfume(
        ml_id="FORMAT001",
        title="Versace Eros <EDT> & Edición Especial 100 ml",
        brand="Versace",
        price=1200.0,
        original_price=1600.0,
        discount=25.0,
        url="https://example.com/perfume",
        image="https://example.com/perfume.jpg",
        seller="Amora Beauty Market",
        trusted_seller=True,
        mercado_lider=True,
        full=True,
        condition="Nuevo",
    )

    score = OfferScorer().apply(perfume)

    formatter = TelegramOfferFormatter()

    message = formatter.format(
        perfume=perfume,
        score=score,
    )

    assert "&lt;EDT&gt;" in message.text
    assert "&amp;" in message.text
    assert len(message.text) <= MAX_CAPTION_LENGTH

    assert message.button_url == (
        "https://example.com/perfume"
    )

    assert message.image_url == (
        "https://example.com/perfume.jpg"
    )

    logger.info("Mensaje generado:")
    logger.info("\n" + message.text)

    logger.info(
        "Prueba del formateador completada correctamente."
    )


if __name__ == "__main__":
    main()
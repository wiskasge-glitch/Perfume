import re
from dataclasses import dataclass

from app.config.blacklist import BLACKLIST_WORDS
from app.config.sellers import TRUSTED_SELLERS
from app.models.perfume import Perfume
from app.utils.logger import logger
from app.utils.text import normalize_text


SMALL_VOLUME_PATTERN = re.compile(
    r"\b(?:[1-9]|1\d|20)\s*ml\b"
)


@dataclass(slots=True, frozen=True)
class FilterDecision:
    """
    Resultado de evaluar una publicación.
    """

    accepted: bool
    trusted_seller: bool
    reasons: tuple[str, ...]


class PerfumeFilter:
    """
    Filtra publicaciones que no cumplen con las reglas
    establecidas para el bot de perfumes.
    """

    def __init__(self) -> None:
        self._trusted_sellers = {
            normalize_text(seller)
            for seller in TRUSTED_SELLERS
        }

        self._blacklist_words = tuple(
            normalize_text(word)
            for word in BLACKLIST_WORDS
        )

    def is_trusted_seller(
        self,
        seller_name: str,
    ) -> bool:
        """
        Comprueba si el vendedor pertenece a la lista blanca.
        """

        normalized_seller = normalize_text(
            seller_name
        )

        return normalized_seller in self._trusted_sellers

    def evaluate(
        self,
        perfume: Perfume,
    ) -> FilterDecision:
        """
        Evalúa un perfume y devuelve los motivos
        por los que fue aceptado o rechazado.
        """

        reasons: list[str] = []

        normalized_title = normalize_text(
            perfume.title
        )

        normalized_condition = normalize_text(
            perfume.condition
        )

        trusted_seller = self.is_trusted_seller(
            perfume.seller
        )

        if not perfume.title.strip():
            reasons.append(
                "El producto no tiene título."
            )

        if perfume.price <= 0:
            reasons.append(
                "El precio no es válido."
            )

        if not trusted_seller:
            reasons.append(
                "El vendedor no pertenece a la lista blanca."
            )

        if normalized_condition not in {
            "nuevo",
            "new",
        }:
            reasons.append(
                "El producto no está marcado como nuevo."
            )

        forbidden_words = [
            word
            for word in self._blacklist_words
            if word and word in normalized_title
        ]

        if forbidden_words:
            reasons.append(
                "El título contiene palabras prohibidas: "
                + ", ".join(forbidden_words)
            )

        if SMALL_VOLUME_PATTERN.search(
            normalized_title
        ):
            reasons.append(
                "La presentación es de 20 ml o menos."
            )

        return FilterDecision(
            accepted=not reasons,
            trusted_seller=trusted_seller,
            reasons=tuple(reasons),
        )

    def filter_many(
        self,
        perfumes: list[Perfume],
    ) -> list[Perfume]:
        """
        Filtra una lista completa y devuelve únicamente
        las publicaciones aceptadas.
        """

        accepted_perfumes: list[Perfume] = []

        for perfume in perfumes:
            decision = self.evaluate(perfume)

            # Actualizamos este campo con nuestra propia
            # lista blanca, sin confiar en la fuente externa.
            perfume.trusted_seller = (
                decision.trusted_seller
            )

            if decision.accepted:
                accepted_perfumes.append(perfume)

                logger.info(
                    f"ACEPTADO | {perfume.ml_id} | "
                    f"{perfume.title}"
                )

                continue

            logger.warning(
                f"RECHAZADO | {perfume.ml_id} | "
                f"{perfume.title} | "
                f"{' '.join(decision.reasons)}"
            )

        logger.info(
            f"Filtro terminado: "
            f"{len(accepted_perfumes)} de "
            f"{len(perfumes)} publicaciones aceptadas."
        )

        return accepted_perfumes
        
import math
from dataclasses import dataclass
from typing import Mapping

from app.config.scoring import (
    DISCOUNT_SCORE_BANDS,
    FULL_POINTS,
    MERCADO_LIDER_POINTS,
    MIN_ALERT_SCORE,
    MIN_HISTORY_OBSERVATIONS,
    NEW_CONDITION_POINTS,
    REFERENCE_PRICE_POINTS,
    SCORE_LEVELS,
    TRUSTED_SELLER_POINTS,
)
from app.models.perfume import Perfume
from app.utils.logger import logger
from app.utils.text import normalize_text
from app.models.price_history import HistoricalPriceStats





@dataclass(slots=True, frozen=True)
class ScoreBreakdown:
    """
    Desglose de los puntos obtenidos por una oferta.
    """

    trusted_seller: float = 0.0
    discount: float = 0.0
    history: float = 0.0
    mercado_lider: float = 0.0
    full: float = 0.0
    condition: float = 0.0
    reference_price: float = 0.0

    @property
    def total(self) -> float:
        """
        Suma todos los componentes del puntaje.
        """

        value = (
            self.trusted_seller
            + self.discount
            + self.history
            + self.mercado_lider
            + self.full
            + self.condition
            + self.reference_price
        )

        return round(min(max(value, 0.0), 100.0), 2)


@dataclass(slots=True, frozen=True)
class OfferScore:
    """
    Resultado completo de la evaluación.
    """

    total: float
    level: str
    eligible_for_alert: bool
    effective_discount: float
    breakdown: ScoreBreakdown
    reasons: tuple[str, ...]


class OfferScorer:
    """
    Calcula una puntuación de 0 a 100 para una oferta.
    """

    def __init__(
        self,
        minimum_alert_score: float = MIN_ALERT_SCORE,
    ) -> None:
        if not 0 <= minimum_alert_score <= 100:
            raise ValueError(
                "El puntaje mínimo debe estar entre 0 y 100."
            )

        self.minimum_alert_score = minimum_alert_score

    @staticmethod
    def _is_valid_price(
        value: float | None,
    ) -> bool:
        """
        Comprueba que un precio sea positivo y finito.
        """

        return (
            value is not None
            and math.isfinite(value)
            and value > 0
        )

    def _get_effective_discount(
        self,
        perfume: Perfume,
    ) -> float:
        """
        Obtiene el descuento publicado o lo calcula
        usando el precio original.
        """

        if (
            perfume.discount is not None
            and math.isfinite(perfume.discount)
            and 0 <= perfume.discount <= 100
        ):
            return round(perfume.discount, 2)

        if (
            self._is_valid_price(perfume.original_price)
            and self._is_valid_price(perfume.price)
            and perfume.original_price > perfume.price
        ):
            discount = (
                (
                    perfume.original_price
                    - perfume.price
                )
                / perfume.original_price
            ) * 100

            return round(discount, 2)

        return 0.0

    @staticmethod
    def _get_discount_points(
        discount: float,
    ) -> float:
        """
        Asigna puntos según el descuento.
        """

        for minimum_discount, points in DISCOUNT_SCORE_BANDS:
            if discount >= minimum_discount:
                return points

        return 0.0

    def _get_history_points(
        self,
        perfume: Perfume,
        history: HistoricalPriceStats | None,
    ) -> tuple[float, str | None]:
        """
        Compara el precio actual contra el historial.
        """

        if history is None:
            return 0.0, None

        if history.observations < MIN_HISTORY_OBSERVATIONS:
            return 0.0, None

        current_price = perfume.price

        if not self._is_valid_price(current_price):
            return 0.0, None

        if (
            self._is_valid_price(history.lowest_price)
            and current_price <= history.lowest_price
        ):
            return (
                30.0,
                "El precio actual iguala o mejora "
                "el mínimo histórico.",
            )

        if not self._is_valid_price(history.average_price):
            return 0.0, None

        price_ratio = current_price / history.average_price

        if price_ratio <= 0.85:
            return (
                25.0,
                "El precio está al menos 15% debajo "
                "del promedio histórico.",
            )

        if price_ratio <= 0.90:
            return (
                20.0,
                "El precio está al menos 10% debajo "
                "del promedio histórico.",
            )

        if price_ratio <= 0.95:
            return (
                12.0,
                "El precio está al menos 5% debajo "
                "del promedio histórico.",
            )

        if price_ratio < 1.0:
            return (
                6.0,
                "El precio está debajo del promedio histórico.",
            )

        return 0.0, None

    @staticmethod
    def _get_level(
        score: float,
    ) -> str:
        """
        Devuelve la clasificación textual del puntaje.
        """

        for minimum_score, level in SCORE_LEVELS:
            if score >= minimum_score:
                return level

        return "Baja"

    def calculate(
        self,
        perfume: Perfume,
        history: HistoricalPriceStats | None = None,
    ) -> OfferScore:
        """
        Calcula el puntaje sin modificar el objeto Perfume.
        """

        reasons: list[str] = []

        effective_discount = (
            self._get_effective_discount(perfume)
        )

        discount_points = self._get_discount_points(
            effective_discount
        )

        if discount_points > 0:
            reasons.append(
                f"Descuento de {effective_discount:.2f}%."
            )

        trusted_seller_points = 0.0

        if perfume.trusted_seller:
            trusted_seller_points = TRUSTED_SELLER_POINTS
            reasons.append("Vendedor incluido en la lista blanca.")

        mercado_lider_points = 0.0

        if perfume.mercado_lider:
            mercado_lider_points = MERCADO_LIDER_POINTS
            reasons.append("El vendedor es MercadoLíder.")

        full_points = 0.0

        if perfume.full:
            full_points = FULL_POINTS
            reasons.append("La publicación cuenta con envío FULL.")

        condition_points = 0.0

        if normalize_text(perfume.condition) in {
            "nuevo",
            "new",
        }:
            condition_points = NEW_CONDITION_POINTS
            reasons.append("El producto está marcado como nuevo.")

        reference_price_points = 0.0

        if (
            self._is_valid_price(perfume.original_price)
            and perfume.original_price > perfume.price
        ):
            reference_price_points = REFERENCE_PRICE_POINTS
            reasons.append(
                "La publicación incluye un precio anterior válido."
            )

        history_points, history_reason = (
            self._get_history_points(
                perfume=perfume,
                history=history,
            )
        )

        if history_reason:
            reasons.append(history_reason)

        breakdown = ScoreBreakdown(
            trusted_seller=trusted_seller_points,
            discount=discount_points,
            history=history_points,
            mercado_lider=mercado_lider_points,
            full=full_points,
            condition=condition_points,
            reference_price=reference_price_points,
        )

        total = breakdown.total

        return OfferScore(
            total=total,
            level=self._get_level(total),
            eligible_for_alert=(
                total >= self.minimum_alert_score
            ),
            effective_discount=effective_discount,
            breakdown=breakdown,
            reasons=tuple(reasons),
        )

    def apply(
        self,
        perfume: Perfume,
        history: HistoricalPriceStats | None = None,
    ) -> OfferScore:
        """
        Calcula el puntaje y lo guarda en perfume.score.
        """

        result = self.calculate(
            perfume=perfume,
            history=history,
        )

        perfume.score = result.total

        return result

    def score_many(
        self,
        perfumes: list[Perfume],
        history_by_id: Mapping[
            str,
            HistoricalPriceStats,
        ] | None = None,
    ) -> list[tuple[Perfume, OfferScore]]:
        """
        Puntúa varias publicaciones.

        Mantiene el orden original de entrada.
        """

        histories = history_by_id or {}
        results: list[tuple[Perfume, OfferScore]] = []

        for perfume in perfumes:
            result = self.apply(
                perfume=perfume,
                history=histories.get(perfume.ml_id),
            )

            results.append(
                (perfume, result)
            )

            logger.info(
                f"SCORE | {perfume.ml_id} | "
                f"{result.total:.2f}/100 | "
                f"{result.level} | "
                f"Alerta: "
                f"{'sí' if result.eligible_for_alert else 'no'}"
            )

        return results
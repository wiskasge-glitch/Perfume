from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class HistoricalPriceStats:
    """
    Resumen de los precios históricos de un producto.
    """

    lowest_price: float | None = None
    average_price: float | None = None
    observations: int = 0
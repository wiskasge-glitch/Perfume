from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class Perfume:
    """
    Representa una publicación de un perfume.
    Todo el proyecto trabajará con este objeto.
    """

    # Identificador de Mercado Libre
    ml_id: str

    # Información principal
    title: str
    brand: str

    # Precio
    price: float
    original_price: Optional[float] = None
    discount: Optional[float] = None

    # Publicación
    url: str = ""
    image: str = ""

    # Vendedor
    seller: str = ""
    trusted_seller: bool = False

    # Calidad del vendedor
    mercado_lider: bool = False
    full: bool = False

    # Producto
    condition: str = "Nuevo"

    # Fecha en que detectamos la oferta
    detected_at: datetime = field(default_factory=datetime.now)

    # Score de nuestra IA
    score: float = 0.0
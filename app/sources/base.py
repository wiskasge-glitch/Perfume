from typing import Protocol

from app.models.perfume import Perfume


class PerfumeSource(Protocol):
    """
    Contrato que debe cumplir cualquier fuente de perfumes.

    Puede ser Mercado Libre, un archivo local, otra API
    o un proveedor autorizado.
    """

    async def get_perfumes(self) -> list[Perfume]:
        """
        Obtiene publicaciones de perfumes.
        """
        ...
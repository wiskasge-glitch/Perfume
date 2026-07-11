from urllib.parse import quote_plus

from app.config.settings import BASE_URL


class SearchBuilder:
    """
    Construye URLs de búsqueda para Mercado Libre.

    Ejemplo:
        SearchBuilder().keyword("versace eros").build()
    """

    def __init__(self):
        self._keyword = ""
        self._min_price = None
        self._max_price = None

    def keyword(self, text: str):
        self._keyword = text.strip()
        return self

    def min_price(self, value: int):
        self._min_price = value
        return self

    def max_price(self, value: int):
        self._max_price = value
        return self

    def build(self) -> str:

        if not self._keyword:
            raise ValueError("Debe especificar una palabra clave.")

        keyword = quote_plus(self._keyword.replace(" ", "-"))

        url = f"{BASE_URL}/{keyword}"

        params = []

        if self._min_price is not None:
            params.append(f"price={self._min_price}-")

        if self._max_price is not None:

            if self._min_price is None:
                params.append(f"price=0-{self._max_price}")
            else:
                params = [f"price={self._min_price}-{self._max_price}"]

        if params:
            url += "?" + "&".join(params)

        return url
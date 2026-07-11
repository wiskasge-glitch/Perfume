import asyncio
import re

from app.clients.mercadolibre import (
    MercadoLibreAPIError,
    MercadoLibreClient,
)
from app.utils.logger import logger
from urllib.parse import parse_qs, urlparse


ITEM_ID_PATTERN = re.compile(
    r"MLM[-_]?\d+",
    flags=re.IGNORECASE,
)


def normalize_item_id(item_id: str) -> str:
    """
    Normaliza un identificador de publicación de Mercado Libre.
    """

    return (
        item_id.strip()
        .upper()
        .replace("-", "")
        .replace("_", "")
    )


def extract_item_id(value: str) -> str:
    """
    Extrae el identificador de una publicación.

    Prioriza el parámetro `wid`, porque las páginas de catálogo
    pueden contener primero un ID de producto /p/MLM... y después
    el ID real de la publicación en wid=MLM...
    """

    value = value.strip()

    if not value:
        raise ValueError(
            "Debes proporcionar una URL o un identificador MLM."
        )

    # Permite pegar directamente algo como MLM2638718467
    direct_match = ITEM_ID_PATTERN.fullmatch(value)

    if direct_match:
        return normalize_item_id(direct_match.group(0))

    parsed_url = urlparse(value)

    # Mercado Libre puede colocar `wid` en la consulta normal
    # o después del símbolo # dentro del fragmento.
    parameter_groups = [
        parse_qs(parsed_url.query),
        parse_qs(parsed_url.fragment),
    ]

    for parameters in parameter_groups:
        for parameter_name in ("wid", "item_id", "itemId"):
            values = parameters.get(parameter_name)

            if not values:
                continue

            item_match = ITEM_ID_PATTERN.search(values[0])

            if item_match:
                return normalize_item_id(
                    item_match.group(0)
                )

    # Algunas URLs tradicionales contienen directamente
    # el ID de la publicación en la ruta.
    if "/p/" not in parsed_url.path.lower():
        path_match = ITEM_ID_PATTERN.search(
            parsed_url.path
        )

        if path_match:
            return normalize_item_id(
                path_match.group(0)
            )

    raise ValueError(
        "La URL parece corresponder a un producto de catálogo, "
        "pero no contiene el parámetro wid con la publicación real."
    )

    return (
        match.group(0)
        .upper()
        .replace("-", "")
        .replace("_", "")
    )


async def main() -> None:
    value = input(
        "Pega la URL de una publicación "
        "del vendedor confiable:\n\n"
    ).strip()

    try:
        item_id = extract_item_id(value)

        async with MercadoLibreClient() as client:
            item = await client.get_item(item_id)

            seller_id = item.get("seller_id")

            if seller_id is None:
                raise MercadoLibreAPIError(
                    "La publicación no contiene seller_id."
                )

            seller = await client.get_user(
                int(seller_id)
            )

            print("\nVendedor encontrado")
            print("-------------------")
            print(
                f"Publicación: {item.get('title')}"
            )
            print(
                f"Item ID: {item.get('id')}"
            )
            print(
                f"Seller ID: {seller_id}"
            )
            print(
                f"Nickname: {seller.get('nickname')}"
            )
            print(
                f"Estado: {seller.get('status', {}).get('site_status')}"
            )

    except (
        ValueError,
        MercadoLibreAPIError,
    ) as error:
        logger.error(str(error))


if __name__ == "__main__":
    asyncio.run(main())
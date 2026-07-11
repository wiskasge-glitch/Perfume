import asyncio
import hmac
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dotenv import set_key

from app.clients.mercadolibre_oauth import (
    MercadoLibreOAuth,
    MercadoLibreOAuthError,
)


ENV_FILE = Path(".env")


def get_query_value(
    parameters: dict[str, list[str]],
    key: str,
) -> str | None:
    values = parameters.get(key)

    if not values:
        return None

    return values[0]


async def main() -> None:
    if not ENV_FILE.exists():
        raise FileNotFoundError(
            "No se encontró el archivo .env "
            "en la raíz del proyecto."
        )

    oauth = MercadoLibreOAuth()

    authorization_url, expected_state, verifier = (
        oauth.create_authorization_request()
    )

    print("\nAbriendo Mercado Libre en el navegador...\n")
    print("URL de autorización:\n")
    print(authorization_url)
    print()

    webbrowser.open(authorization_url)

    redirected_url = input(
        "Después de autorizar la aplicación, "
        "pega aquí la URL completa a la que te redirigió:\n\n"
    ).strip()

    query_parameters = parse_qs(
        urlparse(redirected_url).query
    )

    oauth_error = get_query_value(
        query_parameters,
        "error",
    )

    if oauth_error:
        description = get_query_value(
            query_parameters,
            "error_description",
        )

        raise MercadoLibreOAuthError(
            f"Autorización rechazada: {oauth_error}. "
            f"{description or ''}"
        )

    received_state = get_query_value(
        query_parameters,
        "state",
    )

    if not received_state:
        raise MercadoLibreOAuthError(
            "La URL no contiene el parámetro state."
        )

    if not hmac.compare_digest(
        received_state,
        expected_state,
    ):
        raise MercadoLibreOAuthError(
            "El parámetro state no coincide. "
            "La autorización fue cancelada por seguridad."
        )

    code = get_query_value(
        query_parameters,
        "code",
    )

    if not code:
        raise MercadoLibreOAuthError(
            "La URL no contiene el código de autorización."
        )

    tokens = await oauth.exchange_code(
        code=code,
        code_verifier=verifier,
    )

    set_key(
        str(ENV_FILE),
        "ML_ACCESS_TOKEN",
        tokens.access_token,
    )

    if tokens.refresh_token:
        set_key(
            str(ENV_FILE),
            "ML_REFRESH_TOKEN",
            tokens.refresh_token,
        )

    print("\nAutenticación completada correctamente.")
    print("Los tokens fueron guardados en .env.")
    print(f"Vigencia informada: {tokens.expires_in} segundos.")

    if tokens.user_id is not None:
        print(f"Usuario autorizado: {tokens.user_id}")

    print(
        "\nCierra y vuelve a abrir la terminal antes "
        "de ejecutar las pruebas de la API."
    )


if __name__ == "__main__":
    asyncio.run(main())
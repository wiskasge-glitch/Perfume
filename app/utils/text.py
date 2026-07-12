import re
import unicodedata


NON_ALPHANUMERIC_PATTERN = re.compile(
    r"[^a-z0-9]+"
)


def normalize_text(value: str) -> str:
    """
    Normaliza un texto para facilitar comparaciones.

    - Convierte a minúsculas.
    - Elimina acentos.
    - Sustituye símbolos por espacios.
    - Elimina espacios repetidos.
    """

    if not value:
        return ""

    normalized = unicodedata.normalize(
        "NFKD",
        value,
    )

    without_accents = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    lowercase_text = without_accents.casefold()

    clean_text = NON_ALPHANUMERIC_PATTERN.sub(
        " ",
        lowercase_text,
    )

    return " ".join(clean_text.split())
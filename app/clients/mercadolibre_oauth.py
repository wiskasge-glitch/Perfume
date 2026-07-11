import base64
import hashlib
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config.settings import (
    ML_AUTH_URL,
    ML_CLIENT_ID,
    ML_CLIENT_SECRET,
    ML_REDIRECT_URI,
    ML_TOKEN_URL,
)


class MercadoLibreOAuthError(RuntimeError):
    """
    Error producido durante la autenticación OAuth.
    """


@dataclass(slots=True, frozen=True)
class PKCEPair:
    verifier: str
    challenge: str


@dataclass(slots=True, frozen=True)
class OAuthTokens:
    access_token: str
    refresh_token: str | None
    token_type: str
    expires_in: int
    scope: str | None
    user_id: int | None

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
    ) -> "OAuthTokens":
        access_token = payload.get("access_token")

        if not access_token:
            raise MercadoLibreOAuthError(
                "La respuesta no contiene access_token."
            )

        return cls(
            access_token=str(access_token),
            refresh_token=payload.get("refresh_token"),
            token_type=str(payload.get("token_type", "Bearer")),
            expires_in=int(payload.get("expires_in", 0)),
            scope=payload.get("scope"),
            user_id=payload.get("user_id"),
        )


class MercadoLibreOAuth:
    """
    Gestiona el flujo OAuth 2.0 con PKCE.
    """

    def __init__(
        self,
        client_id: str = ML_CLIENT_ID,
        client_secret: str = ML_CLIENT_SECRET,
        redirect_uri: str = ML_REDIRECT_URI,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        self._validate_configuration()

    def _validate_configuration(self) -> None:
        missing = []

        if not self.client_id:
            missing.append("ML_CLIENT_ID")

        if not self.client_secret:
            missing.append("ML_CLIENT_SECRET")

        if not self.redirect_uri:
            missing.append("ML_REDIRECT_URI")

        if missing:
            raise MercadoLibreOAuthError(
                "Faltan variables en .env: "
                + ", ".join(missing)
            )

    @staticmethod
    def generate_pkce_pair() -> PKCEPair:
        """
        Genera el code_verifier y code_challenge de PKCE.
        """

        verifier = secrets.token_urlsafe(64)

        digest = hashlib.sha256(
            verifier.encode("utf-8")
        ).digest()

        challenge = (
            base64.urlsafe_b64encode(digest)
            .rstrip(b"=")
            .decode("ascii")
        )

        return PKCEPair(
            verifier=verifier,
            challenge=challenge,
        )

    def create_authorization_request(
        self,
    ) -> tuple[str, str, str]:
        """
        Devuelve:

        - URL de autorización
        - state
        - code_verifier
        """

        state = secrets.token_urlsafe(32)
        pkce = self.generate_pkce_pair()

        parameters = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "code_challenge": pkce.challenge,
            "code_challenge_method": "S256",
        }

        authorization_url = (
            f"{ML_AUTH_URL}?{urlencode(parameters)}"
        )

        return authorization_url, state, pkce.verifier

    async def exchange_code(
        self,
        code: str,
        code_verifier: str,
    ) -> OAuthTokens:
        """
        Intercambia el código temporal por tokens.
        """

        form_data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "code_verifier": code_verifier,
        }

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.post(
                ML_TOKEN_URL,
                data=form_data,
                headers={
                    "Accept": "application/json",
                },
            )

        if response.is_error:
            raise MercadoLibreOAuthError(
                "Mercado Libre rechazó el intercambio "
                f"del código: HTTP {response.status_code} - "
                f"{response.text[:500]}"
            )

        return OAuthTokens.from_payload(
            response.json()
        )

    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> OAuthTokens:
        """
        Renueva el access token.
        """

        if not refresh_token:
            raise MercadoLibreOAuthError(
                "El refresh token está vacío."
            )

        form_data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.post(
                ML_TOKEN_URL,
                data=form_data,
                headers={
                    "Accept": "application/json",
                },
            )

        if response.is_error:
            raise MercadoLibreOAuthError(
                "No fue posible renovar el token: "
                f"HTTP {response.status_code} - "
                f"{response.text[:500]}"
            )

        return OAuthTokens.from_payload(
            response.json()
        )
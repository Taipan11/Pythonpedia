
"""Authentification des routes administratives de Pythonpédia."""

import hmac

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import get_settings


api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


def require_admin(
    key: str | None = Security(api_key_header),
) -> None:
    """Vérifie la clé administrateur configurée."""

    settings = get_settings()

    # SecretStr protège la représentation de la clé.
    expected = (
        settings.ADMIN_API_KEY.get_secret_value()
        if settings.ADMIN_API_KEY is not None
        else None
    )

    if (
        not expected
        or not key
        or not hmac.compare_digest(key, expected)
    ):
        raise HTTPException(
            status_code=403,
            detail="Accès administrateur refusé",
        )

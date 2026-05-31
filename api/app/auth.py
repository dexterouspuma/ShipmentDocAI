"""Entra ID (Azure AD) bearer-token auth.

In local mode auth is bypassed and a fake analyst identity is returned, so you can
develop without an Entra tenant. In dev/prod, the JWT is validated against the
tenant's JWKS and audience. Routers depend on `current_user`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings

_bearer = HTTPBearer(auto_error=False)


@dataclass
class User:
    id: str
    name: str
    email: Optional[str] = None


def current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> User:
    if settings.is_local:
        return User(id="local-analyst", name="Local Analyst", email="analyst@local")

    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    claims = _validate_token(creds.credentials)
    return User(
        id=claims.get("oid") or claims.get("sub", "unknown"),
        name=claims.get("name", "Unknown"),
        email=claims.get("preferred_username") or claims.get("email"),
    )


def _validate_token(token: str) -> dict:
    """Validate an Entra ID JWT against the tenant JWKS + audience."""
    import jwt
    from jwt import PyJWKClient

    tenant = settings.entra_tenant_id
    jwks_url = f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
    issuer = f"https://login.microsoftonline.com/{tenant}/v2.0"
    try:
        signing_key = PyJWKClient(jwks_url).get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.entra_api_audience or settings.entra_api_client_id,
            issuer=issuer,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {exc}") from exc

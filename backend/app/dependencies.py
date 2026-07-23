from functools import lru_cache
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import create_client, Client
from app.config import settings

_bearer = HTTPBearer()


@lru_cache(maxsize=1)
def _anon_client() -> Client:
    """Anon key client - used for sign_up / sign_in (respects RLS)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


@lru_cache(maxsize=1)
def _admin_client() -> Client:
    """Service-role client - bypasses RLS for server-side reads/writes."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def anon_client() -> Client:
    return _anon_client()


def admin_client() -> Client:
    return _admin_client()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> dict:
    """FastAPI dependency - validates Bearer JWT and returns the Supabase user dict."""
    token = credentials.credentials
    try:
        response = _admin_client().auth.get_user(token)
        if response.user is None:
            raise ValueError("no user")
        return {"id": response.user.id, "email": response.user.email}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

"""
core/auth.py — JWT Authentication
===================================
Simple JWT-based auth.
Provides:
  - create_access_token()   → used in login endpoint (add your own auth router)
  - get_current_user()      → FastAPI dependency for protected routes
  - User dataclass          → minimal user object injected into route handlers

For production: replace with your IdP (Auth0, Clerk, Supabase Auth, etc.)
For development: use the /dev/token endpoint to get a test JWT.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from core.config import settings

# FastAPI security scheme — reads "Authorization: Bearer <token>"
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class User:
    id: str
    email: str
    is_admin: bool = False


# ─── Token creation ───────────────────────────────────────────────────────────

def create_access_token(
    user_id: str,
    email: str,
    is_admin: bool = False,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": user_id,
        "email": email,
        "is_admin": is_admin,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ─── Token verification ───────────────────────────────────────────────────────

def decode_token(token: str) -> dict:
    """Decode and validate JWT. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        if payload.get("sub") is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject claim.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─── FastAPI dependency ───────────────────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> User:
    """
    FastAPI dependency. Inject into any route that needs authentication:

        @router.get("/protected")
        async def my_route(user = Depends(get_current_user)):
            ...

    In DEBUG mode (settings.DEBUG=True), returns a hardcoded dev user
    so you don't need a token during local development.
    """
    if settings.DEBUG:
        # Dev shortcut — no token needed locally
        return User(id="dev-user-001", email="dev@localhost", is_admin=True)

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    return User(
        id=payload["sub"],
        email=payload.get("email", ""),
        is_admin=payload.get("is_admin", False),
    )


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency that additionally checks for admin role."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user

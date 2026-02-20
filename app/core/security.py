from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings

# Build user store once at import time from USERS_SEED env var
USER_STORE: dict[str, bytes] = {}
if settings.USERS_SEED:
    for pair in settings.USERS_SEED.split(","):
        pair = pair.strip()
        if ":" in pair:
            username, password = pair.split(":", 1)
            USER_STORE[username.strip()] = bcrypt.hashpw(
                password.strip().encode(), bcrypt.gensalt()
            )


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta is not None
        else timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        sub: str = payload.get("sub")
        if sub is None:
            raise credentials_exception
        return sub
    except JWTError:
        raise credentials_exception


def authenticate_user(username: str, password: str) -> Optional[str]:
    hashed = USER_STORE.get(username)
    if not hashed:
        return None
    if not bcrypt.checkpw(password.encode(), hashed):
        return None
    return username

from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from secrets import token_bytes
from typing import Any

import jwt
from passlib.context import CryptContext

from django.conf import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PBKDF2_SCHEME = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 390_000
PBKDF2_SALT_BYTES = 16


def _derive_pbkdf2(password: str, salt: bytes, iterations: int) -> bytes:
    return pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith(f"{PBKDF2_SCHEME}$"):
        try:
            _, iterations_raw, salt_encoded, digest_encoded = hashed_password.split("$", 3)
            iterations = int(iterations_raw)
            salt = urlsafe_b64decode(salt_encoded.encode("ascii"))
            expected_digest = urlsafe_b64decode(digest_encoded.encode("ascii"))
        except (TypeError, ValueError):
            return False
        derived_digest = _derive_pbkdf2(plain_password, salt, iterations)
        return compare_digest(derived_digest, expected_digest)

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    salt = token_bytes(PBKDF2_SALT_BYTES)
    digest = _derive_pbkdf2(password, salt, PBKDF2_ITERATIONS)
    salt_encoded = urlsafe_b64encode(salt).decode("ascii")
    digest_encoded = urlsafe_b64encode(digest).decode("ascii")
    return f"{PBKDF2_SCHEME}${PBKDF2_ITERATIONS}${salt_encoded}${digest_encoded}"


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    expires_delta = timedelta(minutes=settings.WORKFLOW_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

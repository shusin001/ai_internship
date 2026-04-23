import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Optional
import logging

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

logger = logging.getLogger(__name__)

# Prefer pbkdf2_sha256 for broad compatibility across local Python builds.
# bcrypt remains enabled for compatibility if hashes already exist.
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def sanitize_text(value: Optional[str], fallback: str = "Unknown") -> str:
    if not value:
        return fallback
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned or fallback


def parse_salary_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        numeric = re.sub(r"[^0-9.]", "", value)
        if not numeric:
            return None
        try:
            return float(numeric)
        except ValueError:
            return None
    return None


def parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                parsed = parsedate_to_datetime(value)
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                return None
    return None


def serialize_mongo_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    serialized = {**doc}
    if "_id" in serialized:
        serialized["_id"] = str(serialized["_id"])
    return serialized


def hash_password(password: str) -> str:
    # Explicit scheme avoids bcrypt backend issues on some local environments.
    return pwd_context.hash(password, scheme="pbkdf2_sha256")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(password, hashed_password)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Password verification failed due to hash backend error: %s", exc)
        return False


def create_access_token(subject: str) -> str:
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not configured.")
    expire = utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not configured.")
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        subject = payload.get("sub")
        if not subject:
            raise JWTError("Missing subject")
        return subject
    except JWTError as exc:
        raise ValueError("Invalid or expired token.") from exc

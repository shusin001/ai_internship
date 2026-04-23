"""Utility helpers for the resume intelligence module."""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

MAX_RESUME_BYTES = 5 * 1024 * 1024


@lru_cache(maxsize=1)
def load_skill_dictionary() -> List[str]:
    """Load predefined skills from the local JSON dictionary."""
    path = Path(__file__).with_name("skills_dictionary.json")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        skills = payload.get("skills", [])
        normalized = sorted({str(skill).strip().lower() for skill in skills if str(skill).strip()})
        return normalized
    except Exception as exc:  # pragma: no cover - defensive file parsing
        logger.error("Failed to load skill dictionary: %s", exc)
        return []


@lru_cache(maxsize=1)
def get_spacy_nlp():
    """Load spaCy pipeline once per process with graceful fallback.

    Attempts to load `en_core_web_sm` for noun phrase extraction. If unavailable,
    it falls back to a blank English pipeline so the service remains operational.
    """
    try:
        import spacy
    except ImportError as exc:  # pragma: no cover - dependency check
        raise RuntimeError("spaCy is not installed.") from exc

    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        logger.warning("spaCy model en_core_web_sm not found; using blank English pipeline fallback.")
        return spacy.blank("en")


def sanitize_email(email: str) -> str:
    """Normalize email for storage consistency."""
    return email.strip().lower()


def validate_pdf_file(filename: Optional[str], content_type: Optional[str], file_bytes: bytes) -> None:
    """Validate file extension, MIME type, and max size for uploaded resumes."""
    safe_name = (filename or "").strip().lower()
    safe_type = (content_type or "").strip().lower()

    if not safe_name.endswith(".pdf"):
        raise ValueError("Only PDF files are allowed.")

    if safe_type and "pdf" not in safe_type:
        raise ValueError("Invalid content type. Only PDF files are allowed.")

    if len(file_bytes) > MAX_RESUME_BYTES:
        raise ValueError("Resume file exceeds the 5MB limit.")


def serialize_document(doc: Dict) -> Dict:
    """Convert MongoDB ObjectId to string for API responses."""
    serialized = dict(doc)
    if "_id" in serialized:
        serialized["_id"] = str(serialized["_id"])
    return serialized

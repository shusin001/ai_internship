from datetime import datetime, timezone
from typing import Any, Dict, Optional


def build_user_document(
    email: str,
    hashed_password: str,
    full_name: Optional[str] = None,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "email": email.lower().strip(),
        "hashed_password": hashed_password,
        "full_name": full_name,
        "saved_jobs": [],
        "resume_uploaded": False,
        "created_at": now,
        "updated_at": now,
    }

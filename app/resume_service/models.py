"""Document builders for resume profile persistence."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def build_resume_profile_document(
    user_id: str,
    name: Optional[str],
    email: str,
    raw_text: str,
    extracted_sections: Dict[str, Optional[str]],
    extracted_skills: List[str],
    certifications: List[str],
    projects: List[str],
    experience_years_estimated: Optional[float],
) -> Dict[str, Any]:
    """Build normalized resume_profiles document payload."""
    now = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "name": name,
        "email": email,
        "raw_text": raw_text,
        "extracted_sections": {
            "skills": extracted_sections.get("skills"),
            "certifications": extracted_sections.get("certifications"),
            "experience": extracted_sections.get("experience"),
            "projects": extracted_sections.get("projects"),
            "summary": extracted_sections.get("summary"),
        },
        "extracted_skills": extracted_skills,
        "certifications": certifications,
        "projects": projects,
        "experience_years_estimated": experience_years_estimated,
        "recommendation_cache": [],
        "created_at": now,
        "updated_at": now,
    }

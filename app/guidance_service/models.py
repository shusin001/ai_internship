"""Document builders for optional guidance report persistence."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def build_guidance_report_document(
    user_id: str,
    job_id: str,
    missing_skills: List[str],
    gap_percentage: float,
    roadmap: Dict[str, List[str]],
    strategy: Dict[str, Any],
    resource_links: List[Dict[str, str]],
    llm_refined: bool,
    llm_summary: Optional[str],
    llm_daily_remaining: int,
) -> Dict[str, Any]:
    """Create normalized guidance_reports payload."""
    return {
        "user_id": user_id,
        "job_id": job_id,
        "missing_skills": missing_skills,
        "gap_percentage": gap_percentage,
        "roadmap": roadmap,
        "strategy": strategy,
        "resource_links": resource_links,
        "llm_refined": llm_refined,
        "llm_summary": llm_summary,
        "llm_daily_remaining": llm_daily_remaining,
        "created_at": datetime.now(timezone.utc),
    }

from datetime import datetime, timezone
from typing import Any, Dict


def build_job_document(job_data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "title": job_data.get("title"),
        "company": job_data.get("company"),
        "location": job_data.get("location"),
        "description": job_data.get("description"),
        "salary_min": job_data.get("salary_min"),
        "salary_max": job_data.get("salary_max"),
        "employment_type": job_data.get("employment_type"),
        "source": job_data.get("source"),
        "posted_date": job_data.get("posted_date"),
        "url": job_data.get("url"),
        "created_at": job_data.get("created_at", now),
        "updated_at": now,
    }

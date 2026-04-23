"""Helpers for scraping/injection service query shaping and text sanitation."""

from typing import List

from app.guidance_service.utils import unique_preserve_order


def build_job_search_query(extracted_skills: List[str], summary_text: str = "") -> str:
    """Build a concise query from resume profile data for job scraping.

    Prioritizes top skills and summary hints to keep SerpAPI query relevant.
    """
    skills = unique_preserve_order([skill.strip() for skill in extracted_skills if skill and skill.strip()])
    top_skills = skills[:3]

    summary_seed = ""
    if summary_text:
        summary_seed = " ".join(summary_text.split()[:4])

    if top_skills:
        return "{} jobs {}".format(" ".join(top_skills), summary_seed).strip()

    if summary_seed:
        return "{} jobs".format(summary_seed).strip()

    return "entry level jobs"


def safe_text(value) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


def _infer_role_hints(extracted_skills: List[str], summary_text: str = "") -> List[str]:
    normalized = {skill.strip().lower() for skill in extracted_skills if isinstance(skill, str) and skill.strip()}
    summary_lc = (summary_text or "").lower()
    combined = " ".join(sorted(normalized)) + " " + summary_lc

    hints: List[str] = []
    if any(token in combined for token in ["etl", "airflow", "spark", "data engineering", "warehouse"]):
        hints.extend(["data engineer jobs", "etl developer jobs", "analytics engineer jobs"])
    if any(token in combined for token in ["python", "django", "flask", "fastapi", "backend"]):
        hints.extend(["python developer jobs", "backend developer jobs"])
    if any(token in combined for token in ["sql", "tableau", "power bi", "analyst"]):
        hints.extend(["data analyst jobs", "business analyst jobs"])
    if any(token in combined for token in ["react", "frontend", "javascript", "typescript"]):
        hints.extend(["frontend developer jobs", "full stack developer jobs"])
    if any(token in combined for token in ["aws", "azure", "gcp", "docker", "kubernetes", "devops"]):
        hints.extend(["devops engineer jobs", "cloud engineer jobs"])

    if not hints:
        hints.extend(["software engineer jobs", "analyst jobs"])
    return unique_preserve_order(hints)


def build_query_candidates(extracted_skills: List[str], summary_text: str = "") -> List[str]:
    """Create prioritized fallback query candidates for resilient SerpAPI fetching."""
    primary = build_job_search_query(extracted_skills=extracted_skills, summary_text=summary_text)
    role_hints = _infer_role_hints(extracted_skills=extracted_skills, summary_text=summary_text)

    generic_fallback = [
        "software engineer jobs",
        "data analyst jobs",
        "project manager jobs",
        "operations specialist jobs",
        "entry level jobs",
    ]

    return unique_preserve_order([primary] + role_hints + generic_fallback)

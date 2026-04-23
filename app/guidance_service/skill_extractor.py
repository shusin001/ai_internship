"""Job skill extraction for the guidance service."""

from typing import Any, Dict, List

from app.guidance_service.utils import (
    extract_skills_from_text,
    get_shared_skill_dictionary,
    unique_preserve_order,
)

ROLE_HINT_SKILLS: Dict[str, List[str]] = {
    "data engineer": ["python", "sql", "etl", "spark", "airflow", "data engineering"],
    "data scientist": ["python", "machine learning", "pandas", "numpy", "scikit-learn", "sql"],
    "backend engineer": ["python", "sql", "rest api", "docker", "git"],
    "backend developer": ["python", "sql", "rest api", "docker", "git"],
    "full stack": ["javascript", "react", "node.js", "sql", "git"],
    "devops engineer": ["docker", "kubernetes", "terraform", "linux", "ci/cd", "aws"],
    "general engineer": ["problem solving", "system design", "project management", "communication"],
    "lead engineer": ["leadership", "problem solving", "system design", "project management", "communication"],
    "systems engineer": ["system design", "problem solving", "project management", "communication"],
    "mechanical engineer": ["problem solving", "project management", "communication"],
    "civil engineer": ["problem solving", "project management", "communication"],
    "electrical engineer": ["problem solving", "project management", "communication"],
    # Non-tech / operations-heavy roles
    "air traffic control": ["communication", "problem solving", "leadership", "project management"],
    "traffic management": ["communication", "problem solving", "project management"],
    "operations specialist": ["communication", "problem solving", "project management"],
    "manager": ["communication", "leadership", "project management", "problem solving"],
    "management": ["communication", "leadership", "project management"],
    "program manager": ["communication", "leadership", "project management"],
    "project coordinator": ["communication", "project management", "leadership"],
    "case administrator": ["communication", "problem solving", "project management"],
    "administrator": ["communication", "project management", "problem solving"],
    "analyst": ["data analysis", "problem solving", "communication"],
    "representative": ["communication", "problem solving"],
    "administrative officer": ["communication", "project management"],
    "logistics specialist": ["communication", "problem solving", "project management"],
    "compliance officer": ["communication", "project management", "problem solving"],
}

KEYWORD_HINTS: Dict[str, List[str]] = {
    "pipeline": ["etl", "data engineering"],
    "pipelines": ["etl", "data engineering"],
    "transforming data": ["etl", "data engineering"],
    "data platform": ["data engineering", "sql"],
    "engineering": ["problem solving", "system design"],
    "technical": ["problem solving", "communication"],
    "design": ["system design"],
    "systems": ["system design", "problem solving"],
    "analysis": ["data analysis", "problem solving"],
    "stakeholders": ["communication", "project management"],
    # Non-tech keyword hints
    "traffic management": ["communication", "project management", "problem solving"],
    "air traffic": ["communication", "problem solving"],
    "coordinator": ["communication", "project management"],
    "operations": ["communication", "problem solving"],
    "cross-functional": ["communication", "leadership"],
    "stakeholder": ["communication", "project management"],
    "mission-critical": ["problem solving", "leadership"],
    "management": ["leadership", "project management"],
    "reporting": ["communication", "project management"],
    "planning": ["project management", "problem solving"],
    "audit": ["data analysis", "excel"],
}


def extract_job_skills(job_document: Dict[str, Any]) -> List[str]:
    """Extract detectable skills from a job document.

    Uses the shared resume skill dictionary and keyword matching over title,
    description, company, location, and employment type.
    """
    dictionary = get_shared_skill_dictionary()

    title = str(job_document.get("title") or "")
    description = str(job_document.get("description") or "")
    employment_type = str(job_document.get("employment_type") or "")
    company = str(job_document.get("company") or "")
    location = str(job_document.get("location") or "")

    combined = "\n".join([title, company, location, employment_type, description])
    combined_lc = combined.lower()
    title_lc = title.lower()

    detected = extract_skills_from_text(combined, dictionary)
    inferred: List[str] = []

    for role_key, skills in ROLE_HINT_SKILLS.items():
        if role_key in title_lc or role_key in combined_lc:
            inferred.extend(skills)

    for keyword, skills in KEYWORD_HINTS.items():
        if keyword in combined_lc:
            inferred.extend(skills)

    valid_dictionary_skills = set(dictionary)
    inferred = [skill for skill in inferred if skill in valid_dictionary_skills]

    extracted = unique_preserve_order(detected + inferred)

    # Last-resort fallback for non-tech job postings with sparse descriptions.
    if not extracted:
        fallback: List[str] = []
        if any(token in combined_lc for token in ["specialist", "coordinator", "officer", "manager", "administrator", "analyst", "representative"]):
            fallback.extend(["communication", "project management", "leadership"])
        if "engineer" in combined_lc:
            fallback.extend(["problem solving", "system design", "project management", "communication"])
        if any(token in combined_lc for token in ["critical", "operations", "monitor", "incident", "control"]):
            fallback.extend(["problem solving"])
        extracted = unique_preserve_order(fallback)

    return extracted

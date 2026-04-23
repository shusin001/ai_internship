"""Preparation strategy builder based on gap results."""

from typing import Dict, List


def _estimate_time(gap_percentage: float) -> str:
    if gap_percentage < 30:
        return "1-2 months"
    if gap_percentage <= 60:
        return "3-4 months"
    return "6+ months"


def build_preparation_strategy(gap_percentage: float, categorized_missing_skills: Dict[str, List[str]]) -> Dict:
    """Build practical strategy with project and certification suggestions."""
    project_suggestions: List[str] = []

    if categorized_missing_skills.get("frameworks"):
        project_suggestions.append("Build an end-to-end web app aligned with target job responsibilities")
    if categorized_missing_skills.get("cloud"):
        project_suggestions.append("Deploy one project to cloud with monitoring and basic CI/CD")
    if categorized_missing_skills.get("databases"):
        project_suggestions.append("Design and implement a data-intensive project with optimized queries")
    if categorized_missing_skills.get("devops"):
        project_suggestions.append("Containerize and automate deployment for one portfolio project")
    if not project_suggestions:
        project_suggestions.append("Create one job-aligned project and document architecture decisions")

    certification_suggestions: List[str] = []
    if categorized_missing_skills.get("cloud"):
        certification_suggestions.append("AWS Cloud Practitioner or Azure Fundamentals")
    if categorized_missing_skills.get("databases"):
        certification_suggestions.append("MongoDB Associate Developer or SQL-focused certification")
    if categorized_missing_skills.get("devops"):
        certification_suggestions.append("Docker and Kubernetes fundamentals certification path")
    if categorized_missing_skills.get("frameworks"):
        certification_suggestions.append("Framework-specific professional certification (if available)")
    if not certification_suggestions:
        certification_suggestions.append("No certification required; prioritize practical project outcomes")

    return {
        "estimated_time": _estimate_time(gap_percentage),
        "project_suggestions": project_suggestions,
        "certification_suggestions": certification_suggestions,
    }

"""Skill gap analysis utilities.

This module avoids unstable 0/100 outputs on sparse job-skill sets by using:
1) Smoothed skill match ratio (Bayesian-style smoothing)
2) Optional semantic similarity blending

Formulas:
    raw_match = matched_skill_count / total_job_skills
    smoothed_match = (matched_skill_count + 1) / (total_job_skills + 2)
    current_match_score = weighted(skill_match, semantic_similarity)
    gap_percentage = (1 - current_match_score) * 100
"""

from typing import Dict, List

from app.guidance_service.utils import normalize_skills


def analyze_skill_gap(
    resume_skills: List[str],
    job_skills: List[str],
    semantic_similarity: float = 0.0,
) -> Dict:
    """Compute matched/missing skill sets and a stabilized gap score."""
    resume_set = set(normalize_skills(resume_skills))
    job_ordered = normalize_skills(job_skills)
    job_set = set(job_ordered)

    matched = [skill for skill in job_ordered if skill in resume_set]
    missing = [skill for skill in job_ordered if skill not in resume_set]

    total_job_skills = len(job_set)
    matched_count = len(set(matched))
    missing_count = len(set(missing))

    semantic_similarity = max(0.0, min(1.0, float(semantic_similarity or 0.0)))

    if total_job_skills == 0:
        gap_percentage = 0.0
        current_match_score = 0.0
    else:
        raw_match = matched_count / float(total_job_skills)
        smoothed_match = (matched_count + 1.0) / float(total_job_skills + 2.0)

        if total_job_skills <= 3:
            skill_match = smoothed_match
            semantic_weight = 0.20
        elif total_job_skills <= 6:
            skill_match = (0.5 * raw_match) + (0.5 * smoothed_match)
            semantic_weight = 0.15
        else:
            skill_match = raw_match
            semantic_weight = 0.10

        blended_match = ((1.0 - semantic_weight) * skill_match) + (semantic_weight * semantic_similarity)
        current_match_score = round(max(0.0, min(1.0, blended_match)), 4)
        gap_percentage = round((1.0 - current_match_score) * 100.0, 2)

    return {
        "total_job_skills": total_job_skills,
        "matched_skills": matched_count,
        "missing_skills": missing,
        "gap_percentage": gap_percentage,
        "current_match_score": current_match_score,
    }

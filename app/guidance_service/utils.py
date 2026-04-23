"""Utility helpers for guidance analysis and formatting."""

import re
from typing import Dict, List

from app.resume_service.utils import load_skill_dictionary

SKILL_CATEGORY_MAP: Dict[str, str] = {
    # Programming Languages
    "python": "programming_languages",
    "java": "programming_languages",
    "javascript": "programming_languages",
    "typescript": "programming_languages",
    "c": "programming_languages",
    "c++": "programming_languages",
    "c#": "programming_languages",
    "golang": "programming_languages",
    "rust": "programming_languages",
    "kotlin": "programming_languages",
    "swift": "programming_languages",

    # Frameworks
    "react": "frameworks",
    "next.js": "frameworks",
    "vue": "frameworks",
    "angular": "frameworks",
    "node.js": "frameworks",
    "express": "frameworks",
    "fastapi": "frameworks",
    "django": "frameworks",
    "flask": "frameworks",
    "spring": "frameworks",
    "spring boot": "frameworks",
    "dotnet": "frameworks",

    # Tools
    "git": "tools",
    "jira": "tools",
    "postman": "tools",
    "selenium": "tools",
    "playwright": "tools",
    "tableau": "tools",
    "power bi": "tools",
    "excel": "tools",

    # Cloud
    "aws": "cloud",
    "azure": "cloud",
    "gcp": "cloud",

    # Databases
    "sql": "databases",
    "mysql": "databases",
    "postgresql": "databases",
    "sqlite": "databases",
    "mongodb": "databases",
    "redis": "databases",
    "dynamodb": "databases",
    "elasticsearch": "databases",

    # DevOps
    "docker": "devops",
    "kubernetes": "devops",
    "terraform": "devops",
    "ansible": "devops",
    "jenkins": "devops",
    "github actions": "devops",
    "ci/cd": "devops",
    "linux": "devops",
    "bash": "devops",

    # Soft Skills
    "communication": "soft_skills",
    "problem solving": "soft_skills",
    "leadership": "soft_skills",
    "project management": "soft_skills",
    "agile": "soft_skills",
    "scrum": "soft_skills",
}

SKILL_ALIAS_MAP: Dict[str, List[str]] = {
    "ci/cd": ["ci cd", "continuous integration", "continuous delivery", "continuous deployment"],
    "node.js": ["nodejs", "node js"],
    "next.js": ["nextjs", "next js"],
    "dotnet": [".net", "asp.net", "asp net"],
    "rest api": ["restful api", "rest apis", "api development"],
    "scikit-learn": ["sklearn"],
    "github actions": ["github action"],
}


def unique_preserve_order(items: List[str]) -> List[str]:
    """Return de-duplicated list while preserving first appearance order."""
    seen = set()
    result: List[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item.strip())
    return result


def normalize_skills(skills: List[str]) -> List[str]:
    """Normalize skills into lower-cased canonical form."""
    normalized = [skill.strip().lower() for skill in skills if isinstance(skill, str) and skill.strip()]
    return unique_preserve_order(normalized)


def get_shared_skill_dictionary() -> List[str]:
    """Load the shared skill dictionary from resume_service."""
    return load_skill_dictionary()


def extract_skills_from_text(text: str, skill_dictionary: List[str]) -> List[str]:
    """Extract known skills from text using exact + alias-aware matching."""
    text_lc = (text or "").lower()
    text_flat = re.sub(r"[^a-z0-9+#./\\s-]", " ", text_lc)
    text_flat = re.sub(r"\s+", " ", text_flat).strip()
    tokens = set(re.findall(r"[a-z0-9+#.]+", text_flat))

    matches = []
    for skill in skill_dictionary:
        if skill == "c":
            # Restrict ambiguous single-letter skill to explicit language mentions.
            if not re.search(r"\b(c language|c programming|ansi c)\b", text_lc):
                continue

        variants = [skill] + SKILL_ALIAS_MAP.get(skill, [])
        detected = False

        for variant in variants:
            escaped = re.escape(variant)
            pattern = rf"(?<!\w){escaped}(?!\w)"
            if re.search(pattern, text_lc):
                detected = True
                break

            variant_tokens = re.findall(r"[a-z0-9+#.]+", variant.lower())
            if variant_tokens and all(tok in tokens or f"{tok}s" in tokens for tok in variant_tokens):
                detected = True
                break

        if detected:
            matches.append(skill)

    return unique_preserve_order(matches)


def categorize_missing_skills(missing_skills: List[str]) -> Dict[str, List[str]]:
    """Group missing skills into fixed categories for guidance readability."""
    buckets: Dict[str, List[str]] = {
        "programming_languages": [],
        "frameworks": [],
        "tools": [],
        "cloud": [],
        "databases": [],
        "devops": [],
        "soft_skills": [],
    }

    for skill in missing_skills:
        category = SKILL_CATEGORY_MAP.get(skill.lower(), "tools")
        buckets[category].append(skill)

    for key in buckets:
        buckets[key] = unique_preserve_order(buckets[key])

    return buckets

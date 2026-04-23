"""Rule-based section detection for resume text."""

import re
from typing import Dict, List, Optional, Tuple

SECTION_HEADINGS = {
    "skills": ["skills", "technical skills", "core skills"],
    "certifications": ["certifications", "licenses", "licenses & certifications"],
    "experience": ["experience", "work experience", "professional experience", "employment"],
    "projects": ["projects", "key projects", "project experience"],
    "summary": ["summary", "professional summary", "about", "profile"],
}

# Additional headings used only as section boundaries to avoid over-capturing.
SECTION_STOP_HEADINGS = {
    "achievements",
    "education",
    "languages",
    "language",
    "interests",
    "hobbies",
    "certificates",
    "declaration",
    "contact",
    "personal details",
}


def _normalize_heading(line: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\s&]", "", line.lower()).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _is_heading_candidate(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    # Resume headings are usually short single lines.
    return len(stripped) <= 60


def detect_sections(raw_text: str) -> Dict[str, Optional[str]]:
    """Detect primary resume sections from raw text using heading rules.

    Missing sections are returned as `None` to avoid hard failures.
    """
    lines = [line.strip() for line in raw_text.splitlines()]
    indexed_lines: List[Tuple[int, str]] = [(idx, line) for idx, line in enumerate(lines) if line]

    found_sections: List[Tuple[str, int]] = []
    for idx, line in indexed_lines:
        if not _is_heading_candidate(line):
            continue
        normalized = _normalize_heading(line)
        for section, aliases in SECTION_HEADINGS.items():
            if normalized in aliases:
                found_sections.append((section, idx))
                break

    result: Dict[str, Optional[str]] = {
        "skills": None,
        "certifications": None,
        "experience": None,
        "projects": None,
        "summary": None,
    }

    if not found_sections:
        return result

    found_sections.sort(key=lambda item: item[1])
    for position, (section_name, start_idx) in enumerate(found_sections):
        end_idx = len(lines)
        if position + 1 < len(found_sections):
            end_idx = found_sections[position + 1][1]

        # Stop section capture when we reach unrelated known headings.
        for idx in range(start_idx + 1, end_idx):
            if not _is_heading_candidate(lines[idx]):
                continue
            candidate = _normalize_heading(lines[idx])
            if candidate in SECTION_STOP_HEADINGS:
                end_idx = idx
                break

        body_lines = [line for line in lines[start_idx + 1:end_idx] if line.strip()]
        section_text = "\n".join(body_lines).strip()
        result[section_name] = section_text if section_text else None

    return result

"""Skill extraction using dictionary matching + spaCy phrase analysis."""

import re
from typing import Dict, List, Optional

from app.resume_service.utils import get_spacy_nlp, load_skill_dictionary

SKILL_VARIANT_PATTERNS: Dict[str, List[str]] = {
    "communication": [r"\bcommunicat(e|ion|ing|ions)\b", r"\bstakeholder(s)?\b"],
    "problem solving": [r"\bproblem[-\s]?solv(ing|e|ed)?\b", r"\btroubleshoot(ing|s)?\b"],
    "leadership": [r"\bleadership\b", r"\bteam lead\b", r"\bled\b"],
    "project management": [r"\bproject coordinat(e|ion|ing)\b", r"\bproject planning\b"],
    "data analysis": [r"\bdata analysis\b", r"\banaly(sis|zing)\b"],
}


def _fallback_candidate_phrases(text: str) -> List[str]:
    # Simple backup when noun_chunks are unavailable (e.g. blank spaCy model).
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.\-/]*", text.lower())
    phrases: List[str] = []
    for idx in range(len(words)):
        phrases.append(words[idx])
        if idx + 1 < len(words):
            phrases.append(f"{words[idx]} {words[idx + 1]}")
    return phrases


def _contains_skill(text_lc: str, skill: str) -> bool:
    if skill == "c":
        # Avoid false positives for single-letter token "c".
        return bool(re.search(r"\b(c language|c programming|ansi c)\b", text_lc))
    escaped = re.escape(skill)
    return bool(re.search(rf"(?<!\w){escaped}(?!\w)", text_lc))


def _matches_skill_variant(text_lc: str, skill: str) -> bool:
    patterns = SKILL_VARIANT_PATTERNS.get(skill, [])
    return any(re.search(pattern, text_lc) for pattern in patterns)


def extract_skills(raw_text: str, sections: Dict[str, Optional[str]]) -> List[str]:
    """Extract normalized skill set from resume text.

    Strategy:
    1) Direct dictionary phrase matching.
    2) spaCy noun-phrase candidates mapped back to dictionary terms.
    """
    skill_dict = load_skill_dictionary()
    if not skill_dict:
        return []

    working_text = raw_text.lower()
    matched = set()

    for skill in skill_dict:
        if _contains_skill(working_text, skill) or _matches_skill_variant(working_text, skill):
            matched.add(skill)

    phrase_source = sections.get("skills") or sections.get("summary") or raw_text
    try:
        nlp = get_spacy_nlp()
        doc = nlp(phrase_source[:25000])
        phrases = []
        try:
            phrases = [chunk.text.lower().strip() for chunk in doc.noun_chunks if chunk.text.strip()]
        except Exception:
            phrases = _fallback_candidate_phrases(phrase_source[:8000])
    except Exception:
        phrases = _fallback_candidate_phrases(phrase_source[:8000])

    for phrase in phrases:
        phrase_lc = phrase.lower().strip()
        if not phrase_lc:
            continue
        for skill in skill_dict:
            if _contains_skill(phrase_lc, skill):
                matched.add(skill)

    return sorted(matched)

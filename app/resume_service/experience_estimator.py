"""Heuristics for estimating years of experience from resume text."""

import re
from datetime import datetime
from typing import Optional


def estimate_experience_years(text: str) -> Optional[float]:
    """Estimate experience years from date ranges and explicit year mentions.

    Looks for patterns like `2019-2023`, `2018 to Present`, and `3+ years`.
    Returns `None` when a reliable estimate is not available.
    """
    if not text:
        return None

    current_year = datetime.utcnow().year

    range_pattern = re.compile(
        r"\b((?:19|20)\d{2})\s*(?:-|–|—|to)\s*((?:19|20)\d{2}|present|current)\b",
        flags=re.IGNORECASE,
    )
    ranges = range_pattern.findall(text)

    durations = []
    for start_raw, end_raw in ranges:
        try:
            start_year = int(start_raw)
            end_year = current_year if end_raw.lower() in {"present", "current"} else int(end_raw)
            if end_year >= start_year:
                durations.append(float(end_year - start_year))
        except ValueError:
            continue

    if durations:
        return round(max(durations), 2)

    explicit_pattern = re.compile(r"\b(\d{1,2})(?:\+)?\s+years?\b", flags=re.IGNORECASE)
    explicit = [int(val) for val in explicit_pattern.findall(text)]
    if explicit:
        return float(max(explicit))

    return None

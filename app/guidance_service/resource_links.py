"""Curated free learning resource link generator for missing skills.

Output policy:
- max 4 links total
- 2 YouTube links
- 1 GeeksforGeeks link
- 1 additional helpful website link
"""

from typing import Dict, List, Optional
from urllib.parse import quote_plus

from app.guidance_service.utils import unique_preserve_order

RESOURCE_MAP: Dict[str, Dict[str, List[Dict[str, str]]]] = {
    "python": {
        "youtube": [
            {"title": "Python Full Course (freeCodeCamp)", "url": "https://www.youtube.com/watch?v=rfscVS0vtbw", "platform": "youtube"},
            {"title": "Python Crash Course", "url": "https://www.youtube.com/watch?v=ix9cRaBkVe0", "platform": "youtube"},
        ],
        "geeksforgeeks": [
            {"title": "Python Programming - GeeksforGeeks", "url": "https://www.geeksforgeeks.org/python-programming-language/", "platform": "geeksforgeeks"},
        ],
        "web": [
            {"title": "Python Official Documentation", "url": "https://docs.python.org/3/", "platform": "web"},
        ],
    },
    "sql": {
        "youtube": [
            {"title": "SQL Full Course (freeCodeCamp)", "url": "https://www.youtube.com/watch?v=HXV3zeQKqGY", "platform": "youtube"},
            {"title": "SQL Tutorial for Beginners", "url": "https://www.youtube.com/watch?v=7S_tz1z_5bA", "platform": "youtube"},
        ],
        "geeksforgeeks": [
            {"title": "SQL Tutorial - GeeksforGeeks", "url": "https://www.geeksforgeeks.org/sql-tutorial/", "platform": "geeksforgeeks"},
        ],
        "web": [
            {"title": "SQLBolt Interactive Lessons", "url": "https://sqlbolt.com/", "platform": "web"},
        ],
    },
    "data engineering": {
        "youtube": [
            {"title": "Data Engineering Full Course", "url": "https://www.youtube.com/watch?v=QJqNYhiHysM", "platform": "youtube"},
            {"title": "Data Engineering Roadmap", "url": "https://www.youtube.com/watch?v=8M20LyCZDOY", "platform": "youtube"},
        ],
        "geeksforgeeks": [
            {"title": "Data Engineering Overview - GeeksforGeeks", "url": "https://www.geeksforgeeks.org/what-is-data-engineering/", "platform": "geeksforgeeks"},
        ],
        "web": [
            {"title": "Data Engineering Roadmap", "url": "https://roadmap.sh/data-engineer", "platform": "web"},
        ],
    },
    "spark": {
        "youtube": [
            {"title": "Apache Spark Tutorial", "url": "https://www.youtube.com/watch?v=_C8kWso4ne4", "platform": "youtube"},
            {"title": "PySpark Full Course", "url": "https://www.youtube.com/watch?v=_C8kWso4ne4", "platform": "youtube"},
        ],
        "geeksforgeeks": [
            {"title": "Apache Spark Tutorial - GeeksforGeeks", "url": "https://www.geeksforgeeks.org/introduction-to-apache-spark/", "platform": "geeksforgeeks"},
        ],
        "web": [
            {"title": "Spark Official Docs", "url": "https://spark.apache.org/docs/latest/", "platform": "web"},
        ],
    },
    "airflow": {
        "youtube": [
            {"title": "Apache Airflow Tutorial", "url": "https://www.youtube.com/watch?v=AHMm1wfGuHE", "platform": "youtube"},
            {"title": "Airflow End-to-End Guide", "url": "https://www.youtube.com/watch?v=K9AnJ9_ZAXE", "platform": "youtube"},
        ],
        "geeksforgeeks": [
            {"title": "Apache Airflow - GeeksforGeeks", "url": "https://www.geeksforgeeks.org/introduction-to-apache-airflow/", "platform": "geeksforgeeks"},
        ],
        "web": [
            {"title": "Airflow Official Docs", "url": "https://airflow.apache.org/docs/", "platform": "web"},
        ],
    },
}


def _fallback_bundle(skill: str) -> Dict[str, List[Dict[str, str]]]:
    encoded = quote_plus(skill)
    return {
        "youtube": [
            {
                "title": "YouTube search: {}".format(skill.title()),
                "url": "https://www.youtube.com/results?search_query={}".format(encoded),
                "platform": "youtube",
            }
        ],
        "geeksforgeeks": [
            {
                "title": "GeeksforGeeks search: {}".format(skill.title()),
                "url": "https://www.geeksforgeeks.org/?s={}".format(encoded),
                "platform": "geeksforgeeks",
            }
        ],
        "web": [
            {
                "title": "freeCodeCamp search: {}".format(skill.title()),
                "url": "https://www.freecodecamp.org/news/search/?query={}".format(encoded),
                "platform": "web",
            }
        ],
    }


def _append_unique(target: List[Dict[str, str]], candidate: Optional[Dict[str, str]]) -> None:
    if not candidate:
        return
    url = candidate.get("url", "").strip()
    if not url:
        return
    if any(existing.get("url") == url for existing in target):
        return
    target.append(candidate)


def generate_resource_links(missing_skills: List[str]) -> List[Dict[str, str]]:
    """Generate limited free-learning links in a fixed structure.

    Returns up to exactly 4 links in this order:
    1) YouTube
    2) YouTube
    3) GeeksforGeeks
    4) Helpful website
    """
    normalized_skills = unique_preserve_order([skill.lower().strip() for skill in missing_skills if skill and skill.strip()])
    seed_skills = normalized_skills[:3] if normalized_skills else ["software engineering"]

    youtube_links: List[Dict[str, str]] = []
    geeks_link: Optional[Dict[str, str]] = None
    web_link: Optional[Dict[str, str]] = None

    for skill in seed_skills:
        bundle = RESOURCE_MAP.get(skill, _fallback_bundle(skill))

        for candidate in bundle.get("youtube", []):
            _append_unique(youtube_links, candidate)
            if len(youtube_links) >= 2:
                break

        if geeks_link is None:
            geeks_candidates = bundle.get("geeksforgeeks", [])
            if geeks_candidates:
                geeks_link = geeks_candidates[0]

        if web_link is None:
            web_candidates = bundle.get("web", [])
            if web_candidates:
                web_link = web_candidates[0]

        if len(youtube_links) >= 2 and geeks_link and web_link:
            break

    if len(youtube_links) < 2:
        fallback = _fallback_bundle(seed_skills[0])
        for candidate in fallback.get("youtube", []):
            _append_unique(youtube_links, candidate)
            if len(youtube_links) >= 2:
                break

    if geeks_link is None:
        geeks_candidates = _fallback_bundle(seed_skills[0]).get("geeksforgeeks", [])
        geeks_link = geeks_candidates[0] if geeks_candidates else None

    if web_link is None:
        web_candidates = _fallback_bundle(seed_skills[0]).get("web", [])
        web_link = web_candidates[0] if web_candidates else None

    output: List[Dict[str, str]] = []
    for link in youtube_links[:2]:
        _append_unique(output, link)
    _append_unique(output, geeks_link)
    _append_unique(output, web_link)

    return output[:4]

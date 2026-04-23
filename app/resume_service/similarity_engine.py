"""Similarity and scoring utilities for resume-job matching.

Cosine similarity formula:
    cosine(A, B) = (A · B) / (||A|| * ||B||)

This module computes TF-IDF vectors for resume text and job descriptions, then
compares them using cosine similarity.
"""

from typing import List


def compute_cosine_similarity_scores(resume_text: str, job_texts: List[str]):
    """Return cosine similarity scores between resume text and each job text."""
    if not job_texts:
        return []

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError as exc:  # pragma: no cover - dependency check
        raise RuntimeError("scikit-learn is not installed.") from exc

    corpus = [resume_text or ""] + [text or "" for text in job_texts]
    vectorizer = TfidfVectorizer(stop_words="english", max_features=10000)
    matrix = vectorizer.fit_transform(corpus)

    resume_vector = matrix[0:1]
    job_vectors = matrix[1:]
    similarities = cosine_similarity(resume_vector, job_vectors).flatten()
    return [float(score) for score in similarities]


def compute_skill_overlap_scores(resume_skills: List[str], job_texts: List[str]) -> List[float]:
    """Compute overlap ratio between resume skills and each job description text."""
    if not job_texts:
        return []

    normalized_resume_skills = {skill.lower() for skill in resume_skills}
    if not normalized_resume_skills:
        return [0.0 for _ in job_texts]

    scores = []
    denominator = float(len(normalized_resume_skills))

    for text in job_texts:
        text_lc = (text or "").lower()
        matched = sum(1 for skill in normalized_resume_skills if skill in text_lc)
        scores.append(matched / denominator)

    return scores

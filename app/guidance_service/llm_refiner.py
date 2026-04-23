"""Optional Gemini-based refinement for guidance reports.

Core scoring and roadmap logic stays algorithmic. This module only refines final
presentation text and is guarded by API key + daily rate limits.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

MAX_LLM_REFINES_PER_DAY = 3
logger = logging.getLogger(__name__)


def _is_llm_enabled() -> bool:
    return os.getenv("GUIDANCE_LLM_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def _get_gemini_api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


def _get_preferred_model() -> str:
    return os.getenv("GUIDANCE_GEMINI_MODEL", "").strip()


def _discover_supported_models_sync(api_key: str) -> List[str]:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    available: List[str] = []
    for model in genai.list_models():
        methods = set(getattr(model, "supported_generation_methods", []) or [])
        if "generateContent" in methods:
            name = str(getattr(model, "name", "")).strip()
            if name:
                available.append(name)
    return available


def _select_model_name(available_models: List[str], preferred: str) -> str:
    if not available_models:
        raise RuntimeError("No Gemini models with generateContent support were found for this API key.")

    normalized_preferred = preferred.strip()
    if normalized_preferred:
        if not normalized_preferred.startswith("models/"):
            normalized_preferred = "models/{}".format(normalized_preferred)
        if normalized_preferred in available_models:
            return normalized_preferred

        preferred_suffix = normalized_preferred.split("/", 1)[-1]
        for model_name in available_models:
            if model_name.endswith(preferred_suffix):
                return model_name

    priority_tokens = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "flash",
    ]
    for token in priority_tokens:
        for model_name in available_models:
            if token in model_name:
                return model_name
    return available_models[0]


async def get_daily_usage(db: AsyncIOMotorDatabase, user_id: str) -> Tuple[int, int]:
    """Return used and remaining LLM refinements for current UTC day."""
    now = datetime.now(timezone.utc)
    day_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    used = await db.guidance_reports.count_documents(
        {
            "user_id": user_id,
            "llm_refined": True,
            "created_at": {"$gte": day_start, "$lt": day_end},
        }
    )
    remaining = max(0, MAX_LLM_REFINES_PER_DAY - int(used))
    return int(used), remaining


def _build_prompt(report_payload: Dict[str, Any]) -> str:
    """Build a constrained prompt to rewrite guidance into concise natural language."""
    data_json = json.dumps(report_payload, ensure_ascii=True)
    return (
        "You are a career guidance assistant. Rewrite the structured guidance into concise, practical text. "
        "Keep it under 180 words. Include: key gaps, phased plan summary, and prep strategy. "
        "Do not invent new skills or links.\\n\\n"
        "Structured input:\\n{}".format(data_json)
    )


def _call_gemini_sync(prompt: str, api_key: str) -> str:
    """Synchronous Gemini API call wrapped by asyncio.to_thread."""
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    available_models = _discover_supported_models_sync(api_key=api_key)
    selected_model = _select_model_name(available_models, _get_preferred_model())
    model = genai.GenerativeModel(selected_model)
    response = model.generate_content(prompt)
    text = getattr(response, "text", "")
    return (text or "").strip()


async def maybe_refine_with_gemini(
    db: AsyncIOMotorDatabase,
    user_id: str,
    report_payload: Dict[str, Any],
) -> Tuple[bool, Optional[str], Optional[str], int]:
    """Optionally refine report with Gemini if enabled and under daily cap.

    Returns:
        (llm_refined, llm_summary, status_message, remaining_after_call)
    """
    used, remaining = await get_daily_usage(db=db, user_id=user_id)

    if not _is_llm_enabled():
        return False, None, "LLM refinement disabled.", remaining

    api_key = _get_gemini_api_key()
    if not api_key:
        return False, None, "GEMINI_API_KEY is not configured.", remaining

    if remaining <= 0:
        return False, None, "Daily LLM limit reached (max 3/day).", 0

    prompt = _build_prompt(report_payload)
    try:
        llm_summary = await asyncio.to_thread(_call_gemini_sync, prompt, api_key)
        if not llm_summary:
            return False, None, "LLM returned empty response. Using algorithmic guidance.", remaining
        return True, llm_summary, "LLM refinement applied.", max(0, remaining - 1)
    except Exception as exc:  # pragma: no cover - external API errors
        logger.exception("LLM refinement failed for user_id=%s error=%s", user_id, exc)
        reason = str(exc).strip().splitlines()[0] if str(exc).strip() else "Unknown Gemini API error"
        if len(reason) > 180:
            reason = reason[:180].rstrip() + "..."
        return False, None, "LLM refinement unavailable ({}). Using algorithmic guidance.".format(reason), remaining

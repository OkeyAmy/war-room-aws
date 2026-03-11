"""
WAR ROOM — Voice Discovery
Returns available voice names for Nova Sonic or falls back to the
hardcoded pool in constants.py.
"""

from __future__ import annotations

import logging
from typing import Optional

from config.constants import (
    NOVA_VOICE_POOL, NOVA_VOICE_STYLE_MAP,
    GEMINI_VOICE_POOL, GEMINI_VOICE_STYLE_MAP,
)

logger = logging.getLogger(__name__)

_cached_voices: Optional[list[str]] = None


async def discover_voices(force_refresh: bool = False) -> list[str]:
    """
    Return the voice pool for the currently active provider.
    Results are cached until force_refresh=True.
    """
    global _cached_voices

    if _cached_voices is not None and not force_refresh:
        return _cached_voices

    try:
        from utils.model_provider import get_active_provider
        provider = get_active_provider()
    except Exception:
        provider = "aws"

    if provider == "gemini":
        _cached_voices = GEMINI_VOICE_POOL
        logger.info(f"Voice discovery: Gemini Live voices ({len(GEMINI_VOICE_POOL)} voices).")
    else:
        _cached_voices = NOVA_VOICE_POOL
        logger.info(f"Voice discovery: Nova Sonic voices ({len(NOVA_VOICE_POOL)} voices).")

    return _cached_voices


async def get_voice_style_map() -> dict[str, list[str]]:
    """
    Returns the voice-style → voice-names mapping for the active provider.
    Used by the /api/voices endpoint so the frontend knows which voices are available.
    """
    try:
        from utils.model_provider import get_active_provider
        provider = get_active_provider()
    except Exception:
        provider = "aws"

    return GEMINI_VOICE_STYLE_MAP if provider == "gemini" else NOVA_VOICE_STYLE_MAP


async def check_voice_health() -> dict:
    """
    Health check for the voice subsystem.
    Validates that:
    1. The voice pool is available
    2. Voice assignment logic works
    """
    try:
        voices = await discover_voices()
        if not voices:
            return {"status": "fail", "message": "No voices available"}

        from agents.voice_assignment import assign_voices
        test_agents = [
            {"role_key": "test_legal", "voice_style": "authoritative"},
            {"role_key": "test_pr", "voice_style": "urgent"},
        ]
        assignments = assign_voices(test_agents)
        if len(assignments) != 2:
            return {
                "status": "fail",
                "message": f"Voice assignment returned {len(assignments)}/2",
            }

        return {
            "status": "pass",
            "message": f"{len(voices)} voices available, assignment working",
            "voice_count": len(voices),
        }

    except Exception as e:
        return {"status": "fail", "message": f"Voice check failed: {e}"}

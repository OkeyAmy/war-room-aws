"""
WAR ROOM — Voice Assignment
Maps each agent's voice_style (set by the Scenario Analyst) to a concrete
voice name for the active provider, guaranteeing no two agents share a voice.

Provider routing:
  AWS active  → Nova Sonic voice names (e.g. "tiffany", "matthew")
  Gemini      → Gemini Live voice names (e.g. "Fenrir", "Kore", "Puck")
"""

from __future__ import annotations

import logging
from config.constants import (
    NOVA_VOICE_POOL,
    NOVA_VOICE_STYLE_MAP,
    GEMINI_VOICE_POOL,
    GEMINI_VOICE_STYLE_MAP,
)

logger = logging.getLogger(__name__)


def _get_style_map_and_pool() -> tuple[dict[str, list[str]], list[str]]:
    """
    Return (style_map, full_voice_pool) for the currently active provider.
    Falls back to Nova if the provider check hasn't run yet.
    """
    try:
        from utils.model_provider import get_active_provider
        provider = get_active_provider()
    except Exception:
        provider = "aws"

    if provider == "gemini":
        return GEMINI_VOICE_STYLE_MAP, GEMINI_VOICE_POOL
    return NOVA_VOICE_STYLE_MAP, NOVA_VOICE_POOL


def assign_voices(agents: list[dict]) -> dict[str, str]:
    """
    Takes the agent list from the Scenario Analyst output.
    Returns a dict of { role_key: voice_name }.

    The Scenario Analyst sets each agent's voice_style
    ("authoritative", "warm", "clipped", "measured", "urgent", "calm", "aggressive").
    This function maps each style to the best available voice for the active
    provider, guaranteeing no two agents share the same voice.

    Args:
        agents: List of agent config dicts with 'role_key' and 'voice_style'.

    Returns:
        Dict mapping role_key → voice_name.
    """
    style_map, full_pool = _get_style_map_and_pool()
    assigned: dict[str, str] = {}
    used_voices: set[str] = set()

    for agent in agents:
        role_key = agent.get("role_key", "unknown")
        style = agent.get("voice_style", "measured")

        # First try preferred candidates for this style
        candidates = style_map.get(style, style_map.get("measured", []))
        voice_found = False
        for voice in candidates:
            if voice not in used_voices:
                assigned[role_key] = voice
                used_voices.add(voice)
                voice_found = True
                break

        if not voice_found:
            # Fallback: pick any unused voice from the full pool
            remaining = [v for v in full_pool if v not in used_voices]
            if remaining:
                fallback = remaining[0]
                assigned[role_key] = fallback
                used_voices.add(fallback)
                logger.warning(
                    f"Fallback voice for {role_key}: {fallback} "
                    f"(preferred style '{style}' fully used)"
                )
            else:
                logger.error(f"No voices left for agent {role_key}")

    logger.info(f"Voice assignments: {assigned}")
    return assigned

"""
WAR ROOM — Model Provider with AWS → Gemini Fallback

Startup behaviour:
  1. On first request (or explicit startup check), validate AWS credentials.
  2. If AWS is valid  → use Amazon Nova (text + voice) for the entire process run.
  3. If AWS is invalid on startup → immediately activate Gemini.

Runtime behaviour:
  4. If AWS was active and a call fails → call mark_provider_failed().
     The process switches to Gemini permanently for the rest of this run.
  5. The next process restart re-checks AWS from scratch.

Text LLM:
  AWS active  → Amazon Nova 2 Lite via OpenAI-compatible endpoint
  Gemini      → Gemini 2.5 Flash/Lite via OpenAI-compatible endpoint

Voice:
  AWS active  → aws.realtime.RealtimeModel (Nova Sonic 2)
  Gemini      → google.realtime.RealtimeModel (Gemini Live)
"""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)

# ── Process-level provider state ────────────────────────────────────────────
# "aws" or "gemini". Starts as "aws" — startup check may flip it to "gemini".
_active_provider: str = "aws"
_startup_check_done: bool = False


def get_active_provider() -> str:
    """Return the currently active provider: 'aws' or 'gemini'."""
    return _active_provider


def is_aws_active() -> bool:
    return _active_provider == "aws"


def mark_provider_failed(reason: str = "") -> None:
    """
    Called when an AWS/Nova call fails at runtime.
    Permanently switches this process run to Gemini.
    On next restart the startup check will re-evaluate AWS.
    """
    global _active_provider
    if _active_provider == "aws":
        logger.warning(
            f"[PROVIDER] AWS Nova failed ({reason}). "
            "Switching to Gemini fallback for the rest of this session."
        )
        _active_provider = "gemini"


# ── Startup check ────────────────────────────────────────────────────────────

async def check_provider_on_startup() -> str:
    """
    Run once at application startup.
    Validates AWS credentials via a lightweight STS call.
    Sets the process-level provider flag and returns "aws" or "gemini".
    """
    global _active_provider, _startup_check_done

    if _startup_check_done:
        return _active_provider

    from config.settings import get_settings
    settings = get_settings()

    aws_ok = await _check_aws_credentials(settings)
    if aws_ok:
        _active_provider = "aws"
        logger.info("[PROVIDER] AWS Nova credentials valid — Amazon Nova stack is active")
    else:
        _active_provider = "gemini"
        logger.warning(
            "[PROVIDER] AWS Nova unavailable on startup — "
            "Gemini fallback is now active for this process run"
        )

    _startup_check_done = True
    return _active_provider


async def _check_aws_credentials(settings) -> bool:
    """
    Validate AWS credentials by making a lightweight STS GetCallerIdentity call.
    Returns True if credentials are present and valid.
    """
    if not settings.aws_access_key_id or not settings.aws_secret_access_key:
        logger.warning("[PROVIDER] AWS credentials not set in .env")
        return False
    try:
        import boto3
        await asyncio.to_thread(
            lambda: boto3.client(
                "sts",
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
            ).get_caller_identity()
        )
        return True
    except Exception as e:
        logger.warning(f"[PROVIDER] AWS credential validation failed: {e}")
        return False


# ── Text LLM client ──────────────────────────────────────────────────────────

def get_text_client(model_type: str = "agent") -> tuple:
    """
    Return (openai_client, model_id) for the current active provider.

    model_type: one of "agent", "scenario", "fast", "vision"
    """
    from openai import OpenAI
    from config.settings import get_settings
    settings = get_settings()

    if is_aws_active():
        model_map = {
            "agent": settings.nova_agent_model,
            "scenario": settings.nova_scenario_model,
            "fast": settings.nova_fast_model,
            "vision": settings.nova_vision_model,
        }
        client = OpenAI(
            api_key=settings.nova_api_key,
            base_url=settings.nova_base_url,
            timeout=60.0,
            max_retries=2,
        )
        return client, model_map.get(model_type, settings.nova_agent_model)
    else:
        model_map = {
            "agent": settings.gemini_agent_model,
            "scenario": settings.gemini_scenario_model,
            "fast": settings.gemini_fast_model,
            "vision": settings.gemini_vision_model,
        }
        client = OpenAI(
            api_key=settings.google_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            timeout=60.0,
            max_retries=2,
        )
        return client, model_map.get(model_type, settings.gemini_agent_model)


async def run_text_llm(
    messages: list[dict],
    model_type: str = "agent",
    call_timeout: float = 75.0,
    **kwargs,
):
    """
    Run a chat completion with automatic AWS → Gemini fallback.

    - If AWS is active and the call fails, marks the provider as failed,
      then immediately retries with Gemini.
    - If Gemini is already active, runs directly.
    - Raises the final exception if Gemini also fails.
    - Hard wall-clock timeout via call_timeout (default 75s) so a single
      hung or 503-retrying call can never block the bootstrapper indefinitely.

    Args:
        messages: OpenAI-format message list.
        model_type: "agent" | "scenario" | "fast" | "vision"
        call_timeout: Hard asyncio timeout in seconds for the whole call + retries.
        **kwargs: Passed through to chat.completions.create (temperature, max_tokens, etc.)

    Returns:
        OpenAI ChatCompletion response object.
    """
    client, model = get_text_client(model_type)

    async def _call(c, m):
        return await asyncio.wait_for(
            asyncio.to_thread(
                c.chat.completions.create,
                model=m,
                messages=messages,
                **kwargs,
            ),
            timeout=call_timeout,
        )

    try:
        return await _call(client, model)
    except asyncio.TimeoutError:
        logger.warning(
            f"[PROVIDER] {model_type} call timed out after {call_timeout}s"
        )
        raise
    except Exception as e:
        if is_aws_active():
            mark_provider_failed(str(e))
            # Retry with Gemini
            client, model = get_text_client(model_type)
            logger.info(f"[PROVIDER] Retrying with Gemini ({model})...")
            return await _call(client, model)
        raise


# ── Voice (realtime) model ────────────────────────────────────────────────────

def get_voice_model(voice: str | None = None):
    """
    Return the appropriate realtime voice model for the active provider.

    Args:
        voice: Per-agent voice name assigned by the Scenario Analyst via
               voice_assignment.py.  If None, falls back to the settings default.

    AWS active  → aws.realtime.RealtimeModel (Nova Sonic 2) with agent voice
    Gemini      → google.realtime.RealtimeModel (Gemini Live) with agent voice

    On AWS init failure the provider is marked failed and Gemini is used.
    """
    from config.settings import get_settings
    settings = get_settings()

    if is_aws_active():
        try:
            from livekit.plugins import aws
            agent_voice = voice or settings.nova_sonic_voice
            return aws.realtime.RealtimeModel.with_nova_sonic_2(
                voice=agent_voice,
                turn_detection=settings.nova_sonic_turn_detection,
                region=settings.aws_region,
            )
        except Exception as e:
            mark_provider_failed(str(e))
            logger.info("[PROVIDER] Falling back to Gemini realtime model for voice")
            return _build_gemini_voice_model(settings, voice)
    else:
        return _build_gemini_voice_model(settings, voice)


def _build_gemini_voice_model(settings, voice: str | None = None):
    """Build a Gemini realtime voice model with the given per-agent voice name."""
    from livekit.plugins import google
    # Default to "Puck" only if no per-agent voice was assigned
    agent_voice = voice or "Puck"
    return google.realtime.RealtimeModel(
        model=settings.gemini_realtime_model,
        voice=agent_voice,
        api_key=settings.google_api_key or None,
    )

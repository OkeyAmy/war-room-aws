"""
WAR ROOM — Application Settings
Loads environment variables and provides typed configuration.
"""

import os
import logging

from pydantic_settings import BaseSettings
from functools import lru_cache

logger = logging.getLogger(__name__)

DEPRECATED_GEMINI_MODEL_MAP = {
    "gemini-flash-lite-latest": "gemini-2.0-flash",
    "gemini-2.0-flash-lite": "gemini-2.0-flash",
    "gemini-3-flash": "gemini-2.0-flash",
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # GCP
    gcp_project_id: str = "war-room-dev"
    google_application_credentials: str = ""

    # Amazon Nova API (OpenAI-compatible)
    nova_api_key: str = ""
    nova_base_url: str = "https://api.nova.amazon.com/v1"

    # Amazon Nova Models — all configurable via .env
    nova_scenario_model: str = "nova-2-lite-v1"   # Scenario generation, document finalization
    nova_agent_model: str = "nova-2-lite-v1"      # Per-agent reasoning
    nova_fast_model: str = "nova-2-lite-v1"       # Speaker selection, observer analysis
    nova_vision_model: str = "nova-2-lite-v1"     # Visual/multimodal document understanding

    # AWS credentials (for Nova Sonic via LiveKit + Bedrock)
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"

    # Google Gemini fallback (activated if AWS is unavailable or fails)
    # Voice is assigned per-agent by the Scenario Analyst via GEMINI_VOICE_STYLE_MAP.
    google_api_key: str = ""
    gemini_agent_model: str = "gemini-2.0-flash"
    gemini_scenario_model: str = "gemini-2.0-flash"
    gemini_fast_model: str = "gemini-2.0-flash"
    gemini_vision_model: str = "gemini-2.0-flash"
    gemini_realtime_model: str = "gemini-2.5-flash-native-audio-preview-12-2025"

    # Firestore
    firestore_emulator_host: str = ""

    # FastAPI
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Pub/Sub
    pubsub_emulator_host: str = ""
    pubsub_topic: str = "war-room-events"

    # Voice backend:
    # - "livekit_aws": Amazon Nova Sonic via LiveKit AWS plugin (realtime speech-to-speech)
    voice_backend: str = "livekit_aws"
    single_agent_voice_mode: bool = False
    single_agent_voice_target: str = ""

    # Nova Sonic voice settings
    nova_sonic_voice: str = "tiffany"
    nova_sonic_turn_detection: str = "MEDIUM"

    # LiveKit (server API)
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""

    # Session config
    max_agents_per_session: int = 5
    session_timeout_minutes: int = 45
    escalation_score_penalty: int = -8

    # Environment: "development" or "production"
    environment: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    s = Settings()
    for field_name in (
        "gemini_agent_model",
        "gemini_scenario_model",
        "gemini_fast_model",
        "gemini_vision_model",
        "gemini_realtime_model",
    ):
        current = getattr(s, field_name)
        replacement = DEPRECATED_GEMINI_MODEL_MAP.get(current)
        if replacement:
            logger.warning(
                "Deprecated Gemini model '%s' configured for %s; using '%s' instead",
                current,
                field_name,
                replacement,
            )
            setattr(s, field_name, replacement)
    if s.google_application_credentials:
        os.environ.setdefault(
            "GOOGLE_APPLICATION_CREDENTIALS", s.google_application_credentials
        )
    return s

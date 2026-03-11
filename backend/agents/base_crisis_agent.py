"""
WAR ROOM — Base Crisis Agent
Per voice.md: ONE agent = ONE LiveKit session = ONE Firestore collection.

Each agent runs a PERSISTENT background loop:
  _voice_loop() → Amazon Nova Sonic (speech-to-speech via LiveKit AWS plugin)
  _introduce_on_join()  → opening character line on session start

Text reasoning uses Amazon Nova 2 Lite via OpenAI-compatible API.

MEMORY ISOLATION:
  - self.live_session belongs to THIS agent only, NEVER shared
  - Firestore writes use agent_id_{session_id} as doc key
  - Agent tools can ONLY read shared board state (via tools)
"""

from __future__ import annotations

import asyncio
import base64
import uuid
import logging
import re
import time
import random
from datetime import datetime, timezone
from typing import Optional

from config.constants import ALLOWED_VOICE_POOL
from config.settings import get_settings

logger = logging.getLogger(__name__)


class CrisisAgent:
    """
    One CrisisAgent = one LiveKit session = one Firestore collection.

    AUDIO PIPELINE (livekit_aws mode):
      chairman mic PCM → audio_in_queue → Amazon Nova Sonic (speech-to-speech)
              → Nova 2 Lite text LLM reasoning → Nova Sonic audio output
              → push_event_direct(agent_audio_chunk) → browser speakers
    """

    ALLOWED_VOICE_POOL = ALLOWED_VOICE_POOL

    def __init__(
        self,
        session_id: str,
        agent_id: str,
        role_config: dict,
        skill_md: str,
        assigned_voice: str,
        turn_manager=None,
        livekit_session_config: Optional[dict] = None,
    ):
        self.session_id = session_id
        self.agent_id = agent_id
        self.role_config = role_config
        self.assigned_voice = assigned_voice
        self.skill_md = skill_md

        # Turn manager — session-level coordination so only one agent speaks
        self.turn_manager = turn_manager
        self.livekit_session_config = livekit_session_config or {}

        # Live session presence marker
        self.live_session = None

        settings = get_settings()
        self.voice_backend = settings.voice_backend

        # Amazon Nova Sonic realtime model (via LiveKit AWS plugin)
        self._nova_sonic_model = None

        # Firestore refs (lazy-initialized)
        self._db = None
        self._memory_ref = None
        self._crisis_ref = None

        # ── QUEUES: chairman → agent ─────────────────────────────────
        # ISOLATION: these queues are PRIVATE to this agent instance.
        # The VoiceRouter is the ONLY thing that puts into these queues.
        self.audio_in_queue: asyncio.Queue = asyncio.Queue()   # PCM bytes from chairman mic
        self.text_in_queue: asyncio.Queue = asyncio.Queue()    # text commands from chairman

        # Background tasks
        self._running = False
        self._tasks: list[asyncio.Task] = []
        # Hard serialization for one-agent mode:
        # prevent overlapping TTS generations from the same agent.
        self._speak_lock = asyncio.Lock()
        self._introduced = False
        self._conversation_history: list[dict[str, str]] = []
        self._last_user_input: str = ""
        self._last_user_input_at: float = 0.0
        self._last_agent_utterance: str = ""
        self._last_agent_utterance_at: float = 0.0

    def voice_runtime_summary(self) -> str:
        """
        Human-readable runtime stack marker for backend logs.
        """
        if self._nova_sonic_model:
            from utils.model_provider import get_active_provider
            allow_interruptions = self.livekit_session_config.get(
                "voice_options", {}
            ).get("allow_interruptions", True)
            settings = get_settings()
            provider = get_active_provider()
            if provider == "aws":
                llm_label = f"nova:{settings.nova_agent_model}"
                voice_label = f"nova-sonic-2:{self.assigned_voice}"
            else:
                llm_label = f"gemini:{settings.gemini_agent_model}"
                voice_label = f"gemini-live:{self.assigned_voice}"
            return (
                f"backend={provider} "
                f"voice={voice_label} "
                f"llm={llm_label} "
                f"allow_interruptions={str(bool(allow_interruptions)).lower()}"
            )
        return f"backend=unavailable requested_backend={self.voice_backend}"

    # ── Lazy Firestore ────────────────────────────────────────────────

    @property
    def db(self):
        if self._db is None:
            from utils.firestore_helpers import _get_db
            self._db = _get_db()
        return self._db

    @property
    def memory_ref(self):
        """Scoped to THIS agent's memory document ONLY."""
        if self._memory_ref is None:
            from config.constants import COLLECTION_AGENT_MEMORY
            self._memory_ref = self.db.collection(COLLECTION_AGENT_MEMORY).document(
                f"{self.agent_id}_{self.session_id}"
            )
        return self._memory_ref

    @property
    def crisis_ref(self):
        """Shared crisis session document (read-mostly)."""
        if self._crisis_ref is None:
            from config.constants import COLLECTION_CRISIS_SESSIONS
            self._crisis_ref = self.db.collection(COLLECTION_CRISIS_SESSIONS).document(
                self.session_id
            )
        return self._crisis_ref

    # ── LLM Client (provider-aware) ────────────────────────────────────

    def _get_nova_client(self):
        """
        Kept for internal compatibility — delegates to model_provider.
        Returns (client, model) for the currently active provider.
        """
        from utils.model_provider import get_text_client
        return get_text_client("agent")

    def _build_tools(self) -> list:
        """Build the tool list. Tools are the ONLY way agents touch shared state."""
        from tools.crisis_board_tools import (
            read_crisis_board, write_agreed_decision,
            write_open_conflict, write_critical_intel,
            update_document_draft, flag_deadline_risk,
        )
        from tools.memory_tools import read_my_private_memory, write_my_private_memory
        from tools.event_tools import publish_room_event
        from tools.agent_tools import read_other_agent_last_statement, update_my_trust_score

        sid = self.session_id
        aid = self.agent_id

        async def _read_crisis_board() -> dict:
            """Read the current Crisis Board state."""
            return await read_crisis_board(sid, aid)

        async def _write_agreed_decision(text: str, agents_agreed: list[str]) -> dict:
            """Record an agreed decision on the Crisis Board."""
            return await write_agreed_decision(sid, aid, text, agents_agreed)

        async def _write_open_conflict(
            description: str, agents_involved: list[str], severity: str = "medium",
        ) -> dict:
            """Register a conflict on the Crisis Board."""
            return await write_open_conflict(sid, aid, description, agents_involved, severity)

        async def _write_critical_intel(text: str, source: str, is_escalation: bool = False) -> dict:
            """Drop critical intelligence onto the Crisis Board."""
            return await write_critical_intel(sid, aid, text, source, is_escalation)

        async def _read_my_private_memory() -> dict:
            """Read your private memory for consistency."""
            return await read_my_private_memory(sid, aid)

        async def _write_my_private_memory(key: str, value: str) -> dict:
            """Write to your private memory."""
            return await write_my_private_memory(sid, aid, key, value)

        async def _read_other_agent_last_statement(target_agent_id: str) -> dict:
            """Read another agent's last public statement."""
            return await read_other_agent_last_statement(sid, aid, target_agent_id)

        async def _update_my_trust_score(delta: int, reason: str) -> dict:
            """Update trust score."""
            return await update_my_trust_score(sid, aid, delta, reason)

        async def _publish_room_event(event_type: str, payload: dict) -> dict:
            """Publish an event to the room."""
            return await publish_room_event(sid, aid, event_type, payload)

        async def _update_document_draft(doc_id: str, section: str, content: str, status: str = "draft") -> dict:
            """Draft or update a section of an assigned response document."""
            return await update_document_draft(sid, aid, doc_id, section, content, status)

        async def _flag_deadline_risk(deadline_label: str, risk_note: str, hours_remaining: float = None) -> dict:
            """Escalate when a critical deadline is at risk."""
            return await flag_deadline_risk(sid, aid, deadline_label, risk_note, hours_remaining)

        return [
            _read_crisis_board, _write_agreed_decision, _write_open_conflict,
            _write_critical_intel, _read_other_agent_last_statement,
            _update_my_trust_score, _publish_room_event,
            _read_my_private_memory, _write_my_private_memory,
            _update_document_draft, _flag_deadline_risk,
        ]

    # ── Voice Session Setup ───────────────────────────────────────────

    async def initialize_live_session(self):
        """
        Initialize per-agent voice runtime.
        Primary:  Amazon Nova Sonic via livekit-plugins-aws
        Fallback: Google Gemini Live via livekit-plugins-google
        The active provider is determined by model_provider (set at startup).
        """
        from utils.model_provider import get_voice_model, get_active_provider, is_aws_active

        try:
            # Pass per-agent voice assigned by the Scenario Analyst
            self._nova_sonic_model = get_voice_model(voice=self.assigned_voice)
            self.live_session = object()
            active = get_active_provider()
            settings = get_settings()

            voice_label = self.assigned_voice

            try:
                await self.memory_ref.update({
                    "voice_session_active": True,
                    "voice_name": voice_label,
                    "voice_backend": active,
                })
            except Exception:
                logger.debug(
                    f"[VOICE] memory_ref not ready for {self.agent_id} "
                    "(will be created by bootstrapper)"
                )

            logger.info(
                f"[VOICE] {active} voice ready for {self.agent_id} "
                f"(voice={voice_label})"
            )
            return
        except Exception as e:
            logger.warning(
                f"[VOICE] Voice init failed for {self.agent_id}: {e}. "
                "Voice disabled for this agent."
            )
            self.live_session = None
            return

    def _build_live_system_prompt(self) -> str:
        """System instruction for the LLM."""
        role = self.role_config
        char = role.get("character_name", "Agent")
        title = role.get("role_title", "Advisor")
        traits = ", ".join(role.get("personality_traits", []))
        style = role.get("voice_style", "measured")

        prompt = (
            f"{self.skill_md}\n\n"
            f"---\n"
            f"VOICE PERSONA: You are {char}, the {title}.\n"
            f"Voice style: {style}. Personality: {traits}.\n\n"
            f"RULES:\n"
            f"- Speak naturally and in character at all times.\n"
            f"- Keep responses concise: 2-3 sentences unless elaborating on a key point.\n"
            f"- If interrupted, stop immediately and listen.\n"
            f"- React to what other agents say — agree, push back, add nuance.\n"
            f"- You are in a live crisis simulation. The stakes are real to you.\n"
        )
        return prompt

    # ── Persistent Background Tasks (voice.md §1.3) ───────────────────

    async def start_background_tasks(self):
        """
        Launch the three persistent background tasks per voice.md §1.3.
        These run for the lifetime of the session.
        Call this AFTER initialize_live_session().
        """
        if not self.live_session:
            logger.warning(
                f"[{self.agent_id}] No live session — background tasks not started"
            )
            return

        self._running = True
        if self._nova_sonic_model:
            self._tasks = [
                asyncio.create_task(self._voice_loop(), name=f"{self.agent_id}_voice"),
                asyncio.create_task(self._introduce_on_join(), name=f"{self.agent_id}_intro"),
            ]
            logger.info(
                f"[{self.agent_id}] Background tasks started "
                "(livekit_aws Nova Sonic voice)"
            )
        else:
            logger.warning(
                f"[{self.agent_id}] No supported voice runtime. "
                "Live session unavailable."
            )

    async def _introduce_on_join(self):
        """
        LiveKit-mode opening line so the active agent announces itself on entry.
        """
        startup = self.livekit_session_config.get("startup", {})
        if not startup.get("introduce_on_join", True):
            return
        if self._introduced:
            return
        delay = float(startup.get("intro_delay_seconds", 1.0))
        intro_message = startup.get("intro_message", "")
        if not intro_message:
            char = self.role_config.get("character_name", "Agent")
            title = self.role_config.get("role_title", "Advisor")
            intro_message = (
                f"I am {char}, {title}. I am online and ready. "
                "Share the immediate crisis objective."
            )
        await asyncio.sleep(max(0.2, delay))
        if self._running and self.live_session and not self._introduced:
            await self.send_text(intro_message)
            self._introduced = True

    async def _kickoff_opening_turn(self):
        """
        Seed one initial turn quickly after startup so agents begin speaking
        without waiting for chairman input.
        """
        try:
            # Small jitter based on agent id to reduce same-time collisions.
            jitter = (abs(hash(self.agent_id)) % 5) * 0.4
            await asyncio.sleep(2.0 + jitter)
            if self._running and self.live_session:
                await self.send_text(
                    "Opening turn: introduce your immediate assessment and top priority "
                    "for this crisis in 2 concise sentences."
                )
        except Exception as e:
            logger.debug(f"[{self.agent_id}] kickoff turn skipped: {e}")

    async def _voice_loop(self):
        """
        Voice loop for Amazon Nova stack:
          Voice: Nova Sonic (speech-to-speech via LiveKit AWS plugin)
          Text LLM: Nova 2 Lite via OpenAI SDK
        """
        logger.info(f"[{self.agent_id}] Starting livekit_aws voice loop")
        while self._running and self.live_session:
            try:
                if not self.text_in_queue.empty():
                    text = await self.text_in_queue.get()
                    if text:
                        await self._generate_and_speak_reply(text, is_directive=True)
                    continue

                try:
                    first_chunk = await asyncio.wait_for(self.audio_in_queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue

                chunks = [first_chunk]
                while True:
                    try:
                        nxt = await asyncio.wait_for(self.audio_in_queue.get(), timeout=0.35)
                        chunks.append(nxt)
                    except asyncio.TimeoutError:
                        break

                audio_data = b"".join(chunks)
                if audio_data:
                    await self._generate_and_speak_reply(
                        "[Audio input received from chairman]", is_directive=False
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[{self.agent_id}] voice loop error: {e}")
                await asyncio.sleep(0.5)

    async def _generate_llm_reply(self, user_text: str) -> str:
        from utils.model_provider import run_text_llm, get_active_provider
        settings = get_settings()

        if not settings.nova_api_key and not settings.google_api_key:
            return "[LLM unavailable — neither NOVA_API_KEY nor GOOGLE_API_KEY configured]"

        crisis_brief = await self._read_crisis_brief()
        defining_line = self.role_config.get("defining_line", "")
        initial_position = self.role_config.get("initial_position", "")
        agenda = self.role_config.get("agenda", "")

        intro_rule = (
            "You already introduced yourself earlier. Do NOT re-introduce your name/title."
            if self._introduced else
            "This is your first speaking turn. Introduce yourself in ONE sentence, "
            "then immediately address the crisis with specifics."
        )

        position_context = ""
        if not self._introduced:
            if defining_line:
                position_context += f"Your opening stance: \"{defining_line}\"\n"
            if initial_position:
                position_context += f"Your initial position: {initial_position}\n"
            if agenda:
                position_context += f"Your priority: {agenda}\n"

        system_prompt = (
            f"{self.skill_md}\n\n"
            f"VOICE PERSONA: You are {self.role_config.get('character_name', 'Agent')}, "
            f"the {self.role_config.get('role_title', 'Advisor')}.\n"
            f"CRISIS BRIEF:\n{crisis_brief}\n\n"
            f"{position_context}"
            "Respond in character as spoken dialogue only. "
            "Reference SPECIFIC facts, names, and stakes from the crisis — never be generic. "
            "Do NOT print JSON, markdown code fences, tool call lists, or function-call arguments. "
            f"{intro_rule} "
            "Continue the current conversation; do not reset context. "
            "Use 2-4 sentences. "
            "Do not fabricate debate with other agents unless explicitly asked."
        )

        messages = [{"role": "system", "content": system_prompt}]
        for item in self._conversation_history[-8:]:
            turn_role = "user" if item.get("role") == "chairman" else "assistant"
            messages.append({"role": turn_role, "content": item.get("text", "")})
        messages.append({"role": "user", "content": user_text})

        try:
            response = await run_text_llm(
                messages=messages,
                model_type="agent",
                temperature=0.88,
                max_tokens=600,
            )
            text = self._sanitize_agent_reply(
                (response.choices[0].message.content or "").strip()
            )
            if text:
                return text
        except Exception as e:
            provider = get_active_provider()
            err_str = str(e)
            logger.error(
                f"[{self.agent_id}] {provider} LLM generation failed: {e}"
            )
            if "404" in err_str or "401" in err_str or "NOT_FOUND" in err_str:
                return ""
            if "503" in err_str or "overloaded" in err_str.lower():
                return ""

        return ""

    def _sanitize_agent_reply(self, text: str) -> str:
        """
        Strip tool-call JSON/code-fence noise so only spoken dialogue reaches TTS/feed.
        """
        if not text:
            return ""

        # Remove fenced code blocks (often tool-call JSON dumps).
        text = re.sub(r"```[\s\S]*?```", " ", text)
        # Remove leading JSON array/object blobs if model emits tool traces.
        text = re.sub(r"^\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*", " ", text)
        # Collapse whitespace.
        text = re.sub(r"\s+", " ", text).strip()
        return text

    async def _read_crisis_brief(self) -> str:
        try:
            doc = await self.crisis_ref.get()
            if doc.exists:
                return (doc.to_dict() or {}).get("crisis_brief", "")
        except Exception:
            pass
        return ""

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip().lower())

    def _append_conversation(self, role: str, text: str) -> None:
        if not text:
            return
        self._conversation_history.append({"role": role, "text": text.strip()})
        if len(self._conversation_history) > 14:
            self._conversation_history = self._conversation_history[-14:]

    def _render_conversation_history(self) -> str:
        if not self._conversation_history:
            return "No prior turns."
        rendered = []
        for item in self._conversation_history[-10:]:
            role = item.get("role", "unknown").upper()
            text = item.get("text", "")
            rendered.append(f"{role}: {text}")
        return "\n".join(rendered)

    def _is_probable_echo(self, transcript: str) -> bool:
        now = time.monotonic()
        if now - self._last_agent_utterance_at > 8.0:
            return False
        t = self._normalize_text(transcript)
        a = self._normalize_text(self._last_agent_utterance)
        if not t or not a:
            return False
        return t in a or a.startswith(t)

    async def _stream_tts_audio(self, text: str) -> bool:
        """
        Convert text to speech and stream audio chunks to the frontend.

        Primary:  Amazon Nova Sonic Realtime API (if AWS active + NOVA_API_KEY set)
        Fallback: Google Gemini Live API

        Returns True if audio was generated, False on any failure.
        """
        from utils.model_provider import is_aws_active

        if is_aws_active():
            ok = await self._stream_tts_nova(text)
            if ok:
                return True
            logger.warning(
                f"[{self.agent_id}] Nova Sonic TTS failed — falling back to Gemini"
            )

        return await self._stream_tts_gemini(text)

    async def _stream_tts_nova(self, text: str) -> bool:
        """
        TTS via Amazon Nova Sonic Realtime WebSocket API.
        Protocol: connect → session.update → conversation.item.create → receive audio.
        """
        import json as _json
        import ssl
        from utils.events import push_event_direct

        try:
            import websockets
        except ImportError:
            logger.debug(f"[{self.agent_id}] websockets package not available")
            return False

        settings = get_settings()
        if (
            not settings.nova_api_key
            or settings.nova_api_key.startswith("your-")
        ):
            return False

        try:
            ssl_context = ssl.create_default_context()
            url = "wss://api.nova.amazon.com/v1/realtime?model=nova-2-sonic-v1"
            headers = {
                "Authorization": f"Bearer {settings.nova_api_key}",
                "Origin": "https://api.nova.amazon.com",
            }

            got_audio = False
            chunk_count = 0
            logger.info(
                f"[{self.agent_id}] TTS connecting to Nova Sonic "
                f"(voice={self.assigned_voice})"
            )

            async with websockets.connect(
                url, ssl=ssl_context, additional_headers=headers
            ) as ws:
                event = _json.loads(
                    await asyncio.wait_for(ws.recv(), timeout=10.0)
                )
                if event.get("type") != "session.created":
                    logger.warning(
                        f"[{self.agent_id}] Nova unexpected: {event.get('type')}"
                    )
                    return False

                await ws.send(_json.dumps({
                    "type": "session.update",
                    "session": {
                        "type": "realtime",
                        "instructions": "Read the following text naturally.",
                        "audio": {
                            "output": {
                                "voice": self.assigned_voice or "tiffany"
                            }
                        },
                    },
                }))
                await asyncio.wait_for(ws.recv(), timeout=10.0)

                await ws.send(_json.dumps({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": text}],
                    },
                }))

                while True:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=20.0)
                        event = _json.loads(raw)
                        etype = event.get("type", "")

                        if etype == "response.output_audio.delta":
                            audio_bytes = base64.b64decode(event["delta"])
                            audio_b64 = base64.b64encode(audio_bytes).decode()
                            chunk_count += 1
                            await push_event_direct(
                                self.session_id,
                                "agent_audio_chunk",
                                {
                                    "agent_id": self.agent_id,
                                    "audio_b64": audio_b64,
                                    "sample_rate": 24000,
                                    "channels": 1,
                                    "bit_depth": 16,
                                },
                                source_agent_id=self.agent_id,
                            )
                            got_audio = True
                        elif etype == "response.done":
                            break
                        elif etype == "error":
                            logger.error(
                                f"[{self.agent_id}] Nova TTS error: "
                                f"{event.get('error', event)}"
                            )
                            break
                    except asyncio.TimeoutError:
                        logger.warning(f"[{self.agent_id}] Nova TTS receive timeout")
                        break

            logger.info(
                f"[{self.agent_id}] Nova TTS complete: {chunk_count} audio chunks"
            )
            return got_audio

        except Exception as e:
            logger.error(f"[{self.agent_id}] Nova Sonic TTS FAILED: {e}")
            return False

    async def _stream_tts_gemini(self, text: str) -> bool:
        """
        TTS via Google Gemini Live API.
        Uses google.genai client for audio-only generation.
        """
        from utils.events import push_event_direct
        try:
            from google import genai as _genai
            from google.genai import types as _gtypes
        except ImportError:
            logger.warning(
                f"[{self.agent_id}] google-genai not installed — TTS disabled"
            )
            return False

        settings = get_settings()
        if not settings.google_api_key:
            logger.warning(f"[{self.agent_id}] No GOOGLE_API_KEY — TTS disabled")
            return False

        try:
            client = _genai.Client(api_key=settings.google_api_key)
            live_config = _gtypes.LiveConnectConfig(
                response_modalities=["AUDIO"],
                speech_config=_gtypes.SpeechConfig(
                    voice_config=_gtypes.VoiceConfig(
                        prebuilt_voice_config=_gtypes.PrebuiltVoiceConfig(
                            voice_name=self.assigned_voice
                        )
                    )
                ),
            )
            got_audio = False
            chunk_count = 0
            logger.info(
                f"[{self.agent_id}] TTS connecting to Gemini Live "
                f"(model={settings.gemini_realtime_model}, "
                f"voice={self.assigned_voice})"
            )
            async with client.aio.live.connect(
                model=settings.gemini_realtime_model,
                config=live_config,
            ) as session:
                await session.send(input=text, end_of_turn=True)
                async for response in session.receive():
                    if response.data:
                        audio_b64 = base64.b64encode(response.data).decode()
                        chunk_count += 1
                        await push_event_direct(
                            self.session_id,
                            "agent_audio_chunk",
                            {
                                "agent_id": self.agent_id,
                                "audio_b64": audio_b64,
                                "sample_rate": 24000,
                                "channels": 1,
                                "bit_depth": 16,
                            },
                            source_agent_id=self.agent_id,
                        )
                        got_audio = True
                    turn_done = (
                        response.server_content
                        and getattr(response.server_content, "turn_complete", False)
                    )
                    if turn_done:
                        break
            logger.info(
                f"[{self.agent_id}] Gemini TTS complete: "
                f"{chunk_count} audio chunks streamed"
            )
            return got_audio
        except Exception as e:
            logger.error(f"[{self.agent_id}] Gemini Live TTS FAILED: {e}")
            return False

    async def _generate_and_speak_reply(self, user_text: str, is_directive: bool = False) -> None:
        from utils.events import push_event, push_event_direct
        from config.constants import (
            EVENT_AGENT_THINKING,
            EVENT_AGENT_SPEAKING_START,
            EVENT_AGENT_SPEAKING_CHUNK,
            EVENT_AGENT_SPEAKING_END,
            EVENT_AGENT_INTERRUPTED,
            EVENT_AGENT_STATUS_CHANGE,
        )

        async with self._speak_lock:
            normalized_user = self._normalize_text(user_text)
            now = time.monotonic()
            if (
                normalized_user
                and normalized_user == self._last_user_input
                and (now - self._last_user_input_at) < 3.0
            ):
                logger.info(f"[{self.agent_id}] Dropping duplicate user input")
                return
            self._last_user_input = normalized_user
            self._last_user_input_at = now
            self._append_conversation("chairman", user_text)

            await push_event(self.session_id, EVENT_AGENT_THINKING, {"agent_id": self.agent_id})
            logger.info(
                f"[VOICE_RUNTIME] session={self.session_id} agent={self.agent_id} "
                f"{self.voice_runtime_summary()}"
            )
            reply_text = await self._generate_llm_reply(user_text)
            if not reply_text:
                return
            if not self._introduced:
                self._introduced = True
            self._append_conversation("agent", reply_text)
            self._last_agent_utterance = reply_text
            self._last_agent_utterance_at = time.monotonic()

            holding_turn = False
            allow_interruptions = bool(
                self.livekit_session_config.get("voice_options", {}).get(
                    "allow_interruptions", True
                )
            )
            try:
                if self.turn_manager:
                    if is_directive:
                        wait_start = time.monotonic()
                        while True:
                            acquired = await self.turn_manager.try_acquire_turn(self.agent_id)
                            if acquired or time.monotonic() - wait_start > 45.0:
                                break
                            await asyncio.sleep(0.5)
                    else:
                        acquired = await self.turn_manager.try_acquire_turn(self.agent_id)

                    if not acquired:
                        return
                    holding_turn = True

                await push_event(self.session_id, EVENT_AGENT_SPEAKING_START, {
                    "agent_id": self.agent_id,
                    "character_name": self.role_config.get("character_name", "Agent"),
                    "voice_name": self.assigned_voice,
                })
                await push_event(self.session_id, EVENT_AGENT_STATUS_CHANGE, {
                    "agent_id": self.agent_id,
                    "status": "speaking",
                    "previous_status": "thinking",
                })
                await self._update_roster_status("speaking", "thinking")

                # Always push the text transcript so the UI stays in sync.
                await push_event_direct(
                    self.session_id,
                    EVENT_AGENT_SPEAKING_CHUNK,
                    {"agent_id": self.agent_id, "transcript_chunk": reply_text},
                    source_agent_id=self.agent_id,
                )

                # Stream TTS audio via Gemini Live API.
                # Run with a timeout so a hung TTS connection never blocks the loop.
                tts_task = asyncio.create_task(
                    self._stream_tts_audio(reply_text),
                    name=f"{self.agent_id}_tts",
                )

                # Word-count-based max speaking time as a hard ceiling
                word_count = len(reply_text.split())
                max_speak_secs = max(8.0, word_count * 0.55)
                deadline = time.monotonic() + max_speak_secs
                tts_done = False

                while time.monotonic() < deadline:
                    if (
                        allow_interruptions
                        and self.turn_manager
                        and self.turn_manager.should_yield(self.agent_id)
                    ):
                        tts_task.cancel()
                        await push_event(self.session_id, EVENT_AGENT_INTERRUPTED, {
                            "agent_id": self.agent_id,
                        })
                        await self._update_roster_status("listening", "speaking")
                        break
                    if tts_task.done():
                        tts_done = True
                        break
                    await asyncio.sleep(0.15)

                if not tts_task.done():
                    # TTS is still running past the deadline — let it finish
                    # in background but don't block the turn any longer.
                    tts_task.cancel()
                elif not tts_done:
                    pass  # interrupted

                # Small buffer after TTS completes for audio to finish playing
                if tts_done:
                    await asyncio.sleep(0.5)

                await push_event(self.session_id, EVENT_AGENT_SPEAKING_END, {
                    "agent_id": self.agent_id,
                    "full_transcript": reply_text,
                })
                await push_event(self.session_id, EVENT_AGENT_STATUS_CHANGE, {
                    "agent_id": self.agent_id,
                    "status": "listening",
                    "previous_status": "speaking",
                })
                await self._update_roster_status("listening", "speaking")
                await self._on_turn_complete(reply_text)
            finally:
                if holding_turn and self.turn_manager:
                    self.turn_manager.release_turn(self.agent_id)



    async def _autonomous_turn_trigger(self):
        """
        PERSISTENT LOOP: Per voice.md §1.6 — if no one speaks for N seconds,
        agent considers speaking based on board state.
        This keeps the room alive without the Chairman driving everything.

        TURN MANAGEMENT: Uses try_acquire (non-blocking) so agents don't
        pile up waiting.  If the floor is occupied, this cycle is skipped.
        """
        char = self.role_config.get("character_name", "Agent")
        title = self.role_config.get("role_title", "Advisor")

        # Warm up briefly, then keep room active.
        await asyncio.sleep(4)

        while self._running and self.live_session:
            try:
                # Poll frequently to accurately hit the 5-8s silence window
                await asyncio.sleep(1.0)

                if not self._running or not self.live_session:
                    break

                # ── Turn gating: skip if someone else is speaking ─────
                if self.turn_manager and not self.turn_manager.is_floor_free():
                    continue

                if self.turn_manager:
                    # Each agent picks a random silence target for their next autonomous turn
                    target_silence = getattr(self, '_current_target_silence', 0)
                    if not target_silence:
                        self._current_target_silence = random.uniform(5.5, 8.0)
                        target_silence = self._current_target_silence

                    silent_duration = time.monotonic() - self.turn_manager.last_turn_end_time
                    if silent_duration < target_silence:
                        continue
                        
                    # Target reached! Try to trigger, and pick a new target for next time
                    self._current_target_silence = random.uniform(5.5, 8.0)
                    
                    # Prevent multiple agents from triggering simultaneously (due to same polling cycle)
                    last_trigger = getattr(self.turn_manager, 'last_autonomous_trigger', 0)
                    if time.monotonic() - last_trigger < 6.0:
                        continue
                    self.turn_manager.last_autonomous_trigger = time.monotonic()

                # Read shared board state
                try:
                    doc = await self.crisis_ref.get()
                    board_data = doc.to_dict() if doc.exists else {}
                except Exception:
                    board_data = {}

                threat = board_data.get("threat_level", "elevated")
                score = board_data.get("resolution_score", 50)
                decisions = len(board_data.get("agreed_decisions", []))
                conflicts = len(board_data.get("open_conflicts", []))

                prompt = (
                    f"[BOARD STATE] Threat: {threat} | Score: {score}/100 | "
                    f"Decisions: {decisions} | Open conflicts: {conflicts}\n\n"
                    f"You are {char}, the {title}. "
                    f"Based on the current board state and your expertise, "
                    f"decide whether to speak now. If yes, make your point "
                    f"(2-3 sentences). If the situation doesn't warrant it, "
                    f"stay silent by saying nothing."
                )

                await self.send_text(prompt)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[{self.agent_id}] Auto-trigger error: {e}")
                await asyncio.sleep(5)

    # ── Chairman Input Handlers ───────────────────────────────────────

    async def receive_chairman_audio(self, pcm_bytes: bytes) -> None:
        """
        Called by VoiceRouter when Chairman targets this agent (or full room).
        Per voice.md §1.6 — puts into audio_in_queue, consumed by _voice_loop.

        ISOLATION: Only called for the intended agent. VoiceRouter enforces this.
        """
        await self.audio_in_queue.put(pcm_bytes)

    async def receive_text_command(self, text: str) -> None:
        """
        Chairman text command → agent responds in voice.
        Per voice.md §1.6.
        """
        await self.send_text(text)

    async def send_text(self, text: str) -> None:
        """
        Send text to the agent's voice loop queue.
        Queues to text_in_queue for processing by the voice loop.
        """
        await self.text_in_queue.put(text)

    async def send_audio(self, audio_data: bytes) -> None:
        """Send raw PCM audio to the agent's Live session."""
        await self.audio_in_queue.put(audio_data)

    async def _update_roster_status(self, status: str, previous_status: str = "") -> None:
        """
        Keep crisis_sessions.agent_roster status in sync with live speaking state
        so REST APIs reflect the same state as websocket events.
        """
        try:
            doc = await self.crisis_ref.get()
            if not doc.exists:
                return
            crisis = doc.to_dict() or {}
            roster = crisis.get("agent_roster", [])
            changed = False
            now = datetime.now(timezone.utc).isoformat()
            for entry in roster:
                if entry.get("agent_id") == self.agent_id:
                    if entry.get("status") != status:
                        entry["status"] = status
                        if status == "speaking":
                            entry["last_spoke_at"] = now
                        changed = True
                    break
            if changed:
                await self.crisis_ref.update({"agent_roster": roster, "updated_at": now})
        except Exception as e:
            logger.debug(f"[{self.agent_id}] roster status sync skipped: {e}")

    # ── Turn Complete Handler ─────────────────────────────────────────

    async def _on_turn_complete(self, transcript: str) -> None:
        """
        Per voice.md §1.5 — processes what agent said after each turn.
        Writes ONLY to this agent's own data. Never touches other agents.
        """
        now = datetime.now(timezone.utc).isoformat()

        # 1. Update last_statement in shared session (the ONE shared field)
        try:
            await self.crisis_ref.update({
                f"agent_last_statement_{self.agent_id}": transcript[:200],
                "last_speaker_agent_id": self.agent_id,
                "last_speaker_excerpt": transcript[:240],
                "updated_at": now,
            })
        except Exception as e:
            logger.warning(f"[{self.agent_id}] Failed to update last_statement: {e}")

        # 2. Append to THIS agent's private memory
        try:
            statement = {"text": transcript, "spoken_at": now}
            try:
                from google.cloud import firestore as fs
                await self.memory_ref.update({
                    "previous_statements": fs.ArrayUnion([statement]),
                    "last_spoke_at": now,
                })
            except Exception:
                doc = await self.memory_ref.get()
                data = doc.to_dict() if doc.exists else {}
                prev = data.get("previous_statements", [])
                if not isinstance(prev, list):
                    prev = []
                prev.append(statement)
                await self.memory_ref.set({
                    **data,
                    "previous_statements": prev[-20:],
                    "last_spoke_at": now,
                }, merge=True)
        except Exception as e:
            logger.warning(f"[{self.agent_id}] Failed to update private memory: {e}")

        # 3. Trigger Observer analysis so board/conflicts/intel keep evolving.
        try:
            from gateway.chairman_handler import get_observer_agent
            observer = get_observer_agent(self.session_id)
            if observer:
                await observer.analyze_statement(
                    session_id=self.session_id,
                    agent_id=self.agent_id,
                    transcript=transcript,
                )
        except Exception as e:
            logger.warning(f"[{self.agent_id}] Observer analysis failed: {e}")

    async def _clear_audio_buffer(self) -> None:
        """Clear pending audio chunks when interrupted."""
        while not self.audio_in_queue.empty():
            try:
                self.audio_in_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    # ── Lifecycle ────────────────────────────────────────────────────

    async def close(self) -> None:
        """Clean up: cancel background tasks and close voice session."""
        self._running = False

        # Cancel all background tasks
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []

        # Mark live session as closed
        self.live_session = None

        if self._nova_sonic_model:
            try:
                await self._nova_sonic_model.aclose()
            except Exception:
                pass
            self._nova_sonic_model = None

        try:
            await self.memory_ref.update({"voice_session_active": False})
        except Exception:
            pass

        logger.info(f"[{self.agent_id}] Closed cleanly")

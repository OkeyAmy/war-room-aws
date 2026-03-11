"""
WAR ROOM — Constants
Voice pool, event types, Firestore collection names, and static config.
"""

# ── FIRESTORE COLLECTIONS ────────────────────────────────────────────────
COLLECTION_CRISIS_SESSIONS = "crisis_sessions"
COLLECTION_AGENT_MEMORY = "agent_memory"
COLLECTION_AGENT_SKILLS = "agent_skills"
COLLECTION_SESSION_EVENTS = "session_events"
COLLECTION_DOCUMENT_DRAFTS = "document_drafts"
SUBCOLLECTION_EVENTS = "events"

# ── SESSION STATUSES ─────────────────────────────────────────────────────
SESSION_ASSEMBLING = "assembling"
SESSION_BRIEFING = "briefing"
SESSION_ACTIVE = "active"
SESSION_ESCALATION = "escalation"
SESSION_RESOLUTION = "resolution"
SESSION_CLOSED = "closed"

# ── AGENT STATUSES ───────────────────────────────────────────────────────
AGENT_IDLE = "idle"
AGENT_THINKING = "thinking"
AGENT_SPEAKING = "speaking"
AGENT_CONFLICTED = "conflicted"
AGENT_SILENT = "silent"

# ── THREAT LEVELS ────────────────────────────────────────────────────────
THREAT_CONTAINED = "contained"
THREAT_ELEVATED = "elevated"
THREAT_CRITICAL = "critical"
THREAT_MELTDOWN = "meltdown"

THREAT_LEVEL_THRESHOLDS = {
    THREAT_MELTDOWN: 20,    # score < 20
    THREAT_CRITICAL: 35,    # score < 35
    THREAT_ELEVATED: 55,    # score < 55
    THREAT_CONTAINED: 100,  # score >= 55
}

# ── INTEL SOURCES ────────────────────────────────────────────────────────
INTEL_WORLD = "WORLD"
INTEL_MEDIA = "MEDIA"
INTEL_LEGAL = "LEGAL"
INTEL_INTERNAL = "INTERNAL"
INTEL_SOCIAL = "SOCIAL"

# ── CRISIS DOMAINS ───────────────────────────────────────────────────────
DOMAIN_CORPORATE = "corporate"
DOMAIN_MILITARY = "military"
DOMAIN_MEDICAL = "medical"
DOMAIN_POLITICAL = "political"
DOMAIN_FANTASY = "fantasy"
DOMAIN_OTHER = "other"

# ── EVENT TYPES ──────────────────────────────────────────────────────────
EVENT_SESSION_STATUS = "session_status"
EVENT_AGENT_ASSEMBLING = "agent_assembling"
EVENT_SESSION_READY = "session_ready"
EVENT_AGENT_STATUS_CHANGE = "agent_status_change"
EVENT_AGENT_SPEAKING_START = "agent_speaking_start"
EVENT_AGENT_SPEAKING_CHUNK = "agent_speaking_chunk"
EVENT_AGENT_SPEAKING_END = "agent_speaking_end"
EVENT_AGENT_INTERRUPTED = "agent_interrupted"
EVENT_AGENT_THINKING = "agent_thinking"
EVENT_DECISION_AGREED = "decision_agreed"
EVENT_CONFLICT_OPENED = "conflict_opened"
EVENT_CONFLICT_RESOLVED = "conflict_resolved"
EVENT_INTEL_DROPPED = "intel_dropped"
EVENT_FEED_ITEM = "feed_item"
EVENT_OBSERVER_INSIGHT = "observer_insight"
EVENT_TRUST_SCORE_UPDATE = "trust_score_update"
EVENT_POSTURE_UPDATE = "posture_update"
EVENT_SCORE_UPDATE = "score_update"
EVENT_CRISIS_ESCALATION = "crisis_escalation"
EVENT_THREAT_LEVEL_CHANGE = "threat_level_change"
EVENT_TIMER_TICK = "timer_tick"
EVENT_CHAIRMAN_SPOKE = "chairman_spoke"
EVENT_RESOLUTION_MODE_START = "resolution_mode_start"
EVENT_AGENT_FINAL_POSITION = "agent_final_position"
EVENT_SESSION_RESOLVED = "session_resolved"
EVENT_DOCUMENT_UPDATED = "document_updated"
EVENT_DEADLINE_RISK_FLAGGED = "deadline_risk_flagged"
EVENT_SESSION_FINALIZING = "session_finalizing"
EVENT_SESSION_PACKAGE_READY = "session_package_ready"

# ── NOVA SONIC VOICE POOL ─────────────────────────────────────────────────
# Named voices available in Amazon Nova Sonic.
NOVA_VOICE_POOL = [
    "tiffany", "matthew", "olivia", "liam", "sophia",
    "jackson", "emma", "aiden", "isabella", "lucas",
    "mia", "ethan", "charlotte", "noah", "amelia", "james",
]

# Maps agent voice_style → ordered list of Nova Sonic voice names.
# The scenario analyst sets voice_style per agent; assignment picks the
# first unused voice from the matching candidates.
NOVA_VOICE_STYLE_MAP: dict[str, list[str]] = {
    "authoritative": ["matthew", "james",    "ethan",    "lucas"],
    "warm":          ["tiffany", "sophia",   "isabella", "amelia", "mia"],
    "clipped":       ["liam",    "jackson",  "noah",     "aiden"],
    "measured":      ["olivia",  "charlotte","emma",     "tiffany"],
    "urgent":        ["aiden",   "matthew",  "lucas",    "ethan"],
    "calm":          ["tiffany", "olivia",   "mia",      "charlotte"],
    "aggressive":    ["james",   "ethan",    "jackson",  "noah"],
}

# ── GEMINI LIVE VOICE POOL ────────────────────────────────────────────────
# Named voices available in the Gemini Live (realtime) API.
GEMINI_VOICE_POOL = [
    "Puck", "Charon", "Kore", "Fenrir", "Aoede",
    "Orbit", "Zephyr", "Oberon", "Orus",
    "Achird", "Algenib", "Algieba", "Alnilam",
    "Auva", "Callirrhoe", "Despina", "Enceladus", "Erinome",
    "Gacrux", "Iapetus", "Laomedeia", "Leda",
    "Pulcherrima", "Rasalgethi", "Sadachbia", "Sadaltager",
    "Schedar", "Sulafat", "Umbriel", "Vindemiatrix",
    "Zubenelgenubi",
]

# Maps agent voice_style → ordered list of Gemini Live voice names.
GEMINI_VOICE_STYLE_MAP: dict[str, list[str]] = {
    "authoritative": ["Fenrir",  "Charon",  "Orus",     "Oberon"],
    "warm":          ["Kore",    "Aoede",   "Callirrhoe","Leda"],
    "clipped":       ["Puck",    "Zephyr",  "Gacrux",   "Achird"],
    "measured":      ["Charon",  "Orbit",   "Sulafat",  "Schedar"],
    "urgent":        ["Aoede",   "Fenrir",  "Alnilam",  "Erinome"],
    "calm":          ["Kore",    "Umbriel", "Sadachbia","Orbit"],
    "aggressive":    ["Fenrir",  "Orus",    "Rasalgethi","Oberon"],
}

# Combined pool used as a generic fallback (e.g. voice_discovery).
# Populated at runtime based on active provider.
ALLOWED_VOICE_POOL = NOVA_VOICE_POOL

# Legacy alias kept for backwards compatibility with health checks.
VOICE_STYLE_MAP = NOVA_VOICE_STYLE_MAP

# ── POSTURE DEFAULTS ─────────────────────────────────────────────────────
DEFAULT_POSTURE = {
    "public_exposure": 60,
    "legal_exposure": 45,
    "internal_stability": 50,
    "public_trend": "rising",
    "legal_trend": "stable",
    "internal_trend": "stable",
}

# ── ESCALATION EVENT TYPES ───────────────────────────────────────────────
ESCALATION_TYPES = ["media", "legal", "internal", "social", "operational"]

# ── RISK AXES BY ROLE ────────────────────────────────────────────────────
ROLE_RISK_AXES = {
    "legal":    "legal_exposure",
    "pr":       "public_exposure",
    "engineer": "internal_stability",
    "finance":  "legal_exposure",
    "ops":      "internal_stability",
    "comms":    "public_exposure",
    "strategy": "resolution_score",
}

"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import TopCommandBar from "@/components/war-room/TopCommandBar";
import AgentRoster, { type Agent } from "@/components/war-room/AgentRoster";
import CrisisBoard, {
  type DecisionItem,
  type ConflictItem,
  type IntelItem,
  type EscalationEvent,
} from "@/components/war-room/CrisisBoard";
import CrisisFeed, { type FeedItem } from "@/components/war-room/CrisisFeed";
import AgentVoicePods from "@/components/war-room/AgentVoicePods";
import {
  RoomIntelligence,
  CrisisPosture,
  ResolutionScore,
  type IntelligenceItem,
  type PostureLevel,
  type ScoreContributor,
  type IntelAlert,
  type TrustScore,
} from "@/components/war-room/RightPanels";
import ChairmanCommandBar from "@/components/war-room/ChairmanCommandBar";

// ─── Seed Data ────────────────────────────────────────────────────────────────

const INITIAL_AGENTS: Agent[] = [
  { id: "a1", name: "ATLAS", surname: "Strategic", role: "Strategic Analyst", status: "speaking", trustScore: 87, lastWords: "Containment window is closing fast" },
  { id: "a2", name: "NOVA", surname: "Legal", role: "Legal Counsel", status: "thinking", trustScore: 92, lastWords: "We need to verify liability exposure" },
  { id: "a3", name: "CIPHER", surname: "Intel", role: "Intelligence Officer", status: "listening", trustScore: 78, lastWords: "Signal intercept confirmed", conflictWith: "ATLAS" },
  { id: "a4", name: "FELIX", surname: "Ops", role: "Field Operations", status: "conflicted", trustScore: 65, lastWords: "Deploy now, ask later", conflictWith: "NOVA" },
  { id: "a5", name: "ORACLE", surname: "Data", role: "Data Analyst", status: "silent", trustScore: 81, lastWords: "Probability of escalation: 74%" },
  { id: "a6", name: "VANGUARD", surname: "Comms", role: "Communications Lead", status: "listening", trustScore: 73, lastWords: "Media is already aware" },
];

const INITIAL_DECISIONS: DecisionItem[] = [
  { id: "d1", text: "Activate secondary containment protocol and isolate affected nodes immediately.", time: "14:32:01", proposedBy: "ATLAS" },
  { id: "d2", text: "Brief external stakeholders with prepared statement by 15:00 UTC.", time: "14:28:44", proposedBy: "VANGUARD" },
];

const INITIAL_CONFLICTS: ConflictItem[] = [
  { id: "c1", description: "FELIX insists on immediate field deployment; NOVA flags legal risk of unauthorized action in jurisdiction.", agentA: "FELIX", agentB: "NOVA" },
];

const INITIAL_INTEL: IntelItem[] = [
  { id: "i1", text: "External actor attempted perimeter breach at 14:29 UTC. Three vectors confirmed. Origin: indeterminate.", source: "CIPHER / SIGINT" },
  { id: "i2", text: "Internal audit log shows anomalous access pattern starting 13:54 UTC. User token: revoked.", source: "ORACLE / SIEM" },
];

const INITIAL_FEED: FeedItem[] = [
  { id: "f1", timestamp: "14:32:01", source: "ATLAS", text: "Containment window is closing. We have 6 minutes max before this becomes uncontrollable.", category: "INTERNAL" },
  { id: "f2", timestamp: "14:31:48", source: "REUTERS", text: "Rumors of hospital data breach circulating in medical forums.", category: "MEDIA", isBreaking: true },
  { id: "f3", timestamp: "14:31:22", source: "LEGAL", text: "Privacy violation risks identified in secondary system access.", category: "LEGAL" },
  { id: "f4", timestamp: "14:30:55", source: "SYSTEM", text: "Threat level updated: ELEVATED → CRITICAL", category: "INTERNAL" },
  { id: "f5", timestamp: "14:30:11", source: "SOCIAL", text: "Viral post claiming medical records are being leaked on dark web.", category: "SOCIAL", metrics: "12K impressions" },
];

const INITIAL_INTEL_ITEMS: IntelligenceItem[] = [
  { id: "ri1", label: "Agents Active", value: "6 / 6", trend: "neutral" },
  { id: "ri2", label: "Conflicts Open", value: "1", trend: "neutral", critical: false },
  { id: "ri3", label: "Decisions Locked", value: "2", trend: "up" },
  { id: "ri4", label: "Intel Items", value: "2", trend: "up" },
  { id: "ri5", label: "Session Health", value: "NOMINAL", trend: "neutral" },
];

const INITIAL_ALERTS: IntelAlert[] = [
  { id: "ra1", type: "CONTRADICTION", text: "ATLAS claims containment is stable, but CIPHER reports perimeter breach.", timestamp: "14:35:12", meta: "ATLAS vs CIPHER" },
  { id: "ra2", type: "ALLIANCE", text: "NOVA and CIPHER are aligning on legal-intel data protocol.", timestamp: "14:34:45" },
  { id: "ra3", type: "BLIND_SPOT", text: "No response plan for public data leak in European markets.", timestamp: "14:33:20" },
];

const INITIAL_TRUST: TrustScore[] = [
  { agentName: "ATLAS", score: 87 },
  { agentName: "NOVA", score: 92 },
  { agentName: "CIPHER", score: 78 },
  { agentName: "FELIX", score: 65 },
  { agentName: "ORACLE", score: 81 },
  { agentName: "VANGUARD", score: 73 },
];

const INITIAL_CONTRIBUTORS: ScoreContributor[] = [
  { label: "Team Alignment", value: 62, positive: true },
  { label: "Decision Velocity", value: 78, positive: true },
  { label: "Open Conflicts", value: 40, positive: false },
  { label: "Intel Coverage", value: 85, positive: true },
];

// ─── Simulation Helpers ───────────────────────────────────────────────────────

function timestamp(): string {
  const now = new Date();
  return `${String(now.getUTCHours()).padStart(2, "0")}:${String(now.getUTCMinutes()).padStart(2, "0")}:${String(now.getUTCSeconds()).padStart(2, "0")}`;
}

function nextFeedId() {
  return `f-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

let decisionCounter = 10;
function nextDecisionId() {
  return `d${++decisionCounter}`;
}

let conflictCounter = 10;
function nextConflictId() {
  return `c${++conflictCounter}`;
}

let intelCounter = 10;
function nextIntelId() {
  return `i${++intelCounter}`;
}

const SIMULATION_SPEECHES = [
  { agent: "ATLAS", category: "INTERNAL" as const, text: "We need to accelerate the decision cycle. Every second of delay compounds risk." },
  { agent: "NOVA", category: "LEGAL" as const, text: "I can compress the legal review to 90 seconds if we narrow scope. Give me the parameters." },
  { agent: "CIPHER", category: "INTERNAL" as const, text: "New signal intercept uploaded to secure channel. Priority: HIGH." },
  { agent: "ORACLE", category: "INTERNAL" as const, text: "Scenario delta updated. Probability of full escalation now at 81%." },
  { agent: "FELIX", category: "INTERNAL" as const, text: "Field team is standing by. We are burning time." },
  { agent: "VANGUARD", category: "MEDIA" as const, text: "Media silence will break in approximately 4 minutes. I recommend immediate release." },
];

const SIMULATION_INTEL = [
  { text: "Thermal imaging detects unauthorized personnel at coordinates redacted. Count: 3.", source: "FIELD / SAT-4" },
  { text: "Dark web chatter references operation codename matching our incident. Confidence: medium.", source: "CIPHER / OSINT" },
  { text: "External actor communicated via encrypted channel at 14:35 UTC. Content: unknown.", source: "NSA LIAISON" },
];

const SIMULATION_DECISIONS = [
  { text: "Authorize FELIX for limited perimeter deployment under executive mandate. Duration: 30 minutes.", proposedBy: "ATLAS" },
  { text: "Issue public statement draft B — non-confirmatory. Release via VANGUARD at 15:00 UTC.", proposedBy: "VANGUARD" },
  { text: "Revoke all external API tokens effective immediately. Review window: 2 hours.", proposedBy: "ORACLE" },
];

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function WarRoomPage() {
  const [agents, setAgents] = useState<Agent[]>(INITIAL_AGENTS);
  const [decisions, setDecisions] = useState<DecisionItem[]>(INITIAL_DECISIONS);
  const [conflicts, setConflicts] = useState<ConflictItem[]>(INITIAL_CONFLICTS);
  const [intel, setIntel] = useState<IntelItem[]>(INITIAL_INTEL);
  const [feed, setFeed] = useState<FeedItem[]>(INITIAL_FEED);
  const [escalation, setEscalation] = useState<EscalationEvent | null>(null);
  const [intelItems, setIntelItems] = useState<IntelligenceItem[]>(INITIAL_INTEL_ITEMS);
  const [intelAlerts, setIntelAlerts] = useState<IntelAlert[]>(INITIAL_ALERTS);
  const [trustScores, setTrustScores] = useState<TrustScore[]>(INITIAL_TRUST);
  const [postureLevel, setPostureLevel] = useState<PostureLevel>(3);
  const [resolutionScore, setResolutionScore] = useState(42);
  const [scoreDelta, setScoreDelta] = useState(+3);
  const [contributors, setContributors] = useState<ScoreContributor[]>(INITIAL_CONTRIBUTORS);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [activeSpeakerId, setActiveSpeakerId] = useState<string | null>("a1");
  const [micActive, setMicActive] = useState(false);
  const [sessionTimeLeft, setSessionTimeLeft] = useState(5400); // 90 min
  const [commandHistory, setCommandHistory] = useState<string[]>([]);

  const speechIdx = useRef(0);
  const intelIdx = useRef(0);
  const decisionIdx = useRef(0);

  // Session countdown
  useEffect(() => {
    const t = setInterval(() => {
      setSessionTimeLeft((s) => Math.max(0, s - 1));
    }, 1000);
    return () => clearInterval(t);
  }, []);

  // Remove "isNew" flags after 4 seconds
  const clearNewFlags = useCallback(() => {
    setTimeout(() => {
      setFeed((f) => f.map((e) => ({ ...e, isNew: false })));
      setDecisions((d) => d.map((e) => ({ ...e, isNew: false })));
      setConflicts((c) => c.map((e) => ({ ...e, isNew: false })));
      setIntel((i) => i.map((e) => ({ ...e, isNew: false })));
    }, 4000);
  }, []);

  // Add feed entry helper
  const addFeedEntry = useCallback((entry: Omit<FeedItem, "id" | "timestamp" | "isNew">) => {
    const newEntry: FeedItem = {
      ...entry,
      id: nextFeedId(),
      timestamp: timestamp(),
      isNew: true,
    };
    setFeed((f) => [newEntry, ...f].slice(0, 80));
    clearNewFlags();
  }, [clearNewFlags]);

  // Rotate agent statuses
  const rotateAgentStatuses = useCallback(() => {
    const statusCycle: Array<Agent["status"]> = ["speaking", "thinking", "listening", "silent", "listening"];
    setAgents((prev) => {
      const updated = [...prev];
      const idx = Math.floor(Math.random() * updated.length);
      const current = updated[idx].status;
      const nextStatus = statusCycle[(statusCycle.indexOf(current) + 1) % statusCycle.length];
      updated[idx] = { ...updated[idx], status: nextStatus };
      // Update active speaker
      const speaking = updated.find((a) => a.status === "speaking");
      setActiveSpeakerId(speaking?.id ?? null);
      return updated;
    });
  }, []);

  // Simulation tick — every 5 seconds something happens
  useEffect(() => {
    const tick = setInterval(() => {
      const roll = Math.random();

      if (roll < 0.45) {
        // New feed entry (speech/action)
        const s = SIMULATION_SPEECHES[speechIdx.current % SIMULATION_SPEECHES.length];
        speechIdx.current++;
        addFeedEntry({ source: s.agent, category: s.category, text: s.text });
        rotateAgentStatuses();
      } else if (roll < 0.65) {
        // New intel
        const item = SIMULATION_INTEL[intelIdx.current % SIMULATION_INTEL.length];
        intelIdx.current++;
        const newIntel: IntelItem = {
          id: nextIntelId(),
          text: item.text,
          source: item.source,
          isNew: true,
        };
        setIntel((prev) => [newIntel, ...prev].slice(0, 20));
        addFeedEntry({ source: "SYSTEM", category: "INTERNAL", text: `// new intel received from ${item.source}` });
        setIntelItems((prev) =>
          prev.map((i) => (i.id === "ri4" ? { ...i, value: String(Number(i.value) + 1) } : i))
        );
        clearNewFlags();
      } else if (roll < 0.80) {
        // New decision
        const d = SIMULATION_DECISIONS[decisionIdx.current % SIMULATION_DECISIONS.length];
        decisionIdx.current++;
        const newDecision: DecisionItem = {
          id: nextDecisionId(),
          text: d.text,
          time: timestamp(),
          proposedBy: d.proposedBy,
          isNew: true,
        };
        setDecisions((prev) => [newDecision, ...prev].slice(0, 20));
        addFeedEntry({ source: d.proposedBy, category: "INTERNAL", text: `DECISION PROPOSED: ${d.text.slice(0, 60)}...` });
        setResolutionScore((s) => {
          const next = Math.min(100, s + 4);
          setScoreDelta(4);
          return next;
        });
        setIntelItems((prev) =>
          prev.map((i) => (i.id === "ri3" ? { ...i, value: String(Number(i.value) + 1) } : i))
        );
        clearNewFlags();
      } else if (roll < 0.90) {
        // Escalation banner flash
        const evt: EscalationEvent = {
          id: `esc-${Date.now()}`,
          text: "New external threat vector detected — reviewing containment status.",
          time: timestamp(),
          visible: true,
        };
        setEscalation(evt);
        addFeedEntry({ source: "SYSTEM", category: "INTERNAL", text: "⚠ ESCALATION: New external threat vector detected." });
        setPostureLevel((p) => Math.min(5, p + 1) as PostureLevel);
        setTimeout(() => setEscalation(null), 8000);
      } else {
        // Score drift
        const delta = Math.round((Math.random() - 0.4) * 8);
        setResolutionScore((s) => Math.max(0, Math.min(100, s + delta)));
        setScoreDelta(delta);
        rotateAgentStatuses();
      }
    }, 5000);

    return () => clearInterval(tick);
  }, [addFeedEntry, clearNewFlags, rotateAgentStatuses]);

  // Chairman command
  const handleCommand = useCallback((cmd: string) => {
    setCommandHistory((h) => [...h, cmd]);
    addFeedEntry({ source: "CHAIRMAN", category: "INTERNAL", text: `[CMD] ${cmd}` });

    // React to specific commands
    const upper = cmd.toUpperCase();
    if (upper.includes("ESCALATE")) {
      setPostureLevel((p) => Math.min(5, p + 1) as PostureLevel);
    }
    if (upper.includes("LOCK DECISION") || upper.includes("LOCK")) {
      setResolutionScore((s) => Math.min(100, s + 6));
      setScoreDelta(6);
    }
    if (upper.includes("CALL VOTE")) {
      addFeedEntry({ source: "SYSTEM", category: "INTERNAL", text: "// vote initiated by chairman — awaiting agent responses" });
    }
    if (upper.includes("BRIEF ALL")) {
      agents.forEach((a) =>
        setAgents((prev) => prev.map((ag) => (ag.id === a.id ? { ...ag, status: "listening" } : ag)))
      );
    }
    if (upper.includes("STATUS REPORT")) {
      addFeedEntry({ source: "ORACLE", category: "INTERNAL", text: `Status: ${agents.filter(a => a.status !== 'silent').length} agents active. Posture level ${postureLevel}/5. Resolution score: ${resolutionScore}.` });
    }
  }, [addFeedEntry, agents, postureLevel, resolutionScore]);

  return (
    <div
      className="war-room-app"
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
      }}
    >
      {/* ── Top Command Bar ─────────────────────────────────── */}
      <TopCommandBar
        crisisTitle="OPERATION BLACKSITE — SECTOR 7 BREACH"
        threatLevel={postureLevel >= 4 ? "CRITICAL" : postureLevel >= 3 ? "CRITICAL" : postureLevel >= 2 ? "ELEVATED" : "CONTAINED"}
        micActive={micActive}
        sessionTimeLeft={sessionTimeLeft}
      />

      {/* ── Main Body ────────────────────────────────────────── */}
      <div style={{ flex: 1, display: "flex", overflow: "hidden", minHeight: 0 }}>

        {/* Left: Agent Roster */}
        <AgentRoster
          agents={agents}
          selectedAgentId={selectedAgentId}
          onSelectAgent={setSelectedAgentId}
        />

        {/* Center Column */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minWidth: 0 }}>

          {/* Center Top: Crisis Board */}
          <div style={{ flex: 1, overflow: "hidden", minHeight: 0 }}>
            <CrisisBoard
              decisions={decisions}
              conflicts={conflicts}
              intel={intel}
              escalation={escalation}
            />
          </div>

          {/* Center Bottom Row */}
          <div
            style={{
              height: "220px",
              flexShrink: 0,
              display: "flex",
              borderTop: "1px solid #1E2D3D",
              overflow: "hidden",
            }}
          >
            {/* Crisis Feed */}
            <div style={{ width: "260px", flexShrink: 0, borderRight: "1px solid #1E2D3D", overflow: "hidden" }}>
              <CrisisFeed items={feed} />
            </div>

            {/* Agent Voice Pods */}
            <div style={{ flex: 1, overflow: "hidden" }}>
              <AgentVoicePods
                agents={agents}
              />
            </div>
          </div>
        </div>

        {/* Right: Panel Stack */}
        <div
          style={{
            width: "220px",
            flexShrink: 0,
            borderLeft: "1px solid #1E2D3D",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          <div className="wr-scrollbar" style={{ flex: 1, overflowY: "auto" }}>
            <RoomIntelligence 
              items={intelItems} 
              alerts={intelAlerts}
              trustScores={trustScores}
            />
            <div style={{ borderTop: "1px solid #1E2D3D" }}>
              <CrisisPosture
                level={postureLevel}
                label=""
                detail={
                  postureLevel <= 1
                    ? "Situation under control. Monitoring."
                    : postureLevel <= 2
                    ? "Elevated activity. Enhanced vigilance."
                    : postureLevel <= 3
                    ? "Active threat confirmed. Response ongoing."
                    : postureLevel <= 4
                    ? "Critical breach in progress. All hands."
                    : "MELTDOWN — cascading failure. Extreme measures."
                }
              />
            </div>
            <div style={{ borderTop: "1px solid #1E2D3D" }}>
              <ResolutionScore
                score={resolutionScore}
                delta={scoreDelta}
                contributors={contributors}
              />
            </div>
          </div>
        </div>
      </div>

      {/* ── Chairman Command Bar ─────────────────────────────── */}
      <ChairmanCommandBar
        onSendCommand={handleCommand}
        isMicActive={micActive}
        onToggleMic={() => setMicActive((m) => !m)}
        commandHistory={commandHistory}
      />
    </div>
  );
}

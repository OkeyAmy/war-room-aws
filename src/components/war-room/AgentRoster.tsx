"use client";

import { useState } from "react";

export type AgentStatus = "speaking" | "thinking" | "conflicted" | "listening" | "silent";

export interface Agent {
  id: string;
  name: string;
  surname: string;
  role: string;
  status: AgentStatus;
  trustScore: number;
  lastWords?: string;
  conflictWith?: string;
}

interface AgentRosterProps {
  agents: Agent[];
  selectedAgentId: string | null;
  onSelectAgent: (id: string | null) => void;
}

function SpeakingAnimation() {
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: "2px", height: "12px" }}>
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className={`wave-bar-${i}`}
          style={{
            width: "2px",
            background: "#00C896",
            borderRadius: "1px",
            height: "100%",
          }}
        />
      ))}
    </div>
  );
}

export default function AgentRoster({
  agents,
  selectedAgentId,
  onSelectAgent,
}: AgentRosterProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <div
      style={{
        width: "220px",
        flexShrink: 0,
        background: "#0D1117",
        borderRight: "1px solid #1E2D3D",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* Panel Header */}
      <div
        style={{
          height: "36px",
          padding: "0 16px",
          borderBottom: "1px solid #1E2D3D",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontFamily: "'Barlow Condensed', sans-serif",
            fontWeight: 600,
            fontSize: "11px",
            letterSpacing: "0.12em",
            color: "#8A9BB0",
          }}
        >
          CRISIS TEAM
        </span>
      </div>

      {/* Agent List */}
      <div className="wr-scrollbar" style={{ overflowY: "auto", flex: 1 }}>
        {agents.map((agent) => {
          const isSelected = selectedAgentId === agent.id;
          const isHovered = hoveredId === agent.id;

          return (
            <div
              key={agent.id}
              onClick={() => onSelectAgent(isSelected ? null : agent.id)}
              onMouseEnter={() => setHoveredId(agent.id)}
              onMouseLeave={() => setHoveredId(null)}
              style={{
                padding: "12px 16px",
                borderBottom: "1px solid #1E2D3D",
                background: isSelected || isHovered ? "#161F2A" : "transparent",
                cursor: "pointer",
                transition: "background 150ms ease",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
                <span
                  style={{
                    fontFamily: "'Rajdhani', sans-serif",
                    fontWeight: 600,
                    fontSize: "14px",
                    letterSpacing: "0.04em",
                    color: isSelected ? "#4A9EFF" : "#E8EDF2",
                  }}
                >
                  {agent.name}
                </span>
                {agent.status === "speaking" && <SpeakingAnimation />}
              </div>

              <div
                style={{
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontWeight: 400,
                  fontSize: "10px",
                  color: "#8A9BB0",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}
              >
                {agent.role}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

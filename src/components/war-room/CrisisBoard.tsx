"use client";

import { useState, useCallback, useEffect, useRef } from "react";

export interface DecisionItem {
  id: string;
  text: string;
  time: string;
  proposedBy: string;
  isNew?: boolean;
}

export interface ConflictItem {
  id: string;
  description: string;
  agentA: string;
  agentB: string;
  isNew?: boolean;
}

export interface IntelItem {
  id: string;
  text: string;
  source: string;
  isNew?: boolean;
}

export interface EscalationEvent {
  id: string;
  text: string;
  time: string;
  visible: boolean;
}

interface CrisisBoardProps {
  decisions: DecisionItem[];
  conflicts: ConflictItem[];
  intel: IntelItem[];
  escalation: EscalationEvent | null;
}

export default function CrisisBoard({
  decisions,
  conflicts,
  intel,
  escalation,
}: CrisisBoardProps) {
  const [colWidths, setColWidths] = useState([33.33, 33.33, 33.33]);
  const containerRef = useRef<HTMLDivElement>(null);
  const resizingCol = useRef<number | null>(null);

  const handleMouseDown = (index: number) => {
    resizingCol.current = index;
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    document.body.style.cursor = "col-resize";
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (resizingCol.current === null || !containerRef.current) return;

    const containerRect = containerRef.current.getBoundingClientRect();
    const mouseX = e.clientX - containerRect.left;
    const totalWidth = containerRect.width;
    const mousePercent = (mouseX / totalWidth) * 100;

    setColWidths((prev) => {
      const next = [...prev];
      if (resizingCol.current === 0) {
        const delta = mousePercent - prev[0];
        const newWidth = Math.max(15, Math.min(70, mousePercent));
        const diff = newWidth - prev[0];
        next[0] = newWidth;
        next[1] = Math.max(15, prev[1] - diff);
        // Normalize
        const sum = next[0] + next[1] + next[2];
        next[0] = (next[0] / sum) * 100;
        next[1] = (next[1] / sum) * 100;
        next[2] = (next[2] / sum) * 100;
      } else if (resizingCol.current === 1) {
        const currentPos = prev[0] + prev[1];
        const newPos = Math.max(prev[0] + 15, Math.min(85, mousePercent));
        const diff = newPos - currentPos;
        next[1] = Math.max(15, prev[1] + diff);
        next[2] = Math.max(15, prev[2] - diff);
        // Normalize
        const sum = next[0] + next[1] + next[2];
        next[0] = (next[0] / sum) * 100;
        next[1] = (next[1] / sum) * 100;
        next[2] = (next[2] / sum) * 100;
      }
      return next;
    });
  }, []);

  const handleMouseUp = useCallback(() => {
    resizingCol.current = null;
    document.removeEventListener("mousemove", handleMouseMove);
    document.removeEventListener("mouseup", handleMouseUp);
    document.body.style.cursor = "default";
  }, [handleMouseMove]);

  return (
    <div
      ref={containerRef}
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        background: "#080A0E",
        overflow: "hidden",
        position: "relative",
        height: "100%",
      }}
    >
      {/* Escalation Event Banner */}
      {escalation && escalation.visible && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            zIndex: 30,
            height: "48px",
            background: "rgba(255,107,0,0.12)",
            border: "1px solid #FF6B00",
            borderLeft: "4px solid #FF6B00",
            padding: "0 16px",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            animation: "escalationSlide 300ms cubic-bezier(0.16, 1, 0.3, 1) forwards",
          }}
        >
          <span style={{ fontSize: "18px" }}>📡</span>
          <span
            style={{
              fontFamily: "'Rajdhani', sans-serif",
              fontWeight: 600,
              fontSize: "13px",
              color: "#E8EDF2",
              flex: 1,
            }}
          >
            ESCALATION: {escalation.text}
          </span>
          <span
            style={{
              fontFamily: "'IBM Plex Mono', monospace",
              fontWeight: 400,
              fontSize: "10px",
              color: "#4A5568",
            }}
          >
            {escalation.time}
          </span>
        </div>
      )}

      {/* Panel Header */}
      <div
        style={{
          height: "36px",
          padding: "0 16px",
          borderBottom: "1px solid #1E2D3D",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "#0D1117",
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
          CRISIS BOARD
        </span>
      </div>

      {/* Three-Column Board with Resizing Handles */}
      <div
        style={{
          flex: 1,
          display: "flex",
          background: "#080A0E",
          overflow: "hidden",
          position: "relative",
        }}
      >
        {/* Column 1: AGREED DECISIONS */}
        <div style={{ width: `${colWidths[0]}%`, background: "#0D1117", display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div
            style={{
              background: "rgba(0,200,150,0.06)",
              borderBottom: "1px solid rgba(0,200,150,0.25)",
              padding: "8px 12px",
              flexShrink: 0,
            }}
          >
            <span
              style={{
                fontFamily: "'Barlow Condensed', sans-serif",
                fontWeight: 600,
                fontSize: "10px",
                letterSpacing: "0.12em",
                color: "#00C896",
              }}
            >
              ✓ AGREED DECISIONS
            </span>
          </div>
          <div className="wr-scrollbar" style={{ flex: 1, overflowY: "auto" }}>
            {decisions.map((item) => (
              <div
                key={item.id}
                className={item.isNew ? "item-new" : ""}
                style={{
                  padding: "8px 12px",
                  borderBottom: "1px solid #1E2D3D",
                }}
              >
                <div
                  style={{
                    fontFamily: "'IBM Plex Mono', monospace",
                    fontWeight: 400,
                    fontSize: "11px",
                    color: "#E8EDF2",
                    marginBottom: "4px",
                  }}
                >
                  ✅ {item.text}
                </div>
                <div
                  style={{
                    fontFamily: "'IBM Plex Mono', monospace",
                    fontWeight: 400,
                    fontSize: "9px",
                    color: "#4A5568",
                  }}
                >
                  {item.time} • {item.proposedBy}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Handle 1 */}
        <div
          onMouseDown={() => handleMouseDown(0)}
          style={{
            width: "4px",
            background: "#1E2D3D",
            cursor: "col-resize",
            zIndex: 10,
            transition: "background 150ms ease",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "#4A9EFF")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "#1E2D3D")}
        />

        {/* Column 2: OPEN CONFLICTS */}
        <div style={{ width: `${colWidths[1]}%`, background: "#0D1117", display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div
            style={{
              background: "rgba(255,45,45,0.06)",
              borderBottom: "1px solid rgba(255,45,45,0.25)",
              padding: "8px 12px",
              flexShrink: 0,
            }}
          >
            <span
              style={{
                fontFamily: "'Barlow Condensed', sans-serif",
                fontWeight: 600,
                fontSize: "10px",
                letterSpacing: "0.12em",
                color: "#FF2D2D",
              }}
            >
              ⚡ OPEN CONFLICTS
            </span>
          </div>
          <div className="wr-scrollbar" style={{ flex: 1, overflowY: "auto" }}>
            {conflicts.map((item) => (
              <div
                key={item.id}
                className={item.isNew ? "item-new" : ""}
                style={{
                  padding: "8px 12px",
                  borderBottom: "1px solid #1E2D3D",
                  borderLeft: "2px solid #FF2D2D",
                  background: "rgba(255,45,45,0.03)",
                }}
              >
                <div
                  style={{
                    fontFamily: "'IBM Plex Mono', monospace",
                    fontWeight: 400,
                    fontSize: "11px",
                    color: "#E8EDF2",
                    marginBottom: "4px",
                  }}
                >
                  🔥 {item.description}
                </div>
                <div
                  style={{
                    fontFamily: "'IBM Plex Mono', monospace",
                    fontWeight: 500,
                    fontSize: "9px",
                    color: "#FF6B00",
                  }}
                >
                  {item.agentA} ←→ {item.agentB}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Handle 2 */}
        <div
          onMouseDown={() => handleMouseDown(1)}
          style={{
            width: "4px",
            background: "#1E2D3D",
            cursor: "col-resize",
            zIndex: 10,
            transition: "background 150ms ease",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "#4A9EFF")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "#1E2D3D")}
        />

        {/* Column 3: CRITICAL INTEL */}
        <div style={{ width: `${colWidths[2]}%`, background: "#0D1117", display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div
            style={{
              background: "rgba(74,158,255,0.06)",
              borderBottom: "1px solid rgba(74,158,255,0.25)",
              padding: "8px 12px",
              flexShrink: 0,
            }}
          >
            <span
              style={{
                fontFamily: "'Barlow Condensed', sans-serif",
                fontWeight: 600,
                fontSize: "10px",
                letterSpacing: "0.12em",
                color: "#4A9EFF",
              }}
            >
              📌 CRITICAL INTEL
            </span>
          </div>
          <div className="wr-scrollbar" style={{ flex: 1, overflowY: "auto" }}>
            {intel.map((item) => (
              <div
                key={item.id}
                className={item.isNew ? "item-new" : ""}
                style={{
                  padding: "8px 12px",
                  borderBottom: "1px solid #1E2D3D",
                  borderLeft: "2px solid #4A9EFF",
                  background: "rgba(74,158,255,0.03)",
                }}
              >
                <div
                  style={{
                    fontFamily: "'IBM Plex Mono', monospace",
                    fontWeight: 400,
                    fontSize: "11px",
                    color: "#E8EDF2",
                    marginBottom: "4px",
                  }}
                >
                  📌 {item.text}
                </div>
                <div
                  style={{
                    fontFamily: "'IBM Plex Mono', monospace",
                    fontWeight: 400,
                    fontSize: "9px",
                    color: "#4A5568",
                  }}
                >
                  Source: {item.source}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

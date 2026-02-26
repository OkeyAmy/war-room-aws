"use client";

import { useState } from "react";

export interface FeedItem {
  id: string;
  source: string;
  timestamp: string;
  text: string;
  category: "WORLD" | "LEGAL" | "MEDIA" | "INTERNAL" | "SOCIAL";
  metrics?: string;
  isBreaking?: boolean;
  isNew?: boolean;
}

interface CrisisFeedProps {
  items: FeedItem[];
}

const CATEGORIES = ["WORLD", "LEGAL", "MEDIA", "INTERNAL", "SOCIAL"] as const;

export default function CrisisFeed({ items }: CrisisFeedProps) {
  const [activeCategory, setActiveCategory] = useState<(typeof CATEGORIES)[number] | "ALL">("ALL");

  const filteredItems = activeCategory === "ALL" 
    ? items 
    : items.filter(i => i.category === activeCategory);

  const icons: Record<FeedItem["category"], string> = {
    WORLD: "🌍",
    LEGAL: "⚖️",
    MEDIA: "📰",
    INTERNAL: "💬",
    SOCIAL: "🐦",
  };

  return (
    <div
      style={{
        width: "260px",
        height: "100%",
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
          padding: "0 12px",
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
          CRISIS FEED
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
          <div className="dot-live" style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#FF2D2D" }} />
          <span style={{ fontFamily: "'Barlow Condensed', sans-serif", fontWeight: 600, fontSize: "10px", color: "#FF2D2D" }}>LIVE</span>
        </div>
      </div>

      {/* Category Tab Bar */}
      <div
        style={{
          height: "32px",
          borderBottom: "1px solid #1E2D3D",
          display: "flex",
          alignItems: "stretch",
          padding: "0 4px",
          overflowX: "auto",
          gap: "2px",
          flexShrink: 0,
        }}
        className="wr-scrollbar"
      >
        {["ALL", ...CATEGORIES].map((cat) => {
          const isActive = activeCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat as any)}
              style={{
                background: isActive ? "rgba(74,158,255,0.08)" : "transparent",
                border: "none",
                borderBottom: isActive ? "2px solid #4A9EFF" : "2px solid transparent",
                color: isActive ? "#4A9EFF" : "#4A5568",
                fontFamily: "'Barlow Condensed', sans-serif",
                fontWeight: 500,
                fontSize: "10px",
                letterSpacing: "0.08em",
                padding: "0 8px",
                cursor: "pointer",
                transition: "all 150ms ease",
                whiteSpace: "nowrap",
              }}
            >
              {cat}
            </button>
          );
        })}
      </div>

      {/* Feed List */}
      <div className="wr-scrollbar" style={{ flex: 1, overflowY: "auto" }}>
        {filteredItems.map((item) => (
          <div
            key={item.id}
            className={item.isNew ? "item-new" : ""}
            style={{
              padding: "8px 10px",
              borderBottom: "1px solid #1E2D3D",
              background: item.isBreaking ? "rgba(255,45,45,0.05)" : "transparent",
              borderLeft: item.isBreaking ? "2px solid #FF2D2D" : item.isNew ? "2px solid #4A9EFF" : "2px solid transparent",
              cursor: "pointer",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <span style={{ fontSize: "10px" }}>{icons[item.category]}</span>
                <span
                  style={{
                    fontFamily: "'IBM Plex Mono', monospace",
                    fontWeight: 500,
                    fontSize: "10px",
                    color: item.isBreaking ? "#FF2D2D" : "#8A9BB0",
                  }}
                >
                  {item.isBreaking ? "🚨 BREAKING" : item.source}
                </span>
              </div>
              <span
                style={{
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontWeight: 400,
                  fontSize: "9px",
                  color: "#4A5568",
                }}
              >
                {item.timestamp}
              </span>
            </div>
            <div
              style={{
                fontFamily: "'IBM Plex Mono', monospace",
                fontWeight: 400,
                fontSize: "11px",
                color: "#E8EDF2",
                lineHeight: 1.4,
                marginBottom: item.metrics ? "4px" : "0",
              }}
            >
              {item.text}
            </div>
            {item.metrics && (
              <div
                style={{
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontWeight: 400,
                  fontSize: "9px",
                  color: "#FF2D2D",
                }}
              >
                ↗️ {item.metrics}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

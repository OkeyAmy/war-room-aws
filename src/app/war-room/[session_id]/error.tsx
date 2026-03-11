"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

interface WarRoomErrorProps {
    error: Error & { digest?: string };
    reset: () => void;
}

export default function WarRoomError({ error, reset }: WarRoomErrorProps) {
    const router = useRouter();

    useEffect(() => {
        console.error("[WAR ROOM] Runtime error caught by boundary:", error);
    }, [error]);

    return (
        <div style={{
            minHeight: "100vh",
            background: "#080A0E",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontFamily: "'IBM Plex Mono', monospace",
        }}>
            <div style={{
                maxWidth: "480px",
                width: "90%",
                border: "1px solid #2A1010",
                background: "#0D1117",
                padding: "32px",
                textAlign: "center",
            }}>
                {/* Icon */}
                <div style={{ marginBottom: "20px", display: "flex", justifyContent: "center" }}>
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="10" stroke="#FF2D2D" strokeWidth="1.5" />
                        <line x1="12" y1="8" x2="12" y2="12" stroke="#FF2D2D" strokeWidth="2" strokeLinecap="round" />
                        <circle cx="12" cy="16" r="1" fill="#FF2D2D" />
                    </svg>
                </div>

                <h1 style={{
                    fontFamily: "'Rajdhani', sans-serif",
                    fontWeight: 700,
                    fontSize: "20px",
                    letterSpacing: "0.12em",
                    color: "#E8EDF2",
                    margin: "0 0 8px",
                    textTransform: "uppercase",
                }}>
                    WAR ROOM FAULT
                </h1>

                <p style={{ fontSize: "11px", color: "#4A5568", letterSpacing: "0.06em", margin: "0 0 24px", lineHeight: 1.6 }}>
                    A critical error interrupted the session. You can attempt to restore the war room or return to base.
                </p>

                {process.env.NODE_ENV === "development" && (
                    <details style={{ textAlign: "left", marginBottom: "24px" }}>
                        <summary style={{ fontSize: "10px", color: "#4A5568", cursor: "pointer", marginBottom: "8px" }}>
                            ERROR DETAILS
                        </summary>
                        <pre style={{
                            fontSize: "10px", color: "#FF6B6B", background: "#0A0D12",
                            padding: "12px", overflow: "auto", maxHeight: "160px",
                            border: "1px solid #1E2D3D",
                        }}>
                            {error.message}
                            {error.stack && `\n\n${error.stack}`}
                            {error.digest && `\n\nDigest: ${error.digest}`}
                        </pre>
                    </details>
                )}

                <div style={{ display: "flex", gap: "12px", justifyContent: "center" }}>
                    <button
                        onClick={reset}
                        style={{
                            padding: "10px 20px",
                            background: "rgba(74,158,255,0.1)",
                            border: "1px solid #4A9EFF",
                            color: "#4A9EFF",
                            fontFamily: "'Barlow Condensed', sans-serif",
                            fontWeight: 600,
                            fontSize: "12px",
                            letterSpacing: "0.1em",
                            cursor: "pointer",
                            transition: "all 200ms ease",
                        }}
                    >
                        RETRY
                    </button>
                    <button
                        onClick={() => router.replace("/")}
                        style={{
                            padding: "10px 20px",
                            background: "transparent",
                            border: "1px solid #2A3D50",
                            color: "#8A9BB0",
                            fontFamily: "'Barlow Condensed', sans-serif",
                            fontWeight: 500,
                            fontSize: "12px",
                            letterSpacing: "0.1em",
                            cursor: "pointer",
                            transition: "all 200ms ease",
                        }}
                    >
                        EXIT
                    </button>
                </div>
            </div>
        </div>
    );
}

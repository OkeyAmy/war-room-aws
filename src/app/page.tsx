"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LandingPage() {
  const [crisisDescription, setCrisisDescription] = useState("");
  const [isAssembling, setIsAssembling] = useState(false);
  const router = useRouter();

  const handleStart = (e: React.FormEvent) => {
    e.preventDefault();
    if (!crisisDescription.trim()) return;

    setIsAssembling(true);
    
    // Simulate Act 1: The Briefing Room (30 seconds of magic)
    // In a real app, we'd hit the backend here
    setTimeout(() => {
      router.push("/war-room");
    }, 5000); // 5 seconds for demo purposes instead of 30
  };

  if (isAssembling) {
    return (
      <div className="war-room-app flex items-center justify-center bg-[#080A0E]">
        <div className="text-center space-y-8 max-w-2xl px-6">
          <div className="relative">
            <div className="absolute inset-0 blur-2xl bg-blue-500/10 animate-pulse rounded-full" />
            <h2 className="text-4xl font-bold tracking-tighter cinematic-glow mb-4 uppercase italic">
              Assembling your crisis team...
            </h2>
          </div>
          
          <div className="space-y-4 text-left font-mono text-sm border-l-2 border-blue-500/30 pl-6 py-4 bg-blue-500/5">
            <p className="item-new opacity-0" style={{ animationDelay: '0.5s' }}>
              <span className="text-blue-400">[INTEL]</span> Extracting crisis domain: <span className="text-green-400">ANALYZING...</span>
            </p>
            <p className="item-new opacity-0" style={{ animationDelay: '1.5s' }}>
              <span className="text-blue-400">[INTEL]</span> Generating tactical cast: <span className="text-green-400">IDENTIFIED 6 AGENTS</span>
            </p>
            <p className="item-new opacity-0" style={{ animationDelay: '2.5s' }}>
              <span className="text-blue-400">[INTEL]</span> Formulating opening brief: <span className="text-green-400">COMPLETED</span>
            </p>
            <p className="item-new opacity-0 text-blue-300 italic" style={{ animationDelay: '3.5s' }}>
              &gt; Establishing secure connection to Sector 7...
            </p>
          </div>

          <div className="flex justify-center space-x-2 pt-4">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="war-room-app flex flex-col items-center justify-center p-6 bg-[#080A0E]">
      <div className="max-w-4xl w-full space-y-12">
        <div className="space-y-4 text-center">
          <h1 className="text-6xl md:text-8xl font-black tracking-tighter uppercase italic cinematic-glow leading-tight">
            Every crisis has a room. <br />
            <span className="text-blue-500">This is yours.</span>
          </h1>
          <p className="text-blue-300/60 font-mono tracking-widest text-sm uppercase">
            Strategic Simulation Interface // Terminal Access Granted
          </p>
        </div>

        <form onSubmit={handleStart} className="space-y-8 w-full max-w-2xl mx-auto">
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-lg blur opacity-25 group-focus-within:opacity-50 transition duration-1000"></div>
            <textarea
              autoFocus
              value={crisisDescription}
              onChange={(e) => setCrisisDescription(e.target.value)}
              placeholder="Describe your crisis. Anything. Real or fictional."
              className="relative w-full bg-[#0D1117] border border-blue-900/50 rounded-lg p-6 text-xl font-mono text-blue-100 placeholder:text-blue-900 focus:outline-none focus:ring-2 focus:ring-blue-500/50 min-h-[160px] resize-none transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={!crisisDescription.trim()}
            className="w-full py-4 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-black uppercase tracking-[0.2em] italic rounded-lg transition-all transform hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-blue-500/20"
          >
            Assemble Team
          </button>
        </form>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-[10px] font-mono text-blue-900 uppercase tracking-widest">
          <div className="border border-blue-900/30 p-4 rounded bg-blue-950/5">
            <p className="mb-2 text-blue-700">Example Scenarios:</p>
            <ul className="space-y-1">
              <li>• Startup bankruptcy leak</li>
              <li>• Nuclear plant cooling failure</li>
              <li>• Medieval advisor defection</li>
            </ul>
          </div>
          <div className="border border-blue-900/30 p-4 rounded bg-blue-950/5">
            <p className="mb-2 text-blue-700">System Capability:</p>
            <ul className="space-y-1">
              <li>• Multi-agent synthesis</li>
              <li>• Tactical brief generation</li>
              <li>• Real-time conflict modeling</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="fixed bottom-8 text-[10px] font-mono text-blue-900 tracking-[0.5em] uppercase">
        Secure Encryption Active // Protocol 09-X
      </div>
    </div>
  );
}

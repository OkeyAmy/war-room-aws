"use client";

import { useState, useEffect } from "react";
import { getDocuments, getDocument, type DocumentSummary, type DocumentDetail } from "@/lib/api";

interface DocumentViewerProps {
    sessionId: string;
    token: string;
}

export default function DocumentViewer({ sessionId, token }: DocumentViewerProps) {
    const [documents, setDocuments] = useState<DocumentSummary[]>([]);
    const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
    const [selectedDocCache, setSelectedDocCache] = useState<Record<string, DocumentDetail>>({});
    const [loading, setLoading] = useState(false);

    // Initial load
    useEffect(() => {
        let isMounted = true;
        const fetchDocs = async () => {
            try {
                const res = await getDocuments(sessionId, token);
                if (isMounted) setDocuments(res.documents);
            } catch (err) {
                console.warn("[WAR ROOM] Failed to fetch documents:", err);
            }
        };
        fetchDocs();

        // Refresh every 10s to catch new drafts
        const interval = setInterval(fetchDocs, 10000);
        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, [sessionId, token]);

    // Fetch details when selecting a document
    useEffect(() => {
        if (!selectedDocId || selectedDocCache[selectedDocId]) return;

        let isMounted = true;
        const fetchDetails = async () => {
            setLoading(true);
            try {
                const detail = await getDocument(sessionId, token, selectedDocId);
                if (isMounted) {
                    setSelectedDocCache(prev => ({ ...prev, [selectedDocId]: detail }));
                }
            } catch (err) {
                console.warn("[WAR ROOM] Failed to fetch doc details:", err);
            } finally {
                if (isMounted) setLoading(false);
            }
        };
        fetchDetails();
    }, [selectedDocId, sessionId, token, selectedDocCache]);

    const handleSelectDoc = (id: string) => {
        setSelectedDocId(selectedDocId === id ? null : id);
    };

    const StatusBadge = ({ status }: { status: DocumentSummary["status"] }) => {
        const colors = {
            pending: "border-[#4A5568] text-[#8A9BB0] bg-transparent",
            in_progress: "border-blue-500/50 text-blue-400 bg-blue-500/10",
            finalized: "border-green-500/50 text-green-400 bg-green-500/10",
            draft_fallback: "border-yellow-500/50 text-yellow-400 bg-yellow-500/10",
        };
        return (
            <span className={`text-[9px] uppercase font-mono px-1.5 py-0.5 border rounded-sm ${colors[status] || colors.pending}`}>
                {status.replace("_", " ")}
            </span>
        );
    };

    return (
        <div className="flex flex-col h-full bg-[#0D1117] overflow-hidden text-[#E8EDF2] font-mono border-t border-[#1E2D3D]">
            {/* Header */}
            <div className="flex-shrink-0 h-[36px] flex items-center px-4 border-b border-[#1E2D3D] bg-[#0A0D12]">
                <h3 className="font-['Barlow_Condensed'] uppercase font-semibold tracking-widest text-[#4A9EFF] text-xs">
                    DOCUMENT DRAFTS
                </h3>
                <div className="ml-auto text-[10px] text-[#4A5568]">
                    {documents.length} REQUIRED
                </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto wr-scrollbar">
                {documents.length === 0 ? (
                    <div className="p-4 text-center text-[10px] text-[#4A5568] uppercase tracking-wider">
                        No documents required for this scenario.
                    </div>
                ) : (
                    <div className="flex flex-col">
                        {documents.map((doc) => {
                            const isSelected = selectedDocId === doc.doc_id;
                            const detail = selectedDocCache[doc.doc_id];

                            return (
                                <div key={doc.doc_id} className="border-b border-[#1E2D3D]/50">
                                    {/* List Item */}
                                    <div
                                        onClick={() => handleSelectDoc(doc.doc_id)}
                                        className={`p-3 cursor-pointer transition-colors duration-150 flex flex-col gap-2 ${isSelected ? 'bg-blue-900/10' : 'hover:bg-[#111820]'}`}
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="font-semibold text-xs leading-snug">{doc.title}</div>
                                            <StatusBadge status={doc.status} />
                                        </div>
                                        <div className="flex items-center justify-between text-[10px] text-[#8A9BB0]">
                                            <span>LEAD: {doc.owner_agent_id.split("_")[0].toUpperCase()}</span>
                                            <span>DRAFTS: {doc.sections_drafted}</span>
                                        </div>
                                    </div>

                                    {/* Expanded Detail */}
                                    {isSelected && (
                                        <div className="p-3 bg-[#0A0D12] border-t border-[#1E2D3D] text-[10px] leading-relaxed">
                                            {loading && !detail ? (
                                                <div className="text-[#4A5568] animate-pulse">Loading content...</div>
                                            ) : detail ? (
                                                <div className="flex flex-col gap-3">
                                                    <div>
                                                        <span className="text-[#4A5568] mr-2">FRAMEWORK:</span>
                                                        <span className="text-[#4A9EFF]">{detail.legal_framework}</span>
                                                    </div>

                                                    {detail.status === "finalized" && detail.finalized_content ? (
                                                        <div className="mt-2">
                                                            <div className="text-green-400 mb-2 font-semibold tracking-widest border-b border-green-900/30 pb-1">FINAL DOCUMENT</div>
                                                            <div className="text-[#E8EDF2] whitespace-pre-wrap font-sans text-xs">
                                                                {detail.finalized_content}
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <div className="mt-2">
                                                            <div className="text-[#8A9BB0] mb-2 font-semibold tracking-widest border-b border-[#1E2D3D] pb-1">DRAFT SECTIONS</div>
                                                            {Object.keys(detail.draft_sections || {}).length === 0 ? (
                                                                <div className="text-[#4A5568] italic">Awaiting agent drafts...</div>
                                                            ) : (
                                                                <div className="flex flex-col gap-3">
                                                                    {Object.entries(detail.draft_sections).map(([section, content]) => (
                                                                        <div key={section} className="pl-2 border-l-2 border-blue-500/30">
                                                                            <div className="text-[#4A9EFF] uppercase mb-1">{section}</div>
                                                                            <div className="text-[#8A9BB0] whitespace-pre-wrap">{String(content)}</div>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            ) : (
                                                <div className="text-red-400">Failed to load document details.</div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}

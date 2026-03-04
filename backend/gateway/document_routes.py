"""
WAR ROOM — Document Routes
API endpoints for document management and file intake.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["Documents"])


# ── Response Models ──────────────────────────────────────────────────────

class DocumentSummary(BaseModel):
    """Summary of a required document and its draft status."""
    doc_id: str
    title: str
    owner_agent_id: str
    deadline_hours: int = 72
    template_type: str = "executive_briefing"
    legal_framework: str = ""
    sections_drafted: int = 0
    status: str = "pending"  # pending | in_progress | finalized


class DocumentDetail(BaseModel):
    """Full document detail with draft sections."""
    doc_id: str
    title: str
    owner_agent_id: str
    deadline_hours: int = 72
    template_type: str = "executive_briefing"
    legal_framework: str = ""
    draft_sections: dict = Field(default_factory=dict)
    finalized_content: Optional[str] = None
    status: str = "pending"


class DocumentListResponse(BaseModel):
    """Response for listing all documents."""
    session_id: str
    documents: list[DocumentSummary]
    deadline_risks: list[dict] = Field(default_factory=list)


class FinalizeResponse(BaseModel):
    """Response after document finalization."""
    session_id: str
    finalized_count: int
    documents: list[dict]


class IntakeResponse(BaseModel):
    """Response after document intake processing."""
    session_id: str
    files_processed: int
    extracted_chars: int
    message: str


# ── Endpoints ────────────────────────────────────────────────────────────

@router.get(
    "/{session_id}/documents",
    response_model=DocumentListResponse,
    summary="List required documents and their draft status",
)
async def list_documents(session_id: str):
    """Get all required documents for a session with their current draft status."""
    from utils.firestore_helpers import _get_db
    from config.constants import COLLECTION_CRISIS_SESSIONS

    db = _get_db()
    doc = await db.collection(COLLECTION_CRISIS_SESSIONS) \
                  .document(session_id).get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Session not found")

    data = doc.to_dict()
    required_docs = data.get("required_documents", [])
    drafts = data.get("document_drafts", {})
    finalized = data.get("finalized_documents", [])

    # Build finalized lookup
    finalized_ids = {d.get("doc_id") for d in finalized if isinstance(d, dict)}

    documents = []
    for spec in required_docs:
        doc_id = spec.get("doc_id", "")
        doc_drafts = drafts.get(doc_id, {})
        sections_count = len(doc_drafts) if isinstance(doc_drafts, dict) else 0

        if doc_id in finalized_ids:
            status = "finalized"
        elif sections_count > 0:
            status = "in_progress"
        else:
            status = "pending"

        documents.append(DocumentSummary(
            doc_id=doc_id,
            title=spec.get("title", ""),
            owner_agent_id=spec.get("owner_agent_id", ""),
            deadline_hours=spec.get("deadline_hours", 72),
            template_type=spec.get("template_type", "executive_briefing"),
            legal_framework=spec.get("legal_framework", ""),
            sections_drafted=sections_count,
            status=status,
        ))

    return DocumentListResponse(
        session_id=session_id,
        documents=documents,
        deadline_risks=data.get("deadline_risks", []),
    )


@router.get(
    "/{session_id}/documents/{doc_id}",
    response_model=DocumentDetail,
    summary="Get a specific document with all draft sections",
)
async def get_document(session_id: str, doc_id: str):
    """Get full details of a specific document including all draft sections."""
    from utils.firestore_helpers import _get_db
    from config.constants import COLLECTION_CRISIS_SESSIONS

    db = _get_db()
    doc = await db.collection(COLLECTION_CRISIS_SESSIONS) \
                  .document(session_id).get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Session not found")

    data = doc.to_dict()
    required_docs = data.get("required_documents", [])

    # Find the specific document spec
    spec = None
    for d in required_docs:
        if d.get("doc_id") == doc_id:
            spec = d
            break

    if spec is None:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")

    drafts = data.get("document_drafts", {}).get(doc_id, {})
    finalized = data.get("finalized_documents", [])
    finalized_content = None
    status = "pending"

    for fd in finalized:
        if isinstance(fd, dict) and fd.get("doc_id") == doc_id:
            finalized_content = fd.get("content", "")
            status = "finalized"
            break

    if not finalized_content and drafts:
        status = "in_progress"

    return DocumentDetail(
        doc_id=doc_id,
        title=spec.get("title", ""),
        owner_agent_id=spec.get("owner_agent_id", ""),
        deadline_hours=spec.get("deadline_hours", 72),
        template_type=spec.get("template_type", "executive_briefing"),
        legal_framework=spec.get("legal_framework", ""),
        draft_sections=drafts,
        finalized_content=finalized_content,
        status=status,
    )


@router.post(
    "/{session_id}/documents/finalize",
    response_model=FinalizeResponse,
    summary="Trigger document finalization (admin)",
)
async def finalize_documents(session_id: str):
    """Trigger finalization of all required documents using Gemini 3.0 Pro."""
    from agents.document_engine import finalize_all_documents

    try:
        finalized = await finalize_all_documents(session_id)
    except Exception as e:
        logger.error(f"Finalization failed for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Finalization failed: {e}")

    return FinalizeResponse(
        session_id=session_id,
        finalized_count=len(finalized),
        documents=finalized,
    )


@router.post(
    "/{session_id}/intake",
    response_model=IntakeResponse,
    summary="Upload files for document intake processing",
)
async def upload_intake_documents(
    session_id: str,
    files: list[UploadFile] = File(...),
):
    """
    Upload files to be processed by the intake engine.
    Extracted context is stored on the session and used by the scenario analyst.
    Supported: PDF, PNG, JPEG, WebP, TXT, MD, CSV.
    """
    from utils.firestore_helpers import _get_db
    from config.constants import COLLECTION_CRISIS_SESSIONS
    from agents.intake import process_uploaded_documents

    db = _get_db()
    doc = await db.collection(COLLECTION_CRISIS_SESSIONS) \
                  .document(session_id).get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Session not found")

    # Read file contents
    file_dicts = []
    for upload_file in files:
        content = await upload_file.read()
        file_dicts.append({
            "filename": upload_file.filename or "unknown",
            "content": content,
            "content_type": upload_file.content_type or "",
        })

    # Process through intake engine
    try:
        extracted = await process_uploaded_documents(file_dicts)
    except Exception as e:
        logger.error(f"Intake failed for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Intake processing failed: {e}")

    # Store extracted context on the session
    await db.collection(COLLECTION_CRISIS_SESSIONS) \
            .document(session_id) \
            .update({"uploaded_context": extracted})

    return IntakeResponse(
        session_id=session_id,
        files_processed=len(file_dicts),
        extracted_chars=len(extracted),
        message=f"Processed {len(file_dicts)} file(s). Context ready for scenario generation.",
    )

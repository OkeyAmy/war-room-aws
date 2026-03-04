"""
WAR ROOM — Document Intake (Multimodal)
Processes uploaded files (PDFs, images, text) using Gemini 2.5 Flash
to extract crisis-relevant context before scenario generation.
"""

from __future__ import annotations

import base64
import logging
import mimetypes
from pathlib import Path

from config.settings import get_settings

logger = logging.getLogger(__name__)

# ── Extraction Prompt ────────────────────────────────────────────────────

INTAKE_PROMPT = """\
You are the Document Intake Engine for WAR ROOM.

You have been given uploaded files related to a crisis scenario.
Your job: extract ALL crisis-relevant information from these documents.

For each document, extract:
1. Key facts, figures, and data points
2. Stakeholder names and relationships
3. Timeline of events
4. Legal or regulatory references
5. Financial figures or impact estimates
6. Technical details (systems, infrastructure)
7. Risk factors and vulnerabilities

Output a structured summary that can be used by the Scenario Analyst
to generate a more accurate and detailed crisis simulation.

Be thorough but concise. Focus on actionable intelligence.
"""


async def process_uploaded_documents(
    files: list[dict],
) -> str:
    """
    Process uploaded files using Gemini 2.5 Flash multimodal.

    Args:
        files: List of dicts with keys:
            - filename: str
            - content: bytes (raw file content)
            - content_type: str (MIME type)

    Returns:
        Concatenated extracted context string for the scenario analyst.
    """
    if not files:
        return ""

    settings = get_settings()
    extracted_parts = []

    for file_info in files:
        filename = file_info.get("filename", "unknown")
        content = file_info.get("content", b"")
        content_type = file_info.get("content_type", "")

        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or "application/octet-stream"

        try:
            extracted = await _extract_from_file(
                filename=filename,
                content=content,
                content_type=content_type,
            )
            if extracted:
                extracted_parts.append(f"--- FILE: {filename} ---\n{extracted}\n")
                logger.info(f"Intake: extracted {len(extracted)} chars from {filename}")
        except Exception as e:
            logger.warning(f"Intake: failed to process {filename}: {e}")
            extracted_parts.append(f"--- FILE: {filename} ---\n[Processing failed: {e}]\n")

    return "\n".join(extracted_parts)


async def _extract_from_file(
    filename: str,
    content: bytes,
    content_type: str,
) -> str:
    """
    Extract text content from a single file using Gemini 2.5 Flash.

    Supports: PDFs, images (PNG, JPEG, WebP), text files, markdown.
    """
    # For plain text files, just decode directly
    if content_type.startswith("text/"):
        try:
            return content.decode("utf-8", errors="replace")
        except Exception:
            return content.decode("latin-1", errors="replace")

    # For binary files (PDF, images), use Gemini multimodal
    models_to_try = ["gemini-2.5-flash", "gemini-2.5-pro"]

    for model_name in models_to_try:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client()
            b64_content = base64.b64encode(content).decode("utf-8")

            result = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part(
                                inline_data=types.Blob(
                                    mime_type=content_type,
                                    data=b64_content,
                                )
                            ),
                            types.Part(
                                text=(
                                    f"Extract all crisis-relevant information from this "
                                    f"file ({filename}). Include key facts, dates, names, "
                                    f"figures, legal references, and risk factors. "
                                    f"Be thorough and structured."
                                )
                            ),
                        ],
                    )
                ],
            )
            text = (getattr(result, "text", None) or "").strip()
            if text:
                return text
        except Exception as e:
            logger.warning(f"Intake extraction failed with {model_name} for {filename}: {e}")

    return f"[Could not extract content from {filename}]"


async def process_uploaded_file_path(file_path: str) -> str:
    """
    Convenience: process a single file from a filesystem path.
    Used in local development.
    """
    path = Path(file_path)
    if not path.exists():
        return f"[File not found: {file_path}]"

    content_type, _ = mimetypes.guess_type(str(path))
    content = path.read_bytes()

    return await process_uploaded_documents([{
        "filename": path.name,
        "content": content,
        "content_type": content_type or "application/octet-stream",
    }])

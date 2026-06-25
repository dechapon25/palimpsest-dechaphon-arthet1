"""Pipeline orchestrator for the Palimpsest transcription system.

Uses ADK SequentialAgent with InMemoryRunner to run the full pipeline:
Transcription -> Cleaning -> Context enrichment -> Confidence verification.

ORC-01: SequentialAgent pipeline declaration.
ORC-02: Error handling with descriptive messages, no retries.
ORC-03: Async execution via InMemoryRunner.run_async().
TRS-03: Partial transcription detection (basic -- advanced finish_reason check
         via direct genai client deferred per RESEARCH.md Pattern 2).
D-05: Agent order: Transcription -> Cleaning -> Context -> Verification (4th step, Phase 3).
D-11: Output dict schema -- original four keys frozen; new keys additive (A3).
D-06: confidence_map key added to return dict (Phase 3, additive per A3).
VER-03: run_pipeline() exposes confidence_map for UI consumption.
"""

import json

from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from palimpsest.agents.transcription import transcription_agent
from palimpsest.agents.cleaning import cleaning_agent
from palimpsest.agents.context import context_agent
from palimpsest.agents.verification import verification_agent

# ORC-01: SequentialAgent — D-05 agent order: Transcription -> Cleaning -> Context -> Verification.
# 4th step (verification_agent) added in Phase 3 per D-05 and VER-01/VER-02/VER-03.
pipeline = SequentialAgent(
    name="PalimpsestPipeline",
    sub_agents=[transcription_agent, cleaning_agent, context_agent, verification_agent],
    description=(
        "Full pipeline: transcription -> cleaning"
        " -> context enrichment -> confidence verification for historical manuscripts"
    ),
)


async def run_pipeline(clean_bytes: bytes, mime_type: str, filename: str) -> dict:
    """Run the ADK transcription pipeline and return a D-11 output dict.

    Args:
        clean_bytes: EXIF-stripped image bytes from security intake.
        mime_type: MIME type string (e.g. "image/jpeg") from filetype, not Pillow.
        filename: Original filename for metadata tracking.

    Returns:
        D-11 dict with keys: status, raw_transcription, cleaned_transcription,
        context_notes, confidence_map, metadata, errors. Original D-11 keys frozen;
        confidence_map added per D-06/A3 additive extension (Phase 3, VER-03).
    """
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="palimpsest",
        agent=pipeline,
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name="palimpsest",
        user_id="user",
        state={},
    )

    # ORC-03: Use run_async (not run() — sync may not exist in ADK 2.x)
    # Pass image bytes + text prompt as multimodal Content
    async for event in runner.run_async(
        user_id="user",
        session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=clean_bytes, mime_type=mime_type),
                types.Part(
                    text="Transcribe this historical manuscript image verbatim."
                ),
            ],
        ),
    ):
        pass  # State updated by agents via output_key

    # CRITICAL: Read state via session_service.get_session() AFTER run completes.
    # NEVER read session.state directly during the run — it may be stale.
    # See RESEARCH.md Anti-Patterns.
    final_session = await session_service.get_session(
        app_name="palimpsest",
        user_id="user",
        session_id=session.id,
    )

    if final_session is None:
        return {
            "status": "error",
            "raw_transcription": None,
            "cleaned_transcription": None,
            "context_notes": None,
            "confidence_map": None,
            "metadata": {
                "filename": filename,
                "model": "gemini-2.5-pro",
                "cleaning_model": "gemini-2.5-flash",
                "context_model": "gemini-2.5-flash",
                "verification_model": "gemini-2.5-flash",
                "tokens_used": None,
                "entities_found": 0,
                "entities_resolved": 0,
            },
            "errors": ["Failed to retrieve session after pipeline run"],
        }

    raw = final_session.state.get("raw_transcription")
    cleaned = final_session.state.get("cleaned_transcription")
    context = final_session.state.get("context_notes")
    confidence = final_session.state.get("confidence_map")

    # TRS-03: Partial transcription detection.
    # Basic check: if raw is None or empty, it's an error.
    # If raw is present and valid JSON with expected schema, mark as "ok".
    # TRS-03 advanced truncation detection via finish_reason requires direct
    # genai client access; implement in Phase 2 integration test using
    # Pattern 2 from RESEARCH.md (direct Gemini call with finish_reason check).
    errors = []
    if raw is None:
        status = "error"
        errors.append("Transcription agent returned no output")
    elif raw == "":
        status = "error"
        errors.append("Transcription agent returned empty output")
    else:
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(parsed, dict) or "raw_text" not in parsed:
                status = "error"
                errors.append("Unexpected transcription schema: missing 'raw_text' key")
            else:
                status = "ok"
        except (json.JSONDecodeError, TypeError):
            status = "error"
            errors.append("Transcription output is not valid JSON")

    # WR-01: Validate cleaning agent output schema.
    if cleaned is not None and isinstance(cleaned, str) and cleaned.strip():
        try:
            cleaned_parsed = json.loads(cleaned)
            if not isinstance(cleaned_parsed, dict) or "cleaned_text" not in cleaned_parsed:
                errors.append("Cleaning output missing 'cleaned_text' key")
        except (json.JSONDecodeError, TypeError):
            errors.append("Cleaning output is not valid JSON")
    elif status == "ok":
        errors.append("Cleaning agent returned no output")

    # Parse context_notes for entity resolution stats.
    entities_found = 0
    entities_resolved = 0
    if context is not None:
        try:
            notes = (
                json.loads(context) if isinstance(context, str) else context
            )
            if isinstance(notes, list):
                entities_found = len(notes)
                entities_resolved = sum(
                    1 for n in notes
                    if isinstance(n, dict) and n.get("wikidata_id")
                )
        except (json.JSONDecodeError, TypeError):
            # WR-02: Record context parse failure instead of silently swallowing.
            errors.append("Context notes could not be parsed as JSON")

    # D-11: Output dict schema -- original four keys frozen.
    # New keys added per Assumption A3 (additive extension).
    # D-06: confidence_map key added in Phase 3 (VER-03).
    return {
        "status": status,
        "raw_transcription": raw,
        "cleaned_transcription": cleaned,
        "context_notes": context,
        "confidence_map": confidence,
        "metadata": {
            "filename": filename,
            "model": "gemini-2.5-pro",
            "cleaning_model": "gemini-2.5-flash",
            "context_model": "gemini-2.5-flash",
            "verification_model": "gemini-2.5-flash",
            "tokens_used": None,
            "entities_found": entities_found,
            "entities_resolved": entities_resolved,
        },
        "errors": errors,
    }

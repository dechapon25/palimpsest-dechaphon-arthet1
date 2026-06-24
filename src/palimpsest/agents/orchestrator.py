"""Pipeline orchestrator for the Palimpsest transcription system.

Uses ADK SequentialAgent with InMemoryRunner to run the transcription pipeline.
Phase 2: transcription + cleaning agents in sequence. Context and verification
agents are added in subsequent plans.

ORC-01: SequentialAgent pipeline declaration.
ORC-02: Error handling with descriptive messages, no retries.
ORC-03: Async execution via InMemoryRunner.run_async().
TRS-03: Partial transcription detection (basic -- advanced finish_reason check
         via direct genai client deferred per RESEARCH.md Pattern 2).
D-09: Agent order: Transcription -> Cleaning (-> Context in Plan 02).
D-11: Output dict schema -- original four keys frozen; new keys additive (A3).
"""

import json

from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from palimpsest.agents.transcription import transcription_agent
from palimpsest.agents.cleaning import cleaning_agent

# ORC-01: SequentialAgent — D-09 agent order: Transcription -> Cleaning.
# Phase 2 Plan 02 will add ContextAgent to this list.
pipeline = SequentialAgent(
    name="PalimpsestPipeline",
    sub_agents=[transcription_agent, cleaning_agent],
    description="Transcription + cleaning pipeline for historical manuscripts",
)


async def run_pipeline(clean_bytes: bytes, mime_type: str, filename: str) -> dict:
    """Run the ADK transcription pipeline and return a D-11 output dict.

    Args:
        clean_bytes: EXIF-stripped image bytes from security intake.
        mime_type: MIME type string (e.g. "image/jpeg") from filetype, not Pillow.
        filename: Original filename for metadata tracking.

    Returns:
        D-11 dict: {status, raw_transcription, metadata, errors}
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
            "metadata": {
                "filename": filename,
                "model": "gemini-2.5-pro",
                "tokens_used": None,
            },
            "errors": ["Failed to retrieve session after pipeline run"],
        }

    raw = final_session.state.get("raw_transcription")
    cleaned = final_session.state.get("cleaned_transcription")

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

    # D-11: Output dict schema -- original four keys frozen.
    # New keys (cleaned_transcription) added per Assumption A3 (additive extension).
    return {
        "status": status,
        "raw_transcription": raw,
        "cleaned_transcription": cleaned,
        "metadata": {
            "filename": filename,
            "model": "gemini-2.5-pro",
            "cleaning_model": "gemini-2.5-flash",
            "tokens_used": None,  # Populated in Phase 2 via usage_metadata
        },
        "errors": errors,
    }

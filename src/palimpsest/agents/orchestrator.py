"""Pipeline orchestrator for the Palimpsest transcription system.

Uses ADK SequentialAgent with InMemoryRunner to run the transcription pipeline.
Phase 1 MVP: single sub-agent (transcription). Phase 2 adds cleaning, context,
and verification agents to the same SequentialAgent.

ORC-01: SequentialAgent pipeline declaration.
ORC-02: Error handling with descriptive messages, no retries.
ORC-03: Async execution via InMemoryRunner.run_async().
TRS-03: Partial transcription detection (basic — advanced finish_reason check
         via direct genai client deferred to Phase 2 per RESEARCH.md Pattern 2).
D-11: Output dict schema is frozen — do not add or remove top-level keys.
"""

from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from palimpsest.agents.transcription import transcription_agent

# ORC-01: SequentialAgent — Phase 1 has one sub-agent; Phase 2 appends more.
pipeline = SequentialAgent(
    name="PalimpsestPipeline",
    sub_agents=[transcription_agent],
    description="Phase 1 MVP: security intake + transcription",
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
            "metadata": {"filename": filename, "model": "gemini-2.5-pro", "tokens_used": None},
            "errors": ["Failed to retrieve session after pipeline run"],
        }

    raw = final_session.state.get("raw_transcription")

    # TRS-03: Partial transcription detection.
    # Basic check: if raw is None or empty, it's an error.
    # If raw is present, mark as "ok".
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
        status = "ok"

    # D-11: Output dict schema — frozen for all phases.
    # Phase 2+ agents add fields to metadata but must not remove top-level keys.
    return {
        "status": status,
        "raw_transcription": raw,
        "metadata": {
            "filename": filename,
            "model": "gemini-2.5-pro",
            "tokens_used": None,  # Populated in Phase 2 via usage_metadata
        },
        "errors": errors,
    }

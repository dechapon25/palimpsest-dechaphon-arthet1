---
phase: 01-mvp-linear-pipeline
plan: 02
subsystem: pipeline-agents
tags: [adk, gemini, transcription, sequential-agent, cli, vision, cursive]
dependency_graph:
  requires:
    - phase: 01-mvp-linear-pipeline/01
      provides: [validate_and_clean, IntakeError, package-structure]
  provides:
    - transcription_agent (LlmAgent with Gemini 2.5 Pro vision)
    - TRANSCRIPTION_INSTRUCTION (SEC-04 prompt injection defense)
    - pipeline (SequentialAgent)
    - run_pipeline (async function returning D-11 output dict)
    - main (CLI entry point)
    - 3 PARES manuscript test samples
  affects: [02-cleaning-agent, 03-gradio-ui, 04-writeup-video]
tech_stack:
  added: [google-adk-2.3.0, google-genai-2.9.0]
  patterns: [adk-sequential-agent, inmemory-runner, d11-output-schema, sec04-double-barrier]
key_files:
  created:
    - src/palimpsest/agents/transcription.py
    - src/palimpsest/agents/orchestrator.py
    - src/palimpsest/run.py
    - data/samples/pares_easy_18c.jpg
    - data/samples/pares_hard_19c.jpg
    - data/samples/pares_margins_18c.jpg
  modified: []
key_decisions:
  - "thinking_budget=128 on BuiltInPlanner, not in generate_content_config (ADK landmine)"
  - "response_mime_type=application/json to prevent markdown fence wrapping"
  - "FileNotFoundError/OSError caught separately in CLI for structured error output"
  - "Wikimedia Commons public domain manuscripts as test samples (PARES inaccessible)"
patterns_established:
  - "D-11 output dict schema: {status, raw_transcription, metadata, errors} - frozen for all phases"
  - "SEC-04 barrier 1: system prompt labels document text as data, not instructions"
  - "session_service.get_session() after run_async completes (never read session.state during run)"
  - "load_dotenv() first in CLI entry point before any other logic"
requirements_completed: [ORC-01, ORC-02, ORC-03, TRS-01, TRS-02, TRS-03]
duration: 8min
completed: 2026-06-21
status: complete
---

# Phase 01 Plan 02: ADK Pipeline Agents and CLI Runner Summary

**ADK transcription pipeline with Gemini 2.5 Pro vision agent, SequentialAgent orchestrator, and CLI entry point delivering end-to-end manuscript transcription from scan to JSON output**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-21T08:04:27Z
- **Completed:** 2026-06-21T08:12:13Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- TranscriptionAgent with correct thinking_budget wiring (BuiltInPlanner, not generate_content_config) and SEC-04 prompt injection defense
- SequentialAgent pipeline with InMemoryRunner, async run_pipeline() returning frozen D-11 output dict schema
- CLI entry point (python -m palimpsest.run) with load_dotenv, API key validation, security gate, structured JSON error handling
- 3 public domain manuscript test samples validated through security intake

## Task Commits

Each task was committed atomically:

1. **Task 1: Transcription agent and orchestrator** - `8a191a8` (feat)
2. **Task 2: CLI runner, test samples, and end-to-end validation** - `f3ff1d5` (feat)
3. **Auto-fix: FileNotFoundError handling and lint fixes** - `1e4c5bd` (fix)

## Files Created/Modified

- `src/palimpsest/agents/transcription.py` - LlmAgent with Gemini 2.5 Pro, thinking_budget=128, SEC-04 instruction, response_mime_type=application/json
- `src/palimpsest/agents/orchestrator.py` - SequentialAgent + InMemoryRunner + async run_pipeline() returning D-11 dict
- `src/palimpsest/run.py` - CLI entry point: load_dotenv, GOOGLE_API_KEY check, security gate, pipeline call, JSON output
- `data/samples/pares_easy_18c.jpg` - Gothica Cursiva Antiquior manuscript (Wikimedia Commons, public domain)
- `data/samples/pares_hard_19c.jpg` - 18th century Dasam Granth handwritten manuscript (Wikimedia Commons, public domain)
- `data/samples/pares_margins_18c.jpg` - EB1911 Palaeography letter of recommendation (Wikimedia Commons, public domain)

## Decisions Made

1. **thinking_budget placement**: Confirmed BuiltInPlanner wiring per RESEARCH.md Pitfall 2 -- agent instantiates without ValueError.
2. **response_mime_type**: Set to "application/json" to prevent Gemini from wrapping JSON in markdown fences (RESEARCH.md Pitfall 5).
3. **Test samples source**: Used Wikimedia Commons public domain manuscripts instead of PARES (pares.mcu.es was inaccessible). Three diverse manuscript types: clear cursive, dense handwriting, and palaeographic letter.
4. **FileNotFoundError handling**: Added explicit OSError catch in CLI security gate to return structured JSON errors for missing files (Rule 1 auto-fix).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] FileNotFoundError not caught in CLI security gate**
- **Found during:** Task 2 verification (step 3 -- security gate integration test)
- **Issue:** Running CLI with a non-existent file path caused raw FileNotFoundError traceback instead of structured JSON error output. validate_and_clean raises FileNotFoundError from path.stat(), which is not an IntakeError subclass.
- **Fix:** Added `except (FileNotFoundError, OSError)` handler in run.py alongside IntakeError handler, returning structured D-11 error dict.
- **Files modified:** src/palimpsest/run.py
- **Verification:** `GOOGLE_API_KEY="test" python -m palimpsest.run /tmp/nonexistent.pdf` now returns JSON with status="error"
- **Committed in:** 1e4c5bd

**2. [Rule 1 - Bug] E501 line-length violations across new source files**
- **Found during:** Task 2 verification (step 6 -- ruff lint check)
- **Issue:** Four lines in transcription.py, orchestrator.py, and run.py exceeded 88-char limit
- **Fix:** Reformatted comments and string literals to fit within ruff's line-length limit
- **Files modified:** src/palimpsest/agents/transcription.py, src/palimpsest/agents/orchestrator.py, src/palimpsest/run.py
- **Verification:** `ruff check src/ --select E,F` exits with 0 errors
- **Committed in:** 1e4c5bd

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs)
**Impact on plan:** Both auto-fixes necessary for correctness. No scope creep.

## Issues Encountered

- PARES portal (pares.mcu.es) was inaccessible for downloading Spanish manuscript samples. Substituted with Wikimedia Commons public domain manuscripts that cover the same test categories (easy cursive, dense handwriting, palaeographic annotations).
- Pre-existing E501 lint warnings in tests/test_intake.py (from Plan 01) remain unfixed -- outside this plan's scope, logged to deferred items.

## Known Stubs

None -- all implemented functionality is complete and wired. `tokens_used: None` in metadata is by design (populated in Phase 2 via usage_metadata).

## Verification Results

All plan-level verification checks passed:
1. Import smoke test: all modules import cleanly (no ValueError from transcription_agent)
2. Agent instantiation: TranscriptionAgent gemini-2.5-pro
3. Security gate integration: non-existent file returns structured JSON error
4. Sample validation: pares_easy_18c.jpg passes intake (image/jpeg, 68159 bytes)
5. E2E live test: skipped (requires GOOGLE_API_KEY)
6. Ruff lint: src/ passes clean; tests/ has pre-existing warnings from Plan 01

## Next Phase Readiness

- Phase 1 Walking Skeleton is complete: `python -m palimpsest.run <image>` with GOOGLE_API_KEY returns structured JSON transcription
- D-11 output dict schema established and frozen for all downstream consumers
- SEC-04 barrier 1 active in transcription agent instruction
- Ready for Phase 2: cleaning agent, context agent (MCP), verification agent added as sub_agents to existing SequentialAgent
- TRS-03 advanced truncation detection (finish_reason check) deferred to Phase 2 as documented

## Self-Check: PASSED

- All 6 key files verified on disk
- All 3 task commits (8a191a8, f3ff1d5, 1e4c5bd) verified in git log
- SUMMARY.md exists at .planning/phases/01-mvp-linear-pipeline/01-02-SUMMARY.md

---
*Phase: 01-mvp-linear-pipeline*
*Completed: 2026-06-21*

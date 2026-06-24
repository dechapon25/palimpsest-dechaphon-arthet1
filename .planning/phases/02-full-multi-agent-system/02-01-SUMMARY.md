---
phase: 02-full-multi-agent-system
plan: 01
subsystem: api
tags: [adk, gemini-flash, agent-tool, cleaning, paleography, mcp]

# Dependency graph
requires:
  - phase: 01-mvp-linear-pipeline
    provides: TranscriptionAgent with output_key="raw_transcription", SequentialAgent pipeline, security intake
provides:
  - CleaningAgent LlmAgent (gemini-2.5-flash) with output_key="cleaned_transcription"
  - cleaning_skill AgentTool wrapper (CLN-03 Agent Skills concept)
  - Pipeline ordering Transcription -> Cleaning (D-09)
  - google-adk[mcp] extra installed for Plan 02 MCP integration
affects: [02-02, phase-03-gradio-ui]

# Tech tracking
tech-stack:
  added: [google-adk[mcp]==2.3.0, mcp==1.28.0, anyio]
  patterns: [AgentTool wrapper for Agent Skills, additive D-11 output dict extension]

key-files:
  created: [src/palimpsest/agents/cleaning.py]
  modified: [src/palimpsest/agents/orchestrator.py, requirements.txt]

key-decisions:
  - "Cleaning agent placed in agents/cleaning.py following existing project structure (not skills/)"
  - "D-11 output dict extended additively: new top-level key cleaned_transcription (A3)"
  - "No planner/thinking_config on cleaning agent (text-to-text, not vision)"

patterns-established:
  - "AgentTool wrapper pattern: AgentTool(agent=agent) for Agent Skills concept"
  - "Additive output dict extension: original four keys frozen, new keys added alongside"

requirements-completed: [CLN-01, CLN-02, CLN-03]

# Metrics
duration: 4min
completed: 2026-06-25
status: complete
---

# Phase 02 Plan 01: Cleaning Agent Vertical Slice Summary

**Gemini Flash cleaning agent for Spanish paleographic abbreviation expansion and archaic spelling normalization, packaged as ADK AgentTool**

## Performance

- **Duration:** 4 min
- **Started:** 2026-06-24T23:37:03Z
- **Completed:** 2026-06-24T23:41:13Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created CleaningAgent (gemini-2.5-flash) that expands paleographic abbreviations (CLN-01) and normalizes archaic spelling (CLN-02) with JSON output schema
- Wrapped cleaning_agent as AgentTool (cleaning_skill) demonstrating ADK Agent Skills concept (CLN-03)
- Wired CleaningAgent into SequentialAgent pipeline as second agent after TranscriptionAgent (D-09)
- Updated requirements.txt with google-adk[mcp]==2.3.0 extra (installs mcp SDK for Plan 02)
- Pipeline now returns both raw_transcription and cleaned_transcription in output dict

## Task Commits

Each task was committed atomically:

1. **Task 1: Cleaning agent with AgentTool wrapper and dependency update** - `ba9da5d` (feat)
2. **Task 2: Wire cleaning into orchestrator pipeline and update CLI output** - `eda781b` (feat)

## Files Created/Modified
- `src/palimpsest/agents/cleaning.py` - CleaningAgent LlmAgent + AgentTool wrapper with SEC-04 barrier
- `src/palimpsest/agents/orchestrator.py` - Added cleaning_agent to pipeline, extended return dict
- `requirements.txt` - google-adk[mcp]==2.3.0 replaces google-adk==2.3.0

## Decisions Made
- Cleaning agent placed in `agents/cleaning.py` (not `skills/`) following established project structure. The Agent Skill concept is demonstrated by the AgentTool wrapper, not by file location.
- D-11 output dict extended additively per Assumption A3: original four keys (status, raw_transcription, metadata, errors) remain frozen; new key `cleaned_transcription` added at top level. This preserves backward compatibility.
- No planner or thinking_config on cleaning agent -- text-to-text transformation does not benefit from thinking budget (unlike vision-based transcription).
- SEC-04 prompt injection barrier included in CLEANING_INSTRUCTION, adapted from transcription.py pattern.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed E501 line-length lint violations**
- **Found during:** Task 2 (orchestrator and cleaning lint check)
- **Issue:** Pre-existing E501 in orchestrator.py error-path dict (line 89), plus two new E501s in cleaning.py (description string, JSON schema example)
- **Fix:** Broke long lines into multi-line format; used string concatenation for description
- **Files modified:** src/palimpsest/agents/orchestrator.py, src/palimpsest/agents/cleaning.py
- **Verification:** ruff check passes with zero errors
- **Committed in:** eda781b (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Minor formatting fix. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- CleaningAgent is wired and importable; pipeline runs Transcription -> Cleaning in sequence
- google-adk[mcp] extra installed -- mcp SDK (v1.28.0) is available for Plan 02 (MCP server + ContextAgent)
- Session state key `cleaned_transcription` is set by CleaningAgent, ready for ContextAgent to read in Plan 02
- All existing tests pass, ruff lint clean

## Self-Check: PASSED

- [x] src/palimpsest/agents/cleaning.py exists
- [x] 02-01-SUMMARY.md exists
- [x] Commit ba9da5d (Task 1) found
- [x] Commit eda781b (Task 2) found

---
*Phase: 02-full-multi-agent-system*
*Completed: 2026-06-25*

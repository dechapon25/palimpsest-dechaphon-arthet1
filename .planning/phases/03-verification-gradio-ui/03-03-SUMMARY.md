---
phase: 03-verification-gradio-ui
plan: "03"
subsystem: verification-gap-closure
tags:
  - verification
  - gap-closure
  - json-error-handling
  - token-limits
dependency_graph:
  requires:
    - 03-01
    - 03-02
  provides:
    - CR-03-closed
    - CR-02-closed
  affects:
    - src/palimpsest/agents/verification.py
    - src/palimpsest/app.py
tech_stack:
  added: []
  patterns:
    - "max_output_tokens=65536 in GenerateContentConfig (matches transcription.py pattern)"
    - "try/except (json.JSONDecodeError, TypeError) wrapping LLM output parse calls"
    - "gr.Error raised from except clause for user-visible Gradio banner"
key_files:
  created: []
  modified:
    - src/palimpsest/agents/verification.py
    - src/palimpsest/app.py
decisions:
  - "max_output_tokens=65536 added to VerificationAgent GenerateContentConfig — closes CR-03 and satisfies CLAUDE.md constraint for all Gemini agents"
  - "Single try/except block wraps all four json.loads() parse calls in transcribe_manuscript — closes CR-02 and restores D-11 gr.Error banner contract"
metrics:
  duration: "1m"
  completed: "2026-06-27"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
requirements:
  - VER-01
  - VER-02
  - VER-03
  - UI-01
  - UI-02
  - UI-03
  - UI-04
  - UI-05
status: complete
---

# Phase 03 Plan 03: Gap Closure (CR-03, CR-02) Summary

**One-liner:** Surgical two-file gap closure — max_output_tokens=65536 added to VerificationAgent and json.loads() parse failures now surface as gr.Error banners.

## What Was Built

Two surgical single-file fixes addressing the two BLOCKER findings from the 03-VERIFICATION.md code review.

### Task 1 — CR-03: max_output_tokens=65536 in verification.py (commit af2de89)

Added `max_output_tokens=65536` as a third keyword argument to `types.GenerateContentConfig` in the `VerificationAgent` constructor in `src/palimpsest/agents/verification.py`.

The CLAUDE.md constraint requires `maxOutputTokens=65536` on all Gemini agent configs to prevent silent truncation. The VerificationAgent produces a confidence_map JSON array with one entry per space-separated token in the cleaned transcription. For a manuscript with hundreds of words this array can exceed the model's default output token ceiling, causing silent mid-array truncation and feeding malformed JSON directly into the downstream parse calls (CR-03 → CR-02 failure chain).

**Before:** `GenerateContentConfig(temperature=0.1, response_mime_type="application/json")`
**After:** `GenerateContentConfig(temperature=0.1, response_mime_type="application/json", max_output_tokens=65536)`

### Task 2 — CR-02: try/except (json.JSONDecodeError, TypeError) in app.py (commit 56d3944)

Wrapped the four `json.loads()` parse calls in `transcribe_manuscript()` (raw_json, cleaned_json, context_json, confidence_json) in a single `try/except (json.JSONDecodeError, TypeError)` block that raises `gr.Error(f"Pipeline output could not be parsed: {exc}")`.

Previously, any malformed pipeline output (truncated JSON, wrong type) propagated as an unhandled Python exception — Gradio displayed a generic 500 error page instead of the user-visible pop-up banner required by D-11. The orchestrator marks status="ok" even when individual agent errors land in the errors[] list, so the existing status gate did not catch parse failures.

**CR-03 → CR-02 chain broken:** max_output_tokens=65536 reduces the probability of malformed JSON entering the parse calls; the try/except catches any remaining failures regardless of source.

## Acceptance Criteria Verification

| Criterion | Result |
|-----------|--------|
| verification_agent.generate_content_config.max_output_tokens == 65536 | PASS |
| verification_agent.generate_content_config.temperature == 0.1 (unchanged) | PASS |
| verification_agent.generate_content_config.response_mime_type == "application/json" (unchanged) | PASS |
| verification_agent.output_key == "confidence_map" (unchanged) | PASS |
| CONFIDENCE_THRESHOLD == 0.7 (unchanged) | PASS |
| grep -c "max_output_tokens=65536" verification.py == 1 | PASS |
| inspect.getsource(transcribe_manuscript) contains "JSONDecodeError" | PASS |
| inspect.getsource(transcribe_manuscript) contains "TypeError" | PASS |
| render_confidence_html([]) is not None | PASS |
| render_context_table([]) == "No historical entities found in this document." | PASS |
| isinstance(demo, gr.Blocks) | PASS |
| grep -c "JSONDecodeError" app.py == 1 | PASS |

## Commits

| Task | Commit | Message |
|------|--------|---------|
| Task 1 — CR-03 | af2de89 | fix(03-03): add max_output_tokens=65536 to verification.py GenerateContentConfig |
| Task 2 — CR-02 | 56d3944 | fix(03-03): wrap json.loads() calls in try/except gr.Error in transcribe_manuscript |

## Deviations from Plan

None — plan executed exactly as written. Both fixes are single-file surgical edits matching the plan's exact code snippets.

## Known Stubs

None — no stubs introduced. Both fixes are error-handling and configuration changes with no placeholder values.

## Threat Flags

No new threat surface introduced. T-03-07 (information disclosure risk of partial LLM output in gr.Error message) was pre-identified in the plan threat model and accepted — the exception string comes from the json module parser, not from user input.

## Self-Check: PASSED

Files verified to exist:
- src/palimpsest/agents/verification.py: FOUND
- src/palimpsest/app.py: FOUND

Commits verified to exist:
- af2de89 (CR-03 fix): FOUND
- 56d3944 (CR-02 fix): FOUND

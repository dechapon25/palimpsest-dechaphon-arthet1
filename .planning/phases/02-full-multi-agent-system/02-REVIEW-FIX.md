---
phase: 02-full-multi-agent-system
fixed_at: 2026-06-25T14:45:00Z
review_path: .planning/phases/02-full-multi-agent-system/02-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 2: Code Review Fix Report

**Fixed at:** 2026-06-25T14:45:00Z
**Source review:** .planning/phases/02-full-multi-agent-system/02-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 7
- Fixed: 7
- Skipped: 0

## Fixed Issues

### CR-01: SPARQL Injection via Unvalidated Wikidata QID

**Files modified:** `src/palimpsest/mcp/server.py`
**Commit:** ca14a72
**Applied fix:** Added a compiled `QID_PATTERN = re.compile(r"^Q\d+$")` at module level and validation checks before SPARQL interpolation in both `lookup_entity` (line 94-96) and `place_context` (line 273-282). Invalid QIDs now return early with an error instead of being interpolated into SPARQL queries.

### CR-02: normalize_date Produces Invalid ISO 8601 Dates

**Files modified:** `src/palimpsest/mcp/server.py`
**Commit:** 394eb6e
**Applied fix:** Added `import datetime` and a `datetime.date()` validation call after parsing day/month/year components. Invalid date combinations (e.g., Feb 30, day 99) now return `iso_date: None` with an explanatory error instead of producing malformed ISO strings.

### CR-03: Inconsistent Error-Path Return Schema in run_pipeline

**Files modified:** `src/palimpsest/agents/orchestrator.py`
**Commit:** c9fc729
**Applied fix:** Updated the `final_session is None` error-path return dict to include all 6 keys (`cleaned_transcription`, `context_notes` set to None, plus the full metadata dict with `cleaning_model`, `context_model`, `entities_found`, `entities_resolved`). Also updated the docstring to document the full 6-key return schema.

### WR-01: No Validation of Cleaning Agent Output

**Files modified:** `src/palimpsest/agents/orchestrator.py`
**Commit:** 0feb07d
**Applied fix:** Added a validation block after transcription validation that checks: (1) if cleaned output is present and non-empty, parse it as JSON and verify the `cleaned_text` key exists; (2) if cleaned output is missing when status is "ok", append an error. Mirrors the existing transcription validation pattern.

### WR-02: Silent Swallow of context_notes Parse Failures

**Files modified:** `src/palimpsest/agents/orchestrator.py`
**Commit:** 97007e7
**Applied fix:** Replaced the silent `pass` in the `except (json.JSONDecodeError, TypeError)` block with `errors.append("Context notes could not be parsed as JSON")` so callers can distinguish "no entities found" from "context agent parse failure."

### WR-03: Abbreviation Dictionary Entry "no" -> "noviembre" Is a High-Risk False Positive

**Files modified:** `src/palimpsest/mcp/abbreviations.py`, `src/palimpsest/mcp/server.py`
**Commit:** 4d300a8
**Applied fix:** Added an `AMBIGUOUS_ABBREVIATIONS` set (`{"no", "q", "mo"}`) in `abbreviations.py` and updated the `expand_abbreviation` tool in `server.py` to return `"medium"` confidence for tokens in that set instead of the default `"high"`. The import was also updated to include `AMBIGUOUS_ABBREVIATIONS`.

### WR-04: requests Is an Undeclared Direct Dependency

**Files modified:** `requirements.txt`
**Commit:** 0b46661
**Applied fix:** Added `requests>=2.28.0` to `requirements.txt` as a direct dependency, since `server.py` imports and uses `requests` directly for Wikidata/Wikipedia HTTP calls.

---

_Fixed: 2026-06-25T14:45:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_

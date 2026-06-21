---
phase: 01-mvp-linear-pipeline
fixed_at: 2026-06-21T08:30:00Z
review_path: .planning/phases/01-mvp-linear-pipeline/01-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 5
skipped: 1
status: partial
---

# Phase 1: Code Review Fix Report

**Fixed at:** 2026-06-21T08:30:00Z
**Source review:** .planning/phases/01-mvp-linear-pipeline/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 6 (2 Critical, 4 Warning)
- Fixed: 5
- Skipped: 1 (WR-01 already resolved by CR-01 fix)

## Fixed Issues

### CR-01: DecompressionBombError crashes CLI with unhandled traceback

**Files modified:** `src/palimpsest/security/intake.py`
**Commit:** 38afb83
**Applied fix:** Wrapped all Pillow image processing operations in a try/except block that catches `Image.DecompressionBombError` specifically (converts to IntakeError with descriptive message about decompression bomb) and a broad `Exception` catch (converts to IntakeError with generic validation failure message). This ensures all Pillow exceptions are encapsulated within the intake layer's exception contract.

### CR-02: Null dereference in orchestrator when get_session returns None

**Files modified:** `src/palimpsest/agents/orchestrator.py`
**Commit:** 15b9f9e
**Applied fix:** Added an explicit None check after `session_service.get_session()` call. If session is None, returns a structured D-11 error dict with a clear diagnostic message ("Failed to retrieve session after pipeline run") instead of allowing an AttributeError to propagate.

### WR-02: TOCTOU race between size check and file read in intake

**Files modified:** `src/palimpsest/security/intake.py`
**Commit:** acc1dab
**Applied fix:** Replaced the two-step pattern (stat + read_bytes) with a single read-first approach: `raw_bytes = path.read_bytes()` followed by `len(raw_bytes) > MAX_FILE_SIZE_BYTES`. This eliminates the TOCTOU race window and also removes one syscall.

### WR-03: Deprecated Pillow API usage -- getdata() removed in Pillow 14

**Files modified:** `src/palimpsest/security/intake.py`
**Commit:** 9b9bb2b
**Applied fix:** Replaced `img.getdata()` with `img.get_flattened_data()`. Verified that `get_flattened_data()` is available in installed Pillow 12.2.0 and produces identical output (tuple-per-pixel sequence compatible with `putdata()`). Eliminates the DeprecationWarning in test output.

### WR-04: No validation of raw_transcription content type in orchestrator

**Files modified:** `src/palimpsest/agents/orchestrator.py`
**Commit:** 7c3cf63
**Applied fix:** Added `import json` and JSON schema validation after the None/empty checks. Parses the raw_transcription value as JSON and verifies it contains a `"raw_text"` key in a dict structure. On parse failure or missing key, sets status to "error" with a descriptive message. This prevents downstream consumers from receiving output that looks "ok" but doesn't match the expected schema.

## Skipped Issues

### WR-01: Corrupt image files cause unhandled Pillow exceptions in validate_and_clean

**File:** `src/palimpsest/security/intake.py:56-61`
**Reason:** Already resolved by CR-01 fix. The broad `except Exception as e: raise IntakeError(...)` block added in CR-01 catches all Pillow exceptions from corrupt images (SyntaxError, OSError from truncated files, etc.) and converts them to IntakeError. No additional code change needed.
**Original issue:** A file that passes magic-byte check but has a corrupted body would cause unhandled SyntaxError or OSError from Pillow, escaping the IntakeError exception contract.

---

_Fixed: 2026-06-21T08:30:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_

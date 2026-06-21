---
phase: 01-mvp-linear-pipeline
plan: 01
subsystem: security-intake
tags: [scaffold, security, tdd, intake, exif, validation]
dependency_graph:
  requires: []
  provides: [validate_and_clean, IntakeError, MAX_FILE_SIZE_BYTES, ALLOWED_MIME_TYPES, package-structure]
  affects: [02-pipeline-agent, 03-gradio-ui]
tech_stack:
  added: [Pillow-12.2.0, filetype-1.2.0, python-dotenv-1.2.2, google-adk-2.3.0, google-genai-2.9.0]
  patterns: [magic-byte-validation, exif-strip-via-reconstruction, src-layout-package]
key_files:
  created:
    - src/palimpsest/__init__.py
    - src/palimpsest/agents/__init__.py
    - src/palimpsest/security/__init__.py
    - src/palimpsest/security/intake.py
    - src/palimpsest/mcp/__init__.py
    - tests/__init__.py
    - tests/test_intake.py
    - requirements.txt
    - pyproject.toml
    - .env.example
    - .gitignore
    - data/samples/.gitkeep
  modified: []
decisions:
  - Used Pillow built-in Exif API for test EXIF creation instead of piexif (no extra dependency)
  - filetype.guess() for magic-byte validation before any Pillow call (anti-pattern prevention)
  - Image.new() + putdata() for EXIF-free reconstruction (not img.copy() which preserves metadata)
metrics:
  duration: 4 minutes
  completed: 2026-06-21
status: complete
---

# Phase 01 Plan 01: Project Scaffold and Security Intake Summary

Installable src/palimpsest/ package with 10 passing unit tests for validate_and_clean() covering file size rejection, magic-byte type validation, and EXIF metadata stripping via pixel-only image reconstruction.

## Task Results

| Task | Name | Type | Commits | Key Files |
|------|------|------|---------|-----------|
| 1 | Project scaffold | auto | 1bf7863 | src/palimpsest/, requirements.txt, pyproject.toml, .env.example, .gitignore |
| 2 | Security intake (TDD) | auto/tdd | c38bb91 (RED), 9692c22 (GREEN) | src/palimpsest/security/intake.py, tests/test_intake.py |

## TDD Gate Compliance

- RED gate: `test(01-01)` commit c38bb91 -- 10 failing tests (ModuleNotFoundError)
- GREEN gate: `feat(01-01)` commit 9692c22 -- all 10 tests passing
- REFACTOR gate: skipped (implementation clean, no refactoring needed)

## What Was Built

### Package Structure
- `src/palimpsest/` with `agents/`, `security/`, `mcp/` subpackages
- `tests/` directory with test infrastructure
- `data/samples/` for test manuscript images

### Security Intake Module (SEC-01, SEC-02, SEC-03)
- `validate_and_clean(file_path)` -- validates and sanitizes manuscript images
- SEC-02: File size check via `stat().st_size` before reading any bytes (20 MB limit)
- SEC-01: Magic-byte validation via `filetype.guess()` -- never trusts file extension
- SEC-03: EXIF strip via `Image.new()` + `putdata()` pixel reconstruction -- zero metadata carried over
- SEC-04: Documented in comment as handled by transcription agent (Plan 02)

### Configuration Files
- `requirements.txt`: 5 pinned production deps
- `pyproject.toml`: Ruff config targeting Python 3.11
- `.env.example`: Documents GOOGLE_API_KEY with aistudio.google.com reference
- `.gitignore`: Excludes .env, __pycache__/, .venv/, build artifacts

### Test Coverage (10 tests)
- `test_rejects_oversized_file` -- SEC-02: >20MB rejection
- `test_accepts_file_at_exact_limit` -- SEC-02: boundary case (exactly 20MB not rejected for size)
- `test_rejects_pdf` -- SEC-01: PDF magic bytes rejected
- `test_accepts_jpeg` -- SEC-01: valid JPEG accepted with correct MIME
- `test_accepts_png` -- SEC-01: valid PNG accepted with correct MIME
- `test_extension_is_irrelevant` -- SEC-01: PNG with .jpg extension detected as PNG
- `test_exif_strip` -- SEC-03: EXIF metadata removed from output bytes
- `test_exif_strip_preserves_dimensions` -- SEC-03: pixel dimensions preserved after strip
- `test_max_file_size_constant` -- constant equals 20971520
- `test_allowed_mime_types` -- set contains exactly image/jpeg and image/png

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

All plan-level verification checks passed:
1. `pytest tests/test_intake.py -v` -- 10/10 passed, exit code 0
2. `MAX_FILE_SIZE_BYTES` prints 20971520
3. `filetype.guess` found in intake.py (1 occurrence)
4. `Image.new` found at line 60 in intake.py
5. `.env.example` contains GOOGLE_API_KEY
6. `pyproject.toml` contains [tool.ruff] section

## Known Stubs

None -- all implemented functionality is complete and wired.

## Decisions Made

1. **Pillow Exif API for tests**: Used Pillow's built-in `Image.getexif().tobytes()` to create test EXIF data instead of adding piexif as a test dependency.
2. **Deprecation warning noted**: `Image.getdata()` deprecated in Pillow 14 (2027-10-15) in favor of `get_flattened_data()`. No action needed for Pillow 12.2.0; document for future upgrade.

## Notes

- Virtual environment created at `.venv/` for development (gitignored)
- All tests are pure Python logic -- no API calls, no network access
- The `kind.mime` return pattern (not `img.format`) is critical for downstream `types.Part.from_bytes()` compatibility in Plan 02

## Self-Check: PASSED

- All 8 key files verified on disk
- All 3 task commits (1bf7863, c38bb91, 9692c22) verified in git log

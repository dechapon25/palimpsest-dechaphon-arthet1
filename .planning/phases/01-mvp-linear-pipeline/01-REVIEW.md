---
phase: 01-mvp-linear-pipeline
reviewed: 2026-06-21T08:18:47Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - src/palimpsest/security/intake.py
  - src/palimpsest/agents/transcription.py
  - src/palimpsest/agents/orchestrator.py
  - src/palimpsest/run.py
  - tests/test_intake.py
findings:
  critical: 2
  warning: 4
  info: 1
  total: 7
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-06-21T08:18:47Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed the Phase 1 MVP linear pipeline: security intake (file validation, EXIF stripping), transcription agent configuration, orchestrator pipeline execution, and CLI entry point. The security intake layer is well-designed with defense-in-depth (magic bytes, size limits, EXIF stripping), and the prompt injection defense is thoughtfully implemented.

However, there are two critical issues: an unhandled `DecompressionBombError` path that bypasses structured error handling and crashes the CLI, and a null-safety gap in the orchestrator where `get_session()` can return `None`. There are also several warnings around incomplete exception handling in the intake layer and use of deprecated Pillow API.

## Critical Issues

### CR-01: DecompressionBombError crashes CLI with unhandled traceback

**File:** `src/palimpsest/run.py:51-69`
**Issue:** A crafted PNG can be small on disk (passes the 20 MB size check at `intake.py:37`) but decompress to over 178 million pixels, triggering Pillow's `DecompressionBombError`. This exception inherits from `Exception` -- NOT from `OSError` -- so it escapes both the `IntakeError` handler (line 53) and the `(FileNotFoundError, OSError)` handler (line 62). The broad `except Exception` at line 75 only covers the `asyncio.run()` call, not `validate_and_clean()`. The result: an unhandled exception, ugly traceback to stderr, and no structured JSON output.

This is a security concern because decompression bombs are a known attack vector for image-processing services. A malicious user could crash the pipeline and cause resource exhaustion (memory allocation for the decompressed pixel buffer).

**Fix:** Either catch `DecompressionBombError` in `validate_and_clean` and convert it to `IntakeError`, or broaden the exception handling in `run.py`:

```python
# Option A: In intake.py, wrap Pillow operations
from PIL import Image, ImageOps

try:
    img = Image.open(io.BytesIO(raw_bytes))
    img = ImageOps.exif_transpose(img)
    clean_img = Image.new(img.mode, img.size)
    clean_img.putdata(list(img.getdata()))
except Image.DecompressionBombError:
    raise IntakeError("Image dimensions exceed safe limits (possible decompression bomb)")
except Exception as e:
    raise IntakeError(f"Failed to process image: {e}") from e

# Option B: In run.py, add a catch-all before the pipeline try block
except (IntakeError) as e:
    ...
except Exception as e:
    result = {
        "status": "error",
        "raw_transcription": None,
        "metadata": {"filename": filename, "model": None, "tokens_used": None},
        "errors": [f"Intake error: {e}"],
    }
```

Option A is preferred because it keeps the security boundary clean in `intake.py`.

### CR-02: Null dereference in orchestrator when get_session returns None

**File:** `src/palimpsest/agents/orchestrator.py:74-80`
**Issue:** `InMemorySessionService.get_session()` has return type `Optional[Session]` (confirmed by inspecting the ADK source). If the session is not found (e.g., internal session service error, session eviction, or ADK bug), line 80 executes `final_session.state.get("raw_transcription")` on a `None` value, raising `AttributeError: 'NoneType' object has no attribute 'state'`. This would propagate as an unstructured exception through `run.py`'s broad `except Exception` handler (line 75), producing a generic "Pipeline error" message rather than a clear diagnostic.

**Fix:**
```python
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
```

## Warnings

### WR-01: Corrupt image files cause unhandled Pillow exceptions in validate_and_clean

**File:** `src/palimpsest/security/intake.py:56-61`
**Issue:** A file that passes the filetype magic-byte check (valid JPEG/PNG header in the first 261 bytes) but has a corrupted body will cause `Image.open()` or `img.getdata()` to raise `OSError` ("Truncated File Read"), `SyntaxError` (corrupt structure), or other PIL-specific exceptions. While `run.py` catches `OSError` at line 62, `SyntaxError` is NOT caught. More importantly, `validate_and_clean` should encapsulate these as `IntakeError` since they represent validation failures, not I/O errors. Currently the function's exception contract is incomplete -- it documents only `IntakeError` but can raise `OSError`, `SyntaxError`, `DecompressionBombError`, and potentially others.

**Fix:** Wrap the entire Pillow processing block in `validate_and_clean`:
```python
try:
    img = Image.open(io.BytesIO(raw_bytes))
    img = ImageOps.exif_transpose(img)
    clean_img = Image.new(img.mode, img.size)
    clean_img.putdata(list(img.getdata()))
except Exception as e:
    raise IntakeError(f"Image validation failed: {e}") from e
```

### WR-02: TOCTOU race between size check and file read in intake

**File:** `src/palimpsest/security/intake.py:36-42`
**Issue:** `path.stat().st_size` (line 36) and `path.read_bytes()` (line 42) are two separate system calls. Between them, the file could be replaced with a larger file (symlink swap, concurrent write). The size check would pass on the original small file, but `read_bytes()` would load the larger replacement into memory. For a CLI tool this is low-probability, but if `validate_and_clean` is reused for the Gradio web UI in Phase 2 (concurrent uploads), this becomes exploitable to bypass the 20 MB limit.

**Fix:** Read the file first, then check the byte length of what was actually read:
```python
raw_bytes = path.read_bytes()
if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
    raise IntakeError(
        f"File too large: {len(raw_bytes)} bytes (max {MAX_FILE_SIZE_BYTES})"
    )
```
This also eliminates one syscall, making the function simpler.

### WR-03: Deprecated Pillow API usage -- getdata() removed in Pillow 14

**File:** `src/palimpsest/security/intake.py:61`
**Issue:** `img.getdata()` is deprecated since Pillow 12.x and will be removed in Pillow 14 (2027-10-15). The deprecation warning is already active (`DeprecationWarning: Image.Image.getdata is deprecated`). While the Kaggle competition deadline (2026-07-06) is well before removal, this creates noise in test output and any CI that treats warnings as errors.

**Fix:**
```python
clean_img.putdata(list(img.get_flattened_data()))
```
Note: `get_flattened_data()` is available in the currently installed Pillow 12.2.0.

### WR-04: No validation of raw_transcription content type in orchestrator

**File:** `src/palimpsest/agents/orchestrator.py:80-96`
**Issue:** The transcription agent uses `response_mime_type="application/json"` and `output_key="raw_transcription"`. ADK stores the model's text output in session state under that key. The orchestrator checks only for `None` and empty string, but does not validate that the value is actually a parseable JSON string or matches the expected `{"raw_text": "..."}` schema. If the model returns valid JSON that doesn't match the schema (e.g., `{"error": "cannot process"}` or a bare string `"hello"`), the output dict will have `status: "ok"` with a `raw_transcription` value that downstream consumers cannot reliably parse.

**Fix:** Add basic JSON schema validation:
```python
import json

raw = final_session.state.get("raw_transcription")

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
            errors.append(f"Unexpected transcription schema: missing 'raw_text' key")
        else:
            status = "ok"
    except (json.JSONDecodeError, TypeError):
        status = "error"
        errors.append("Transcription output is not valid JSON")
```

## Info

### IN-01: Test file missing coverage for corrupt/adversarial image inputs

**File:** `tests/test_intake.py`
**Issue:** The test suite covers happy paths (valid JPEG/PNG), size limits, and EXIF stripping, but does not test corrupt files (truncated JPEG, malformed PNG), decompression bombs, or zero-byte files. These are the exact edge cases where the intake layer has unhandled exceptions (see CR-01, WR-01). Adding these tests would have caught the exception contract gaps.

**Fix:** Add test cases:
```python
def test_rejects_truncated_jpeg(tmp_path):
    """A JPEG with valid magic bytes but truncated body raises IntakeError."""
    path = _make_jpeg(tmp_path)
    raw = Path(path).read_bytes()
    truncated = tmp_path / "truncated.jpg"
    truncated.write_bytes(raw[:50])
    with pytest.raises(IntakeError):
        validate_and_clean(str(truncated))

def test_rejects_zero_byte_file(tmp_path):
    """A zero-byte file raises IntakeError (not a crash)."""
    empty = tmp_path / "empty.jpg"
    empty.write_bytes(b"")
    with pytest.raises(IntakeError):
        validate_and_clean(str(empty))
```

---

_Reviewed: 2026-06-21T08:18:47Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

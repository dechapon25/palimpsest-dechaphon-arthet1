---
phase: 03-verification-gradio-ui
reviewed: 2026-06-26T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - src/palimpsest/agents/verification.py
  - src/palimpsest/agents/orchestrator.py
  - src/palimpsest/app.py
  - requirements.txt
findings:
  critical: 3
  warning: 6
  info: 2
  total: 11
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-06-26
**Depth:** standard
**Files Reviewed:** 4 (+ cross-referenced `src/palimpsest/security/intake.py`, `src/palimpsest/agents/cleaning.py`)
**Status:** issues_found

## Summary

Reviewed the Phase 3 additions: the verification agent, orchestrator extension, Gradio UI (`app.py`), and `requirements.txt`. Three blockers were found. The most severe is in `intake.py` (cross-referenced from `app.py`): `img.get_flattened_data()` is not a Pillow API method, which means the EXIF-stripping security control crashes on every image upload, making the entire pipeline non-functional. The verification agent is also missing `max_output_tokens`, violating the project's own explicit requirement stated in CLAUDE.md. And `app.py`'s JSON parsing of pipeline outputs lacks error handling, meaning LLM failures that do not set `status="error"` in the orchestrator (cleaning, context, and confidence failures) propagate as unhandled Python exceptions rather than user-visible `gr.Error` banners.

---

## Critical Issues

### CR-01: `img.get_flattened_data()` is not a Pillow API method — EXIF stripping crashes on every upload

**File:** `src/palimpsest/security/intake.py:61` (cross-referenced from `src/palimpsest/app.py:159`)
**Issue:** `clean_img.putdata(list(img.get_flattened_data()))` calls a method that does not exist in Pillow. The correct Pillow API is `Image.getdata()`. Because `AttributeError` is caught by the broad `except Exception as e` block at intake.py:71 and re-raised as `IntakeError("Image validation failed: ...")`, every single image upload fails validation. Security control SEC-03 (EXIF stripping) never executes. The pipeline is completely non-functional.

**Fix:**
```python
# Before (line 61)
clean_img.putdata(list(img.get_flattened_data()))

# After
clean_img.putdata(list(img.getdata()))
```

---

### CR-02: Unhandled `JSONDecodeError` in `transcribe_manuscript` for cleaning, context, and confidence outputs

**File:** `src/palimpsest/app.py:185-200`
**Issue:** The four `json.loads()` calls on pipeline outputs have no try/except. The orchestrator's validation sets `status="error"` only for `raw_transcription` JSON failures (orchestrator.py:139). Cleaning, context, and confidence parse failures append to `errors` but leave `status="ok"` (orchestrator.py:148-151). When `app.py` passes the status gate at line 170, it then calls `json.loads()` on potentially malformed strings from those agents. Any `JSONDecodeError` or `TypeError` propagates as an unhandled exception that Gradio surfaces as a generic 500 error rather than a user-readable `gr.Error` banner.

**Fix:** Wrap the four parse calls in a try/except and raise `gr.Error` on failure:
```python
try:
    raw_text = json.loads(raw_json).get("raw_text", "") if isinstance(raw_json, str) else ""
    cleaned_text = (
        json.loads(cleaned_json).get("cleaned_text", "")
        if isinstance(cleaned_json, str)
        else ""
    )
    context_list = (
        json.loads(context_json) if isinstance(context_json, str) else (context_json or [])
    )
    confidence_list = (
        json.loads(confidence_json)
        if isinstance(confidence_json, str)
        else (confidence_json or [])
    )
except (json.JSONDecodeError, TypeError) as exc:
    raise gr.Error(f"Pipeline output could not be parsed: {exc}") from exc
```

---

### CR-03: `verification_agent` missing `max_output_tokens` — output silently truncated for long manuscripts

**File:** `src/palimpsest/agents/verification.py:66-79`
**Issue:** The verification agent must emit one JSON object per space-separated token in the cleaned transcription. For a long manuscript, this array can easily exceed the model's default output token limit, causing silent mid-array truncation. The resulting truncated JSON string fails to parse in `app.py`, producing an unhandled `JSONDecodeError` (see CR-02) or an empty confidence map with no diagnostic. The project's own CLAUDE.md explicitly states: *"Token limits: Set maxOutputTokens=65536 explicitly or transcription silently truncates."* The transcription agent (transcription.py:60) already follows this requirement; the verification agent does not.

**Fix:**
```python
generate_content_config=types.GenerateContentConfig(
    temperature=0.1,
    response_mime_type="application/json",
    max_output_tokens=65536,  # Required: prevents silent truncation of large word arrays
),
```

---

## Warnings

### WR-01: `float()` conversion without exception handling or range clamping in `render_confidence_html`

**File:** `src/palimpsest/app.py:79`
**Issue:** `score = float(entry.get("score", 1.0))` has no try/except. If the LLM returns a null value (JSON `null` → Python `None`) or a non-numeric string, `float(None)` or `float("high")` raises `TypeError`/`ValueError`, crashing the Gradio handler. Additionally, if the LLM returns a score outside `[0.0, 1.0]` (scores > 1.0 are plausible given the instruction wording "0.0 to 1.0" is advisory, not enforced), `opacity = round(1 - score, 2)` produces a negative value, which is invalid CSS and suppressed by browsers without visible error.

**Fix:**
```python
try:
    score = float(entry.get("score", 1.0))
except (TypeError, ValueError):
    score = 1.0  # treat unscored words as confident rather than crashing
score = max(0.0, min(1.0, score))  # clamp to valid CSS opacity range
```

---

### WR-02: No type guard on `confidence_list` or `context_list` before rendering — `AttributeError` if LLM returns object instead of array

**File:** `src/palimpsest/app.py:211-214`
**Issue:** `render_confidence_html(confidence_list)` and `render_context_table(context_list)` assume their argument is a `list`. If the LLM or MCP server returns a JSON object `{}` instead of an array `[]`, `json.loads()` produces a dict. For `render_confidence_html`, `not word_scores` is `False` (non-empty dict is truthy), the loop `for entry in word_scores` iterates over dict keys (strings), and `entry.get(...)` on a string raises `AttributeError`. Neither renderer validates the type of its input.

**Fix:**
```python
if not isinstance(confidence_list, list):
    confidence_list = []
if not isinstance(context_list, list):
    context_list = []
```
Add these guards after the json.loads calls and before the render calls.

---

### WR-03: Pipe characters in LLM-generated entity values corrupt the Markdown table

**File:** `src/palimpsest/app.py:130`
**Issue:** `render_context_table` inserts entity values directly into a Markdown table row:
```python
rows.append(f"| {entity} | {entity_type} | {description} | {dates} | {source} |")
```
If any value contains a `|` character (e.g., a description like `"Governor of New Spain | also known as..."` from a MCP lookup), it creates extra columns. This misaligns all subsequent rows and can truncate visible columns without any indication of data loss.

**Fix:** Strip or escape pipe characters before insertion:
```python
def _md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")

rows.append(
    f"| {_md_cell(entity)} | {_md_cell(entity_type)} | "
    f"{_md_cell(description)} | {_md_cell(dates)} | {_md_cell(source)} |"
)
```

---

### WR-04: Markdown injection risk in context table — LLM-generated content rendered as HTML

**File:** `src/palimpsest/app.py:115-132`
**Issue:** `render_context_table` applies no escaping to any column value before inserting into Markdown. Gradio 6.x renders `gr.Markdown` content to HTML using the `markdown` library, which allows inline HTML by default. A misbehaving MCP server or an adversarial manuscript exploiting the context agent's LLM could inject Markdown hyperlinks, inline HTML, or image tags into the `description` or `source_url` fields. The `render_confidence_html` function correctly applies `html.escape()` for the same threat model (SEC-04, T-03-03), but `render_context_table` does not. The security posture is inconsistent.

**Fix:** Escape HTML special characters in all values that go into Markdown string cells. For the `source` column, validate it is an `http(s)://` URL before including it as a link; otherwise render it as plain text.

---

### WR-05: `CONFIDENCE_THRESHOLD` duplicated in `app.py` and `verification.py` — silent drift risk

**File:** `src/palimpsest/app.py:47` and `src/palimpsest/agents/verification.py:24`
**Issue:** Both files independently define `CONFIDENCE_THRESHOLD = 0.7`. If the threshold is updated in `verification.py` (e.g., raised to 0.8 based on empirical calibration) without updating `app.py`, the scoring model flags more words as uncertain but the UI highlights fewer of them. The mismatch produces an invisible discrepancy between scored confidence and displayed uncertainty, with no test or assertion to catch it.

**Fix:** Remove the definition from `app.py` and import it:
```python
# app.py
from palimpsest.agents.verification import CONFIDENCE_THRESHOLD
```

---

### WR-06: Orchestrator returns `status="ok"` when cleaning agent produces no output

**File:** `src/palimpsest/agents/orchestrator.py:151-152`
**Issue:** When `cleaned` is `None` (cleaning agent returned nothing) and transcription succeeded, the orchestrator appends to `errors` but keeps `status="ok"`. This passes `app.py`'s error gate at line 170. The verification agent's instruction then receives `cleaned_transcription = None` in session state. Depending on how ADK substitutes `{cleaned_transcription}` into the instruction template (verification.py:36), the LLM is asked to parse "None" as JSON. This produces an empty or malformed `confidence_map` downstream, and the user sees the confidence map section silently blank with no indication of what failed.

**Fix:** Treat missing cleaning output as a pipeline error to halt early and surface a clear message:
```python
elif status == "ok":
    status = "error"  # downgrade; can't verify without cleaned text
    errors.append("Cleaning agent returned no output — pipeline halted")
```

---

## Info

### IN-01: `requests` dependency is unpinned

**File:** `requirements.txt:6`
**Issue:** `requests>=2.28.0` accepts any future major version, while all other dependencies are pinned to exact versions. On a fresh install months from now, `pip` could resolve `requests 3.x` if released, which may have breaking API changes that affect the MCP server or other networking code.

**Fix:** Pin to a tested version:
```
requests==2.32.3
```

---

### IN-02: Verification agent uses template variable injection pattern inconsistent with other agents

**File:** `src/palimpsest/agents/verification.py:35-36`
**Issue:** `verification.py` injects session state into the system prompt via `{cleaned_transcription}` template substitution. The three other agents (cleaning, context, transcription) describe the state key in prose and rely on ADK's conversation mechanism — they do not use template variables. This is a novel pattern in this codebase. If ADK's template substitution behavior changes in a future version, or if the substitution mechanism does not handle the JSON string's curly braces correctly in some edge case, the verification agent would silently send a literal `{cleaned_transcription}` string to the model while the others remain unaffected. The pattern should be documented or harmonized.

---

_Reviewed: 2026-06-26_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

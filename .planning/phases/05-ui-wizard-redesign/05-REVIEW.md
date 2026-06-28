---
phase: 05-ui-wizard-redesign
reviewed: 2026-06-28T00:00:00Z
depth: standard
files_reviewed: 1
files_reviewed_list:
  - src/palimpsest/app.py
findings:
  critical: 3
  warning: 2
  info: 2
  total: 7
status: issues_found
---

# Phase 05: Code Review Report

**Reviewed:** 2026-06-28
**Depth:** standard
**Files Reviewed:** 1 (`src/palimpsest/app.py`)
**Status:** issues_found

## Summary

`app.py` implements the Bento Grid + Glassmorphism wizard redesign cleanly: XSS escaping in `render_confidence_html` is solid, the 10-output `outputs_full` wiring is consistent across `transcribe_manuscript` and `reset_manuscript`, and the security intake delegation pattern is correct.

Three blockers were found, all stemming from the same root cause: LLM output is polymorphic and partially validated, but the rendering and parsing helpers assume perfectly-shaped data without catching the specific exceptions that arise when that assumption fails. A single `null` score from the verification agent, a JSON array at the top level of `raw_transcription`, or a stray `null` element in `confidence_map` will each cause an unhandled exception that crashes the Gradio handler silently rather than surfacing a graceful `gr.Error`.

Two warnings round out the findings: Markdown table cells are not pipe-escaped (LLM output containing `|` corrupts table structure), and the `asyncio.run()` call is fragile in embedded-event-loop environments such as Jupyter.

---

## Critical Issues

### CR-01: `float()` crashes on `score: null` from LLM

**File:** `src/palimpsest/app.py:159`

**Issue:** `entry.get("score", 1.0)` only uses the default `1.0` when the key is **absent** from the dict. When the verification agent returns `"score": null` in the JSON array (a valid LLM output), Python deserializes it as `None` and the key is present, so `get` returns `None`. `float(None)` raises `TypeError`. This exception is not caught anywhere in `render_confidence_html` and propagates unhandled through the Gradio click handler, producing a generic internal error instead of a graceful message.

**Fix:**
```python
# Use `or` to treat both absent-key and None as the fallback
score_raw = entry.get("score")
try:
    score = float(score_raw) if score_raw is not None else 1.0
except (TypeError, ValueError):
    score = 1.0  # treat unparseable score as fully confident
```

---

### CR-02: `AttributeError` not caught in `transcribe_manuscript` JSON parsing block

**File:** `src/palimpsest/app.py:265-273`

**Issue:** The try/except block catches `(json.JSONDecodeError, TypeError)` but not `AttributeError`. If `json.loads(raw_json)` succeeds but returns a JSON array (e.g. `[...]`) instead of a dict, calling `.get("raw_text", "")` on a `list` raises `AttributeError`. The same applies to the `cleaned_json` path on line 268. Malformed-but-valid JSON from the pipeline would escape the error handler and crash the Gradio callback.

**Fix:**
```python
try:
    raw_parsed = json.loads(raw_json) if isinstance(raw_json, str) else {}
    if not isinstance(raw_parsed, dict):
        raise gr.Error("Pipeline returned unexpected transcription format.")
    raw_text = raw_parsed.get("raw_text", "")

    cleaned_parsed = json.loads(cleaned_json) if isinstance(cleaned_json, str) else {}
    if not isinstance(cleaned_parsed, dict):
        cleaned_text = ""
    else:
        cleaned_text = cleaned_parsed.get("cleaned_text", "")
except (json.JSONDecodeError, TypeError, AttributeError) as exc:
    raise gr.Error(f"Pipeline output could not be parsed: {exc}") from exc
```

---

### CR-03: No type guard on loop entries in `render_confidence_html` and `render_context_table`

**File:** `src/palimpsest/app.py:154-169` and `199-210`

**Issue:** Both rendering helpers iterate over a list that originated from LLM JSON output and call `.get()` on each element, assuming each element is a dict. A single `null` element (e.g. `[{"word":"foo",...}, null, {"word":"bar",...}]`) makes `None.get(...)` raise `AttributeError`. A string element has no `.get` either. The `context_list` and `confidence_list` are type-checked at the top level (`isinstance(..., list)`) but not at the element level. The exception is unhandled, crashing the Gradio handler.

**Fix — `render_confidence_html` loop:**
```python
for entry in word_scores:
    if not isinstance(entry, dict):
        continue  # skip malformed entries silently
    escaped_word = html.escape(str(entry.get("word", "")))
    ...
```

**Fix — `render_context_table` loop:**
```python
for note in context_notes:
    if not isinstance(note, dict):
        continue
    entity = str(note.get("entity", ""))
    ...
```

---

## Warnings

### WR-01: Pipe characters in LLM-generated fields corrupt Markdown table structure

**File:** `src/palimpsest/app.py:210`

**Issue:** `entity`, `entity_type`, `description`, `dates`, and `source` are concatenated directly into `|`-delimited Markdown table cells without escaping pipe characters or stripping newlines. Any LLM response containing `|` in a description or entity name breaks the table's column alignment. A newline inside any field would split the row across two lines, rendering garbled output. This is a reliable display defect given that historical descriptions frequently include `|` — or when `source_url` carries URLs with pipe-encoded parameters.

**Fix:**
```python
def _md_cell(value: str) -> str:
    """Escape Markdown table special characters in a single cell value."""
    return value.replace("|", "\\|").replace("\n", " ").replace("\r", "")

rows.append(
    f"| {_md_cell(entity)} | {_md_cell(entity_type)} | "
    f"{_md_cell(description)} | {_md_cell(dates)} | {_md_cell(source)} |"
)
```

---

### WR-02: `asyncio.run()` inside sync Gradio handler fails in embedded-loop environments

**File:** `src/palimpsest/app.py:247`

**Issue:** `asyncio.run()` raises `RuntimeError: This event loop is already running` whenever it is called from within a thread that already owns a running event loop. Gradio's thread-pool workers have no event loop by default, so the current deployment is safe. However, running the app from Jupyter (`jupyter nbconvert --execute`), from pytest with `asyncio` fixtures, or if a future Gradio version moves to an async-first architecture will all trigger this crash. The docstring comment ("safe in Gradio thread pool") acknowledges the assumption without a guard.

**Fix:** Use `nest_asyncio` for embedded contexts, or restructure to an async Gradio handler (supported natively in Gradio 4+):
```python
# Option A: make the Gradio handler async (cleanest)
async def transcribe_manuscript(file_path: str) -> tuple:
    ...
    result = await run_pipeline(clean_bytes, mime_type, filename)
    ...
```
Gradio 4+ accepts coroutines as `fn=` arguments directly; `asyncio.run()` is then unnecessary.

---

## Info

### IN-01: `transcribe_manuscript` docstring documents a 5-tuple return but function returns 10-tuple

**File:** `src/palimpsest/app.py:222-231`

**Issue:** The docstring `Returns` section says:
> `5-tuple: (cleaned_text, raw_text, cleaned_text, markdown_table, html_string)`

The actual return value is a 10-element tuple (lines 298-309) that additionally includes four `gr.update(visible=True)` values and a status string. This stale docstring would mislead a contributor adding a new output to `outputs_full`.

**Fix:** Update the docstring to reflect the current 10-element return:
```
Returns:
    10-tuple mapped to outputs_full:
        (cleaned_text, raw_text, cleaned_text, notes_markdown, confidence_html,
         gr.update(transcription_section), gr.update(confidence_section),
         gr.update(notes_section), gr.update(reset_btn), status_string)
```

---

### IN-02: `toggle_view` docstring uses "Cleaned" but UI Radio choice is "Limpiada"

**File:** `src/palimpsest/app.py:316` vs `365`

**Issue:** The function's `Args` docstring says `view: Selected radio value ("Raw" or "Cleaned")`, but the actual `gr.Radio` widget at line 365 uses `choices=["Raw", "Limpiada"]`. The function logic works correctly (`if view == "Raw" else cleaned`) regardless of the exact string for the non-Raw branch, but the docstring is misleading and would cause confusion if a reader expects "Cleaned" to be a valid input value.

**Fix:** Update docstring to `("Raw" or "Limpiada")` to match the actual widget choices.

---

_Reviewed: 2026-06-28_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

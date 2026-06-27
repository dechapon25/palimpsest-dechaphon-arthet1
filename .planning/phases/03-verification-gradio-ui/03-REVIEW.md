---
phase: 03-verification-gradio-ui
reviewed: 2026-06-27T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - src/palimpsest/agents/orchestrator.py
  - src/palimpsest/agents/verification.py
  - src/palimpsest/app.py
findings:
  critical: 2
  warning: 5
  info: 2
  total: 9
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-06-27
**Depth:** standard
**Files Reviewed:** 3 (orchestrator.py, verification.py, app.py)
**Status:** issues_found

## Summary

Reviewed the three Phase 3 source files at standard depth with cross-file analysis.
Two blockers were found. The first is a security vulnerability: `render_context_table`
inserts LLM-generated entity values directly into a Markdown string without any
escaping, while Gradio renders `gr.Markdown` as HTML — creating an XSS path from
adversarial manuscript content through the context agent. The second blocker is a
contract violation in the orchestrator: cleaning and context failures append to
`errors` without setting `status = "error"`, so the app's error gate passes and
the UI renders silently empty/corrupt outputs instead of raising a `gr.Error`
banner. Five warnings cover unhandled type/value errors in rendering, missing list
type guards before render functions, pipe character injection into the Markdown
table, a duplicated constant, and a failure path that raises an unhandled `KeyError`
from deep in ADK's template engine when `cleaned_transcription` is absent from
session state.

The ADK instruction template engine was inspected directly
(`google/adk/utils/instructions_utils.py`). It uses regex-based substitution
(`r'{+[^{}]*}+'`) and validates names against `_is_valid_state_name()` before
substituting. Literal JSON-schema examples such as `{"word": "<token>", ...}` in
`verification.py` are left untouched because their inner text fails the identifier
check. The "unescaped braces" concern noted in the previous review (IN-02) is
confirmed to be a false positive against this ADK version.

---

## Critical Issues

### CR-01: XSS via unescaped LLM values in `render_context_table`

**File:** `src/palimpsest/app.py:119-131`
**Issue:** `render_context_table` converts all five column values with `str()` and
inserts them directly into a Markdown table row — no `html.escape()`, no pipe
escaping, nothing. Gradio 6.x renders `gr.Markdown` as HTML. A misbehaving MCP
server or manuscript content that prompt-injects the context agent can produce
entity values containing raw HTML tags (`<script>`, inline event handlers,
`javascript:` links, `<img onerror=...>`). Those tags pass through the Markdown
renderer to the browser and execute. The contrast with `render_confidence_html`
(which explicitly applies `html.escape()` for the same threat model, documented
at lines 75-78) makes this a clear, inconsistent oversight against a threat the
codebase explicitly models (SEC-04, T-03-03, OWASP LLM01:2025).

**Fix:**
```python
import html as _html

def _md_cell(value: str) -> str:
    """Escape HTML and pipe characters for safe Markdown table cells."""
    return _html.escape(value).replace("|", "&#124;").replace("\n", " ")

# In render_context_table, replace the raw f-string with:
rows.append(
    f"| {_md_cell(entity)} | {_md_cell(entity_type)} | "
    f"{_md_cell(description)} | {_md_cell(dates)} | {_md_cell(source)} |"
)
```

For the `source` column, additionally validate that the value starts with
`https://` or `http://` before rendering it as a plain link; otherwise treat it
as plain (escaped) text.

---

### CR-02: Orchestrator returns `status="ok"` when cleaning or context agents fail

**File:** `src/palimpsest/agents/orchestrator.py:143-152, 168-170`
**Issue:** The orchestrator sets `status` only in the transcription validation
block (lines 125-141). The cleaning validation block (lines 143-152) and the
context parse block (lines 168-170) each `errors.append(...)` without ever
setting `status = "error"`. The result is that a partial pipeline run — where
transcription succeeded but cleaning or context failed — returns a dict with
`"status": "ok"` and a non-empty `errors` list.

`app.py` gates on `result.get("status") == "error"` (line 170). When status is
"ok" despite cleaning failure, the gate passes. `app.py` then calls
`json.loads("{}")` on the missing cleaned output, gets `""` for `cleaned_text`,
and the user sees an empty transcription textbox with no error banner and no
indication that the pipeline partially failed. A researcher can silently receive
a blank result and assume the manuscript was illegible.

**Fix:**
```python
# orchestrator.py — cleaning block (around line 143)
if cleaned is not None and isinstance(cleaned, str) and cleaned.strip():
    try:
        cleaned_parsed = json.loads(cleaned)
        if not isinstance(cleaned_parsed, dict) or "cleaned_text" not in cleaned_parsed:
            status = "error"
            errors.append("Cleaning output missing 'cleaned_text' key")
    except (json.JSONDecodeError, TypeError):
        status = "error"
        errors.append("Cleaning output is not valid JSON")
elif status == "ok":
    status = "error"
    errors.append("Cleaning agent returned no output — pipeline halted")

# orchestrator.py — context block (around line 168)
    except (json.JSONDecodeError, TypeError):
        status = "error"
        errors.append("Context notes could not be parsed as JSON")
```

---

## Warnings

### WR-01: Unhandled `ValueError`/`TypeError` in `float()` call crashes confidence render

**File:** `src/palimpsest/app.py:79`
**Issue:** `score = float(entry.get("score", 1.0))` is unguarded. If the
verification LLM returns a `null` value (JSON `null` → Python `None`),
`float(None)` raises `TypeError`. If it returns a non-numeric string such as
`"high"` or `"0.8 (uncertain)"`, `float(...)` raises `ValueError`. Either
exception propagates out of `render_confidence_html`, through
`transcribe_manuscript`, and surfaces as an unhandled server error rather than a
`gr.Error` banner, crashing the entire confidence panel for all entries even if
only one is malformed. Additionally, if the LLM returns a value outside `[0.0,
1.0]` (e.g., `1.2`), `opacity = round(1 - score, 2)` produces a negative CSS
value which browsers silently ignore, causing invisible span styling.

**Fix:**
```python
try:
    score = float(entry.get("score", 1.0))
except (TypeError, ValueError):
    score = 1.0  # treat malformed scores as confident; do not crash
score = max(0.0, min(1.0, score))  # clamp to valid CSS opacity range
```

---

### WR-02: No type guard on `confidence_list`/`context_list` before render calls

**File:** `src/palimpsest/app.py:193-215`
**Issue:** After the `json.loads()` calls, `context_list` and `confidence_list`
are passed directly to `render_context_table` and `render_confidence_html`
respectively. Both functions are typed as `list[dict]` and contain `for entry in
word_scores` / `for note in context_notes` loops. If the LLM returns a JSON
object (`{}`) instead of a JSON array (`[]`) — a plausible LLM formatting failure
— `json.loads()` returns a `dict`. A non-empty dict is truthy, so the early
`if not word_scores:` guard passes. The loop then iterates over the dict's string
keys, and `entry.get("word", "")` on a string raises `AttributeError`, crashing
the handler.

**Fix:**
```python
# Add immediately after the json.loads block, before render calls:
if not isinstance(context_list, list):
    context_list = []
if not isinstance(confidence_list, list):
    confidence_list = []
```

---

### WR-03: Pipe characters in LLM-generated values corrupt the Markdown table

**File:** `src/palimpsest/app.py:130`
**Issue:** All five column values (`entity`, `entity_type`, `description`,
`dates`, `source`) are interpolated into a Markdown table row using a bare
f-string. If any value contains a `|` character — common in historical
descriptions such as `"Governor of New Spain | also known as..."` from a MCP
lookup — it creates extra columns, misaligns every following row, and silently
truncates visible data. Newlines in LLM-generated descriptions also split the
Markdown table row across multiple lines, breaking the table parser.

This finding is partially subsumed by CR-01's fix (the `_md_cell` helper should
also replace `|` and `\n`), but is called out separately because it is a data
integrity failure independent of the XSS path.

**Fix:** See the `_md_cell` helper under CR-01, which handles both pipe and
newline escaping alongside HTML escaping.

---

### WR-04: `CONFIDENCE_THRESHOLD` duplicated in two modules — silent drift risk

**File:** `src/palimpsest/agents/verification.py:24` and `src/palimpsest/app.py:47`
**Issue:** Both files independently define `CONFIDENCE_THRESHOLD = 0.7`. The
comment in `app.py` says it "mirrors" the other. If the threshold is updated in
`verification.py` based on empirical calibration (e.g., raised to `0.8`) without
updating `app.py`, the verification LLM flags more words uncertain but the UI
highlights fewer — an invisible discrepancy. No test or import enforces the
invariant.

**Fix:**
```python
# Remove from app.py line 47 and replace with:
from palimpsest.agents.verification import CONFIDENCE_THRESHOLD
```

---

### WR-05: `KeyError` from ADK template engine when `cleaned_transcription` absent from session state

**File:** `src/palimpsest/agents/verification.py:36`, `src/palimpsest/agents/orchestrator.py:151-152`
**Issue:** `VERIFICATION_INSTRUCTION` contains `{cleaned_transcription}` (line
36). ADK's `inject_session_state` (confirmed in
`google/adk/utils/instructions_utils.py:122`) raises `KeyError: 'Context
variable not found: cleaned_transcription'` when the key is absent from session
state. This occurs when the cleaning agent fails and does not write its
`output_key` — a case that is now possible given the status logic gap in CR-02.
The `SequentialAgent` does not short-circuit on individual agent failures, so
the verification agent still executes. The `KeyError` propagates from inside the
ADK runner and surfaces as an unhandled exception from `runner.run_async()` in
`orchestrator.run_pipeline()`, which has no except block around the runner call.

**Fix (two-part):**

1. Fix CR-02 so that cleaning failures set `status="error"` and the orchestrator
   returns before the UI renders anything. This eliminates the primary path.

2. Make `{cleaned_transcription}` optional in the instruction template using ADK's
   optional syntax to avoid a hard crash if the key is missing:
```python
# verification.py line 36 — use {cleaned_transcription?} for optional substitution
INPUT DATA (cleaned transcription JSON from the previous pipeline agent):
{cleaned_transcription?}
```
   With the `?` suffix, ADK substitutes an empty string when the key is absent
   instead of raising `KeyError`.

---

## Info

### IN-01: Model name strings hardcoded in metadata rather than sourced from agent objects

**File:** `src/palimpsest/agents/orchestrator.py:102-106`
**Issue:** The metadata dict uses string literals `"gemini-2.5-pro"`,
`"gemini-2.5-flash"` that are independent copies of the model names defined in
the individual agent modules. If any agent's model is updated, the metadata will
silently diverge, producing misleading audit logs.

**Fix:**
```python
from palimpsest.agents.transcription import transcription_agent
from palimpsest.agents.cleaning import cleaning_agent
from palimpsest.agents.context import context_agent
from palimpsest.agents.verification import verification_agent

# In run_pipeline metadata:
"model": transcription_agent.model,
"cleaning_model": cleaning_agent.model,
"context_model": context_agent.model,
"verification_model": verification_agent.model,
```

---

### IN-02: `asyncio.run()` inside Gradio sync handler — pattern fragility

**File:** `src/palimpsest/app.py:167`
**Issue:** `asyncio.run(run_pipeline(...))` is called inside a synchronous Gradio
click handler. This is safe today because Gradio 6.x runs sync handlers in a
thread pool where no event loop is active. If the handler is ever converted to
`async def` (which Gradio 6.x supports natively), `asyncio.run()` would raise
`RuntimeError: This event loop is already running`. The comment at line 166
acknowledges the assumption but future contributors may not notice it.

**Suggestion:** Document the constraint with a more prominent comment or use
`asyncio.new_event_loop().run_until_complete(...)` for defensive safety — though
the current form is functionally correct in Gradio's thread pool.

---

_Reviewed: 2026-06-27_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

---
phase: 05-ui-wizard-redesign
fixed_at: 2026-06-28T00:00:00Z
review_path: .planning/phases/05-ui-wizard-redesign/05-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 05: Code Review Fix Report

**Fixed at:** 2026-06-28
**Source review:** `.planning/phases/05-ui-wizard-redesign/05-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (3 Critical + 2 Warning)
- Fixed: 5
- Skipped: 0

## Fixed Issues

All five fixes were applied to `src/palimpsest/app.py` and committed together in one atomic commit (single file, all changes consistent).

### CR-01: `float()` crashes on `score: null` from LLM

**Files modified:** `src/palimpsest/app.py`
**Commit:** 566a3ad
**Applied fix:** Replaced `float(entry.get("score", 1.0))` with an explicit `score_raw = entry.get("score")` extraction followed by a `try/except (TypeError, ValueError)` block that treats both `None` and unparseable values as `1.0`. The `get()` default only covers absent keys, not JSON `null`; the new code handles both.

### CR-02: `AttributeError` not caught in `transcribe_manuscript` JSON parsing block

**Files modified:** `src/palimpsest/app.py`
**Commit:** 566a3ad
**Applied fix:** Replaced the one-liner `json.loads(...).get(...)` chains with a two-step pattern: parse into a variable, then validate the result is a `dict` before calling `.get()`. When parsing succeeds but returns a non-dict (e.g. a JSON array), `raw_parsed` raises `gr.Error("Pipeline returned unexpected transcription format.")`. Added `AttributeError` to the except clause. A `except gr.Error: raise` guard ensures the explicit `gr.Error` is re-raised rather than swallowed by the broader except.

### CR-03: No type guard on loop entries in `render_confidence_html` and `render_context_table`

**Files modified:** `src/palimpsest/app.py`
**Commit:** 566a3ad
**Applied fix:** Added `if not isinstance(entry, dict): continue` as the first statement inside both loops. This silently skips `null` elements and any non-dict values from LLM output, preventing `AttributeError` on `.get()` calls. The guard was also merged with the CR-01 fix inside `render_confidence_html` so that `score_raw` extraction only runs on confirmed-dict entries.

### WR-01: Pipe characters in LLM-generated fields corrupt Markdown table structure

**Files modified:** `src/palimpsest/app.py`
**Commit:** 566a3ad
**Applied fix:** Added a private `_md_cell(value: str) -> str` helper that escapes `|` as `\|`, replaces `\n` with a space, and strips `\r`. All five table-cell expressions (`entity`, `entity_type`, `description`, `dates`, `source`) in the `rows.append()` call now pass through `_md_cell()`. The row `f-string` was split across two lines for readability.

### WR-02: `asyncio.run()` inside sync Gradio handler fails in embedded-loop environments

**Files modified:** `src/palimpsest/app.py`
**Commit:** 566a3ad
**Applied fix:** Converted `transcribe_manuscript` from a sync `def` to an `async def`. The `asyncio.run(run_pipeline(...))` call was replaced with `await run_pipeline(...)`. Gradio 4+ accepts coroutine functions as `fn=` arguments directly; no other wiring changes were needed. The module-level `import asyncio` is retained (still used elsewhere) — the D-13 comment was updated to reflect the new approach.

## Skipped Issues

None — all findings were fixed.

---

_Fixed: 2026-06-28_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_

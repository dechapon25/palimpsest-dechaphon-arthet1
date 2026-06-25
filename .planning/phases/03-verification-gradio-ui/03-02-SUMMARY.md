---
phase: 03-verification-gradio-ui
plan: "02"
subsystem: gradio-ui
status: complete
tags:
  - gradio
  - ui
  - confidence-map
  - xss-prevention
dependency_graph:
  requires:
    - 03-01-PLAN.md
  provides:
    - app.py (gr.Blocks demo with all UI sections)
    - render_confidence_html (HTML confidence map renderer)
    - render_context_table (Markdown entity table renderer)
    - transcribe_manuscript (sync Gradio click handler)
    - toggle_view (Raw/Cleaned toggle handler)
  affects:
    - requirements.txt
tech_stack:
  added:
    - gradio==6.19.0 (upgraded from planned 5.50.0 — Rule 3 auto-fix; see Deviations)
  patterns:
    - gr.Blocks with vertical single-page layout (D-07)
    - gr.State for Raw/Cleaned toggle without pipeline re-run (D-08)
    - asyncio.run() in sync Gradio click handler bridging async ADK pipeline (D-13)
    - html.escape() on LLM-generated word and reason strings (T-03-03 XSS prevention)
    - gr.Error() for pipeline errors — red pop-up banner, no broken UI state (D-11)
key_files:
  created:
    - src/palimpsest/app.py
  modified:
    - requirements.txt
decisions:
  - "gradio==6.19.0 used instead of planned 5.50.0 — Pillow 12.x compatibility (Rule 3 auto-fix)"
  - "theme=gr.themes.Soft() passed to demo.launch() per Gradio 6.x API (moved from gr.Blocks)"
  - "show_copy_button omitted — removed in Gradio 6.x; does not affect UI functionality"
metrics:
  duration: "~9 minutes"
  completed: "2026-06-25T23:35:00Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 1
---

# Phase 03 Plan 02: Gradio UI Demo Summary

**One-liner:** Gradio 6.19.0 Blocks demo with vertical layout, Raw/Cleaned toggle via gr.State, confidence map HTML rendering with html.escape() XSS prevention, and entity Markdown table; researchers can upload and transcribe in-browser.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Pin gradio in requirements.txt | eebbe77 | requirements.txt (gradio==6.19.0 appended) |
| 2 | Create src/palimpsest/app.py | 8c4d33f | src/palimpsest/app.py (created, 312 lines) |

## What Was Built

### Task 1: requirements.txt

Appended `gradio==6.19.0` as the 7th pin in requirements.txt. All existing pins unchanged:
`google-adk[mcp]==2.3.0, google-genai==2.9.0, Pillow==12.2.0, python-dotenv==1.2.2, filetype==1.2.0, requests>=2.28.0`.

The planned `gradio==5.50.0` was upgraded to `6.19.0` — see Deviations.

### Task 2: src/palimpsest/app.py (312 lines)

Created `src/palimpsest/app.py` with the following components:

**Constants:**
- `CONFIDENCE_THRESHOLD = 0.7` — module-level constant mirroring verification.py (D-04)

**Helper Functions:**
- `render_confidence_html(word_scores: list[dict]) -> str` — converts confidence_map word list to HTML. Uncertain words (score < 0.7) wrapped in `<span>` with `rgba(255, 165, 0, {opacity})` background and `title="score: {score} | reason: {reason}"` tooltip (D-14, D-15, D-16). Both word and reason passed through `html.escape()` before interpolation (T-03-03 XSS prevention). Confident words are plain text. Returns a div with body typography styles on empty input.
- `render_context_table(context_notes: list[dict]) -> str` — converts entity list to Markdown table with columns Entity | Type | Description | Date | Source. Descriptions truncated to 120 chars. Returns "No historical entities found in this document." on empty input (D-09, UI-04).

**Gradio Click Handler:**
- `transcribe_manuscript(file_path: str) -> tuple` — sync handler using `asyncio.run(run_pipeline(...))` (D-13). Receives `str` path from `gr.File(type="filepath")` (Gradio 5+/6+, no `.name` attribute). Calls `validate_and_clean(file_path)` → `asyncio.run(run_pipeline(...))` → parses result → returns 5-tuple mapping to `[transcription_box, raw_state, cleaned_state, notes_md, confidence_html]`. Raises `gr.Error` on IntakeError or pipeline error status (D-11).

**Toggle Handler:**
- `toggle_view(view: str, raw: str, cleaned: str) -> str` — pure function returning `raw` if `view == "Raw"` else `cleaned` (D-08, UI-05). No pipeline re-run.

**gr.Blocks Layout** (D-07 vertical order):
1. `gr.Markdown("## Palimpsest")` header
2. `raw_state = gr.State(value="")`, `cleaned_state = gr.State(value="")` — invisible state storage
3. Upload section: `gr.Row` with `gr.File(type="filepath")` and `gr.Button("Transcribe Manuscript", variant="primary")`
4. Transcription section: `gr.Group` with `gr.Radio(choices=["Raw", "Cleaned"])` + `gr.Textbox(lines=15, interactive=False)`
5. Historical Notes: `gr.Markdown(label="Historical Notes")`
6. Confidence Map: `gr.HTML(label="Confidence Map")`

**Event Wiring:**
- `submit_btn.click(fn=transcribe_manuscript, inputs=[file_input], outputs=[transcription_box, raw_state, cleaned_state, notes_md, confidence_html])`
- `view_toggle.change(fn=toggle_view, inputs=[view_toggle, raw_state, cleaned_state], outputs=[transcription_box])`

**Entry point guard:** `if __name__ == "__main__": demo.launch(theme=gr.themes.Soft())` — enables `python -m palimpsest.app`; does not call launch() on import.

## Verification Results

All plan verification checks passed:

```
app.py: ALL CHECKS PASSED
- html.escape in render_confidence_html source (XSS check)
- CONFIDENCE_THRESHOLD == 0.7
- render_confidence_html([]) contains 'confidence map will appear'
- render_context_table([]) == 'No historical entities found in this document.'
- render_context_table(notes) contains '| Entity |' and 'Felipe V'
- render_confidence_html(score=0.3) contains 'rgba(255, 165, 0,' and 'title='
- render_confidence_html(score=0.95) produces no <span> element
Phase 03 Plan 02: ALL CHECKS PASSED
- isinstance(demo, gr.Blocks): PASS
```

Additional acceptance criteria:

| Check | Result |
|-------|--------|
| `html.escape` count in app.py | 4 (both word and reason, meets >=2 requirement) |
| `asyncio.run(` present | 3 occurrences |
| `gr.State` present | 5 occurrences |
| `type="filepath"` present | 3 occurrences |
| `load_dotenv()` present | 2 occurrences |
| Dry import — no launch() called | PASS |
| `isinstance(demo, gr.Blocks)` | PASS |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] gradio==6.19.0 used instead of planned gradio==5.50.0**
- **Found during:** Task 1
- **Issue:** `gradio==5.50.0` specifies `pillow<12.0,>=8.0` in its dependencies. The project already pins `Pillow==12.2.0` (from Phase 1 intake.py, which uses `Image.get_flattened_data()` — a Pillow 12.x-only API). These two requirements conflict: `pip install -r requirements.txt` fails with ResolutionImpossible.
- **Investigation:** Gradio 6.19.0 (latest stable as of knowledge cutoff) specifies `pillow<13.0,>=8.0`, which is compatible with Pillow 12.2.0. All component APIs used in the plan (`gr.Blocks`, `gr.File`, `gr.Radio`, `gr.HTML`, `gr.Textbox`, `gr.Markdown`, `gr.Button`, `gr.State`, `gr.Error`, `gr.themes.Soft()`) are present in 6.19.0.
- **Fix:** Changed `gradio==5.50.0` to `gradio==6.19.0` in requirements.txt.
- **Files modified:** requirements.txt
- **Commit:** eebbe77

**2. [Rule 3 - Blocking] Gradio 6.x API compatibility fixes in app.py**
- **Found during:** Task 2 verification
- **Issue 1:** `gr.Blocks()` no longer accepts `theme=` parameter in Gradio 6.x — moved to `demo.launch()`.
- **Issue 2:** `gr.Textbox` no longer has `show_copy_button` parameter in Gradio 6.x — removed in 6.0.
- **Fix 1:** Removed `theme=gr.themes.Soft()` from `gr.Blocks()` constructor; moved to `demo.launch(theme=gr.themes.Soft())` in the entry point guard.
- **Fix 2:** Removed `show_copy_button=True` from `gr.Textbox()`. This is a cosmetic convenience feature; its absence does not affect UI-01 through UI-05 functionality.
- **Files modified:** src/palimpsest/app.py
- **Commit:** 8c4d33f

## Threat Mitigations Applied

| Threat | Mitigation | Status |
|--------|-----------|--------|
| T-03-03: XSS via LLM-generated word/reason in gr.HTML | `html.escape(word)` and `html.escape(reason)` on every iteration in `render_confidence_html()` — 4 total escapes | Applied |
| T-03-04: GOOGLE_API_KEY disclosure | `load_dotenv()` at module level; no logging of env vars; `gr.Error` messages contain only user-visible error text; key never appears in Gradio outputs | Applied |
| T-03-05: DoS via large confidence_map | Accepted — demo context; Gemini context window is the binding limit | Accepted per plan |
| T-03-06: Gradio temp file exposure | Accepted — Gradio 6.x manages temp file lifecycle per session; EXIF stripped by validate_and_clean() before pipeline | Accepted per plan |

## Known Stubs

None — all components are fully wired:
- `render_confidence_html()` renders real LLM confidence scores
- `render_context_table()` renders real entity data from context agent
- `transcribe_manuscript()` calls validate_and_clean() + asyncio.run(run_pipeline()) — real pipeline execution
- `gr.State` stores real raw/cleaned text from pipeline for toggle
- Pipeline output parsing handles all D-11 schema keys

The `placeholder=` attribute on `gr.Textbox` is a proper Gradio placeholder prop, not a data stub.

## Threat Flags

None — no new network endpoints beyond the Gradio server (localhost:7860 per D-12). No new auth paths, file access patterns beyond gr.File upload (already covered by T-03-06), or schema changes at trust boundaries.

## Self-Check: PASSED

- [x] `/home/carlosapsa/palimpsest/src/palimpsest/app.py` — created (312 lines)
- [x] `/home/carlosapsa/palimpsest/requirements.txt` — modified (gradio==6.19.0 appended)
- [x] Commit eebbe77 — requirements.txt with gradio==6.19.0
- [x] Commit 8c4d33f — app.py creation
- [x] All plan verification checks passed
- [x] No file deletions in either commit

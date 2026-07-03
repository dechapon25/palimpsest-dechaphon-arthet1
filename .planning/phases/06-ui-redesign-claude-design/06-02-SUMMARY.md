---
phase: "06"
plan: "06-02"
subsystem: ui
tags: [gradio, html, processing-state, metadata-bar, context-cards, confidence-highlight]
title: "Processing State, Context Cards, Confidence Highlight & Metadata Bar"
status: complete

requires:
  - phase: "06-01"
    provides: "CUSTOM_CSS with all pal-* classes, parchment theme tokens, layout elem_classes"

provides:
  - "Animated processing card (pal-processing-card) shown during pipeline run"
  - "render_context_cards() replacing render_context_table() — HTML card grid with type-colored pills"
  - "render_metadata_bar() — 5-pill bar: Tiempo/Modelo/Palabras/Inciertas/Confianza"
  - "outputs_full expanded to 11 elements (processing_section at index 10)"
  - "copy_btn with JS clipboard wiring (no server round-trip)"
  - "notes_md changed from gr.Markdown to gr.HTML"

affects: [submission, video-demo]

tech-stack:
  added: []
  patterns:
    - "submit_btn.click().then() chain: show_processing() fires before transcribe_manuscript()"
    - "gr.HTML for all dynamic rendered content (notes, status, processing) — no gr.Markdown for LLM output"
    - "fn=None + js= for pure client-side clipboard wiring in Gradio"
    - "html.escape() on all LLM strings before HTML injection (SEC-04 pattern)"

key-files:
  modified:
    - src/palimpsest/app.py

key-decisions:
  - "Deferred transcribe_manuscript() return-tuple refactor to Task 2 to keep Task 1 minimal and verifiable"
  - "notes_md changed to gr.HTML to accept HTML card grid output from render_context_cards()"
  - "_md_cell() and render_context_table() fully removed — render_context_cards() is the sole replacement"
  - "copy_btn uses fn=None + js= pattern (no outputs_full extension needed)"
  - "render_metadata_bar() uses CONFIDENCE_THRESHOLD=0.7 for Inciertas count, GEMINI_MODEL env var for Modelo pill"

requirements-completed: []

coverage:
  - id: D1
    description: "processing_section gr.HTML shown immediately on submit, hidden on pipeline completion"
    verification:
      - kind: manual_procedural
        ref: "Launch app, click Transcribir — processing card appears with spinner and progress bar"
        status: unknown
    human_judgment: true
    rationale: "Visual animation requires browser to verify; no automated test covers Gradio JS event chain"
  - id: D2
    description: "outputs_full has 11 elements; reset_manuscript() and transcribe_manuscript() both return 11-element tuples"
    verification:
      - kind: unit
        ref: "python -c \"from palimpsest.app import reset_manuscript; r=reset_manuscript(); assert len(r)==11\""
        status: pass
    human_judgment: false
  - id: D3
    description: "render_context_cards() returns pal-notes-grid HTML with type-colored pills; render_context_table() removed"
    verification:
      - kind: unit
        ref: "python -c \"from palimpsest.app import render_context_cards; h=render_context_cards([{'entity':'X','type':'Persona','description':'Y'}]); assert 'pal-notes-grid' in h; assert '#AE3B2C' in h\""
        status: pass
    human_judgment: false
  - id: D4
    description: "render_confidence_html() uses amber rgba(217,149,46) + inset 0 -2px box-shadow with HIGHLIGHT_THRESHOLD=0.95"
    verification:
      - kind: unit
        ref: "python -c \"from palimpsest.app import render_confidence_html; h=render_confidence_html([{'word':'test','score':0.5,'reason':'r'}]); assert 'rgba(217,149,46' in h; assert 'inset 0 -2px' in h\""
        status: pass
    human_judgment: false
  - id: D5
    description: "render_metadata_bar() returns 5-pill div.pal-meta-bar with Tiempo/Modelo/Palabras/Inciertas/Confianza"
    verification:
      - kind: unit
        ref: "python -c \"from palimpsest.app import render_metadata_bar; h=render_metadata_bar([{'word':'x','score':0.5,'reason':'r'}],'hola mundo',12.3); assert 'pal-meta-bar' in h; assert 'Tiempo' in h\""
        status: pass
    human_judgment: false
  - id: D6
    description: "copy_btn present in transcription_section with JS clipboard wiring; no extra outputs_full element"
    verification: []
    human_judgment: true
    rationale: "JS clipboard only testable in browser; no server callback to unit-test"

duration: 10min
completed: "2026-07-03"
---

# Phase 06 Plan 02: Processing State, Context Cards, Confidence Highlight & Metadata Bar Summary

**Animated processing card, HTML entity cards with type-colored pills, 5-pill metadata bar, and clipboard copy button — all wired into an 11-element outputs_full via submit_btn.click().then() chain**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-07-03T00:05:57Z
- **Completed:** 2026-07-03T00:10:20Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Added `show_processing()` + `processing_section` gr.HTML: processing card appears immediately on submit, disappears when pipeline completes
- Replaced `render_context_table()` (Markdown) with `render_context_cards()` (HTML grid) — entity type pills colored per _TYPE_COLORS map (Persona=terracotta, Lugar=green, Fecha=amber, Documento/Institución=blue)
- Added `render_metadata_bar()` computing elapsed time, model name, word count, uncertain count, and average confidence as 5 IBM Plex Mono pills
- Expanded outputs_full from 10 to 11 elements; both `reset_manuscript()` and `transcribe_manuscript()` return the matching 11-tuple
- Added `copy_btn` (btn-ghost, sm) with `fn=None + js=` clipboard wiring — no server round-trip, no tuple extension required
- Changed `notes_md` from `gr.Markdown` to `gr.HTML` to accept card grid HTML output

## Task Commits

1. **Task 1: processing_section + outputs_full expansion** - `0e9017e` (feat)
2. **Task 2: context cards + metadata bar + copy button** - `339f76b` (feat)

## Files Created/Modified

- `/home/carlosapsa/palimpsest/src/palimpsest/app.py` — All changes: show_processing(), processing_section, render_context_cards(), render_metadata_bar(), copy_btn, notes_md type change, 11-element tuples

## Decisions Made

- Changed `notes_md` from `gr.Markdown` to `gr.HTML` (required to render HTML card grid output — gr.Markdown strips raw HTML)
- Used `fn=None + js=` for clipboard wiring (Gradio supports this pattern; no server round-trip, no outputs_full extension)
- Removed `_md_cell()` helper entirely (no longer needed after render_context_table removal)
- Kept `render_metadata_bar()` using `CONFIDENCE_THRESHOLD=0.7` for Inciertas count (matches verification.py threshold), not HIGHLIGHT_THRESHOLD

## Deviations from Plan

### Pre-applied changes (not deviations, just noting state)

The following Wave 2 constants were already in app.py before this plan ran (applied during a prior session):
- `import time` (line 35)
- `HIGHLIGHT_THRESHOLD = 0.95`
- `PROCESSING_HTML` constant
- Processing card CSS block in CUSTOM_CSS
- Updated `render_confidence_html()` with new alpha formula and Spectral font wrapper

These were all correct and matching the plan spec — no changes needed. Implementation proceeded directly to the remaining items.

None of the above constituted a deviation; the plan was executed exactly as specified for both tasks.

## Issues Encountered

None. Pre-compiled checks passed cleanly on first attempt for both tasks.

## Known Stubs

None. All UI elements are wired to real pipeline output or computed from it.

## Threat Flags

None — no new network endpoints, auth paths, or file access patterns. `render_context_cards()` applies `html.escape()` to all LLM-generated strings (SEC-04 continuity). `render_metadata_bar()` reads only `os.environ.get("GEMINI_MODEL")` — no injection risk.

## Next Phase Readiness

Phase 06 is now complete. The Gradio UI has the full Claude Design parchment theme with all three states (upload, processing, results). App is ready for:
- End-to-end demo recording (video script already written)
- Kaggle writeup finalization

## Self-Check: PASSED

- `src/palimpsest/app.py` exists and compiles (py_compile exit 0)
- Commit `0e9017e` exists: feat(ui/06-02): add processing_section, expand outputs_full to 11 elements
- Commit `339f76b` exists: feat(ui/06-02): context cards, metadata bar, copy button, notes gr.HTML
- `reset_manuscript()` returns 11-element tuple (verified)
- `render_context_cards()` exists, returns pal-notes-grid with #AE3B2C (verified)
- `render_context_table` raises ImportError (verified)
- `render_metadata_bar()` returns pal-meta-bar with Tiempo/Palabras (verified)
- `render_confidence_html()` uses rgba(217,149,46) + inset 0 -2px (verified)
- `processing_section` gr.HTML added to layout (in app.py lines ~741)
- `outputs_full` has 11 elements (outputs_full list confirmed)

---
*Phase: 06-ui-redesign-claude-design*
*Completed: 2026-07-03*

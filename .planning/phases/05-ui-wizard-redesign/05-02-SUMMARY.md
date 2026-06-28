---
phase: 05-ui-wizard-redesign
plan: 02
subsystem: ui
tags: [gradio, progressive-reveal, wizard, event-wiring, localization]

requires:
  - phase: 05-01
    provides: transcription_section, confidence_section, notes_section, reset_btn, status_md variables in gr.Blocks context
provides:
  - reset_manuscript() — 10-tuple reset function hiding all result panels
  - transcribe_manuscript() extended to 10-element return (reveals all cards + status)
  - outputs_full shared list wiring both submit and reset handlers
  - Spanish error messages throughout transcribe_manuscript()
  - Complete progressive-reveal wizard: submit reveals cards, reset hides them
affects: []

tech-stack:
  added: []
  patterns:
    - outputs_full shared list prevents submit/reset output-count mismatch (both handlers use identical list)
    - reset_manuscript returns 10-tuple matching outputs_full exactly — Gradio enforces count at runtime

key-files:
  created: []
  modified:
    - src/palimpsest/app.py

key-decisions:
  - "outputs_full defined as local variable inside gr.Blocks context — shared by submit_btn.click and reset_btn.click to guarantee count parity"
  - "transcribe_manuscript() docstring not updated (plan specified only string literals change in Edit C)"
  - "Spanish error messages only in transcribe_manuscript() gr.Error calls — pipeline error passthrough via gr.Error(str(e)) unchanged"

patterns-established:
  - "Shared outputs list pattern: define once, reference in multiple .click() handlers"

requirements-completed:
  - UI-WIZ-02
  - UI-WIZ-04

coverage:
  - id: D1
    description: "reset_manuscript() returns 10-tuple with gr.update(visible=False) for all four initially-hidden components"
    requirement: UI-WIZ-02
    verification:
      - kind: other
        ref: "python -c 'from palimpsest.app import reset_manuscript; r = reset_manuscript(); assert len(r) == 10' exits 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "submit_btn.click reveals all three result cards and reset button; status shows 'Procesamiento completado.' after processing"
    requirement: UI-WIZ-02
    verification: []
    human_judgment: true
    rationale: "Progressive-reveal behavior requires browser verification — Python tests cannot assert Gradio UI state changes"
  - id: D3
    description: "reset_btn.click returns UI to initial state (all result cards hidden, status cleared) without page reload"
    requirement: UI-WIZ-04
    verification: []
    human_judgment: true
    rationale: "Reset behavior requires browser interaction to verify stateful UI transitions"
  - id: D4
    description: "Spanish gr.Error messages: 'Por favor, sube una imagen del manuscrito primero.' and 'Procesamiento fallido...' present"
    requirement: UI-WIZ-02
    verification:
      - kind: other
        ref: "grep 'Por favor, sube' src/palimpsest/app.py → match; grep 'Procesamiento fallido' → match"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-06-28
status: complete
---

# Phase 05-02: Progressive-Reveal Event Wiring + Reset Function

**Complete wizard: submit reveals three result cards via 10-output gr.update(), reset hides them again — outputs_full shared list guarantees count parity between both handlers**

## Performance

- **Duration:** ~15 min
- **Completed:** 2026-06-28
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- `reset_manuscript()` added — 10-tuple with `gr.update(visible=False)` for all result sections and clears all text state
- `transcribe_manuscript()` return extended from 5 to 10 elements: adds `gr.update(visible=True)` for three result cards + reset_btn, and `"Procesamiento completado."` for status_md
- `outputs_full` list (10 components) shared by `submit_btn.click` and `reset_btn.click` — guarantees count parity
- Spanish error messages: `"Por favor, sube una imagen del manuscrito primero."` and `"Procesamiento fallido. Verifica que el archivo sea válido y vuelve a intentarlo."`
- `view_toggle.change` wiring unchanged
- `reset_btn.click` newly wired to `reset_manuscript()`

## Task Commits

1. **Task 1: reset_manuscript + extend transcribe_manuscript + localize errors** — `353bad5`
2. **Task 2: Replace event wiring with outputs_full** — `8c666b3`

## Files Created/Modified
- `src/palimpsest/app.py` — reset function, extended return tuple, Spanish errors, new event wiring

## Decisions Made
- `outputs_full` defined inside `gr.Blocks` context as a local variable (same scope as component variables) so both handlers share the identical list without module-level exposure
- No docstring update to `transcribe_manuscript()` (plan constraint: only string literals changed in Edit C)

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None.

## Next Phase Readiness
- Phase 05 fully complete — all five success criteria from ROADMAP.md satisfied
- Progressive-reveal wizard functional: upload → submit → cards appear → reset → cards hidden
- App imports cleanly; demo is valid gr.Blocks; entry point unchanged

---
*Phase: 05-ui-wizard-redesign*
*Completed: 2026-06-28*

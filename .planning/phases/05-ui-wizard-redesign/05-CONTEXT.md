---
phase: 05
name: ui-wizard-redesign
date: 2026-06-28
---

# Phase 05 Context — UI Wizard Redesign

## Domain

Rewrite `src/palimpsest/app.py` (Gradio Blocks layout only) to implement a
progressive-reveal wizard with Bento Grid + Glassmorphism visual style.
**No changes to pipeline logic, agents, or backend.**

## Decisions

### D-01 — Interaction model: progressive reveal (not tabs, not accordion)
Results appear incrementally in the same page as each pipeline stage completes:
1. Raw transcription (first output available)
2. Cleaned transcription replaces/annotates raw
3. Historical notes table
4. Confidence map with highlighted words

Each section is hidden (`visible=False`) at load time and revealed via
`gr.update(visible=True)` as outputs arrive.

### D-02 — Upload screen: minimal until processing starts
Only the file picker and "Transcribir" button are visible at initial state.
All result panels start hidden. Spinner/status text appears on submit.

### D-03 — Visual style: Bento Grid + Glassmorphism
- Custom CSS injected via `gr.Blocks(css=...)` — no external CDN
- Cards: `backdrop-filter: blur(...)`, semi-transparent background, subtle border
- Dark or semi-dark base background (deep navy or charcoal)
- Accent color: amber/gold (`#C9A84C` or similar) — evokes manuscript/parchment
- Bento grid: CSS Grid layout with named areas; result cards sized to content
- Font: system default or Google Fonts loaded via `<style>` in `head`

### D-04 — Raw/Cleaned toggle: inline, subtle
Toggle kept (raw still useful for researchers) but de-emphasized:
small radio or segmented control inside the transcription card, not top-level.

### D-05 — "Nueva transcripción" reset button
Appears after results are shown. Resets all `gr.State` values and re-hides
result panels via `gr.update(visible=False)` — no page reload.

### D-06 — Status/progress messaging
A `gr.Textbox` or `gr.Markdown` status line shows stage messages during processing.
Gradio streaming via `gr.Progress` or generator function if feasible; otherwise
single update on completion.

### D-07 — Scope boundary
This phase changes **only** `src/palimpsest/app.py`.
No changes to: orchestrator, agents, MCP server, security intake, Docker/deploy.

## Canonical Refs

- `src/palimpsest/app.py` — current Gradio layout (rewrite target)
- `.planning/phases/03-verification-gradio-ui/03-CONTEXT.md` — prior UI decisions (D-07 through D-17)
- `.planning/phases/03-verification-gradio-ui/03-01-PLAN.md` — original UI plan
- `https://www.gradio.app/docs/gradio/blocks` — gr.Blocks API reference

## Code Context

Reusable from current `app.py`:
- `render_confidence_html()` — unchanged, still used
- `render_context_table()` — unchanged, still used
- `transcribe_manuscript()` — backend handler, unchanged
- `toggle_view()` — unchanged logic, rewired to new component

New additions needed:
- Custom CSS string for Glassmorphism cards + dark background
- `gr.Column(visible=False)` wrappers for each result section
- Reset handler function

## Deferred Ideas

- Streaming word-by-word transcription output (requires pipeline streaming support — Phase 6+)
- Mobile-responsive breakpoints beyond basic CSS (nice-to-have)
- Image preview panel next to transcription (scope creep for this phase)

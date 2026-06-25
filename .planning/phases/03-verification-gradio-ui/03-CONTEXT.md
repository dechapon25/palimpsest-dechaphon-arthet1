# Phase 3: Verification + Gradio UI - Context

**Gathered:** 2026-06-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Verification agent (confidence scoring per word/span) + Gradio demo interface with full result display (clean transcription, historical notes, raw/clean toggle, color-coded uncertainty highlights).

Delivers: A researcher can upload a manuscript image in the Gradio UI and receive the clean transcription, historical notes panel, and confidence map with highlighted uncertain words — all without running code directly.

Requirements in scope: VER-01, VER-02, VER-03, UI-01, UI-02, UI-03, UI-04, UI-05

</domain>

<decisions>
## Implementation Decisions

### Verification Agent (Confidence Scoring)
- **D-01:** LLM self-assessment via Gemini Flash — send cleaned_transcription text to Gemini Flash and ask it to score each word/span (0.0–1.0) based on: `[?]` markers from cleaning agent, uncertain proper nouns, contextual legibility signals. No external API needed.
- **D-02:** Granularity: per word/span. Output is a JSON array of scored tokens — enables precise word-level highlight rendering in the UI.
- **D-03:** Output schema (VER-03): `[{"word": "Alcántara", "score": 0.45, "reason": "proper noun, unclear origin"}, ...]` — word-level array. Structured JSON so the UI renders highlights programmatically (not prose).
- **D-04:** Threshold: score < 0.7 marks a word as uncertain. Constant defined in the verification agent; plannable as a configurable value.
- **D-05:** Pipeline position: Verification runs last in the SequentialAgent — Transcription → Cleaning → Context → Verification. Reads `cleaned_transcription` from session state. Matches D-09 ordering pattern from Phase 2.
- **D-06:** Output key in session state: `confidence_map` (additive to D-11 schema per A3). Pipeline returns `confidence_map` as a new key in the output dict alongside `raw_transcription`, `cleaned_transcription`, `context_notes`.

### Gradio UI Layout
- **D-07:** Single page, vertical sections — no tabs. Layout top to bottom: Upload → Submit button → Transcription section → Historical Notes section → Confidence Map section.
- **D-08:** Raw/clean toggle: `gr.Radio(choices=["Raw", "Cleaned"])` above a single `gr.Textbox`. Selecting a radio button switches the text box content between `raw_transcription` and `cleaned_transcription`. Separate from the Confidence Map section.
- **D-09:** Historical notes panel: `gr.Markdown` component rendering a formatted table — `Entity | Type | Description | Date | Source`. Context notes JSON array converted to Markdown table before display.
- **D-10:** Processing state: default Gradio spinner (`interactive=False` on button while processing / `loading=True`). No pipeline changes required for progress reporting.
- **D-11 (UI errors):** Pipeline errors surface via `gr.Error(message)` pop-up. If `run_pipeline()` returns `status="error"`, raise `gr.Error` with the error text from the `errors` list. Red Gradio error banner, no extra UI elements.
- **D-12:** Gradio app location: `src/palimpsest/app.py`. Follows existing package structure. Launched via `python -m palimpsest.app` or a CLI entry point in `pyproject.toml`. Consistent with `run.py` pattern.
- **D-13:** Gradio calls `run_pipeline()` via `asyncio.run()` inside the sync click handler. No async Gradio handler needed; standard pattern for Gradio + async backend.

### Uncertainty Highlight Display
- **D-14:** Render via `gr.HTML` in the Confidence Map section. Uncertain words (score < 0.7) rendered as `<span style="background-color: rgba(255, 165, 0, {opacity})" title="score: {score} | reason: {reason}">{word}</span>`, where `opacity = 1 - score`. Confident words rendered as plain text.
- **D-15:** Color: yellow/orange gradient. score 0.0 → opaque orange; score 0.69 → pale yellow. Intuitive: brighter = more uncertain.
- **D-16:** Tooltip: `title=` attribute on each uncertain `<span>`. Shows score and reason on hover. Native browser tooltip, zero JS.
- **D-17:** Confidence Map is a separate section below the Transcription section. The raw/clean toggle shows plain text; the Confidence Map below always shows the highlighted view of the cleaned transcription.

### Claude's Discretion
- Verification agent model param tuning (temperature, thinkingBudget for scoring task) — planner decides based on Phase 2 Flash settings
- Session state key name for confidence_map (`confidence_map` suggested) — planner confirms no conflicts
- `gr.Blocks` vs `gr.Interface` for layout — planner picks (gr.Blocks recommended for vertical sections)
- Exact pyproject.toml entry point name for the Gradio app launcher

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements
- `.planning/PROJECT.md` — Core constraints, model config rationale (maxOutputTokens=65536, temperature=0.1), known Gemini failure modes, D-11 output schema note (A3 additive extension)
- `.planning/REQUIREMENTS.md` — Full requirement list with VER/UI requirement IDs and acceptance criteria
- `.planning/ROADMAP.md` — Phase 3 success criteria, dependency on Phase 2, requirements mapping (VER-01, VER-02, VER-03, UI-01–UI-05)

### Phase 2 Prior Decisions (carry forward)
- `.planning/phases/02-full-multi-agent-system/02-CONTEXT.md` — D-04 (cleaning output JSON schema with `cleaned_text` + `changes` array), D-06 (`[?]` markers for uncertain expansions), D-08 (context_notes entity schema), D-09 (agent ordering), D-11 (output dict schema + A3 additive extension rule)

### Existing Code
- `src/palimpsest/agents/orchestrator.py` — SequentialAgent definition, `run_pipeline()` async function, D-11 output dict structure, session state key names
- `src/palimpsest/agents/cleaning.py` — Cleaning agent that produces `[?]` markers (input signal for verification agent)
- `src/palimpsest/agents/context.py` — Context agent (runs before verification; its output is available in session state)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `run_pipeline()` in `orchestrator.py` — async function returning D-11 dict; Gradio calls via `asyncio.run()`
- `SequentialAgent` in `orchestrator.py` — extend by appending verification agent to the `sub_agents` list
- `[?]` markers in cleaning output (`cleaned_transcription` field) — direct input signal for the verification LLM prompt
- Context notes JSON array from `context_notes` field — convert to Markdown table for `gr.Markdown` display

### Established Patterns
- **Agent pattern**: LlmAgent with `output_key` to write to session state (matching transcription, cleaning, context agents)
- **Model selection**: Gemini Flash for text-to-text tasks (D-02, matches cleaning and context agents)
- **JSON output**: agents emit structured JSON strings stored in session state; orchestrator parses at the end
- **Security barrier**: system prompt labels input as DATA not instructions (SEC-04 pattern — apply to verification prompt)
- **Additive output dict**: new keys added at the end of `run_pipeline()` return dict without changing existing keys (A3)

### Integration Points
- `pipeline` (SequentialAgent) in `orchestrator.py:30` — add verification agent as 4th entry in `sub_agents`
- `run_pipeline()` return dict — add `confidence_map` key after parsing verification agent session state
- `src/palimpsest/app.py` (new file) — imports `run_pipeline` from `orchestrator`, calls via `asyncio.run()`

</code_context>

<specifics>
## Specific Ideas

- Confidence map HTML generation: build a helper function `render_confidence_html(word_scores: list[dict]) -> str` that takes the verification agent output and returns the full HTML string for `gr.HTML`.
- Markdown table builder: helper `render_context_table(context_notes: list[dict]) -> str` that converts entity JSON to Markdown table rows.
- The `[?]` markers from the cleaning agent should be explicitly mentioned in the verification agent's system prompt as a hint ("words ending in [?] were flagged as uncertain by the cleaning agent — weight these toward lower confidence scores").

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 3-verification-gradio-ui*
*Context gathered: 2026-06-26*

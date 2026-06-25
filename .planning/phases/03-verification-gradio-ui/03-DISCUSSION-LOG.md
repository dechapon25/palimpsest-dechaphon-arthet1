# Phase 3: Verification + Gradio UI - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-26
**Phase:** 03-verification-gradio-ui
**Areas discussed:** Confidence scoring, Gradio layout, Uncertainty highlight display, Pipeline wiring

---

## Confidence Scoring

| Option | Description | Selected |
|--------|-------------|----------|
| LLM self-assessment | Gemini Flash scores each word/span (0.0–1.0) based on [?] markers, uncertain proper nouns, context | ✓ |
| [?] markers only | Count [?] markers from cleaning agent. Deterministic but only catches what cleaning flagged | |
| Hybrid: markers + LLM re-check | Two-pass approach. More accurate but adds latency | |

**Granularity question:**

| Option | Description | Selected |
|--------|-------------|----------|
| Per word/span | Each word gets a score. Enables precise highlight rendering | ✓ |
| Per sentence/passage | One score per sentence. Simpler, less precise | |
| Both passage + word flags | Two arrays in JSON. Richest but most complex | |

**Schema question (VER-03):**

| Option | Description | Selected |
|--------|-------------|----------|
| Word-level array | `[{"word": "...", "score": 0.45, "reason": "..."}]` | ✓ |
| Annotated text with inline markers | String with `[[word\|0.45]]` markers | |
| You decide | Claude picks schema | |

**Threshold question:**

| Option | Description | Selected |
|--------|-------------|----------|
| 0.7 threshold | score < 0.7 = uncertain | ✓ |
| 0.5 threshold | Only highlight most uncertain words | |
| You decide | Planner picks configurable constant | |

**User's choice:** LLM self-assessment, per-word granularity, word-level array schema, 0.7 threshold.

---

## Gradio Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Single page, vertical sections | Upload → Transcription → Historical Notes → Confidence Map. No tabs. | ✓ |
| Tabbed interface | Upload tab, Results tab with sub-tabs | |
| Two-column layout | Left: upload + transcription. Right: notes + confidence | |

**Raw/clean toggle:**

| Option | Description | Selected |
|--------|-------------|----------|
| gr.Radio toggle above a single text box | Radio switches text box content | ✓ |
| Two text boxes always visible | Raw left, Cleaned right | |
| gr.Tabs: Raw and Clean tabs | Tab per view | |

**Processing state:**

| Option | Description | Selected |
|--------|-------------|----------|
| Default Gradio spinner | loading=True on button | ✓ (you decide) |
| Status text area with pipeline stage | Requires streaming from pipeline | |
| Simple elapsed timer | Easy to add | |

**Historical notes format:**

| Option | Description | Selected |
|--------|-------------|----------|
| Formatted Markdown table | Entity \| Type \| Description \| Date \| Source via gr.Markdown | ✓ |
| Pretty-printed JSON | gr.JSON or gr.Code component | |
| Plain text list | Bullet list, simplest | |

**User's choice:** Single page vertical, gr.Radio toggle, default spinner, Markdown table.

---

## Uncertainty Highlight Display

**Highlight rendering:**

| Option | Description | Selected |
|--------|-------------|----------|
| Color-coded HTML spans via gr.HTML | `<span style="background-color: rgba(255,165,0,opacity)">` | ✓ |
| gr.HighlightedText component | Built-in Gradio, categorical labels only | |
| Bold/asterisk markers | `**word**` — no intensity gradient | |

**Tooltip on hover:**

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — title tooltip | `title="score: 0.45 \| reason: ..."` on each span | ✓ |
| No — color only | Simpler, reason stays in JSON | |
| Separate legend/key panel | gr.Markdown legend below highlights | |

**Note:** User initially selected "No — color only" then corrected to "Yes — title tooltip".

**Color:**

| Option | Description | Selected |
|--------|-------------|----------|
| Yellow/orange gradient | rgba(255,165,0,opacity), opacity = 1 - score | ✓ |
| Red gradient | rgba(255,0,0,opacity) | |
| You decide | Planner picks palette | |

**Confidence Map placement:**

| Option | Description | Selected |
|--------|-------------|----------|
| Separate section below transcription | Toggle shows plain text; Confidence Map below shows highlighted HTML | ✓ |
| Integrated into Cleaned view | Toggle replaces textbox with HTML | |
| Sub-tabs: [Raw] [Cleaned] [Highlighted] | Three states | |

**User's choice:** gr.HTML spans, title= tooltip, yellow/orange gradient, separate section.

---

## Pipeline Wiring

**Agent order:**

| Option | Description | Selected |
|--------|-------------|----------|
| After context: T → C → Ctx → V | Verification last. Matches D-09 ordering | ✓ |
| Parallel to context after cleaning | ParallelAgent — higher implementation risk | |
| Before context: T → C → V → Ctx | Functional but no advantage | |

**Gradio ↔ pipeline interaction:**

| Option | Description | Selected |
|--------|-------------|----------|
| asyncio.run() in sync handler | Standard pattern, no Gradio changes | ✓ |
| Sync wrapper in orchestrator.py | Adds run_pipeline_sync() wrapper | |
| gr.Interface with async function | Requires Gradio 4.x async support | |

**App file location:**

| Option | Description | Selected |
|--------|-------------|----------|
| src/palimpsest/app.py | Follows existing package structure | ✓ |
| app.py at project root | Common Gradio convention but breaks package structure | |
| src/palimpsest/ui/app.py | Cleanest separation, overkill for one file | |

**Error handling in UI:**

| Option | Description | Selected |
|--------|-------------|----------|
| gr.Error() pop-up | Red error banner, no extra UI | ✓ |
| Error text box always visible | Dedicated gr.Textbox for errors | |
| Inline error in transcription box | Mixes output and error | |

**User's choice:** Verification last, asyncio.run(), src/palimpsest/app.py, gr.Error().

---

## Claude's Discretion

- Verification agent model param tuning (temperature, thinkingBudget)
- Session state key name for confidence_map
- gr.Blocks vs gr.Interface for layout (gr.Blocks recommended)
- pyproject.toml entry point name for Gradio app launcher
- Gradio spinner implementation details (loading=True vs interactive=False)

## Deferred Ideas

None — discussion stayed within phase scope.

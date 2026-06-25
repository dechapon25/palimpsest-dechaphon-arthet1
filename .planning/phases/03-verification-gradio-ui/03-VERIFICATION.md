---
phase: 03-verification-gradio-ui
verified: 2026-06-26T00:00:00Z
status: gaps_found
score: 9/12 must-haves verified
behavior_unverified: 2
overrides_applied: 0
re_verification: false
gaps:
  - truth: "Pipeline errors surface as a gr.Error pop-up banner — no broken UI state"
    status: failed
    reason: "CR-02: the four json.loads() calls in transcribe_manuscript (app.py:185-199) have no try/except. The orchestrator sets status=error only for raw_transcription parse failures; cleaning, context, and confidence parse failures set status=ok while appending to errors[]. When those json.loads() calls hit malformed JSON, an unhandled JSONDecodeError propagates as a Python exception that Gradio surfaces as a generic 500 error rather than a gr.Error banner."
    artifacts:
      - path: "src/palimpsest/app.py"
        issue: "Lines 185-199: four json.loads() calls lack try/except (json.JSONDecodeError, TypeError) wrapping"
    missing:
      - "Wrap the four json.loads() calls in app.py:185-199 in a single try/except (json.JSONDecodeError, TypeError) block that raises gr.Error on failure — mirrors the IntakeError handler pattern already in the same function"
  - truth: "Every passage/word carries a confidence score; low-confidence items explicitly flagged (SC-1, VER-01, VER-02)"
    status: partial
    reason: "CR-03: verification.py GenerateContentConfig is missing max_output_tokens=65536. CLAUDE.md explicitly states 'Set maxOutputTokens=65536 explicitly or transcription silently truncates.' For a long manuscript the word-score JSON array can exceed the model default output token limit; silent mid-array truncation produces malformed JSON that fails to parse and leaves the confidence map blank with no user-visible diagnostic. This is a configuration omission against a documented project constraint."
    artifacts:
      - path: "src/palimpsest/agents/verification.py"
        issue: "Line 75-78: GenerateContentConfig has temperature=0.1 and response_mime_type but no max_output_tokens=65536 — violates CLAUDE.md constraint"
    missing:
      - "Add max_output_tokens=65536 to GenerateContentConfig in verification.py to match transcription.py:60 and prevent silent array truncation on long manuscripts"
behavior_unverified_items:
  - truth: "Every passage/word in the transcription output carries a confidence score between 0.0 and 1.0 in the output array (SC-1, VER-01)"
    test: "Upload a real manuscript image via run_pipeline(); inspect the returned confidence_map JSON array for completeness — one entry per space-separated token in cleaned_text, all scores in [0.0, 1.0]"
    expected: "confidence_map is a JSON array with one object per word; all scores are floats in [0.0, 1.0]; no words omitted"
    why_human: "Completeness and range of LLM-generated scores cannot be verified by grep or import tests. Only an actual Gemini Flash call against a real manuscript reveals whether the instruction produces the expected coverage."
  - truth: "A researcher can upload an image in the Gradio interface and see all pipeline results without running code (SC-2, UI-01, UI-02)"
    test: "Launch `python -m palimpsest.app`, open http://localhost:7860, upload a JPG manuscript scan, click Transcribe Manuscript, and confirm all four sections populate"
    expected: "Transcription panel shows cleaned text; Historical Notes panel shows entity table; Confidence Map shows color-coded words; Raw/Cleaned toggle switches content without re-run"
    why_human: "Full end-to-end pipeline execution requires a live GOOGLE_API_KEY and Gemini API calls. Additionally, the pre-existing CR-01 bug in intake.py:61 (get_flattened_data() should be getdata()) must be fixed before this path works — that bug predates Phase 03 and belongs to Phase 02, but it blocks end-to-end verification of this truth."
human_verification:
  - test: "End-to-end pipeline upload in Gradio browser interface"
    expected: "All four UI sections populate after upload: Transcription (cleaned_text default), Historical Notes (entity table), Confidence Map (orange-highlighted uncertain words), Raw/Cleaned toggle functional"
    why_human: "Requires live GOOGLE_API_KEY, Gemini API, and browser. Pre-existing intake.py:61 bug (CR-01, Phase 02 regression) must be fixed first."
  - test: "Confidence scoring completeness on a real manuscript"
    expected: "confidence_map JSON array contains one entry per token; all scores in [0.0, 1.0]; uncertain tokens correctly get lower scores than clearly legible common Spanish function words"
    why_human: "LLM self-assessment quality and coverage cannot be verified by static analysis. max_output_tokens gap (CR-03) should be fixed before this test to prevent silent truncation."
---

# Phase 03: Verification + Gradio UI — Verification Report

**Phase Goal:** The system scores transcription confidence per passage, marks uncertain words with highlights, and presents all results (clean transcription, historical notes, raw/clean toggle, confidence map) through a Gradio demo interface.
**Verified:** 2026-06-26
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

All 12 truths are drawn from the merged set of ROADMAP.md Success Criteria (SC-1 through SC-4) and PLAN frontmatter must-haves. ROADMAP SCs take precedence; PLAN truths add detail.

| # | Truth | Source | Status | Evidence |
|---|-------|--------|--------|----------|
| 1 | Every passage/word carries a confidence score; low-confidence items explicitly flagged | SC-1, VER-01, VER-02 | PRESENT_BEHAVIOR_UNVERIFIED | Code wired: verification_agent produces confidence_map JSON array; CONFIDENCE_THRESHOLD=0.7 defined. LLM scoring completeness and score range require runtime execution — no automated test exercises the invariant. CR-03 (missing max_output_tokens) also puts completeness at risk for long manuscripts. |
| 2 | Researcher can upload image in browser, see all results, without running code | SC-2, UI-01, UI-02 | PRESENT_BEHAVIOR_UNVERIFIED | Gradio Blocks layout correct; all four sections present; event wiring confirmed. Full pipeline execution requires live Gemini API. Pre-existing CR-01 bug (intake.py:61 get_flattened_data() vs getdata(), Phase 02 regression) crashes every upload before it reaches the pipeline — must be fixed before end-to-end verification. |
| 3 | Raw/clean toggle lets researcher compare original Gemini output against cleaned version | SC-3, UI-05 | VERIFIED | gr.State(raw_state) and gr.State(cleaned_state) declared; toggle_view(view, raw, cleaned) pure function wired to view_toggle.change(); returns raw when view=="Raw" else cleaned. No re-run triggered. |
| 4 | Confidence output structured as JSON for programmatic rendering | SC-4, VER-03 | VERIFIED | verification_agent.output_key="confidence_map"; response_mime_type="application/json"; schema {"word", "score", "reason"} per-element; run_pipeline() exposes confidence_map key; render_confidence_html() parses the list and produces HTML. |
| 5 | CONFIDENCE_THRESHOLD = 0.7 defined in verification.py (D-04) | P01-T2 | VERIFIED | `from palimpsest.agents.verification import CONFIDENCE_THRESHOLD; assert CONFIDENCE_THRESHOLD == 0.7` — PASS |
| 6 | confidence_map returned as key in run_pipeline() dict alongside existing D-11 keys (A3, D-06) | P01-T3, VER-03 | VERIFIED | orchestrator.py:180 success return contains "confidence_map": confidence; orchestrator.py:99 early-error return contains "confidence_map": None; no existing D-11 keys mutated. |
| 7 | Pipeline SequentialAgent runs 4 sub_agents in order: Transcription, Cleaning, Context, Verification (D-05) | P01-T4 | VERIFIED | `len(pipeline.sub_agents) == 4` PASS; `pipeline.sub_agents[3].name == "VerificationAgent"` PASS |
| 8 | Verification agent injects {cleaned_transcription} from session state and parses cleaned_text field | P01-T5 | VERIFIED | VERIFICATION_INSTRUCTION contains literal `{cleaned_transcription}` (ADK template injection); Step 1 instructs model to extract "cleaned_text" field from JSON. |
| 9 | Uncertain words highlighted with orange/yellow opacity gradient; hover tooltip shows score and reason | P02-T2, UI-03 | VERIFIED | render_confidence_html([{"word":"Alcantara","score":0.3,"reason":"proper noun"}]) produces `rgba(255, 165, 0, 0.7)` span with `title="score: 0.3 \| reason: proper noun"` — automated test PASS |
| 10 | Historical notes render as Markdown table with columns Entity, Type, Description, Date, Source | P02-T4, UI-04 | VERIFIED | render_context_table([{"entity":"Felipe V","type":"person",...}]) produces `\| Entity \| Type \| Description \| Date \| Source \|` table — automated test PASS |
| 11 | Pipeline errors surface as a gr.Error pop-up banner — no broken UI state | P02-T5 | FAILED | CR-02: json.loads() at app.py:185-199 has no try/except. Orchestrator marks status="ok" when cleaning/context/confidence agents fail while appending to errors[]. When app.py passes the status gate and those json.loads() calls hit malformed JSON, unhandled JSONDecodeError propagates as Python exception — Gradio surfaces a generic 500, not a gr.Error banner. Only the explicit status=="error" path is handled correctly. |
| 12 | html.escape() called on word and reason values before HTML insertion (T-03-03, XSS) | P02-T6 | VERIFIED | 4 occurrences of html.escape() in app.py confirmed (2 per call: escaped_word and escaped_reason); automated test PASS; both inserted into span content and title attribute |

**Score:** 9/12 truths verified (2 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/palimpsest/agents/verification.py` | VerificationAgent + CONFIDENCE_THRESHOLD + VERIFICATION_INSTRUCTION | VERIFIED | 79 lines; imports cleanly; all three exports correct |
| `src/palimpsest/agents/orchestrator.py` | 4 sub_agents, confidence_map in return dict, verification_agent import | VERIFIED | 4 sub_agents confirmed; confidence_map in both return paths; verification_agent imported at line 27 |
| `src/palimpsest/app.py` | gr.Blocks demo; all helper functions; event wiring | VERIFIED (with gap) | 313 lines; all components present; CR-02 json.loads gap |
| `requirements.txt` | gradio pinned | VERIFIED | gradio==6.19.0 (upgraded from planned 5.50.0 due to Pillow 12.x incompatibility — auto-fix documented in SUMMARY) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| verification_agent | InMemorySession state | output_key="confidence_map" | VERIFIED | output_key confirmed; ADK writes LLM response to state under this key |
| VERIFICATION_INSTRUCTION | session state | `{cleaned_transcription}` template | VERIFIED | Literal `{cleaned_transcription}` present in instruction string; cleaned_text parse step present |
| run_pipeline() | confidence_map key | `final_session.state.get("confidence_map")` | VERIFIED | orchestrator.py:116 reads state; line 180 adds to return dict |
| gr.File(type="filepath") | transcribe_manuscript(file_path) | submit_btn.click | VERIFIED | app.py:291-294: inputs=[file_input], fn=transcribe_manuscript |
| run_pipeline() confidence_map key | render_confidence_html() | json.loads() + app.py:196-200 | VERIFIED (with gap) | Data flows to renderer; json.loads() has no exception handling (CR-02) |
| run_pipeline() context_notes key | render_context_table() | json.loads() + app.py:193-195 | VERIFIED (with gap) | Data flows to renderer; same CR-02 applies |
| gr.State(raw_state) + gr.State(cleaned_state) | transcription_box | view_toggle.change → toggle_view | VERIFIED | app.py:298-301: wired; toggle_view returns raw or cleaned based on view value |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `render_confidence_html` in app.py | word_scores | confidence_json from run_pipeline() confidence_map key, via json.loads() | LLM-generated at runtime | FLOWING (structurally) — actual content requires live Gemini call |
| `render_context_table` in app.py | context_notes | context_json from run_pipeline() context_notes key, via json.loads() | LLM+MCP-generated at runtime | FLOWING (structurally) |
| transcription_box (gr.Textbox) | cleaned_text | json.loads(cleaned_json).get("cleaned_text") | From cleaning agent session state | FLOWING (structurally) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| verification.py imports with correct attributes | `python -c "from palimpsest.agents.verification import verification_agent, CONFIDENCE_THRESHOLD; assert verification_agent.output_key=='confidence_map'; assert CONFIDENCE_THRESHOLD==0.7"` | PASS | PASS |
| orchestrator has 4 sub_agents ending in VerificationAgent | `python -c "from palimpsest.agents.orchestrator import pipeline; assert len(pipeline.sub_agents)==4; assert pipeline.sub_agents[3].name=='VerificationAgent'"` | PASS | PASS |
| app.py helper functions pass smoke tests | `python -c "from palimpsest.app import render_confidence_html, render_context_table, demo; import gradio as gr; assert isinstance(demo, gr.Blocks)"` | ALL CHECKS PASSED | PASS |
| render_confidence_html highlights uncertain words | score=0.3 entry produces `rgba(255, 165, 0,` and `title=` | PASS | PASS |
| render_confidence_html leaves confident words as plain text | score=0.95 entry produces no `<span` | PASS | PASS |
| render_context_table produces Markdown table | non-empty entity list produces `\| Entity \|` header | PASS | PASS |
| Full pipeline end-to-end | Requires GOOGLE_API_KEY + live Gemini calls | — | SKIP (no live API in verification environment) |

### Requirements Coverage

| Requirement | Plan | Description | Status | Evidence |
|-------------|------|-------------|--------|----------|
| VER-01 | 03-01 | Verification agent scores confidence per passage/sentence | SATISFIED | verification_agent with per-word scoring instruction and output_key="confidence_map" |
| VER-02 | 03-01 | Verification agent marks words/spans with low confidence | SATISFIED | CONFIDENCE_THRESHOLD=0.7; instruction includes scoring guidance for uncertain tokens; render_confidence_html highlights score<0.7 words |
| VER-03 | 03-01 | Output includes confidence scores consumable by the UI | SATISFIED | confidence_map key in run_pipeline() return dict; JSON array parsed and rendered by render_confidence_html() |
| UI-01 | 03-02 | Gradio interface accepts single image file upload | SATISFIED | gr.File(file_types=[".jpg",".jpeg",".png"], file_count="single", type="filepath") |
| UI-02 | 03-02 | UI displays clean transcription after processing | SATISFIED | transcription_box gr.Textbox receives cleaned_text as first tuple element from transcribe_manuscript |
| UI-03 | 03-02 | UI renders confidence highlights (color-coded uncertain words/spans) | SATISFIED | render_confidence_html with orange/yellow rgba spans; output in gr.HTML(confidence_html) |
| UI-04 | 03-02 | UI shows historical notes panel with context enrichment results | SATISFIED | render_context_table produces Markdown table; displayed in gr.Markdown(notes_md) |
| UI-05 | 03-02 | UI provides raw-vs-clean toggle | SATISFIED | gr.Radio + toggle_view + gr.State(raw_state, cleaned_state); no pipeline re-run |

All 8 phase requirements are satisfied by the code structure. End-to-end behavioral verification of VER-01/VER-02/UI-01/UI-02/UI-03 requires a live pipeline execution.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/palimpsest/app.py` | 185–199 | No try/except on four json.loads() calls in transcribe_manuscript | BLOCKER | Unhandled JSONDecodeError propagates as generic 500; defeats gr.Error banner contract (CR-02) |
| `src/palimpsest/agents/verification.py` | 75–78 | GenerateContentConfig missing max_output_tokens=65536 | BLOCKER | Silent mid-array truncation of confidence_map JSON for long manuscripts; violates CLAUDE.md explicit constraint; feeds into CR-02 risk (CR-03) |

No TBD, FIXME, or XXX markers found in any Phase 03 modified file.

**Note on CR-01 (pre-existing, Phase 02):** The code review identified `img.get_flattened_data()` at `intake.py:61` — this method does not exist in Pillow; the correct call is `img.getdata()`. This bug predates Phase 03 (it was introduced in Phase 02) and causes every image upload to crash with AttributeError caught as IntakeError. It is NOT a Phase 03 regression and is not a gap charged to this phase. However, it must be fixed before the end-to-end browser flow (Truth 2) can be verified. It is flagged in the human verification checklist.

**Note on gradio version:** Plan called for 5.50.0; executor auto-upgraded to 6.19.0 due to irreconcilable Pillow 12.x dependency conflict. This deviation is intentional, documented, and functionally equivalent for all components used. Not a gap.

### Human Verification Required

#### 1. End-to-End Pipeline Upload in Gradio Interface

**Pre-condition:** Fix `intake.py:61` `img.get_flattened_data()` → `img.getdata()` (CR-01, Phase 02 regression). Set GOOGLE_API_KEY in .env.

**Test:** `python -m palimpsest.app` → open http://localhost:7860 → upload a JPG or PNG manuscript scan → click "Transcribe Manuscript"

**Expected:**
- Transcription panel (Cleaned default) populates with normalized text
- Historical Notes panel shows a Markdown entity table
- Confidence Map section shows words with orange/yellow highlighting for uncertain tokens
- Raw/Cleaned radio toggle switches the Transcription panel content without re-running the pipeline

**Why human:** Requires live GOOGLE_API_KEY, Gemini API calls, and a browser. Phase 03 structural wiring is correct; actual rendering depends on pipeline execution.

#### 2. Confidence Scoring Completeness and Quality

**Pre-condition:** CR-03 (max_output_tokens) must be fixed first to prevent silent truncation.

**Test:** Using a manuscript with at least 50 words, inspect the confidence_map JSON array returned by run_pipeline()

**Expected:**
- Array contains exactly one entry per space-separated token in cleaned_text
- All scores are floats in [0.0, 1.0]
- Common Spanish function words (el, la, de, que, y) score >= 0.85
- Tokens marked with [?] by the cleaning agent score <= 0.5

**Why human:** LLM self-assessment quality and coverage require runtime execution. Static analysis cannot verify that the model follows the scoring guidance in VERIFICATION_INSTRUCTION.

### Gaps Summary

**2 blockers** prevent gap closure:

**Blocker 1 — CR-02: Unhandled JSONDecodeError (app.py:185-199)**

Truth "Pipeline errors surface as a gr.Error pop-up banner" is FAILED. The `transcribe_manuscript` handler correctly wraps `IntakeError` and the explicit `status=="error"` pipeline path in `gr.Error()`. But the four `json.loads()` calls that parse raw, cleaned, context, and confidence outputs have no exception handling. The orchestrator propagates cleaning, context, and confidence parse failures as `status="ok"` with entries in `errors[]`, so the status gate (line 170) passes. Any `JSONDecodeError` or `TypeError` on those parse calls then propagates as an unhandled Python exception — Gradio shows a generic 500 error page, not the gr.Error banner the design requires.

**Fix:** Wrap app.py:185-199 in:
```python
try:
    raw_text = json.loads(raw_json).get("raw_text", "") if isinstance(raw_json, str) else ""
    cleaned_text = json.loads(cleaned_json).get("cleaned_text", "") if isinstance(cleaned_json, str) else ""
    context_list = json.loads(context_json) if isinstance(context_json, str) else (context_json or [])
    confidence_list = json.loads(confidence_json) if isinstance(confidence_json, str) else (confidence_json or [])
except (json.JSONDecodeError, TypeError) as exc:
    raise gr.Error(f"Pipeline output could not be parsed: {exc}") from exc
```

**Blocker 2 — CR-03: Missing max_output_tokens in verification.py**

CLAUDE.md constraint: "Set maxOutputTokens=65536 explicitly or transcription silently truncates." The transcription agent already follows this (transcription.py:60). The verification agent does not. For a manuscript with hundreds of words, the output word-score array easily exceeds model default output token limits. Silent mid-array truncation produces malformed JSON that fails json.loads(), which then triggers the unhandled JSONDecodeError from Blocker 1.

**Fix:** Add to verification.py GenerateContentConfig:
```python
generate_content_config=types.GenerateContentConfig(
    temperature=0.1,
    response_mime_type="application/json",
    max_output_tokens=65536,
),
```

---

_Verified: 2026-06-26T00:00:00Z_
_Verifier: Claude (gsd-verifier)_

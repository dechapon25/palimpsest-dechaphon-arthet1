"""Gradio demo interface for the Palimpsest manuscript transcription pipeline.

Layout decisions (D-07 through D-17 from 03-CONTEXT.md):
- D-07: Single-page, vertical layout — Upload -> Transcription -> Historical Notes
  -> Confidence Map. No tabs.
- D-08: Raw/Cleaned radio toggle (gr.Radio) switches gr.Textbox content between
  raw_transcription and cleaned_transcription stored in gr.State; no re-run.
- D-09: Historical Notes rendered as a Markdown table via gr.Markdown component.
  Columns: Entity | Type | Description | Date | Source.
- D-12: App lives at src/palimpsest/app.py. Launch: python -m palimpsest.app.
- D-13: run_pipeline() is async; called via asyncio.run() inside a sync Gradio
  click handler (safe in Gradio thread pool; no async Gradio handler needed).

UI requirements satisfied:
- UI-01: gr.File upload + "Transcribe Manuscript" submit button.
- UI-02: gr.Textbox shows cleaned transcription after submit.
- UI-03: Uncertain words (score < 0.7) highlighted with orange/yellow spans in gr.HTML.
- UI-04: Historical entity notes rendered as Markdown table in gr.Markdown panel.
- UI-05: Raw/Cleaned radio toggle switches Textbox content without re-running pipeline.

Security notes:
- SEC-04 (XSS prevention): html.escape() applied to both word and reason values
  from LLM-generated confidence_map before inserting into HTML span elements
  (T-03-03 mitigation per RESEARCH.md Security Domain).
- T-03-04: load_dotenv() loads GOOGLE_API_KEY from .env; key never logged or
  displayed in Gradio outputs; gr.Error messages contain only user-visible text.
"""

import asyncio
import html
import json
import os
import sys
import time

import gradio as gr
from dotenv import load_dotenv

from palimpsest.security.intake import IntakeError, validate_and_clean
from palimpsest.agents.orchestrator import run_pipeline

# Load environment variables (GOOGLE_API_KEY, etc.) at module level.
# Follows run.py pattern; must precede any Gemini API calls.
load_dotenv()

# Confidence threshold — words scoring below this are uncertain.
# Mirrors CONFIDENCE_THRESHOLD in verification.py (D-04).
CONFIDENCE_THRESHOLD = 0.7
HIGHLIGHT_THRESHOLD = 0.95  # Design spec: score >= 0.95 → plain; score < 0.95 → amber highlight

PROCESSING_HTML = """
<div class="pal-card pal-processing-card">
  <div class="pal-card-title">Transcribiendo…</div>
  <div class="pal-progress-bar-wrap"><div class="pal-progress-bar"></div></div>
  <ul class="pal-steps">
    <li class="step-active">
      <span class="step-icon"><span class="step-icon-spin">⟳</span></span>
      Restauración de la imagen
    </li>
    <li>
      <span class="step-icon">·</span>
      Transcripción paleográfica
    </li>
    <li>
      <span class="step-icon">·</span>
      Análisis histórico
    </li>
    <li>
      <span class="step-icon">·</span>
      Mapa de confianza
    </li>
  </ul>
</div>
"""

CUSTOM_CSS = """
/* Palimpsest — Parchment Theme (Claude Design handoff) */

@import url('https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Hanken+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

/* ── Design tokens ──────────────────────────────────────────── */
:root {
    --pal-bg:          #F1EADA;
    --pal-card-bg:     #FBF8F0;
    --pal-text:        #23190F;
    --pal-text-2:      #6E6353;
    --pal-text-muted:  #8A7E6B;
    --pal-accent:      #AE3B2C;
    --pal-green:       #2F6E5A;
    --pal-amber:       #D9952E;
    --pal-blue:        #4A5A86;
    --pal-border:      rgba(35,25,15,0.12);
    --pal-shadow:      0 18px 40px -30px rgba(35,25,15,0.4);
    --pal-radius:      16px;
    --pal-radius-pill: 999px;
    --font-serif:      'Spectral', Georgia, serif;
    --font-sans:       'Hanken Grotesk', system-ui, sans-serif;
    --font-mono:       'IBM Plex Mono', 'Courier New', monospace;
}

/* ── Base ───────────────────────────────────────────────────── */
body, html {
    background-color: #F1EADA !important;
    font-family: var(--font-sans);
    overflow-x: hidden;
}

/* Background watermark — fixed italic Spectral text, barely visible */
body::before {
    content: "Palimpsesto · manuscrito · historia · transcripción paleográfica";
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) rotate(-1deg);
    font-family: 'Spectral', Georgia, serif;
    font-style: italic;
    font-size: 40px;
    color: rgba(35,25,15,0.038);
    white-space: nowrap;
    pointer-events: none;
    z-index: 0;
    user-select: none;
}

.gradio-container {
    background-color: #F1EADA !important;
    max-width: 1200px;
    margin: 0 auto;
    padding: 32px 24px;
    font-family: var(--font-sans);
    /* Gradio CSS variable overrides */
    --loader-color:              #AE3B2C !important;
    --block-background-fill:     #FBF8F0 !important;
    --body-text-color:           #23190F !important;
    --body-text-color-subdued:   #6E6353 !important;
    --border-color-primary:      rgba(35,25,15,0.12) !important;
    --background-fill-secondary: #FBF8F0 !important;
    --background-fill-primary:   #F1EADA !important;
    --color-accent:              #AE3B2C !important;
}

/* ── Header ─────────────────────────────────────────────────── */
.pal-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 32px;
}

.pal-logo-mark {
    width: 48px;
    height: 48px;
    min-width: 48px;
    background: #23190F;
    border-radius: 10px;
    box-shadow: 0 4px 0 #AE3B2C;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Spectral', Georgia, serif;
    font-size: 22px;
    font-weight: 700;
    color: #FBF8F0;
    line-height: 1;
}

.pal-header-title {
    font-family: 'Spectral', Georgia, serif;
    font-size: 28px;
    font-weight: 600;
    color: #23190F;
    line-height: 1.2;
    margin: 0;
}

.pal-header-sub {
    font-size: 14px;
    color: #6E6353;
    font-family: 'Hanken Grotesk', system-ui, sans-serif;
    margin: 3px 0 0 0;
}

/* ── Upload zone ────────────────────────────────────────────── */
.pal-upload-zone {
    border: 2px dashed rgba(174,59,44,0.40);
    border-radius: 16px;
    padding: 32px;
    text-align: center;
    background: #FBF8F0;
    margin-bottom: 16px;
}

/* ── Cards ──────────────────────────────────────────────────── */
.pal-card {
    background: #FBF8F0;
    border-radius: 16px;
    box-shadow: var(--pal-shadow);
    border: 1px solid var(--pal-border);
    padding: 20px 24px 24px;
}

.pal-card h3, .pal-card .pal-card-title {
    font-family: 'Spectral', Georgia, serif;
    font-size: 18px;
    font-weight: 600;
    color: #23190F;
    margin: 0 0 16px 0;
    border: none;
    padding: 0;
}

/* ── Results grid — 1.55fr 1fr with notes spanning full width ── */
.pal-results-grid {
    display: grid;
    grid-template-columns: 1.55fr 1fr;
    grid-template-rows: auto auto;
    grid-template-areas: "transcription confidence" "notes notes";
    gap: 12px;
    margin-top: 24px;
}
.pal-results-grid > .form { display: contents; }
.pal-transcription-card { grid-area: transcription; }
.pal-confidence-card    { grid-area: confidence; }
.pal-notes-card         { grid-area: notes; }

/* ── Notes entity cards grid ────────────────────────────────── */
.pal-notes-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
    gap: 12px;
    margin-top: 12px;
}

.pal-note-card {
    padding: 16px 18px;
}

.pal-note-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 8px;
}

.pal-note-entity {
    font-family: 'Spectral', Georgia, serif;
    font-weight: 600;
    font-size: 15px;
    color: #23190F;
}

.pal-note-type {
    font-size: 11px;
    font-family: 'Hanken Grotesk', system-ui, sans-serif;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 999px;
    white-space: nowrap;
}

.pal-note-desc {
    font-size: 13px;
    color: #6E6353;
    line-height: 1.55;
    margin: 0;
    font-family: 'Hanken Grotesk', system-ui, sans-serif;
}

/* ── Segment toggle — gr.Radio styled as pill switcher ──────── */
.pal-seg-toggle .wrap {
    display: inline-flex !important;
    border: 1px solid rgba(35,25,15,0.12) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    gap: 0 !important;
    padding: 0 !important;
    background: transparent !important;
}
.pal-seg-toggle input[type="radio"] { display: none !important; }
.pal-seg-toggle label {
    padding: 6px 16px !important;
    font-size: 13px !important;
    font-family: 'Hanken Grotesk', system-ui, sans-serif !important;
    cursor: pointer !important;
    color: #6E6353 !important;
    background: transparent !important;
    border: none !important;
    margin: 0 !important;
    transition: background 0.15s, color 0.15s;
}
.pal-seg-toggle input[type="radio"]:checked + label {
    background: #AE3B2C !important;
    color: #FBF8F0 !important;
}

/* ── Buttons ────────────────────────────────────────────────── */
.btn-primary {
    background-color: #AE3B2C !important;
    color: #FBF8F0 !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    font-family: 'Hanken Grotesk', system-ui, sans-serif !important;
    box-shadow: 0 2px 8px rgba(174,59,44,0.35) !important;
    border: none !important;
    width: 100%;
}
.btn-primary:hover { background-color: #8f3024 !important; }

.btn-ghost {
    background: transparent !important;
    border: 1px solid rgba(35,25,15,0.20) !important;
    color: #23190F !important;
    font-family: 'Hanken Grotesk', system-ui, sans-serif !important;
    border-radius: 8px !important;
}
.btn-ghost:hover { background: rgba(35,25,15,0.05) !important; }

/* ── Metadata bar ───────────────────────────────────────────── */
.pal-meta-bar {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    align-items: center;
    margin-bottom: 16px;
}
.pal-meta-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid rgba(35,25,15,0.12);
    background: #FBF8F0;
    font-size: 12px;
    font-family: 'IBM Plex Mono', 'Courier New', monospace;
    color: #6E6353;
}
.pal-meta-pill strong { color: #23190F; font-weight: 500; }

/* ── Status / completion text ───────────────────────────────── */
.pal-status {
    font-size: 13px;
    color: #2F6E5A;
    font-family: 'Hanken Grotesk', system-ui, sans-serif;
    min-height: 20px;
}

/* ── Transcription text modes ───────────────────────────────── */
.pal-transcription-card textarea {
    font-family: 'Spectral', Georgia, serif !important;
    font-size: 18px !important;
    line-height: 1.95 !important;
    color: #23190F !important;
    background: transparent !important;
    border: none !important;
}

/* ── Gradio generating pulse ────────────────────────────────── */
.generating { border-color: #AE3B2C !important; }
.progress-level-inner { color: #23190F !important; }
.meta-text, .meta-text-center { color: #23190F !important; }

/* ── Processing card ────────────────────────────────────────── */
.pal-processing-card {
    margin: 16px 0;
}
.pal-processing-card .pal-card-title {
    font-family: 'Spectral', Georgia, serif;
    font-size: 18px;
    font-weight: 600;
    color: #23190F;
    margin: 0 0 14px 0;
}
.pal-progress-bar-wrap {
    height: 6px;
    background: rgba(35,25,15,0.10);
    border-radius: 999px;
    overflow: hidden;
    margin-bottom: 18px;
}
.pal-progress-bar {
    height: 100%;
    background: #AE3B2C;
    border-radius: 999px;
    animation: pal-progress 30s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
    width: 0%;
}
@keyframes pal-progress { from { width: 0% } to { width: 88% } }
.pal-steps {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.pal-steps li {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
    font-family: 'Hanken Grotesk', system-ui, sans-serif;
    color: #8A7E6B;
}
.pal-steps .step-active { color: #23190F; font-weight: 500; }
.pal-steps .step-done   { color: #2F6E5A; }
.step-icon {
    width: 20px;
    height: 20px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    flex-shrink: 0;
}
.step-icon-spin { animation: pal-spin 1s linear infinite; display: inline-block; }
@keyframes pal-spin { to { transform: rotate(360deg); } }
"""


def render_confidence_html(word_scores: list[dict]) -> str:
    """Convert confidence_map word list to HTML with uncertainty highlights.

    Uncertain words (score < CONFIDENCE_THRESHOLD) are wrapped in styled
    <span> elements with an orange/yellow gradient background and a hover
    tooltip showing score and reason (D-14, D-15, D-16).

    XSS prevention (SEC-04, T-03-03): html.escape() applied to both word
    and reason values before inserting into HTML attribute or content strings.

    Args:
        word_scores: List of dicts with keys 'word', 'score', 'reason'.

    Returns:
        HTML string wrapped in a div with body typography styles.
    """
    if not word_scores:
        return (
            '<div style="font-size:14px;color:#8A7E6B;font-family:\'Hanken Grotesk\',system-ui,sans-serif">'
            "(el mapa de confianza aparecerá tras el procesamiento)"
            "</div>"
        )

    parts = []
    for entry in word_scores:
        if not isinstance(entry, dict):
            continue  # skip null / non-dict elements from LLM (CR-03)
        # SEC-04 / T-03-03: escape both word and reason to prevent XSS from
        # LLM-generated strings inserted into HTML attribute and content contexts.
        escaped_word = html.escape(str(entry.get("word", "")))
        escaped_reason = html.escape(str(entry.get("reason", "")))
        # CR-01: entry.get("score") returns None when score is JSON null;
        # float(None) raises TypeError, so treat None as fully-confident 1.0.
        score_raw = entry.get("score")
        try:
            score = float(score_raw) if score_raw is not None else 1.0
        except (TypeError, ValueError):
            score = 1.0  # treat unparseable score as fully confident

        if score < HIGHLIGHT_THRESHOLD:
            # Alpha formula from design spec: min(0.62, (1-score)*1.05) + 0.05
            alpha = round(min(0.62, (1 - score) * 1.05) + 0.05, 3)
            span = (
                f'<span style="'
                f"background-color: rgba(217,149,46,{alpha}); "
                f"box-shadow: inset 0 -2px 0 rgba(174,59,44,0.42); "
                f"padding: 0 2px; "
                f"border-radius: 2px; "
                f'cursor: help;" '
                f'title="score: {score:.2f} | {escaped_reason}">'
                f"{escaped_word}</span>"
            )
            parts.append(span)
        else:
            parts.append(escaped_word)

    body = " ".join(parts)
    return f'<div style="font-size:16px;line-height:1.8;font-family:\'Spectral\',Georgia,serif;color:#23190F">{body}</div>'


def _md_cell(value: str) -> str:
    """Escape Markdown table special characters in a single cell value (WR-01)."""
    return value.replace("|", "\\|").replace("\n", " ").replace("\r", "")


def render_context_table(context_notes: list[dict]) -> str:
    """Convert context_notes entity list to a Markdown table string.

    Produces a Markdown table with columns: Entity | Type | Description | Date | Source.
    Descriptions are truncated to 120 characters to keep the table readable (D-09,
    UI-SPEC helper contract).

    Args:
        context_notes: List of entity dicts from the context agent.

    Returns:
        Markdown table string, or a no-entities message if the list is empty.
    """
    if not context_notes:
        return "No historical entities found in this document."

    header = "| Entity | Type | Description | Date | Source |"
    separator = "|--------|------|-------------|------|--------|"
    rows = []

    for note in context_notes:
        if not isinstance(note, dict):
            continue  # skip null / non-dict elements from LLM (CR-03)
        entity = str(note.get("entity", ""))
        entity_type = str(note.get("type", ""))
        description = str(note.get("description", ""))
        if len(description) > 120:
            description = description[:120] + "..."
        dates = str(note.get("dates", ""))
        # Source: prefer source_url, fall back to wikidata_id, then empty (D-09 schema)
        source = str(
            note.get("source_url") or note.get("wikidata_id") or ""
        )
        rows.append(
            f"| {_md_cell(entity)} | {_md_cell(entity_type)} | "
            f"{_md_cell(description)} | {_md_cell(dates)} | {_md_cell(source)} |"
        )

    return header + "\n" + separator + "\n" + "\n".join(rows)


async def transcribe_manuscript(file_path: str) -> tuple:
    """Gradio click handler: validate image, run pipeline, return UI outputs.

    Accepts a plain str file path from gr.File(type="filepath") in Gradio 5+/6+.
    Does NOT use a .name attribute — file_path is already a str (RESEARCH.md Pitfall 4).

    Returns a 5-tuple mapped to Gradio outputs:
        (transcription_box, raw_state, cleaned_state, notes_md, confidence_html)

    Error handling (D-11): raises gr.Error() for both intake failures and pipeline
    errors. Gradio displays these as a red pop-up banner — no broken UI state.

    Args:
        file_path: Path string returned by gr.File(type="filepath").

    Returns:
        5-tuple: (cleaned_text, raw_text, cleaned_text, markdown_table, html_string)
    """
    if file_path is None:
        raise gr.Error("Por favor, sube una imagen del manuscrito primero.")

    # SEC-01/02/03: validate file type, size, strip EXIF via security intake layer.
    # file_path is a plain str — validate_and_clean accepts str (pathlib.Path internally).
    try:
        clean_bytes, mime_type = validate_and_clean(file_path)
    except IntakeError as e:
        raise gr.Error(str(e)) from e

    filename = os.path.basename(file_path)

    # WR-02: handler is now async; await run_pipeline() directly.
    # Gradio 4+ accepts coroutines as fn= arguments natively, so asyncio.run()
    # is no longer needed and would raise RuntimeError in embedded-loop contexts.
    result = await run_pipeline(clean_bytes, mime_type, filename)

    # D-11 (UI errors): surface pipeline errors as gr.Error pop-up.
    if result.get("status") == "error":
        errors = result.get("errors", [])
        msg = (
            "; ".join(errors)
            if errors
            else "Procesamiento fallido. Verifica que el archivo sea válido y vuelve a intentarlo."
        )
        raise gr.Error(msg)

    # Extract raw transcription JSON -> raw_text string
    raw_json = result.get("raw_transcription") or "{}"
    cleaned_json = result.get("cleaned_transcription") or "{}"
    context_json = result.get("context_notes") or "[]"
    confidence_json = result.get("confidence_map") or "[]"

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
    except gr.Error:
        raise
    except (json.JSONDecodeError, TypeError, AttributeError) as exc:
        raise gr.Error(f"Pipeline output could not be parsed: {exc}") from exc

    # Context and confidence are optional — parse failures default to empty list
    try:
        context_list = (
            json.loads(context_json)
            if isinstance(context_json, str) and context_json.strip()
            else (context_json or [])
        )
        if not isinstance(context_list, list):
            context_list = []
    except (json.JSONDecodeError, TypeError):
        context_list = []

    try:
        confidence_list = (
            json.loads(confidence_json)
            if isinstance(confidence_json, str) and confidence_json.strip()
            else (confidence_json or [])
        )
        if not isinstance(confidence_list, list):
            confidence_list = []
    except (json.JSONDecodeError, TypeError):
        confidence_list = []

    return (
        cleaned_text,
        raw_text,
        cleaned_text,
        render_context_table(context_list),
        render_confidence_html(confidence_list),
        gr.update(visible=True),
        gr.update(visible=True),
        gr.update(visible=True),
        gr.update(visible=True),
        "Procesamiento completado.",
        gr.update(visible=False),  # processing_section
    )


def toggle_view(view: str, raw: str, cleaned: str) -> str:
    """Switch Textbox content between raw and cleaned transcription texts.

    Pure function; no side effects; no pipeline re-run (D-08, UI-05).

    Args:
        view: Selected radio value ("Raw" or "Cleaned").
        raw: Raw transcription text from raw_state.
        cleaned: Cleaned transcription text from cleaned_state.

    Returns:
        The appropriate text string for the Transcription Textbox.
    """
    return raw if view == "Original" else cleaned


def reset_manuscript() -> tuple:
    """Reset all UI state and hide result panels. Returns 11-tuple matching outputs_full."""
    return (
        "",                          # transcription_box
        "",                          # raw_state
        "",                          # cleaned_state
        "",                          # notes_md (gr.HTML)
        "",                          # confidence_html
        gr.update(visible=False),    # transcription_section
        gr.update(visible=False),    # confidence_section
        gr.update(visible=False),    # notes_section
        gr.update(visible=False),    # reset_btn
        "",                          # status_md (gr.HTML)
        gr.update(visible=False),    # processing_section
    )


def show_processing() -> gr.update:
    """Show the processing state card. Called before transcribe_manuscript via .then() chain."""
    return gr.update(visible=True)


with gr.Blocks(css=CUSTOM_CSS, title="Palimpsest — Manuscript Transcription") as demo:
    gr.HTML("""
<div class="pal-header">
  <div class="pal-logo-mark">P</div>
  <div>
    <div class="pal-header-title">Palimpsest</div>
    <div class="pal-header-sub">Transcripción paleográfica de manuscritos históricos</div>
  </div>
</div>
""")

    raw_state = gr.State(value="")
    cleaned_state = gr.State(value="")

    with gr.Column(elem_classes=["pal-upload-zone"]):
        file_input = gr.File(
            label="Subir imagen de manuscrito",
            file_types=[".jpg", ".jpeg", ".png"],
            file_count="single",
            type="filepath",
        )
        submit_btn = gr.Button("Transcribir", variant="primary", elem_classes=["btn-primary"])

    processing_section = gr.HTML(value=PROCESSING_HTML, visible=False)

    status_md = gr.HTML("", elem_classes=["pal-status"])

    with gr.Column(elem_classes=["pal-results-grid"]):
        with gr.Column(visible=False, elem_classes=["pal-card", "pal-transcription-card"]) as transcription_section:
            gr.Markdown("### Transcripción")
            view_toggle = gr.Radio(label="Vista:", choices=["Limpiada", "Original"], value="Limpiada", elem_classes=["pal-seg-toggle"])
            transcription_box = gr.Textbox(
                label="",
                interactive=False,
                lines=15,
                placeholder="(la transcripción aparecerá aquí)",
            )

        with gr.Column(visible=False, elem_classes=["pal-card", "pal-confidence-card"]) as confidence_section:
            gr.Markdown("### Mapa de Confianza")
            confidence_html = gr.HTML(value="")

        with gr.Column(visible=False, elem_classes=["pal-card", "pal-notes-card"]) as notes_section:
            gr.Markdown("### Notas Históricas")
            notes_md = gr.Markdown(value="")

    reset_btn = gr.Button("Nueva transcripción", visible=False, elem_classes=["btn-ghost"])

    outputs_full = [
        transcription_box,      # 0
        raw_state,              # 1
        cleaned_state,          # 2
        notes_md,               # 3
        confidence_html,        # 4
        transcription_section,  # 5
        confidence_section,     # 6
        notes_section,          # 7
        reset_btn,              # 8
        status_md,              # 9
        processing_section,     # 10  ← NEW
    ]

    submit_btn.click(
        fn=show_processing,
        inputs=[],
        outputs=[processing_section],
    ).then(
        fn=transcribe_manuscript,
        inputs=[file_input],
        outputs=outputs_full,
    )

    reset_btn.click(
        fn=reset_manuscript,
        inputs=[],
        outputs=outputs_full,
    )

    view_toggle.change(
        fn=toggle_view,
        inputs=[view_toggle, raw_state, cleaned_state],
        outputs=[transcription_box],
    )


# ---------------------------------------------------------------------------
# Entry point guard (D-12): enables `python -m palimpsest.app`
# Do NOT call demo.launch() unconditionally — that would prevent import testing.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Pass theme here in Gradio 6.x (moved from gr.Blocks constructor in 6.0)
    # server_name="0.0.0.0" required for Docker — default 127.0.0.1 is not
    # reachable outside the container even with -p 7860:7860 port mapping.
    # server_port reads PORT env var (Cloud Run / Oracle VM convention).
    demo.launch(
        theme=gr.themes.Soft(),
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
    )

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

CUSTOM_CSS = """
/* Palimpsest Wizard — Bento Grid + Glassmorphism */

.gradio-container {
    background-color: #0F172A !important;
    min-height: 100vh;
}

.glass-card {
    background: rgba(30, 41, 59, 0.6);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(201, 168, 76, 0.15);
    border-radius: 12px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
    padding: 20px 20px 24px 20px;
}

.glass-card h3 {
    border-left: 3px solid #C9A84C;
    padding-left: 8px;
    margin-bottom: 16px;
    color: #F1F5F9;
    font-size: 18px;
    font-weight: 600;
    line-height: 1.3;
}

.bento-results {
    display: grid;
    grid-template-columns: 3fr 2fr;
    grid-template-rows: auto auto;
    grid-template-areas: "transcription confidence" "notes notes";
    gap: 12px;
}
.bento-transcription { grid-area: transcription; }
.bento-confidence    { grid-area: confidence; }
.bento-notes         { grid-area: notes; }
.bento-results > .form { display: contents; }

.upload-zone {
    border: 2px dashed #C9A84C;
    border-radius: 12px;
    padding: 32px;
    text-align: center;
}

.btn-primary {
    background-color: #C9A84C !important;
    color: #0F172A !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}

.btn-reset {
    border: 1px solid #C9A84C !important;
    color: #C9A84C !important;
    background: transparent !important;
    border-radius: 8px !important;
}

.status-line {
    font-size: 13px;
    color: #C9A84C;
    font-family: system-ui, -apple-system, sans-serif;
    min-height: 20px;
}

.app-title h2 {
    font-size: 28px;
    font-weight: 600;
    line-height: 1.2;
    color: #F1F5F9;
}

.gradio-container, .gradio-container * {
    color: #CBD5E1;
}
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
            '<div style="font-size:16px;line-height:1.5;font-family:inherit">'
            "(confidence map will appear after processing)"
            "</div>"
        )

    parts = []
    for entry in word_scores:
        # SEC-04 / T-03-03: escape both word and reason to prevent XSS from
        # LLM-generated strings inserted into HTML attribute and content contexts.
        escaped_word = html.escape(str(entry.get("word", "")))
        escaped_reason = html.escape(str(entry.get("reason", "")))
        score = float(entry.get("score", 1.0))

        if score < CONFIDENCE_THRESHOLD:
            # opacity = 1 - score; brighter orange = more uncertain (D-15)
            opacity = round(1 - score, 2)
            span = (
                f'<span style="background-color: rgba(255, 165, 0, {opacity}); '
                f'padding: 0 2px;" '
                f'title="score: {score} | reason: {escaped_reason}">'
                f"{escaped_word}</span>"
            )
            parts.append(span)
        else:
            # Confident word — plain text, no span (D-14 threshold)
            parts.append(escaped_word)

    body = " ".join(parts)
    return f'<div style="font-size:16px;line-height:1.5;font-family:inherit">{body}</div>'


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
        rows.append(f"| {entity} | {entity_type} | {description} | {dates} | {source} |")

    return header + "\n" + separator + "\n" + "\n".join(rows)


def transcribe_manuscript(file_path: str) -> tuple:
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
        raise gr.Error("Please upload a manuscript image first.")

    # SEC-01/02/03: validate file type, size, strip EXIF via security intake layer.
    # file_path is a plain str — validate_and_clean accepts str (pathlib.Path internally).
    try:
        clean_bytes, mime_type = validate_and_clean(file_path)
    except IntakeError as e:
        raise gr.Error(str(e)) from e

    filename = os.path.basename(file_path)

    # D-13: run_pipeline() is async; call via asyncio.run() in this sync handler.
    # Safe inside Gradio's thread pool — no existing event loop in worker threads.
    result = asyncio.run(run_pipeline(clean_bytes, mime_type, filename))

    # D-11 (UI errors): surface pipeline errors as gr.Error pop-up.
    if result.get("status") == "error":
        errors = result.get("errors", [])
        msg = (
            "; ".join(errors)
            if errors
            else "Processing failed. Check your image file and try again."
        )
        raise gr.Error(msg)

    # Extract raw transcription JSON -> raw_text string
    raw_json = result.get("raw_transcription") or "{}"
    cleaned_json = result.get("cleaned_transcription") or "{}"
    context_json = result.get("context_notes") or "[]"
    confidence_json = result.get("confidence_map") or "[]"

    try:
        raw_text = json.loads(raw_json).get("raw_text", "") if isinstance(raw_json, str) else ""
        cleaned_text = (
            json.loads(cleaned_json).get("cleaned_text", "")
            if isinstance(cleaned_json, str)
            else ""
        )
    except (json.JSONDecodeError, TypeError) as exc:
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

    # Return 5-tuple:
    #   [0] transcription_box: show cleaned_text by default (D-08 default = "Cleaned")
    #   [1] raw_state: store raw_text in gr.State for toggle
    #   [2] cleaned_state: store cleaned_text in gr.State for toggle
    #   [3] notes_md: Markdown table from context_notes
    #   [4] confidence_html: HTML string from confidence_map
    return (
        cleaned_text,
        raw_text,
        cleaned_text,
        render_context_table(context_list),
        render_confidence_html(confidence_list),
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
    return raw if view == "Raw" else cleaned


with gr.Blocks(css=CUSTOM_CSS, title="Palimpsest — Manuscript Transcription") as demo:
    with gr.Column(elem_classes=["app-title"]):
        gr.Markdown("## Palimpsest")

    raw_state = gr.State(value="")
    cleaned_state = gr.State(value="")

    with gr.Column(elem_classes=["upload-zone"]):
        file_input = gr.File(
            label="Subir imagen de manuscrito",
            file_types=[".jpg", ".jpeg", ".png"],
            file_count="single",
            type="filepath",
        )
        submit_btn = gr.Button("Transcribir", variant="primary", elem_classes=["btn-primary"])

    status_md = gr.Markdown("", elem_classes=["status-line"])

    with gr.Column(elem_classes=["bento-results"]):
        with gr.Column(visible=False, elem_classes=["glass-card", "bento-transcription"]) as transcription_section:
            gr.Markdown("### Transcripción")
            view_toggle = gr.Radio(label="Vista:", choices=["Raw", "Limpiada"], value="Limpiada")
            transcription_box = gr.Textbox(
                label="",
                interactive=False,
                lines=15,
                placeholder="(la transcripción aparecerá aquí)",
            )

        with gr.Column(visible=False, elem_classes=["glass-card", "bento-confidence"]) as confidence_section:
            gr.Markdown("### Mapa de Confianza")
            confidence_html = gr.HTML(value="")

        with gr.Column(visible=False, elem_classes=["glass-card", "bento-notes"]) as notes_section:
            gr.Markdown("### Notas Históricas")
            notes_md = gr.Markdown(value="")

    reset_btn = gr.Button("Nueva transcripción", visible=False, elem_classes=["btn-reset"])

    # TODO(plan-02): extend outputs to include section visibility and status_md
    submit_btn.click(
        fn=transcribe_manuscript,
        inputs=[file_input],
        outputs=[transcription_box, raw_state, cleaned_state, notes_md, confidence_html],
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

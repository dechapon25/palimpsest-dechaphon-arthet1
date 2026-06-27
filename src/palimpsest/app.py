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
        # Parse context_notes and confidence_map — may be JSON str or already a list
        context_list = (
            json.loads(context_json) if isinstance(context_json, str) and context_json.strip() else (context_json or [])
        )
        confidence_list = (
            json.loads(confidence_json)
            if isinstance(confidence_json, str) and confidence_json.strip()
            else (confidence_json or [])
        )
    except (json.JSONDecodeError, TypeError) as exc:
        raise gr.Error(f"Pipeline output could not be parsed: {exc}") from exc

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


# ---------------------------------------------------------------------------
# Gradio Blocks layout (D-07 vertical order: Upload -> Transcription ->
# Historical Notes -> Confidence Map)
# ---------------------------------------------------------------------------

with gr.Blocks(
    title="Palimpsest — Manuscript Transcription",
) as demo:
    # Note: theme=gr.themes.Soft() is passed to demo.launch() in Gradio 6.x;
    # the Blocks constructor no longer accepts a theme parameter (moved in 6.0).
    gr.Markdown("## Palimpsest")

    # Invisible state components for Raw/Cleaned toggle (D-08, UI-05)
    raw_state = gr.State(value="")
    cleaned_state = gr.State(value="")

    # 1. Upload section (D-10, UI-01)
    with gr.Row():
        file_input = gr.File(
            label="Upload Manuscript Image",
            file_types=[".jpg", ".jpeg", ".png"],
            file_count="single",
            type="filepath",
        )
        submit_btn = gr.Button("Transcribe Manuscript", variant="primary")

    # 2. Transcription section with Raw/Cleaned toggle (D-08, UI-02, UI-05)
    with gr.Group():
        view_toggle = gr.Radio(
            label="View",
            choices=["Raw", "Cleaned"],
            value="Cleaned",
        )
        transcription_box = gr.Textbox(
            label="Transcription",
            interactive=False,
            lines=15,
            placeholder="(transcription will appear here)",
        )
        # Note: show_copy_button was removed in Gradio 6.x; omitted for compatibility.

    # 3. Historical Notes section (D-09, UI-04)
    notes_md = gr.Markdown(
        label="Historical Notes",
        value="(historical notes will appear after processing)",
    )

    # 4. Confidence Map section (D-14, D-17, UI-03)
    confidence_html = gr.HTML(
        label="Confidence Map",
        value="(confidence map will appear after processing)",
    )

    # ---------------------------------------------------------------------------
    # Event wiring
    # ---------------------------------------------------------------------------

    # Submit button: run pipeline, populate all output components
    submit_btn.click(
        fn=transcribe_manuscript,
        inputs=[file_input],
        outputs=[transcription_box, raw_state, cleaned_state, notes_md, confidence_html],
    )

    # Radio toggle: switch Textbox content without re-running pipeline (D-08, UI-05)
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
    demo.launch(theme=gr.themes.Soft())

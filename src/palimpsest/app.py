"""Gradio demo interface for the Palimpsest manuscript transcription pipeline.

Layout decisions (D-07 through D-17 from 03-CONTEXT.md):
- D-07: Single-page, vertical layout — Upload -> Transcription -> Historical Notes
  -> Confidence Map. No tabs.
- D-08: Raw/Cleaned radio toggle (gr.Radio) switches gr.Textbox content between
  raw_transcription and cleaned_transcription stored in gr.State; no re-run.
- D-09: Historical Notes rendered as a Markdown table via gr.Markdown component.
  Columns: Entity | Type | Description | Date | Source.
- D-12: App lives at src/palimpsest/app.py. Launch: python -m palimpsest.app.
- D-13: run_pipeline() is async; the Gradio click handler is itself async and
  awaits run_pipeline() directly (Gradio 4+ accepts coroutine handlers natively).

UI requirements satisfied:
- UI-01: gr.File upload + "Transcribe Manuscript" submit button.
- UI-02: gr.Textbox shows cleaned transcription after submit.
- UI-03: Words scoring below the 0.95 HIGHLIGHT_THRESHOLD get amber highlight
  spans in gr.HTML; the 0.7 CONFIDENCE_THRESHOLD is still used to count
  "Inciertas" in the metadata bar.
- UI-04: Historical entity notes rendered as Markdown table in gr.Markdown panel.
- UI-05: Raw/Cleaned radio toggle switches Textbox content without re-running pipeline.

Security notes:
- SEC-04 (XSS prevention): html.escape() applied to both word and reason values
  from LLM-generated confidence_map before inserting into HTML span elements
  (T-03-03 mitigation per RESEARCH.md Security Domain).
- T-03-04: load_dotenv() loads GOOGLE_API_KEY from .env; key never logged or
  displayed in Gradio outputs; gr.Error messages contain only user-visible text.
"""

import html
import json
import os
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

# Step timing approximates the ~30s pipeline: spin start / done at (0,8) (8,18)
# (18,26) (26,—) seconds via CSS animation-delay. Pure CSS — no Python generator.
def _proc_step(label: str, spin_at: int, done_at: int | None) -> str:
    done_span = (
        f'<span class="ic-done" style="animation-delay:{done_at}s"></span>'
        if done_at is not None
        else ""
    )
    return (
        f'<li><span class="step-icon">'
        f'<span class="ic-pending"></span>'
        f'<span class="ic-spin" style="animation-delay:{spin_at}s"></span>'
        f"{done_span}"
        f"</span>"
        f'<span class="step-label" style="animation-delay:{spin_at}s">{label}</span></li>'
    )


PROCESSING_HTML = (
    '<div class="pal-card pal-processing-card">'
    '<div class="pal-proc-head">'
    '<div class="pal-card-title" style="margin:0">Transcribing…</div>'
    '<div class="eta">~30 s</div>'
    "</div>"
    '<div class="pal-progress-bar-wrap"><div class="pal-progress-bar"></div></div>'
    '<ul class="pal-steps">'
    + _proc_step("Image restoration", 0, 8)
    + _proc_step("Paleographic transcription", 8, 18)
    + _proc_step("Historical analysis", 18, 26)
    + _proc_step("Confidence map", 26, None)
    + "</ul></div>"
)

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
    background-image:
        radial-gradient(1100px 620px at 50% -8%, rgba(255,255,255,0.55), transparent 62%),
        radial-gradient(820px 520px at 102% 104%, rgba(174,59,44,0.05), transparent 58%);
    background-attachment: fixed;
    font-family: var(--font-sans);
    overflow-x: hidden;
}

/* Background watermark — justified faux-manuscript block, barely visible */
body::before {
    content: "In nomine Dei omnipotentis notum sit cunctis presentem cartam videntibus quod ego concedo et cognosco quod vendo vobis domos quas habeo per hereditatem patris mei anno Domini millesimo quingentesimo · sepan cuantos esta carta vieren cómo yo otorgo y conozco que vendo unas casas que tengo por herencia de mi padre que santa gloria haya · In nomine Dei omnipotentis notum sit cunctis presentem cartam videntibus quod ego concedo et cognosco quod vendo vobis domos quas habeo per hereditatem · sepan cuantos esta carta vieren cómo yo otorgo y conozco";
    position: fixed;
    top: 90px;
    left: -3%;
    right: -3%;
    bottom: 0;
    overflow: hidden;
    font-family: 'Spectral', Georgia, serif;
    font-style: italic;
    font-size: 40px;
    line-height: 2.5;
    color: rgba(35,25,15,0.038);
    text-align: justify;
    transform: rotate(-1deg);
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
.pal-header-row {
    align-items: flex-end !important;
    border-bottom: 1px solid rgba(35,25,15,0.13);
    padding: 28px 2px 18px !important;
    margin-bottom: 36px;
    gap: 24px !important;
}
.pal-header-row > .form { display: contents; }

.pal-header {
    display: flex;
    align-items: center;
    gap: 15px;
}

.pal-logo-mark {
    width: 46px;
    height: 46px;
    min-width: 46px;
    background: #23190F;
    border-radius: 11px;
    box-shadow: inset 0 -3px 0 #AE3B2C;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Spectral', Georgia, serif;
    font-size: 26px;
    font-weight: 700;
    color: #F1EADA;
    line-height: 1;
}

.pal-header-title {
    font-family: 'Spectral', Georgia, serif;
    font-size: 27px;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: #23190F;
    line-height: 1;
    margin: 0;
}

.pal-header-sub {
    font-size: 12.5px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #8A7E6B;
    font-weight: 600;
    font-family: 'Hanken Grotesk', system-ui, sans-serif;
    margin: 7px 0 0 0;
}

.pal-adk-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-family: 'IBM Plex Mono', 'Courier New', monospace;
    font-size: 12px;
    color: #6E6353;
    border: 1px solid rgba(35,25,15,0.13);
    border-radius: 999px;
    padding: 7px 13px;
    background: rgba(251,248,240,0.7);
    white-space: nowrap;
}
.pal-adk-badge .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #2F6E5A;
    display: inline-block;
}

/* Reset button inside header (design: ghost w/ border, radius 9px) */
.pal-header-row .btn-ghost {
    border-radius: 9px !important;
    padding: 9px 15px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    width: auto !important;
    align-self: flex-end;
}

/* ── Hero (initial state) ───────────────────────────────────── */
.pal-hero h1 {
    font-family: 'Spectral', Georgia, serif;
    font-weight: 600;
    font-size: 38px;
    line-height: 1.15;
    letter-spacing: -0.015em;
    margin: 34px 0 12px;
    text-align: center;
    color: #23190F;
}
.pal-hero p {
    text-align: center;
    color: #6E6353;
    font-size: 16px;
    line-height: 1.6;
    margin: 0 auto 32px;
    max-width: 480px;
    font-family: 'Hanken Grotesk', system-ui, sans-serif;
}
.pal-initial-col {
    max-width: 680px;
    margin: 0 auto;
}

/* ── Upload zone ────────────────────────────────────────────── */
.pal-upload-zone {
    border: 1.5px dashed rgba(174,59,44,0.40);
    border-radius: 16px;
    padding: 18px;
    text-align: center;
    background: rgba(174,59,44,0.025);
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
    border: none !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    gap: 0 !important;
    padding: 3px !important;
    background: rgba(35,25,15,0.06) !important;
}
.pal-seg-toggle input[type="radio"] { display: none !important; }
.pal-seg-toggle label {
    padding: 6px 14px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    font-family: 'Hanken Grotesk', system-ui, sans-serif !important;
    cursor: pointer !important;
    color: #8A7E6B !important;
    background: transparent !important;
    border: none !important;
    border-radius: 7px !important;
    margin: 0 !important;
    transition: background 0.15s, color 0.15s;
}
.pal-seg-toggle input[type="radio"]:checked + label {
    background: #FBF8F0 !important;
    color: #AE3B2C !important;
    box-shadow: 0 2px 5px -2px rgba(35,25,15,0.35);
}

/* ── Buttons ────────────────────────────────────────────────── */
.btn-primary {
    background-color: #AE3B2C !important;
    color: #FBF8F0 !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    border-radius: 11px !important;
    padding: 15px !important;
    font-family: 'Hanken Grotesk', system-ui, sans-serif !important;
    box-shadow: 0 14px 26px -12px rgba(174,59,44,0.8) !important;
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

/* ── Results top bar — file status + metadata boxes ─────────── */
.pal-meta-bar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 14px 22px;
    margin-bottom: 24px;
    padding-bottom: 22px;
    border-bottom: 1px solid rgba(35,25,15,0.1);
}
.pal-meta-file { display: flex; align-items: center; gap: 12px; }
.pal-meta-file .fname { font-weight: 600; font-size: 14px; color: #23190F; }
.pal-meta-file .fdone {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12.5px;
    color: #2F6E5A;
    font-weight: 600;
    margin-top: 3px;
}
.pal-meta-spacer { flex: 1; }
.pal-meta-boxes { display: flex; flex-wrap: wrap; gap: 9px; }
.pal-meta-box {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 8px 14px;
    border: 1px solid rgba(35,25,15,0.12);
    border-radius: 10px;
    background: rgba(251,248,240,0.6);
    min-width: 74px;
}
.pal-meta-box .mlabel {
    font-size: 10.5px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #A99C86;
    font-weight: 600;
}
.pal-meta-box .mvalue {
    font-family: 'IBM Plex Mono', 'Courier New', monospace;
    font-size: 15px;
    font-weight: 500;
    color: #23190F;
}
.pal-meta-box .mvalue.warn { color: #AE3B2C; }
.pal-meta-box .mvalue.good { color: #2F6E5A; }

/* ── Status / completion text ───────────────────────────────── */
.pal-status {
    font-size: 13px;
    color: #2F6E5A;
    font-family: 'Hanken Grotesk', system-ui, sans-serif;
    min-height: 20px;
}

/* ── Section headers with accent bar ────────────────────────── */
.pal-sec-head {
    display: flex;
    align-items: center;
    gap: 10px;
    justify-content: flex-start;
    margin: 0 0 14px 0;
}
.pal-sec-head .bar {
    width: 6px;
    height: 18px;
    border-radius: 2px;
    display: inline-block;
    flex: none;
}
.pal-sec-head h2 {
    font-family: 'Spectral', Georgia, serif;
    font-size: 19px;
    font-weight: 600;
    margin: 0;
    color: #23190F;
}
.pal-sec-head .count {
    margin-left: auto;
    font-family: 'IBM Plex Mono', 'Courier New', monospace;
    font-size: 12px;
    color: #8A7E6B;
}

/* ── Transcription text modes ───────────────────────────────── */
.pal-transcription-card textarea {
    font-family: 'Spectral', Georgia, serif !important;
    font-size: 18px !important;
    line-height: 1.95 !important;
    color: #2A2014 !important;
    background: transparent !important;
    border: none !important;
}
/* Raw (Original) view — monospace diplomatic transcription */
.pal-transcription-card.pal-raw-mode textarea {
    font-family: 'IBM Plex Mono', 'Courier New', monospace !important;
    font-size: 13.5px !important;
    color: #6E6353 !important;
    white-space: pre-wrap !important;
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
.pal-proc-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 18px;
}
.pal-proc-head .eta {
    font-family: 'IBM Plex Mono', 'Courier New', monospace;
    font-size: 13px;
    color: #AE3B2C;
    font-weight: 500;
}
.pal-steps {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
}
.pal-steps li {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 9px 0;
    font-size: 15px;
    font-weight: 500;
    font-family: 'Hanken Grotesk', system-ui, sans-serif;
    color: #6E6353;
}
/* Step label darkens when its stage starts (delay set inline per step).
   Base color is already legible (#6E6353) so the label is readable even if
   the animation never fires (display:none while hidden can suppress it). */
.pal-steps li .step-label {
    color: #6E6353;
    animation: pal-step-on 0.3s forwards;
    animation-delay: inherit;
}
@keyframes pal-step-on { to { color: #23190F; } }

/* 3-state icon stack: pending dot → spinner → done check.
   Later layers appear over earlier ones via animation-delay (inline). */
.step-icon {
    position: relative;
    width: 28px;
    height: 28px;
    flex-shrink: 0;
}
.step-icon > span {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}
.ic-pending::before {
    content: "";
    width: 11px;
    height: 11px;
    border-radius: 50%;
    border: 2px solid rgba(35,25,15,0.18);
}
.ic-spin {
    opacity: 0;
    animation: pal-appear 0.2s forwards;
    animation-delay: inherit;
}
.ic-spin::before {
    content: "";
    width: 20px;
    height: 20px;
    border-radius: 50%;
    border: 2.5px solid rgba(35,25,15,0.15);
    border-top-color: #AE3B2C;
    animation: pal-spin 0.7s linear infinite;
    background: #FBF8F0;
}
.ic-done {
    opacity: 0;
    animation: pal-appear 0.2s forwards;
    animation-delay: inherit;
}
.ic-done::before {
    content: "✓";
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #2F6E5A;
    color: #FBF8F0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
}
@keyframes pal-appear { to { opacity: 1; } }
@keyframes pal-spin { to { transform: rotate(360deg); } }

/* ── File upload — clear/remove button visibility ───────────── */
.pal-upload-zone button,
.pal-upload-zone .clear-button,
.pal-upload-zone [aria-label="Remove"],
.pal-upload-zone [aria-label="Clear"] {
    color: #AE3B2C !important;
    background: transparent !important;
    border: none !important;
    opacity: 1 !important;
    visibility: visible !important;
}
.pal-upload-zone svg { stroke: #AE3B2C !important; fill: none !important; }

/* ── Gradio footer — hide locale-dependent links ────────────── */
footer { display: none !important; }

/* ── Settings / API modal — readable on parchment ───────────── */
dialog, .gradio-modal, [role="dialog"] {
    background: #FBF8F0 !important;
    color: #23190F !important;
    border: 1px solid rgba(35,25,15,0.18) !important;
    border-radius: 12px !important;
}
dialog label, [role="dialog"] label,
dialog p, [role="dialog"] p,
dialog h3, [role="dialog"] h3,
dialog span, [role="dialog"] span {
    color: #23190F !important;
}
dialog input, [role="dialog"] input,
dialog select, [role="dialog"] select {
    background: #F1EADA !important;
    color: #23190F !important;
    border: 1px solid rgba(35,25,15,0.2) !important;
}
"""


def render_confidence_html(word_scores: list[dict]) -> str:
    """Convert confidence_map word list to HTML with uncertainty highlights.

    Words scoring below HIGHLIGHT_THRESHOLD (0.95) are wrapped in styled
    <span> elements with an amber background and a hover tooltip showing
    score and reason (D-14, D-15, D-16).

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
            "(confidence map will appear after processing)"
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
            # Alpha formula from design spec: min(0.62, (1-score)*1.05*0.85) + 0.05
            alpha = round(min(0.62, (1 - score) * 1.05 * 0.85) + 0.05, 3)
            span = (
                f'<span style="'
                f"background-color: rgba(217,149,46,{alpha}); "
                f"box-shadow: inset 0 -2px 0 rgba(174,59,44,0.42); "
                f"padding: 1px 3px; "
                f"border-radius: 4px; "
                f'cursor: help;" '
                f'title="score: {score:.2f} | {escaped_reason}">'
                f"{escaped_word}</span>"
            )
            parts.append(span)
        else:
            parts.append(escaped_word)

    body = " ".join(parts)
    hint = (
        '<div style="min-height:20px;font-size:13px;font-weight:500;color:#8A7E6B;'
        "font-family:'Hanken Grotesk',system-ui,sans-serif;margin-bottom:12px\">"
        "Hover over a highlighted word to see its confidence score."
        "</div>"
    )
    legend = (
        '<div style="display:flex;align-items:center;gap:10px;font-size:11.5px;'
        "color:#8A7E6B;font-weight:600;font-family:'Hanken Grotesk',system-ui,sans-serif;"
        'margin-top:16px;padding-top:14px;border-top:1px solid rgba(35,25,15,0.09)">'
        "<span>Certain</span>"
        '<div style="flex:1;height:8px;border-radius:99px;'
        "background:linear-gradient(90deg, rgba(217,149,46,0.04), rgba(217,149,46,0.85));"
        'box-shadow:inset 0 -2px 0 rgba(174,59,44,0.3)"></div>'
        "<span>Uncertain</span></div>"
    )
    return (
        f"{hint}"
        f'<div style="font-size:16px;line-height:2.05;max-height:300px;overflow:auto;'
        f"font-family:'Spectral',Georgia,serif;color:#3A2E20\">{body}</div>"
        f"{legend}"
    )


_TYPE_COLORS: dict[str, str] = {
    "Person":      "#AE3B2C",
    "Persona":     "#AE3B2C",
    "Place":       "#2F6E5A",
    "Lugar":       "#2F6E5A",
    "Date":        "#B07A1E",
    "Fecha":       "#B07A1E",
    "Document":    "#4A5A86",
    "Documento":   "#4A5A86",
    "Institution": "#4A5A86",
    "Institución": "#4A5A86",
}


def render_context_cards(context_notes: list[dict]) -> str:
    """Convert context_notes list to an HTML card grid (replaces render_context_table).

    Returns a div.pal-notes-grid containing one .pal-note-card per entity.
    html.escape() applied to all LLM-generated strings (SEC-04, T-03-03).

    Args:
        context_notes: List of entity dicts from the context agent.

    Returns:
        HTML string with the notes grid, or a no-entities message.
    """
    header_tpl = (
        '<div class="pal-sec-head">'
        '<span class="bar" style="background:#4A5A86"></span>'
        "<h2>Historical Notes</h2>"
        '<span class="count">{count} entities</span>'
        "</div>"
    )

    if not context_notes:
        return (
            header_tpl.format(count=0)
            + "<p style='color:#6E6353;font-family:Hanken Grotesk,system-ui,sans-serif;"
            "font-size:14px;margin:0'>No historical entities found.</p>"
        )

    cards: list[str] = []
    for note in context_notes:
        if not isinstance(note, dict):
            continue  # skip null / non-dict elements from LLM (CR-03)
        entity = html.escape(str(note.get("entity", "")))
        entity_type = html.escape(str(note.get("type", "")))
        description = html.escape(str(note.get("description", "")))
        color = _TYPE_COLORS.get(entity_type, "#4A5A86")
        # Inline alpha on border/bg to avoid CSS custom property injection risk
        bg_color = f"{color}1f"
        border_color = f"{color}40"
        cards.append(
            f'<div class="pal-note-card" style="border:1px solid rgba(35,25,15,0.11);'
            f'border-radius:12px;background:rgba(247,242,231,0.5)">'
            f'<div class="pal-note-header">'
            f'<span class="pal-note-entity" style="font-size:16.5px;line-height:1.2">{entity}</span>'
            f'<span class="pal-note-type" style="background:{bg_color};color:{color};'
            f"border:1px solid {border_color};font-family:'IBM Plex Mono',monospace;"
            f"font-size:10.5px;font-weight:500;letter-spacing:0.04em;"
            f'text-transform:uppercase;padding:3px 8px;border-radius:6px">{entity_type}</span>'
            f"</div>"
            f'<p class="pal-note-desc" style="font-size:13.5px">{description}</p>'
            f"</div>"
        )

    inner = "".join(cards)
    return (
        header_tpl.format(count=len(cards))
        + f'<div class="pal-notes-grid">{inner}</div>'
    )


def render_metadata_bar(
    confidence_list: list[dict],
    cleaned_text: str,
    elapsed: float,
    filename: str = "",
) -> str:
    """Render the results top bar: file status + 5 metadata boxes.

    Boxes: Tiempo · Modelo · Palabras · Inciertas · Confianza — uppercase
    label over IBM Plex Mono value (design spec). Uses CONFIDENCE_THRESHOLD
    (0.7) to count uncertain words; average score shown as Confianza %.

    Args:
        confidence_list: Word-score dicts from confidence_map.
        cleaned_text: Cleaned transcription text (for word count).
        elapsed: Pipeline wall-clock seconds.
        filename: Uploaded file name for the status row (html-escaped).

    Returns:
        HTML string with div.pal-meta-bar (file row + div.pal-meta-boxes).
    """
    model_label = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")

    word_count = len(cleaned_text.split()) if cleaned_text.strip() else 0

    uncertain_count = 0
    total_score = 0.0
    valid_count = 0
    for entry in confidence_list:
        if not isinstance(entry, dict):
            continue
        score_raw = entry.get("score")
        try:
            score = float(score_raw) if score_raw is not None else 1.0
        except (TypeError, ValueError):
            score = 1.0
        if score < CONFIDENCE_THRESHOLD:
            uncertain_count += 1
        total_score += score
        valid_count += 1

    avg_conf = (total_score / valid_count * 100) if valid_count else 100.0
    elapsed_str = f"{elapsed:.0f} s" if elapsed < 60 else f"{elapsed / 60:.1f} min"

    boxes = [
        ("Time", elapsed_str, ""),
        ("Model", html.escape(model_label), ""),
        ("Words", str(word_count), ""),
        ("Uncertain", str(uncertain_count), " warn"),
        ("Confidence", f"{avg_conf:.0f}%", " good"),
    ]
    boxes_html = "".join(
        f'<div class="pal-meta-box"><div class="mlabel">{label}</div>'
        f'<div class="mvalue{cls}">{value}</div></div>'
        for label, value, cls in boxes
    )
    file_html = (
        '<div class="pal-meta-file"><div>'
        f'<div class="fname">{html.escape(filename)}</div>'
        '<div class="fdone">✓ Processing complete</div>'
        "</div></div>"
    )
    return (
        f'<div class="pal-meta-bar">{file_html}'
        f'<div class="pal-meta-spacer"></div>'
        f'<div class="pal-meta-boxes">{boxes_html}</div></div>'
    )


async def transcribe_manuscript(file_path: str) -> tuple:
    """Gradio click handler: validate image, run pipeline, return UI outputs.

    Accepts a plain str file path from gr.File(type="filepath") in Gradio 5+/6+.
    Does NOT use a .name attribute — file_path is already a str (RESEARCH.md Pitfall 4).

    Returns a 12-tuple mapped to Gradio outputs (outputs_full):
        (transcription_box, raw_state, cleaned_state, notes_md, confidence_html,
         transcription_section, confidence_section, notes_section, reset_btn,
         status_md, processing_section, initial_section)

    Error handling (D-11): raises gr.Error() for both intake failures and pipeline
    errors. Gradio displays these as a red pop-up banner — no broken UI state.

    Args:
        file_path: Path string returned by gr.File(type="filepath").

    Returns:
        12-tuple matching outputs_full (see component index comments below).
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

    # WR-02: handler is now async; await run_pipeline() directly.
    # Gradio 4+ accepts coroutines as fn= arguments natively, so asyncio.run()
    # is no longer needed and would raise RuntimeError in embedded-loop contexts.
    start_time = time.time()
    result = await run_pipeline(clean_bytes, mime_type, filename)
    elapsed = time.time() - start_time

    # D-11 (UI errors): surface pipeline errors as gr.Error pop-up.
    if result.get("status") == "error":
        errors = result.get("errors", [])
        msg = (
            "; ".join(errors)
            if errors
            else "Processing failed. Verify the file is valid and try again."
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
        cleaned_text,                               # 0 transcription_box
        raw_text,                                   # 1 raw_state
        cleaned_text,                               # 2 cleaned_state
        render_context_cards(context_list),         # 3 notes_md (gr.HTML)
        render_confidence_html(confidence_list),    # 4 confidence_html
        gr.update(visible=True),                    # 5 transcription_section
        gr.update(visible=True),                    # 6 confidence_section
        gr.update(visible=True),                    # 7 notes_section
        gr.update(visible=True),                    # 8 reset_btn
        render_metadata_bar(                        # 9 status_md (gr.HTML)
            confidence_list, cleaned_text, elapsed, filename
        ),
        gr.update(visible=False),                   # 10 processing_section
        gr.update(visible=False),                   # 11 initial_section (hero+upload)
        True,                                       # 12 pipeline_success
    )


def toggle_view(view: str, raw: str, cleaned: str) -> str:
    """Switch Textbox content between raw and cleaned transcription texts.

    Pure function; no side effects; no pipeline re-run (D-08, UI-05).

    Args:
        view: Selected radio value ("Original" or "Limpiada").
        raw: Raw transcription text from raw_state.
        cleaned: Cleaned transcription text from cleaned_state.

    Returns:
        The appropriate text string for the Transcription Textbox.
    """
    return raw if view == "Original" else cleaned  # choices: "Cleaned" | "Original"


def reset_manuscript() -> tuple:
    """Reset all UI state and hide result panels. Returns 12-tuple matching outputs_full."""
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
        gr.update(visible=True),     # initial_section (hero+upload back)
        False,                       # pipeline_success reset
    )


def show_processing() -> tuple:
    """Show processing card and hide hero/upload. Called before transcribe_manuscript."""
    return gr.update(visible=True), gr.update(visible=False)


def hide_processing(success: bool) -> tuple:
    """Hide processing card; restore initial_section only on error.

    .then() fires regardless of gr.Error, so the spinner always clears.
    On gr.Error, transcribe_manuscript outputs are NOT applied — pipeline_success
    stays False and initial_section stays hidden. We restore it here.
    On success, pipeline_success=True and initial_section is already hidden
    by transcribe_manuscript — we leave it hidden.
    """
    return gr.update(visible=False), gr.update(visible=not success)


# Gradio 6: css moved from the gr.Blocks constructor to launch() —
# passed as css=CUSTOM_CSS in demo.launch() below (title remains a
# valid Blocks constructor parameter).
with gr.Blocks(title="Palimpsest — Manuscript Transcription") as demo:
    with gr.Row(elem_classes=["pal-header-row"]):
        gr.HTML("""
<div class="pal-header">
  <div class="pal-logo-mark">P</div>
  <div>
    <div class="pal-header-title">Palimpsest</div>
    <div class="pal-header-sub">Manuscript Transcription</div>
  </div>
</div>
""")
        gr.HTML(
            '<div style="display:flex;justify-content:flex-end;align-items:flex-end;height:100%">'
            '<span class="pal-adk-badge"><span class="dot"></span>ADK · 4 agents</span></div>'
        )
        reset_btn = gr.Button(
            "New transcription", visible=False, elem_classes=["btn-ghost"], scale=0
        )

    raw_state = gr.State(value="")
    cleaned_state = gr.State(value="")
    pipeline_success = gr.State(value=False)  # True on success; stays False on gr.Error (output not applied)

    with gr.Column(elem_classes=["pal-initial-col"]) as initial_section:
        gr.HTML("""
<div class="pal-hero">
  <h1>Upload a manuscript to transcribe</h1>
  <p>We restore the image, transcribe the handwriting, annotate the historical
  context, and measure the confidence of every word.</p>
</div>
""")
        with gr.Column(elem_classes=["pal-upload-zone"]):
            file_input = gr.File(
                label="Upload manuscript image",
                file_types=[".jpg", ".jpeg", ".png"],
                file_count="single",
                type="filepath",
            )
        submit_btn = gr.Button("Transcribe manuscript", variant="primary", elem_classes=["btn-primary"], interactive=False)

    processing_section = gr.HTML(value=PROCESSING_HTML, visible=False)

    status_md = gr.HTML("", elem_classes=["pal-status"])

    with gr.Column(elem_classes=["pal-results-grid"]):
        with gr.Column(visible=False, elem_classes=["pal-card", "pal-transcription-card"]) as transcription_section:
            gr.HTML(
                '<div class="pal-sec-head"><span class="bar" style="background:#AE3B2C"></span>'
                "<h2>Transcription</h2></div>"
            )
            view_toggle = gr.Radio(label="View:", choices=["Cleaned", "Original"], value="Cleaned", elem_classes=["pal-seg-toggle"])
            copy_btn = gr.Button(
                "Copy",
                elem_classes=["btn-ghost"],
                scale=0,
                size="sm",
            )
            transcription_box = gr.Textbox(
                label="",
                interactive=False,
                lines=15,
                placeholder="(transcription will appear here)",
            )

        with gr.Column(visible=False, elem_classes=["pal-card", "pal-confidence-card"]) as confidence_section:
            gr.HTML(
                '<div class="pal-sec-head"><span class="bar" style="background:#D9952E"></span>'
                "<h2>Confidence Map</h2></div>"
            )
            confidence_html = gr.HTML(value="")

        with gr.Column(visible=False, elem_classes=["pal-card", "pal-notes-card"]) as notes_section:
            # Section header (accent bar + counter) is rendered inside notes_md
            # by render_context_cards() — it needs the entity count.
            notes_md = gr.HTML(value="")

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
        processing_section,     # 10
        initial_section,        # 11  hero + upload zone (hidden in results)
        pipeline_success,       # 12  True on success; stays False on gr.Error
    ]

    file_input.change(
        fn=lambda f: gr.update(interactive=f is not None),
        inputs=[file_input],
        outputs=[submit_btn],
    )

    submit_btn.click(
        fn=show_processing,
        inputs=[],
        outputs=[processing_section, initial_section],
        show_progress="hidden",
    ).then(
        fn=transcribe_manuscript,
        inputs=[file_input],
        outputs=outputs_full,
        # Suppress Gradio's native loading overlay on the outputs — our custom
        # PROCESSING_HTML card is the single source of processing feedback.
        # Without this, users see two processing indicators (ours + Gradio's).
        show_progress="hidden",
    ).then(
        # Unconditional cleanup: .then() fires even when transcribe_manuscript
        # raises gr.Error, so the processing card never stays stuck visible.
        # pipeline_success=False on error (gr.Error skips output application),
        # so hide_processing restores initial_section only on the error path.
        fn=hide_processing,
        inputs=[pipeline_success],
        outputs=[processing_section, initial_section],
    )

    reset_btn.click(
        fn=reset_manuscript,
        inputs=[],
        outputs=outputs_full,
    ).then(
        fn=lambda: (None, gr.update(interactive=False)),
        inputs=[],
        outputs=[file_input, submit_btn],
    )

    view_toggle.change(
        fn=toggle_view,
        inputs=[view_toggle, raw_state, cleaned_state],
        outputs=[transcription_box],
        # Client-side: swap the card into monospace "diplomatic" styling for
        # the Original view (design spec). js runs before fn and must return
        # the inputs array unchanged.
        js=(
            "(v, r, c) => { "
            "const card = document.querySelector('.pal-transcription-card'); "
            "if (card) card.classList.toggle('pal-raw-mode', v === 'Original'); "  # "Original" matches choice value
            "return [v, r, c]; }"
        ),
    )

    copy_btn.click(
        fn=None,
        inputs=None,
        outputs=None,
        js=(
            "() => { "
            "const ta = document.querySelector('.pal-transcription-card textarea'); "
            "if (ta) navigator.clipboard.writeText(ta.value || '').catch(() => {}); "
            "const btns = document.querySelectorAll('.pal-transcription-card button'); "
            "for (const b of btns) { "
            "  if (b.textContent.trim() === 'Copy' || b.textContent.trim() === 'Copied') { "
            "    const orig = 'Copy'; b.textContent = 'Copied'; "
            "    setTimeout(() => { b.textContent = orig; }, 1500); break; } } "
            "}"
        ),
    )


# ---------------------------------------------------------------------------
# Entry point guard (D-12): enables `python -m palimpsest.app`
# Do NOT call demo.launch() unconditionally — that would prevent import testing.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Pass theme and css here in Gradio 6.x (both moved from the gr.Blocks
    # constructor in 6.0 — launch() accepts css/css_paths in 6.19.0).
    # server_name="0.0.0.0" required for Docker — default 127.0.0.1 is not
    # reachable outside the container even with -p 7860:7860 port mapping.
    # server_port reads PORT env var (Cloud Run / Oracle VM convention).
    demo.launch(
        theme=gr.themes.Soft(),
        css=CUSTOM_CSS,
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
    )

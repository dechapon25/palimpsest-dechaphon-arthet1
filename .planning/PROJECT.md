# Palimpsest

## What This Is

Palimpsest is a multi-agent system that receives a scanned historical handwritten document, transcribes the cursive script using Gemini 3 Pro vision, cleans and normalizes the text, enriches it with historical context via an MCP server, and marks passages with low confidence. It is built as a Kaggle AI Agents Capstone competition entry targeting the Freestyle track.

## Core Value

A researcher uploads a scan of a difficult historical manuscript and gets back a readable, enriched transcription with uncertainty markers — in one pipeline, without paleography expertise.

## Business Context

- **Customer**: Historians, genealogists, archivists, digital humanities researchers
- **Revenue model**: N/A — competition entry / portfolio project
- **Success metric**: Judging score (70 pts implementation + 30 pts pitch); deadline July 6 2026
- **Strategy notes**: Demonstrate ≥3 course concepts: multi-agent ADK, MCP server, security features. Aim for Freestyle track top-3.

## Requirements

### Validated

- ✓ User can upload a scanned image (JPG/PNG) — Phase 01
- ✓ System validates file type and size; strips EXIF metadata — Phase 01
- ✓ Orchestrator agent coordinates full pipeline via ADK — Phase 02
- ✓ Transcription agent sends image to Gemini 3 Pro and returns raw text — Phase 02
- ✓ Cleaning agent expands abbreviations, normalizes archaic spelling — Phase 02
- ✓ Context agent queries MCP server to resolve named entities — Phase 02
- ✓ MCP server exposes lookup_entity, normalize_date, expand_abbreviation, place_context tools — Phase 02
- ✓ Verification agent scores confidence per word, marks doubtful words — Phase 03
- ✓ Output includes: clean transcription, historical notes, confidence map — Phase 03
- ✓ Gradio UI for demo (Bento Grid + Glassmorphism wizard) — Phase 03 + Phase 05
- ✓ Cloud Run deploy (Oracle VM) with Docker + FastMCP stdio — Phase 04

### Active

- [ ] README with architecture diagram, setup instructions, env-var docs (no credentials in repo)
- [ ] Kaggle Writeup drafted (≤2500 words, Freestyle track, cover image, YouTube video link)
- [ ] YouTube video recorded (≤5 min: problem, agents rationale, architecture, demo, build)

### Out of Scope

- PDF multi-page support — scope risk for solo 16-day timeline; single-image MVP is sufficient for demo
- OAuth / user accounts — no auth needed; local or Cloud Run stateless demo
- Gemini Flash for cursive — failed 3/4 test pages; only Pro for handwriting
- Paid/proprietary data sources for MCP — Wikidata/Wikipedia free tier sufficient
- Physical document scanning — all test data from public domain digital archives (PARES, LoC, Archive.org)

## Context

- **Competition**: Kaggle "AI Agents: Intensive Vibe Coding Capstone Project" with Google. Deadline 2026-07-06 23:59 PT. Individual submission.
- **Track**: Freestyle (manuscript decoder explicitly cited as example in rules).
- **Alternative track considered**: "Agents for Good" (supporting arts/literature/education) — judges may move winners between tracks.
- **Course concepts to demonstrate**: Multi-agent system (ADK) in code + MCP server in code + security features in code/video. Optionally: deployability (Cloud Run) and agent skills (cleaning skill packaged as Agent Skill).
- **Model config for transcription** (critical for quality):
  - `maxOutputTokens: 65536` — default 8192 silently truncates long documents
  - `temperature: 0.1` — reduces variance on proper nouns and dates
  - `thinkingBudget: 128` — lower is better for transcription (counterintuitive)
- **Known Gemini failure modes** (justify verification agent): skips lines, substitutes words, degrades on marginalia and interlinear notes.
- **MCP source decision open**: Wikidata/Wikipedia (broadest, free, multilingual) vs. domain-specific (Chronicling America for English historical press). Lean toward Wikidata.
- **Test data**: public domain scans from PARES (Spanish 18th-19th c.), Library of Congress, British Library, Archive.org. Download 3-5 varied samples Day 1 (easy cursive, hard cursive, marginalia).
- **Frontend**: Gradio (fast to build, works well for file-upload demos, easy Cloud Run deploy).
- **Deploy**: Cloud Run container (optional but adds "deployability" points for judging).
- **Video/Writeup language**: English (international judges).
- **Confidence UI**: color-coded highlights on uncertain words (heatmap or inline spans).

## Constraints

- **Timeline**: 16 days total (2026-06-21 to 2026-07-06). Solo developer. All submission artifacts by Day 14 (2-day buffer).
- **Tech stack**: Python · ADK · Gemini 3 Pro vision · FastMCP · Gradio · (optional) Cloud Run
- **Security**: Zero credentials in repo. Use env vars. Document in README what keys are needed.
- **Model**: Gemini 3 Pro only for cursive. No Flash for handwriting.
- **Token limits**: Set maxOutputTokens=65536 explicitly or transcription silently truncates.
- **Word limit**: Kaggle Writeup ≤2500 words. Penalty for exceeding.
- **Video**: YouTube, ≤5 minutes. Must cover problem, agents rationale, architecture, demo, build.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Multi-agent ADK pipeline (not single prompt) | Separation of concerns: transcribe, clean, contextualize, verify are distinct responsibilities. Justifies agent architecture vs. chatbot. | — Pending |
| Gemini 3 Pro for vision | Best market performer on historical cursive (tested). Native ADK/Google ecosystem. | — Pending |
| FastMCP for MCP server | Python-native, minimal overhead, matches team stack | — Pending |
| Gradio for frontend | Fastest file-upload demo, deploys to Cloud Run, well-known to judges | — Pending |
| Freestyle track (not Agents for Good) | Manuscript decoder explicitly cited as Freestyle example. Lower competition density than Good/Business. | — Pending |
| English for writeup/video | International judges; broader audience | — Pending |
| No PDF multi-page in v1 | Scope risk; single image sufficient for demo quality and judging | — Pending |
| Wikidata as MCP source | Free, multilingual, broad coverage, no API key needed beyond rate limits | — Pending (Q3 open) |
| Cleaning agent packaged as Agent Skill | Demonstrates "agent skills" course concept; reusable; shown in video | — Pending |

## Open Questions

- **Q1** — Demo language: Spanish docs (PARES) or English (LoC)? Affects narrative for judges.
- **Q3** — MCP exact tools and source: Wikidata only, or mix with Chronicling America?
- **Q5** — Deploy to Cloud Run (real endpoint) or repo only? Real deploy adds points but costs time.
- **Q7** — Gemini model version: `gemini-3-pro` stable or `gemini-3.1-pro-preview`?
- **Q10** — Confidence UI: color heatmap, inline brackets, or margin notes?
- **Q11** — Enrichment scope: named entities only, or also date modernization and spelling translation?

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-21 after initialization*

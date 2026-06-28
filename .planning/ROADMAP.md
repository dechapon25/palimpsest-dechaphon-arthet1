# Roadmap: Palimpsest

## Overview

Palimpsest is built in four phases over 16 days. Phase 1 validates the core pipeline end-to-end with a real manuscript image before investing in the full agent graph. Phase 2 wires in the complete multi-agent system: cleaning as an Agent Skill, the MCP server with four tools, and the context agent. Phase 3 adds the verification layer and the Gradio demo UI. Phase 4 containerizes, deploys, and produces all Kaggle submission artifacts. All submission artifacts must be ready by Day 14 (2026-07-04), leaving a 2-day buffer before the July 6 deadline.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: MVP Linear Pipeline** - Security intake + orchestrator + transcription agent running end-to-end on a real test image (completed 2026-06-21)
- [x] **Phase 2: Full Multi-Agent System** - Cleaning agent (Agent Skill) + MCP server (4 tools) + context agent wired into orchestrator (completed 2026-06-24)
- [x] **Phase 3: Verification + Gradio UI** - Confidence scoring, uncertainty highlights, and full Gradio demo interface (completed 2026-06-25)
- [ ] **Phase 4: Deploy + Submission Artifacts** - Cloud Run containerization, README, Kaggle Writeup, and video scaffold
- [ ] **Phase 5: UI Wizard Redesign** - Progressive-reveal wizard with Bento Grid + Glassmorphism style

## Phase Details

### Phase 1: MVP Linear Pipeline

**Goal**: A researcher can upload a manuscript image and receive raw transcribed text through a validated, security-hardened pipeline running end-to-end on a real test document.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: SEC-01, SEC-02, SEC-03, SEC-04, ORC-01, ORC-02, ORC-03, TRS-01, TRS-02, TRS-03
**Success Criteria** (what must be TRUE):

  1. A JPG or PNG image uploaded to the pipeline returns transcribed text from Gemini 3 Pro with no manual intervention
  2. Files with wrong type (PDF, DOCX) or exceeding 20 MB are rejected before reaching Gemini, and EXIF metadata is stripped from accepted images
  3. Transcribed text containing instruction-like phrases is treated as data and does not alter downstream agent behavior
  4. When Gemini returns a partial transcription (skipped lines), the orchestrator surfaces the partial result to the caller without crashing
  5. The orchestrator correctly sequences intake, transcription, and result assembly, surfacing any agent error with a descriptive message

**Plans**: 2/2 plans complete

Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Project scaffold + security intake (SEC-01 through SEC-04)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Transcription agent + ADK orchestrator + CLI runner (end-to-end)

### Phase 2: Full Multi-Agent System

**Goal**: The pipeline gains a cleaning agent packaged as a reusable Agent Skill, a FastMCP server with four historical-context tools, and a context agent that queries those tools to enrich named entities in the cleaned text.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: CLN-01, CLN-02, CLN-03, MCP-01, MCP-02, MCP-03, MCP-04, MCP-05, MCP-06, CTX-01, CTX-02, CTX-03
**Success Criteria** (what must be TRUE):

  1. Raw Gemini output passes through the cleaning agent and emerges with expanded paleographic abbreviations and normalized archaic spelling
  2. The cleaning agent is importable and callable as a standalone ADK Agent Skill (not only as an inline pipeline step)
  3. The FastMCP server responds to all four tool calls — `lookup_entity`, `normalize_date`, `expand_abbreviation`, `place_context` — using Wikidata/Wikipedia with no API key required
  4. Named entities (persons, places, dates) in the cleaned text are identified and resolved through MCP tools, returning structured historical notes

**Plans**: 2/2 plans complete

Plans:
**Wave 1**

- [x] 02-01-PLAN.md — Cleaning agent (AgentTool) + pipeline wiring (CLN-01, CLN-02, CLN-03)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02-PLAN.md — FastMCP server (4 tools) + context agent + pipeline wiring (MCP-01 through MCP-06, CTX-01 through CTX-03)

**UI hint**: yes

### Phase 3: Verification + Gradio UI

**Goal**: The system scores transcription confidence per passage, marks uncertain words with highlights, and presents all results (clean transcription, historical notes, raw/clean toggle, confidence map) through a Gradio demo interface.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: VER-01, VER-02, VER-03, UI-01, UI-02, UI-03, UI-04, UI-05
**Success Criteria** (what must be TRUE):

  1. Every passage in the transcription output carries a confidence score, and individual low-confidence words or spans are explicitly flagged in the output
  2. A researcher can upload an image in the Gradio interface and see the clean transcription, historical notes panel, and color-coded uncertainty highlights — all without running code directly
  3. The raw/clean toggle in the Gradio UI lets the researcher compare the original Gemini output against the cleaned version side by side
  4. The confidence output is structured (JSON or equivalent) so the UI can render highlights programmatically — not as prose

**Plans**: 3/3 plans complete

Plans:
**Wave 1**

- [x] 03-01-PLAN.md — Verification agent (LlmAgent/Flash, confidence_map) + orchestrator extension (VER-01, VER-02, VER-03)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-02-PLAN.md — Gradio Blocks demo interface with confidence highlights, raw/clean toggle, historical notes (UI-01 through UI-05)

**Wave 3** *(gap closure — blocked on Wave 2 completion)*

- [x] 03-03-PLAN.md — Gap closure: max_output_tokens=65536 in verification.py (CR-03) + json.loads try/except in app.py (CR-02)

**UI hint**: yes

### Phase 4: Deploy + Submission Artifacts

**Goal**: The application runs as a publicly accessible Cloud Run container; the repo contains no credentials; and all Kaggle submission artifacts (README, Writeup, video) are complete and ready to submit by Day 14.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: DEP-01, DEP-02, DEP-03, DEP-04, DOC-01, DOC-02, DOC-03, DOC-04
**Success Criteria** (what must be TRUE):

  1. `docker build` succeeds from a clean clone, and the container starts the Gradio app without secrets hard-coded in any file in the repo
  2. The Cloud Run endpoint is publicly reachable and processes a manuscript image upload end-to-end
  3. The README documents the architecture, required environment variables (names only), and setup steps sufficient for a judge to reproduce the demo locally
  4. The Kaggle Writeup is complete (≤2500 words), has a cover image, and contains the YouTube video link; the video (≤5 min) covers problem, architecture, demo, and agent rationale

**Plans**: 2/3 plans executed

Plans:
**Wave 1**

- [x] 04-01-PLAN.md — Dockerfile + .dockerignore + .env.example + app.py launch fix + local Docker smoke test (DEP-01, DEP-03, DEP-04)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 04-02-PLAN.md — Transfer image to Oracle VM + configure both firewall layers + deploy container + public access verification (DEP-02)

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 04-03-PLAN.md — README architecture update + inline code comments/docstrings + Kaggle Writeup draft + YouTube video + Kaggle submission (DOC-01, DOC-02, DOC-03, DOC-04)

### Phase 5: UI Wizard Redesign

**Goal**: Replace the current single-page Gradio layout with a progressive-reveal wizard: one upload screen, then results that appear incrementally as each pipeline stage completes (raw transcription → cleaned → historical notes → confidence map). Visual style: Bento Grid + Glassmorphism using custom CSS in gr.Blocks.
**Depends on**: Phase 4
**Requirements**: UI-WIZ-01, UI-WIZ-02, UI-WIZ-03, UI-WIZ-04
**Success Criteria** (what must be TRUE):

  1. Upload screen shows only the file picker and submit button — no result panels visible until processing starts
  2. Results appear incrementally in order: raw transcription first, then cleaned text replaces/complements it, then historical notes, then confidence map
  3. Visual style is Bento Grid + Glassmorphism (frosted-glass cards, dark or semi-dark background, subtle amber/gold accent color matching manuscript theme)
  4. "New transcription" button resets UI to initial state without page reload
  5. App still runs via `python -m palimpsest.app` and Docker deploy unchanged

**Plans**: 0/0 plans

**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. MVP Linear Pipeline | 2/2 | Complete    | 2026-06-21 |
| 2. Full Multi-Agent System | 2/2 | Complete    | 2026-06-24 |
| 3. Verification + Gradio UI | 3/3 | Complete    | 2026-06-25 |
| 4. Deploy + Submission Artifacts | 2/3 | In Progress|  |
| 5. UI Wizard Redesign | 0/? | Planned |  |

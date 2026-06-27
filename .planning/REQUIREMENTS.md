# Requirements: Palimpsest

**Defined:** 2026-06-21
**Core Value:** A researcher uploads a scan of a difficult historical manuscript and gets back a readable, enriched transcription with uncertainty markers — in one pipeline, without paleography expertise.

## v1 Requirements

### Security & Intake

- [x] **SEC-01**: System validates uploaded file is JPG or PNG and rejects other types
- [x] **SEC-02**: System rejects files exceeding a maximum size limit (e.g., 20 MB)
- [x] **SEC-03**: System strips EXIF metadata from uploaded image before processing
- [x] **SEC-04**: System treats transcribed text as data only — no re-execution of content as instructions (prompt injection defense)

### Orchestration

- [x] **ORC-01**: ADK root orchestrator coordinates all pipeline agents in correct order
- [x] **ORC-02**: Orchestrator handles agent errors and surfaces them to the user with context
- [x] **ORC-03**: Orchestrator assembles final structured output from all agent results

### Transcription

- [x] **TRS-01**: Transcription agent sends image to Gemini 3 Pro with maxOutputTokens=65536, temperature=0.1, thinkingBudget=128
- [x] **TRS-02**: Transcription agent returns raw text with no post-processing
- [x] **TRS-03**: System handles partial transcription (Gemini skipped lines) without crashing

### Cleaning & Normalization

- [x] **CLN-01**: Cleaning agent expands common paleographic abbreviations in the transcribed text
- [x] **CLN-02**: Cleaning agent normalizes archaic spelling to modern equivalents where unambiguous
- [x] **CLN-03**: Cleaning agent is packaged as a reusable Agent Skill (ADK agent skills concept)

### MCP Server

- [x] **MCP-01**: FastMCP server exposes `lookup_entity(name)` tool — disambiguates person/place and returns dates/description
- [x] **MCP-02**: FastMCP server exposes `normalize_date(text)` tool — converts archaic date formats to ISO standard
- [x] **MCP-03**: FastMCP server exposes `expand_abbreviation(token)` tool — resolves paleographic abbreviations
- [x] **MCP-04**: FastMCP server exposes `place_context(place, year)` tool — returns historical/geographic context for a toponym
- [x] **MCP-05**: MCP server uses Wikidata/Wikipedia as data source with no required API keys
- [x] **MCP-06**: MCP server is registered and callable by the context agent via ADK tool use

### Context Enrichment

- [x] **CTX-01**: Context agent identifies named entities (persons, places, dates) in the cleaned text
- [x] **CTX-02**: Context agent queries MCP server tools to resolve and enrich each entity
- [x] **CTX-03**: Context agent produces structured historical notes for enriched entities

### Verification

- [x] **VER-01**: Verification agent scores confidence per passage/sentence in the transcription
- [x] **VER-02**: Verification agent marks individual words or spans with low confidence
- [x] **VER-03**: Verification agent output includes confidence scores consumable by the UI

### UI & Demo

- [x] **UI-01**: Gradio interface accepts a single image file upload
- [x] **UI-02**: UI displays clean transcription after processing
- [x] **UI-03**: UI renders confidence highlights (color-coded uncertain words/spans)
- [x] **UI-04**: UI shows historical notes panel with context enrichment results
- [x] **UI-05**: UI provides raw-vs-clean toggle to compare original Gemini output with cleaned text

### Deploy & Infrastructure

- [x] **DEP-01**: Application is containerized (Dockerfile) for Cloud Run deploy
- [ ] **DEP-02**: Application is deployed to Cloud Run as a publicly accessible endpoint
- [x] **DEP-03**: All credentials loaded from environment variables; no secrets in code or repo
- [x] **DEP-04**: `.env.example` documents required environment variable names without values

### Documentation & Submission

- [ ] **DOC-01**: README.md includes problem statement, architecture diagram, setup instructions, env-var docs
- [ ] **DOC-02**: Code contains inline comments on design, implementation, and agent behaviors
- [ ] **DOC-03**: Kaggle Writeup drafted (≤2500 words, Freestyle track, cover image attached, YouTube link)
- [ ] **DOC-04**: YouTube demo video recorded (≤5 min: problem, agents rationale, architecture, demo, build)

## v2 Requirements

### Extended Input

- **EXT-01**: Support PDF input (multi-page documents) with per-page processing
- **EXT-02**: Support drag-and-drop batch upload of multiple images

### Advanced Enrichment

- **ENR-01**: Pre-transcription context injection — feed known document metadata to Gemini before transcribing
- **ENR-02**: Modern spelling translation toggle (archaic → contemporary)
- **ENR-03**: Multiple MCP data sources (Chronicling America, British Library API)

### UI Polish

- **UIP-01**: Side-by-side image + transcription view
- **UIP-02**: Confidence heatmap overlay on original scan
- **UIP-03**: Export to DOCX/PDF with annotations

## Out of Scope

| Feature | Reason |
|---------|--------|
| PDF multi-page in v1 | Scope risk for 16-day solo timeline; single image sufficient for demo |
| User accounts / auth | Stateless demo; no persistent user data needed |
| Gemini Flash for cursive | Tested: failed 3/4 real manuscript pages |
| Tesseract / classic OCR | Multimodal approach superior for cursive; OCR ~50-63% accuracy |
| Physical document scanning | All test data from public domain digital archives |
| Paid/proprietary MCP data | Wikidata/Wikipedia free tier sufficient for course requirements |
| Real-time collaboration | Out of scope for competition entry |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SEC-01 – SEC-04 | Phase 1 | Pending |
| ORC-01 – ORC-03 | Phase 1 | Pending |
| TRS-01 – TRS-03 | Phase 1 | Pending |
| CLN-01 – CLN-03 | Phase 2 | Pending |
| MCP-01 – MCP-06 | Phase 2 | Pending |
| CTX-01 – CTX-03 | Phase 2 | Pending |
| VER-01 – VER-03 | Phase 3 | Pending |
| UI-01 – UI-05 | Phase 3 | Pending |
| DEP-01 – DEP-04 | Phase 4 | Pending |
| DOC-01 – DOC-04 | Phase 4 | Pending |

**Coverage:**

- v1 requirements: 34 total
- Mapped to phases: 34
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-21*
*Last updated: 2026-06-21 after initial definition*

# Phase 4: Deploy + Submission Artifacts - Context

**Gathered:** 2026-06-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Containerize the Palimpsest application and deploy it to Oracle VM (Docker) as a publicly accessible endpoint; produce all Kaggle submission artifacts: README with architecture diagram, inline code documentation, Kaggle Writeup (≤2500 words), and YouTube demo video (≤5 min).

Requirements in scope: DEP-01, DEP-02, DEP-03, DEP-04, DOC-01, DOC-02, DOC-03, DOC-04

**Execution order (risk-first):** Dockerfile → Deploy → README → Inline comments → Writeup → Video

</domain>

<decisions>
## Implementation Decisions

### Deploy Target
- **D-01:** Deploy to Oracle VM in Netherlands (4 vCPU / 24 GB RAM, existing server) — not Cloud Run. Free, no cold start, already configured. Counts as valid "Public Project Link" per Kaggle rules. Demonstrates "Deployability" course concept.
- **D-02:** Container run: `docker run -d --restart=always` — survives reboots, zero systemd unit needed.
- **D-03:** Public URL via custom domain (user has domain pointing to Oracle IP). Use HTTPS if reverse proxy already configured; otherwise HTTP:port for the submission deadline.
- **D-04:** No GCP setup required. DEP-02 scope revised: Oracle VM replaces Cloud Run.

### Dockerfile
- **D-05:** Base image: `python:3.11-slim` — matches dev environment (ADK 2.3.0 tested on 3.11), small image (~140 MB).
- **D-06:** Entrypoint: `python -m palimpsest.app` — matches existing run pattern. Gradio reads `PORT` env var via `server_port=int(os.environ.get('PORT', 7860))`.
- **D-07:** FastMCP runs as stdio subprocess (already implemented via `StdioServerParameters` in `context.py`). No uvicorn/HTTP mode needed. Docker does not change subprocess behavior. **Note for planner:** verify that Wikidata/Wikipedia HTTPS calls are not blocked in the container network (should be open, but worth a smoke test).
- **D-08:** Memory/CPU allocation: Oracle VM has 24 GB RAM / 4 vCPU — no resource constraints needed in Docker run command. Allow container to use what it needs.

### Environment Variables (.env.example)
- **D-09:** Document all 4 env vars in `.env.example` with comments:
  - `GEMINI_API_KEY=` — required. Google AI Studio API key for Gemini 3 Pro vision.
  - `PALIMPSEST_MAX_UPLOAD_MB=20` — optional. Upload size limit in MB (default 20).
  - `PALIMPSEST_CONFIDENCE_THRESHOLD=0.7` — optional. Verification agent uncertainty threshold (default 0.7).
  - `PORT=7860` — optional. Gradio server port (default 7860). Inject at runtime via Docker.
- **D-10:** Credentials injected at runtime via `docker run -e GEMINI_API_KEY=...`. No secrets in image or repo (satisfies DEP-03).

### Demo Manuscript (Video + Writeup)
- **D-11:** Primary demo image: `data/samples/pares_easy_18c.jpg` — 18th century Spanish colonial doc, easier cursive. Maximizes chance of full clean transcription for live demo.
- **D-12:** Video narration: English (international judges).
- **D-13:** Cover image for Kaggle submission: screenshot of Gradio UI with `pares_easy_18c.jpg` result loaded — uncertainty highlights visible.
- **D-14:** Video recording: OBS Studio.

### Video Script (≤5 min, demo-first structure)
- **D-15:** Timings:
  - 0:00–0:30 — Problem (voice-over on manuscript image: historian can't read 18th-century cursive)
  - 0:30–1:00 — Architecture diagram (quick: 4 agents + MCP server, SequentialAgent flow)
  - 1:00–3:30 — Live demo (upload `pares_easy_18c.jpg`, show pipeline running, transcription panel, historical notes table, uncertainty highlights)
  - 3:30–4:30 — Code highlights (orchestrator SequentialAgent, MCP tools, cleaning Agent Skill, security barrier)
  - 4:30–5:00 — Close (live URL, GitHub link, course concepts demonstrated)

### Kaggle Writeup (≤2500 words)
- **D-16:** Tone: narrative project story — open with historian discovering a colonial doc they can't read, Palimpsest solving it. Weave technical decisions into the story. Not a technical paper.
- **D-17:** Word budget (narrative-heavy):
  - Intro/problem: ~400w
  - Agents + rationale (WHY multi-agent vs single prompt): ~600w
  - Architecture + before/after excerpt from `pares_easy_18c.jpg`: ~500w
  - MCP server + security features: ~300w
  - Results + demo link: ~300w
  - Conclusions: ~200w
  - Buffer: ~200w
- **D-18:** Course concepts explicitly highlighted (all 4):
  1. Multi-agent ADK (SequentialAgent, 4 LlmAgents)
  2. MCP server (FastMCP, 4 tools: lookup_entity, normalize_date, expand_abbreviation, place_context)
  3. Security features (SEC-01–SEC-04: file validation, EXIF strip, prompt injection defense)
  4. Agent Skill (cleaning agent packaged as reusable ADK Agent Skill, CLN-03)
- **D-19:** Include before/after transcript excerpt (~200w of the word budget) showing raw Gemini output vs cleaned text with uncertainty markers.

### README (DOC-01)
- **D-20:** Architecture diagram: expand existing ASCII diagram in `README.md`. Add MCP server branch and verification step. No new tooling (Mermaid not needed).

### Inline Code Comments (DOC-02)
- **D-21:** Depth: module-level docstring per agent file (role + key decisions) + targeted inline comments on non-obvious lines. Key non-obvious decisions to comment:
  - Why `thinkingBudget=128` (lower is better for transcription, counterintuitive)
  - Why `filetype.guess()` before `Pillow.open()` (magic-byte validation must precede image parsing)
  - Why `maxOutputTokens=65536` (default 8192 silently truncates)
  - Why `stdio` transport for MCP (ADK StdioServerParameters pattern, not HTTP)
  - Why `temperature=0.1` for transcription (reduces variance on proper nouns)
  - SEC-04 system prompt pattern (labeling input as DATA, not instructions)

### Claude's Discretion
- Exact Dockerfile COPY/RUN layer ordering (optimize for layer caching)
- Whether to add a `HEALTHCHECK` instruction in Dockerfile
- Nginx/Caddy reverse proxy config if user wants HTTPS on Oracle VM (not in scope of Phase 4 implementation, but can be noted in README)
- Exact pyproject.toml entry point name for `python -m palimpsest.app`

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements
- `.planning/PROJECT.md` — Core constraints, model config rationale (maxOutputTokens=65536, temperature=0.1, thinkingBudget=128), Phase 4 deadline (Day 14 = 2026-07-04), open questions Q1/Q5/Q7 (Q1 resolved: Spanish; Q5 resolved: Oracle VM)
- `.planning/REQUIREMENTS.md` — Full DEP-01–DEP-04 and DOC-01–DOC-04 acceptance criteria
- `.planning/ROADMAP.md` — Phase 4 success criteria, depends on Phase 3

### Prior Phase Decisions
- `.planning/phases/03-verification-gradio-ui/03-CONTEXT.md` — D-12 (Gradio app location: `src/palimpsest/app.py`), D-13 (`asyncio.run()` pattern for Gradio + async backend), D-07 (layout/sections)
- `.planning/phases/02-full-multi-agent-system/02-CONTEXT.md` — D-11 (output dict schema), D-09 (agent ordering)

### Competition Rules
- `docs/rules.md` — Submission requirements: Writeup (≤2500w), cover image, YouTube link in Media Gallery, Public Project Link, submit button before deadline
- `docs/PROYECTO_PALIMPSESTO.md` — Scoring rubric: 70pt implementation (50 technical + 20 docs/README) + 30pt pitch (10 concept + 10 video + 10 writeup); course concepts checklist

### Existing Code
- `src/palimpsest/app.py` — Gradio app; entry point for container; reads PORT env var
- `src/palimpsest/agents/orchestrator.py` — `run_pipeline()` async function, SequentialAgent definition
- `src/palimpsest/agents/context.py` — MCP stdio subprocess pattern (`StdioServerParameters`, `McpToolset`)
- `src/palimpsest/mcp/server.py` — FastMCP server; `mcp.run()` defaults to stdio; external calls to Wikidata/Wikipedia
- `requirements.txt` — Full dependency list for Dockerfile pip install

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/palimpsest/app.py` — already has Gradio launch; add `server_port=int(os.environ.get('PORT', 7860))` and `server_name="0.0.0.0"` for container binding
- `requirements.txt` — use as-is for `pip install -r requirements.txt` in Dockerfile
- `data/samples/pares_easy_18c.jpg` — primary demo image for video and Writeup before/after excerpt

### Established Patterns
- `python -m palimpsest.app` — existing run pattern; use as Docker CMD
- FastMCP stdio subprocess — already works in local env; Docker does not change behavior
- `.env` + `python-dotenv` — already loaded in codebase; `.env.example` mirrors `.env` structure with no values

### Integration Points
- Dockerfile COPY: `src/` + `requirements.txt` + `data/samples/` (for smoke test inside container)
- Port binding: Gradio `server_name="0.0.0.0"` required for Docker (localhost binding won't be reachable from outside)
- Oracle VM firewall: TCP port 7860 (or 80/443 if reverse-proxied) must be open in Oracle Cloud security list

</code_context>

<specifics>
## Specific Ideas

- **Container smoke test:** After `docker build`, run `docker run --rm -e GEMINI_API_KEY=test -p 7860:7860 palimpsest` and hit `http://localhost:7860` to confirm Gradio loads before pushing to Oracle VM.
- **Wikidata network check:** Inside the container, `curl https://www.wikidata.org/w/api.php?action=wbsearchentities&search=test&format=json&language=en` to verify external HTTPS is not blocked.
- **README architecture diagram:** Extend the existing ASCII block to show the MCP server as a branch from Context Agent, and add Verification Agent as the last step before Output.
- **Video opening shot:** Screen-record `pares_easy_18c.jpg` displayed full-screen before uploading — dramatic visual of unreadable cursive is the hook.
- **Writeup before/after excerpt:** Run the pipeline on `pares_easy_18c.jpg` before recording video; save the `raw_transcription` and `cleaned_transcription` output for copy-paste into the Writeup.

</specifics>

<deferred>
## Deferred Ideas

- **UI improvements / friendlier UX** — user mentioned wanting a more usable/friendly UI. Valid improvement but new capability; belongs in v2 or post-competition polish. Noted for backlog.

</deferred>

---

*Phase: 4-deploy-submission-artifacts*
*Context gathered: 2026-06-27*

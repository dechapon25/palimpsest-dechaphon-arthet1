# Phase 4: Deploy + Submission Artifacts - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-27
**Phase:** 04-deploy-submission-artifacts
**Areas discussed:** Cloud Run deploy scope, Dockerfile/startup design, Demo manuscript for video, Writeup content strategy, Inline code comments scope, .env.example content, Submission checklist sequencing, Writeup structure detail, Video script, FastMCP in container

---

## Cloud Run Deploy Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Real deploy (Cloud Run) | Public Cloud Run URL, adds deployability points, needs GCP + billing | |
| Repo-only | Public GitHub counts as Public Project Link, saves ~2h | |

**User's choice:** Real deploy — then revised to Oracle VM (see below)
**Notes:** User revealed they have an existing Oracle VM (4 vCPU / 24 GB RAM) in Netherlands. Changed deploy target from Cloud Run to Oracle VM — free, no cold start, already configured. GCP project: existing (not needed anymore). Region: us-central1 (moot). Memory: 2 vCPU/2 GB Cloud Run allocation replaced by Oracle VM full capacity.

---

## Dockerfile / Startup Design

| Option | Description | Selected |
|--------|-------------|----------|
| Oracle VM | Free, always-on, existing server | ✓ |
| Cloud Run | GCP cloud-native signal for judges | |

**Persistent run:** `docker run -d --restart=always`

| Option | Description | Selected |
|--------|-------------|----------|
| docker run -d --restart=always | Simple, survives reboots | ✓ |
| docker-compose up -d | Adds documentation value | |

**URL:** Custom domain (user has domain pointing to Oracle IP)

**Base image:** `python:3.11-slim` ✓ (vs python:3.12-slim)

**FastMCP in container:** User asked to verify if FastMCP needs uvicorn/HTTP in Docker. Analysis: `mcp.run()` defaults to stdio transport; Docker subprocess behavior identical to local. Risk note for planner: verify Wikidata/Wikipedia external HTTPS not blocked in container network.

---

## Demo Manuscript for Video

| Option | Description | Selected |
|--------|-------------|----------|
| Spanish — PARES docs | More dramatic cursive, differentiates entry | ✓ |
| English — LoC | Immediately legible for judges | |

**Primary image:** `data/samples/pares_easy_18c.jpg` (18th century, easier cursive — maximize pipeline success for live demo)

**Video narration:** English ✓

**Cover image:** Screenshot of Gradio UI with pares_easy_18c.jpg result and highlights visible ✓

**Video recording tool:** OBS Studio ✓

**Video structure:**
| Option | Description | Selected |
|--------|-------------|----------|
| Demo-first | 0:30 problem → 0:30 arch → 2:30 demo → 1:00 code → 0:30 close | ✓ |
| Architecture-first | 1:00 problem → 1:30 arch → 1:30 demo → 1:00 code | |

---

## Writeup Content Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Problem + agent rationale heavy | Strong narrative WHY multi-agent. More memorable. | ✓ |
| Technical architecture heavy | Detailed agent graph, code snippets. More rigorous. | |

**Tone:** Narrative project story ✓ (vs technical paper)

**Course concepts to highlight (all 4):** Multi-agent ADK, MCP server, Security features, Agent Skill (cleaning agent) ✓

**Word distribution (narrative-heavy):** Intro/problem 400w + Agents/rationale 600w + Architecture/excerpt 500w + MCP/security 300w + Results/demo 300w + Conclusions 200w + Buffer 200w

**Before/after excerpt:** Include raw Gemini output vs cleaned text (~200w of budget) ✓

---

## README Architecture Diagram

| Option | Description | Selected |
|--------|-------------|----------|
| Expand existing ASCII | Zero new tooling, fast | ✓ |
| Mermaid diagram | GitHub-rendered, more readable | |

---

## Inline Code Comments Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Key decision points only | ~20-30 targeted comments total | |
| Module docstring per agent + inline on non-obvious | More comprehensive | ✓ |

**Key non-obvious lines to comment:** thinkingBudget=128 rationale, filetype.guess() before Pillow, maxOutputTokens=65536, stdio transport choice, temperature=0.1, SEC-04 system prompt pattern.

---

## .env.example Content

**Selected:** All 4 env vars — GEMINI_API_KEY (required) + PALIMPSEST_MAX_UPLOAD_MB, PALIMPSEST_CONFIDENCE_THRESHOLD, PORT (optional with defaults)
**Notes:** User said "las que tú consideres más correctas" — planner documents all 4.

---

## Submission Checklist Sequencing

| Option | Description | Selected |
|--------|-------------|----------|
| Dockerfile → Deploy → README → Comments → Writeup → Video | Risk-first; demo works before writing about it | ✓ |
| README → Comments → Dockerfile → Deploy → Writeup → Video | Docs-first; risk of writing before deploy validated | |

---

## Claude's Discretion

- Dockerfile COPY/RUN layer ordering (optimize cache)
- Whether to add HEALTHCHECK instruction
- Nginx/Caddy reverse proxy config for HTTPS on Oracle VM (noted in README, not implemented)
- Exact pyproject.toml entry point name

## Deferred Ideas

- **UI improvements / friendlier UX** — user mentioned wanting more usable/friendly UI. Deferred: new capability, belongs in v2 or post-competition. Noted in CONTEXT.md deferred section.

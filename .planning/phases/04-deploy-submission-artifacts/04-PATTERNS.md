# Phase 4: Deploy + Submission Artifacts - Pattern Map

**Mapped:** 2026-06-28
**Files analyzed:** 12 (new or modified)
**Analogs found:** 8 / 12

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `Dockerfile` | config | build artifact | none — new file type | no analog |
| `.dockerignore` | config | build artifact | none — new file type | no analog |
| `.env.example` | config | config | none — new file type | no analog |
| `src/palimpsest/app.py` | component | request-response | itself (modify demo.launch()) | self-modify |
| `README.md` | docs | N/A | itself (extend diagram) | self-modify |
| `src/palimpsest/agents/transcription.py` | service | request-response | itself (add docstring depth) | self-modify |
| `src/palimpsest/agents/cleaning.py` | service | request-response | `src/palimpsest/agents/transcription.py` | role-match |
| `src/palimpsest/agents/context.py` | service | request-response | `src/palimpsest/agents/transcription.py` | role-match |
| `src/palimpsest/agents/verification.py` | service | request-response | `src/palimpsest/agents/transcription.py` | role-match |
| `src/palimpsest/agents/orchestrator.py` | service | request-response | itself (add docstring depth) | self-modify |
| `src/palimpsest/mcp/server.py` | service | request-response | `src/palimpsest/agents/context.py` | role-match |
| `docs/writeup.md` | docs | N/A | none — prose document | no analog |

---

## Pattern Assignments

### `Dockerfile` (config, build artifact)

**Analog:** None — use RESEARCH.md verified pattern directly.

**Recommended Dockerfile** (from RESEARCH.md Code Examples):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Layer 1: dependencies (cached when only source changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Layer 2: application source
COPY src/ ./src/
COPY data/samples/ ./data/samples/

# src/ layout: expose package to Python without pip install -e .
# pyproject.toml has no [project] section (only [tool.ruff]) -- PYTHONPATH is
# the correct fix (see RESEARCH.md Finding 2).
ENV PYTHONPATH=/app/src

# Gradio container binding: GRADIO_SERVER_NAME overrides the default 127.0.0.1.
# Without this, Gradio is unreachable outside the container (RESEARCH.md Pitfall 4).
ENV GRADIO_SERVER_NAME=0.0.0.0

# Prevent stdout buffering -- critical for FastMCP stdio subprocess.
# Buffered print() to stdout corrupts the JSON-RPC channel (RESEARCH.md Pitfall 2).
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

CMD ["python", "-m", "palimpsest.app"]
```

**Optional HEALTHCHECK block** (Claude's Discretion — add if curl is acceptable layer cost):
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1
```

**Layer ordering rationale:** `requirements.txt` COPY+RUN comes before `COPY src/` so that rebuilds triggered only by source changes reuse the cached pip layer. This is the standard Python Docker best practice.

---

### `.dockerignore` (config, build artifact)

**Analog:** None — use RESEARCH.md pattern directly.

**Pattern** (from RESEARCH.md Code Examples):
```
.env
.env.*
.git/
.gitignore
__pycache__/
*.pyc
*.pyo
.venv/
.planning/
docs/
tests/
*.md
```

**Critical rule:** `.env` must be listed here. If `.env` enters the Docker build context, `docker history` can expose it even if it is never COPYed — DEP-03 violation.

---

### `.env.example` (config)

**Analog:** None — but the pattern for env var names comes directly from `src/palimpsest/run.py` (reads `GOOGLE_API_KEY`) and `src/palimpsest/app.py` (reads `GOOGLE_API_KEY` via `load_dotenv()`).

**CRITICAL:** CONTEXT.md D-09 says `GEMINI_API_KEY` but the codebase reads `GOOGLE_API_KEY`. Use `GOOGLE_API_KEY` — that is what `google-adk` and `google-genai` 2.9.0 read (RESEARCH.md Finding 1).

**Pattern** (from RESEARCH.md Code Examples, corrected name):
```bash
# Required: Google AI Studio API key (Gemini API)
# Obtain at: https://aistudio.google.com
GOOGLE_API_KEY=

# Optional: Maximum image upload size in MB (default: 20)
PALIMPSEST_MAX_UPLOAD_MB=20

# Optional: Confidence threshold for uncertainty highlighting (default: 0.7)
PALIMPSEST_CONFIDENCE_THRESHOLD=0.7

# Optional: Gradio server port (default: 7860)
PORT=7860
```

---

### `src/palimpsest/app.py` (component, request-response) — MODIFY

**Analog:** Itself. One targeted change: `demo.launch()` call at line 328.

**Current pattern** (`src/palimpsest/app.py` lines 326–328):
```python
if __name__ == "__main__":
    # Pass theme here in Gradio 6.x (moved from gr.Blocks constructor in 6.0)
    demo.launch(theme=gr.themes.Soft())
```

**Target pattern** (per CONTEXT.md D-06 and RESEARCH.md Finding 3):
```python
if __name__ == "__main__":
    # Pass theme here in Gradio 6.x (moved from gr.Blocks constructor in 6.0)
    # server_name="0.0.0.0" required for Docker -- default 127.0.0.1 is not
    # reachable outside the container even with -p 7860:7860 port mapping.
    # server_port reads PORT env var (Cloud Run convention; harmless on Oracle VM).
    demo.launch(
        theme=gr.themes.Soft(),
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
    )
```

Note: `GRADIO_SERVER_NAME=0.0.0.0` in the Dockerfile (Option A from RESEARCH.md) also works without code change. CONTEXT.md D-06 specifies Option B explicitly. Planner should implement Option B (code change) to make the configuration visible in source, and keep the Dockerfile ENV as belt-and-suspenders.

**Existing module-level docstring** (lines 1–27) already covers UI requirements and security notes. No change needed there — it is the model for other agents' docstrings.

---

### `src/palimpsest/agents/transcription.py` (service, request-response) — MODIFY

**Analog:** Itself (already has strong module-level docstring, lines 1–12). This is the reference pattern that other agent files should match.

**Existing docstring pattern** (lines 1–12):
```python
"""Transcription agent for historical handwritten manuscripts.

Uses Gemini 2.5 Pro (or Gemini 3 Pro when available) with vision capabilities
to transcribe cursive text from scanned manuscript images.

SEC-04 barrier 1: System prompt explicitly labels document text as data,
not instructions — defends against prompt injection via manuscript content.

TRS-01: LlmAgent with correct thinking_budget wiring (on BuiltInPlanner,
NOT in generate_content_config — see RESEARCH.md Pitfall 2).
TRS-02: Gemini 2.5 Pro vision model for transcription.
"""
```

**Comments to add per D-21:**
- On `thinkingBudget=128` line: explain that lower thinking budget is counterintuitive but correct for transcription (reduces over-interpretation of cursive strokes).
- On `maxOutputTokens=65536` line: explain that default 8192 silently truncates long manuscripts.
- On `temperature=0.1` line: explain that low temperature reduces variance on proper nouns and place names.

**Imports pattern** (lines 14–16):
```python
from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types
```

---

### `src/palimpsest/agents/cleaning.py` (service, request-response) — MODIFY

**Analog:** `src/palimpsest/agents/transcription.py` — copy its docstring structure (role + requirement IDs + key decisions).

**Docstring structure to follow** (from transcription.py lines 1–12):
```python
"""[One-line role description].

[One paragraph: what model, what task.]

[Requirement IDs: CLN-01, CLN-02, CLN-03, D-nn references.]
[Key design decisions worth explaining: why Agent Skill, why Flash not Pro.]
"""
```

**Comments to add per D-21:**
- On the Agent Skill packaging: note it is a reusable ADK Agent Skill (CLN-03 course concept).

---

### `src/palimpsest/agents/context.py` (service, request-response) — MODIFY

**Analog:** `src/palimpsest/agents/transcription.py` for docstring structure. The existing module docstring (lines 1–16) already matches the pattern well.

**Existing docstring** (lines 1–16) already covers CTX-01/02/03, D-09, MCP-06, SEC-04. Quality is good.

**Comments to add per D-21:**
- On `StdioConnectionParams` / `StdioServerParameters` usage: explain WHY stdio transport (ADK McpToolset pattern, not HTTP — stdio requires parent/child process relationship, cannot cross container boundaries).

**Imports pattern** (lines 18–26):
```python
import sys

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams,
)
from google.genai import types
from mcp import StdioServerParameters
```

---

### `src/palimpsest/agents/verification.py` (service, request-response) — MODIFY

**Analog:** `src/palimpsest/agents/transcription.py` for docstring structure.

**Docstring structure to follow:**
```python
"""[One-line role description].

[Model used, task.]

[VER-01, VER-02, VER-03, D-nn references.]
[Key decision: confidence threshold 0.7, why it is configurable via env var.]
"""
```

**Comments to add per D-21:**
- On `CONFIDENCE_THRESHOLD`: note it mirrors `app.py` threshold; both read the same env var `PALIMPSEST_CONFIDENCE_THRESHOLD`.

---

### `src/palimpsest/agents/orchestrator.py` (service, request-response) — MODIFY

**Analog:** Itself. Already has a strong module-level docstring (lines 1–15) covering all requirement IDs.

**Existing docstring** (lines 1–15):
```python
"""Pipeline orchestrator for the Palimpsest transcription system.

Uses ADK SequentialAgent with InMemoryRunner to run the full pipeline:
Transcription -> Cleaning -> Context enrichment -> Confidence verification.

ORC-01: SequentialAgent pipeline declaration.
ORC-02: Error handling with descriptive messages, no retries.
ORC-03: Async execution via InMemoryRunner.run_async().
TRS-03: Partial transcription detection ...
D-05: Agent order: Transcription -> Cleaning -> Context -> Verification.
D-11: Output dict schema -- original four keys frozen; new keys additive (A3).
D-06: confidence_map key added to return dict (Phase 3, additive per A3).
VER-03: run_pipeline() exposes confidence_map for UI consumption.
"""
```

No structural changes needed — only targeted inline comments per D-21 if any non-obvious lines exist (e.g., `InMemorySessionService` usage, `asyncio.run()` caller contract).

---

### `src/palimpsest/mcp/server.py` (service, request-response) — MODIFY

**Analog:** `src/palimpsest/agents/context.py` for docstring style. The MCP server is the subprocess that context.py spawns.

**Comments to add per D-21:**
- On `mcp.run()`: note that it defaults to stdio transport — this is intentional. Do NOT add `print()` calls anywhere in this file; any stdout output corrupts the JSON-RPC channel used by `McpToolset`.
- On `if __name__ == "__main__": mcp.run()`: note this is the subprocess entry point invoked by `StdioServerParameters(command=sys.executable, args=["-m", "palimpsest.mcp.server"])`.

---

### `README.md` (docs) — MODIFY

**Analog:** Itself. Two targeted modifications:

**1. Architecture diagram** — extend existing ASCII block to match RESEARCH.md Code Examples pattern (adds MCP server branch and Verification Agent step). The target diagram from RESEARCH.md:
```
Scanned manuscript image
        │
        ▼
┌─────────────────┐
│ Document Intake  │  Security checks, EXIF strip, format validation (SEC-01–SEC-04)
└────────┬────────┘
         ▼
┌─────────────────┐
│ Transcription    │  Gemini 2.5 Pro vision reads cursive handwriting
│ Agent            │  maxOutputTokens=65536 · temperature=0.1 · thinkingBudget=128
└────────┬────────┘
         ▼
┌─────────────────┐
│ Cleaning Agent   │  Gemini 2.5 Flash expands abbreviations,
│ (Agent Skill)    │  normalizes archaic spelling (18th-19th c. Spanish)
└────────┬────────┘
         ▼
┌─────────────────┐     ┌──────────────────────┐
│ Context Agent    │────▶│ FastMCP Server       │
│                  │◀────│ • lookup_entity      │──▶ Wikidata SPARQL
│                  │     │ • normalize_date     │◀── Wikipedia REST
│                  │     │ • expand_abbreviation│
│                  │     │ • place_context      │
└────────┬────────┘     └──────────────────────┘
         ▼
┌─────────────────┐
│ Verification     │  Scores confidence per word/span (0.0–1.0)
│ Agent            │  Marks uncertain passages for UI highlighting
└────────┬────────┘
         ▼
┌─────────────────┐
│ Gradio UI        │  raw_transcription · cleaned_transcription
│ Output           │  context_notes (entity table) · confidence_map (highlights)
└─────────────────┘
```

**2. Quickstart fix** — change `pip install -e .` to `pip install -r requirements.txt` + `export PYTHONPATH=src` (or note that Dockerfile uses `ENV PYTHONPATH=/app/src`). Also update phase status table: Phase 3 → "Complete", Phase 4 → "In Progress". (RESEARCH.md Finding 2 and Finding 5.)

---

### `docs/writeup.md` (docs) — NEW

**Analog:** None — prose document. Structure from CONTEXT.md D-16/D-17/D-18/D-19.

**Not a code pattern.** Planner should treat this as a writing task with a defined structure:
- Intro/problem: ~400w — historian + colonial doc hook
- Agents + rationale: ~600w — WHY multi-agent vs single prompt
- Architecture + before/after excerpt: ~500w — pares_easy_18c.jpg run output
- MCP + security: ~300w
- Results + demo link: ~300w
- Conclusions: ~200w
- Buffer: ~200w
- Total: ≤2500w

All 4 course concepts must appear explicitly: Multi-agent ADK, MCP server, Security features, Agent Skill (CLN-03).

---

## Shared Patterns

### Module-Level Docstring Style
**Source:** `src/palimpsest/app.py` lines 1–27 and `src/palimpsest/agents/transcription.py` lines 1–12
**Apply to:** All agent files being commented in DOC-02

Pattern: One-line summary → blank line → prose paragraph (model + task) → blank line → requirement ID list (REQ-NN: description) → key design decisions with cross-references.

```python
"""[One-line agent role].

[Prose: model name, what it processes, what it produces.]

REQ-01: [what it satisfies].
REQ-02: [what it satisfies].
D-nn: [decision reference and brief rationale].
"""
```

### Environment Variable Loading
**Source:** `src/palimpsest/app.py` lines 41–43
**Apply to:** Any file that reads env vars at startup

```python
# Load environment variables (GOOGLE_API_KEY, etc.) at module level.
# Follows run.py pattern; must precede any Gemini API calls.
load_dotenv()
```

### Security Barrier Comment (SEC-04)
**Source:** `src/palimpsest/agents/transcription.py` lines 18–26 and `src/palimpsest/agents/context.py` lines 28–37
**Apply to:** Any agent whose system prompt includes the DATA labeling pattern

The SEC-04 comment pattern (already in transcription.py and context.py docstrings) should be present in ALL agent file module docstrings, referencing OWASP LLM01:2025.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `Dockerfile` | config | build artifact | No Dockerfiles exist in repo; use RESEARCH.md verified pattern |
| `.dockerignore` | config | build artifact | No Docker config exists in repo; use RESEARCH.md pattern |
| `.env.example` | config | config | No example env file exists; use RESEARCH.md corrected pattern (GOOGLE_API_KEY not GEMINI_API_KEY) |
| `docs/writeup.md` | docs | N/A | Prose document; no code analog; structure from CONTEXT.md D-16/D-17 |

---

## Critical Notes for Planner

1. **GOOGLE_API_KEY vs GEMINI_API_KEY:** `.env.example`, README quickstart, and all docker run command examples MUST use `GOOGLE_API_KEY`. CONTEXT.md D-09/D-10 contain the wrong name. (RESEARCH.md Finding 1)

2. **app.py demo.launch() change is required:** `server_name="0.0.0.0"` must be added or Gradio will not be reachable outside the container. Dockerfile `GRADIO_SERVER_NAME=0.0.0.0` is belt-and-suspenders, not a substitute, because it depends on Gradio reading the env var before binding. (RESEARCH.md Finding 3, Pitfall 4)

3. **pyproject.toml:** Do NOT attempt `pip install -e .` in Dockerfile. Use `ENV PYTHONPATH=/app/src` only. Fix README quickstart separately. (RESEARCH.md Finding 2, Pitfall 1)

4. **Oracle VM firewall has two independent layers:** Both OCI security list AND OS `firewall-cmd` must be configured. (RESEARCH.md Pitfall 3)

5. **MCP smoke test required:** After `docker run`, verify the Context Agent actually populates historical notes — stdio subprocess can fail silently in Docker. (RESEARCH.md Pitfall 2)

---

## Metadata

**Analog search scope:** `src/palimpsest/` (all subdirectories)
**Files scanned:** 6 source files read directly
**Pattern extraction date:** 2026-06-28

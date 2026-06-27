# Phase 4: Deploy + Submission Artifacts - Research

**Researched:** 2026-06-28
**Domain:** Docker containerization · Oracle VM deployment · Gradio production config · FastMCP stdio subprocess · Kaggle competition submission
**Confidence:** MEDIUM (core Dockerfile and Gradio patterns verified against official docs; Oracle VM and FastMCP stdio findings from community sources)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Deploy Target**
- D-01: Deploy to Oracle VM in Netherlands (4 vCPU / 24 GB RAM, existing server) — not Cloud Run. Free, no cold start, already configured. Counts as valid "Public Project Link" per Kaggle rules.
- D-02: Container run: `docker run -d --restart=always`
- D-03: Public URL via custom domain (user has domain pointing to Oracle IP). Use HTTPS if reverse proxy already configured; otherwise HTTP:port for submission deadline.
- D-04: No GCP setup required. DEP-02 scope revised: Oracle VM replaces Cloud Run.

**Dockerfile**
- D-05: Base image: `python:3.11-slim`
- D-06: Entrypoint: `python -m palimpsest.app`. Gradio reads `PORT` env var via `server_port=int(os.environ.get('PORT', 7860))`.
- D-07: FastMCP runs as stdio subprocess (already implemented via `StdioServerParameters` in `context.py`). No uvicorn/HTTP mode needed.
- D-08: No resource constraints in Docker run command.

**Environment Variables**
- D-09: Document 4 env vars in `.env.example`: `GEMINI_API_KEY=`, `PALIMPSEST_MAX_UPLOAD_MB=20`, `PALIMPSEST_CONFIDENCE_THRESHOLD=0.7`, `PORT=7860`
- D-10: Credentials injected at runtime via `docker run -e GEMINI_API_KEY=...`

**Demo / Video**
- D-11: Primary demo image: `data/samples/pares_easy_18c.jpg`
- D-12: Video narration: English
- D-13: Cover image: screenshot of Gradio UI with pares_easy_18c.jpg result loaded
- D-14: Video recording: OBS Studio
- D-15: Video timings: 0:00-0:30 Problem · 0:30-1:00 Architecture · 1:00-3:30 Live demo · 3:30-4:30 Code highlights · 4:30-5:00 Close

**Kaggle Writeup**
- D-16: Tone: narrative project story (historian finding a colonial doc)
- D-17: Word budget: Intro ~400w · Agents+rationale ~600w · Architecture+before/after ~500w · MCP+security ~300w · Results ~300w · Conclusions ~200w · Buffer ~200w
- D-18: Explicitly highlight all 4 course concepts: Multi-agent ADK · MCP server · Security features · Agent Skill
- D-19: Before/after transcript excerpt (~200w) from pares_easy_18c.jpg run

**README**
- D-20: Expand existing ASCII diagram — add MCP server branch and Verification Agent step

**Inline Comments**
- D-21: Module-level docstrings per agent file + targeted comments on: thinkingBudget=128 · filetype.guess() before Pillow.open() · maxOutputTokens=65536 · stdio transport for MCP · temperature=0.1 · SEC-04 system prompt pattern

### Claude's Discretion

- Exact Dockerfile COPY/RUN layer ordering (optimize for layer caching)
- Whether to add a `HEALTHCHECK` instruction in Dockerfile
- Nginx/Caddy reverse proxy config if user wants HTTPS (noted in README only)
- Exact pyproject.toml entry point name for `python -m palimpsest.app`

### Deferred Ideas (OUT OF SCOPE)

- UI improvements / friendlier UX — belongs in v2 or post-competition polish

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEP-01 | Application containerized (Dockerfile) | Dockerfile pattern, PYTHONPATH, Gradio env vars, layer ordering |
| DEP-02 | Application deployed to publicly accessible endpoint | Oracle VM SSH workflow, two-layer firewall, docker run flags |
| DEP-03 | All credentials from environment variables; no secrets in code or repo | `.dockerignore` pattern, runtime `-e` injection, GOOGLE_API_KEY naming |
| DEP-04 | `.env.example` documents required env var names without values | Confirmed env var names (GOOGLE_API_KEY not GEMINI_API_KEY) |
| DOC-01 | README.md: problem statement, architecture diagram, setup, env-var docs | Diagram extension pattern, missing Verification Agent, README gaps identified |
| DOC-02 | Code: inline comments on design, implementation, agent behaviors | Key comment targets from CONTEXT.md D-21, no new pattern research needed |
| DOC-03 | Kaggle Writeup (≤2500 words, cover image, YouTube link) | Kaggle submission steps, word budget structure, deadline confirmed |
| DOC-04 | YouTube demo video (≤5 min) | Video structure locked in D-15; OBS Studio; pares_easy_18c.jpg as demo |

</phase_requirements>

---

## Summary

Phase 4 is the production/submission phase for the Palimpsest Kaggle entry. It has two parallel tracks: (1) Containerize and deploy the Gradio application to Oracle VM so it is publicly reachable; and (2) produce all Kaggle submission artifacts (README, inline comments, Writeup, YouTube video).

The Dockerfile is straightforward for a Python/Gradio application, with one important structural issue: `pyproject.toml` currently has no `[project]` section, so `pip install -e .` does not work. The correct fix for Docker is `ENV PYTHONPATH=/app/src` — this makes `python -m palimpsest.app` work without modifying the package build config. The existing `requirements.txt` is used directly.

The critical deployment risk is the FastMCP stdio subprocess inside Docker. A known issue (fastmcp #507) causes stdio transport to fail silently in some Docker environments. The mitigation is `ENV PYTHONUNBUFFERED=1` plus an explicit smoke test (upload a real manuscript inside the running container before going live). The MCP server.py does not use `print()`, which eliminates the most common failure cause (stdout corruption of the JSON-RPC stream).

Oracle VM deployment requires configuring two independent firewall layers: the OCI Console security list (network level) AND the OS-level firewall (iptables/firewalld). Both must be configured; the OCI security list alone is not sufficient. The env var naming inconsistency (`GOOGLE_API_KEY` in code vs. `GEMINI_API_KEY` in CONTEXT.md D-09) must be resolved to `GOOGLE_API_KEY`, which is what the google-adk SDK and google-genai SDK actually read.

**Primary recommendation:** Use `PYTHONPATH=/app/src` + `GRADIO_SERVER_NAME=0.0.0.0` + `PYTHONUNBUFFERED=1` in the Dockerfile. Open both OCI security list and OS firewall for port 7860. Smoke test the container before deploying to Oracle VM. Resolve `GEMINI_API_KEY` → `GOOGLE_API_KEY` throughout `.env.example` and README.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Containerization | Build artifact | — | Dockerfile encapsulates all runtime dependencies |
| Port binding (Gradio) | Container runtime | — | GRADIO_SERVER_NAME env var controls network binding |
| MCP subprocess | Container process | — | sys.executable spawns palimpsest.mcp.server inside same container |
| Secret injection | Container runtime | Host OS env | `docker run -e GOOGLE_API_KEY=...` at startup |
| External network (Wikidata) | Container egress | Oracle VM network | No OCI egress restriction expected; Wikidata HTTPS must be reachable |
| Oracle VM firewall | OCI security list | OS iptables/firewalld | Two independent layers; both required |
| Public URL | Custom domain DNS | Oracle VM IP | Domain A record → Oracle IP; HTTP or HTTPS depending on reverse proxy |
| Kaggle submission | Kaggle platform | — | Writeup → Media Gallery → Submit button |

---

## Standard Stack

### Core (all already in requirements.txt — no new packages)

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| `python` | 3.11-slim (Docker base image) | Container runtime | Use as-is |
| `google-adk[mcp]` | 2.3.0 (pinned) | ADK pipeline | Already installed |
| `google-genai` | 2.9.0 (pinned) | Gemini SDK | Already installed |
| `gradio` | 6.19.0 (pinned) | Demo UI | Already installed |
| `fastmcp` | via google-adk[mcp] | MCP server | Already installed |
| `requests` | >=2.28.0 | Wikidata/Wikipedia HTTP | Already installed |
| `python-dotenv` | 1.2.2 (pinned) | .env loading | Already installed |
| `Pillow` | 12.2.0 (pinned) | Image processing | Already installed |
| `filetype` | 1.2.0 (pinned) | Magic-byte validation | Already installed |

This phase introduces **no new packages**. The Dockerfile pip-installs the existing `requirements.txt`.

### Build tooling (if pyproject.toml is expanded)

If the planner chooses to add a proper `[project]` section to `pyproject.toml` (see Pitfall 1), `hatchling` is the recommended build backend. This is a development convenience, not required for Docker deployment.

---

## Package Legitimacy Audit

No new packages are introduced in this phase. All packages listed above were established in Phases 1-3. No audit required.

---

## Architecture Patterns

### System Architecture Diagram

```
User (browser)
      │
      ▼ HTTP
┌──────────────────────────────────────────────┐
│  Docker Container (Oracle VM, port 7860)      │
│                                              │
│  Gradio UI (app.py)                          │
│      │  asyncio.run()                        │
│      ▼                                       │
│  run_pipeline()  (orchestrator.py)            │
│      │  SequentialAgent                      │
│      ├──▶ TranscriptionAgent (Gemini Pro)    │
│      ├──▶ CleaningAgent (Gemini Flash)       │
│      ├──▶ ContextAgent ──▶ MCP subprocess   │──▶ Wikidata HTTPS
│      │         │◀─── JSON-RPC stdio ────────│◀── Wikipedia HTTPS
│      └──▶ VerificationAgent (Gemini Flash)  │
│                                              │
│  Env: GOOGLE_API_KEY (runtime injection)     │
└──────────────────────────────────────────────┘
      │
      ▼ public URL (custom domain or http://oracle-ip:7860)
Kaggle judges / evaluators
```

### Recommended Dockerfile

```dockerfile
# Source: Docker official Python best practices + Gradio official Docker guide
FROM python:3.11-slim

WORKDIR /app

# Layer 1: dependencies (cached when only source changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Layer 2: application source
COPY src/ ./src/
COPY data/samples/ ./data/samples/

# src/ layout: expose package to Python without pip install
ENV PYTHONPATH=/app/src

# Gradio container binding: GRADIO_SERVER_NAME overrides the default
# 127.0.0.1 binding — without this, Gradio is unreachable outside the container.
# Source: gradio.app/guides/deploying-gradio-with-docker [CITED]
ENV GRADIO_SERVER_NAME=0.0.0.0

# Prevent stdout buffering — critical for FastMCP stdio subprocess.
# Any buffered print() to stdout corrupts the JSON-RPC channel.
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

CMD ["python", "-m", "palimpsest.app"]
```

### Recommended .dockerignore

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

Excluding `.env` from the Docker context is essential for DEP-03. Docker build context sends files to the Docker daemon; `.env` containing `GOOGLE_API_KEY` must never enter the image.

### Oracle VM Deployment Workflow

```bash
# Step 1: Build on local machine
docker build -t palimpsest .

# Step 2: Transfer image to Oracle VM
# Option A: Via Docker Hub (requires login)
docker tag palimpsest <dockerhub-user>/palimpsest:v1
docker push <dockerhub-user>/palimpsest:v1
# On Oracle VM: docker pull <dockerhub-user>/palimpsest:v1

# Option B: Direct transfer (no registry needed)
docker save palimpsest | gzip | ssh user@oracle-ip 'gunzip | docker load'

# Step 3: On Oracle VM — open OS firewall
# Oracle Linux 8 / Oracle Autonomous Linux (uses firewalld):
sudo firewall-cmd --zone=public --permanent --add-port=7860/tcp
sudo firewall-cmd --reload
# Verify:
sudo firewall-cmd --list-ports

# Step 4: In OCI Console (one-time setup, or verify it's already done)
# VCN > Subnets > Security Lists > Default Security List
# Add Ingress Rule: Stateless=No, Protocol=TCP,
#   Source CIDR=0.0.0.0/0, Destination Port Range=7860

# Step 5: Run container
docker run -d --restart=always \
  -p 7860:7860 \
  -e GOOGLE_API_KEY=<your-key> \
  palimpsest

# Step 6: Smoke test
curl http://localhost:7860
# Then test from external: curl http://<oracle-ip>:7860

# Step 7: MCP subprocess smoke test inside container
docker exec <container-id> \
  python -c "from palimpsest.mcp.server import mcp; print('MCP server imports OK')"
```

### app.py Launch Configuration

The current `app.py` calls `demo.launch(theme=gr.themes.Soft())` without `server_name` or `server_port`.

**Option A (recommended — no code change):** Set `GRADIO_SERVER_NAME=0.0.0.0` in Dockerfile. Gradio reads this env var automatically and overrides the default `127.0.0.1` binding. [CITED: gradio.app/guides/environment-variables]

**Option B (per CONTEXT.md D-06 locked decision):** Modify `demo.launch()`:
```python
# Source: CONTEXT.md D-06
demo.launch(
    theme=gr.themes.Soft(),
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 7860)),
)
```

Both work. Option A requires no code change. Option B makes the configuration explicit in source. CONTEXT.md D-06 specifies the `PORT` env var pattern (Cloud Run convention), but since deploy target is Oracle VM, `GRADIO_SERVER_PORT` (native Gradio) or hardcoded port is equally valid.

**Decision for planner:** Use Option A (Dockerfile env var) for `server_name`. For `server_port`, use Option B only if `PORT` env var flexibility is needed; otherwise leave default 7860.

### Anti-Patterns to Avoid

- **Building image with `.env` in Docker context:** Add `.env` to `.dockerignore`. If `.env` is in the build context, `docker history` can expose it even if it's not COPYed — just having it reachable is a risk.
- **Using `CMD python src/palimpsest/app.py`:** Will fail if `PYTHONPATH` is not set AND working dir is wrong. Use `CMD ["python", "-m", "palimpsest.app"]` with `PYTHONPATH=/app/src`.
- **Running MCP server in a separate container with stdio:** stdio transport requires parent/child process relationship (same host, shared stdio pipes). stdio cannot cross container boundaries. If MCP server needs to be in a separate container, switch to HTTP transport.
- **Configuring only the OCI security list:** OS-level firewall (iptables/firewalld) is a separate independent layer on Oracle Linux. Both must be open.
- **Pressing "Save" on Kaggle writeup without clicking "Submit":** Draft writeups are not evaluated. The Submit button appears in the top-right corner after saving.

---

## Critical Codebase Findings

These are concrete gaps discovered during research that the planner MUST address:

### Finding 1: ENV VAR NAME MISMATCH — GOOGLE_API_KEY vs GEMINI_API_KEY

| Location | Env Var Used |
|----------|-------------|
| `src/palimpsest/run.py` lines 28-31 | `GOOGLE_API_KEY` |
| `src/palimpsest/app.py` docstring | `GOOGLE_API_KEY` |
| `CONTEXT.md` D-09 | `GEMINI_API_KEY` |
| `CONTEXT.md` D-10 | `GEMINI_API_KEY` |

**Resolution:** Use `GOOGLE_API_KEY`. This is the env var name that `google-adk` (Python) and `google-genai` 2.9.0 read. [CITED: adk.dev/agents/models/google-gemini/]

The `.env.example` must say `GOOGLE_API_KEY=` (not `GEMINI_API_KEY=`). The planner should flag this discrepancy to the user in the plan notes.

### Finding 2: pyproject.toml has no [project] section

Current `pyproject.toml` contains only `[tool.ruff]`. This means:
- `pip install -e .` fails (README quickstart is broken)
- `pip install .` fails

**For the Dockerfile:** Use `ENV PYTHONPATH=/app/src` — no pyproject.toml change needed.
**For README correctness:** Either fix pyproject.toml (add `[project]` section) or change quickstart to `pip install -r requirements.txt` + manual `PYTHONPATH` export.

The planner should include a task to fix the README quickstart regardless of which approach is chosen.

### Finding 3: app.py demo.launch() missing server_name

Current `app.py` line 328:
```python
demo.launch(theme=gr.themes.Soft())
```

No `server_name` or `server_port` arguments. Gradio defaults to `127.0.0.1:7860`, which is not reachable from outside the container. Fix via `ENV GRADIO_SERVER_NAME=0.0.0.0` in Dockerfile (no code change) or modify app.py per D-06.

### Finding 4: README architecture diagram missing Verification Agent

The existing README diagram ends at "JSON Output" after the Context Agent. The Verification Agent (Phase 3) and confidence_map output are missing. The diagram also needs to show Gradio UI as the consumer of pipeline output.

### Finding 5: README status table outdated

Current README shows Phase 3 and Phase 4 as "Planned". Both should be updated: Phase 3 → "✓ Complete", Phase 4 → "In Progress".

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Container port binding | Custom server socket code | `GRADIO_SERVER_NAME=0.0.0.0` env var | Gradio handles this natively |
| Process restart on reboot | Custom init scripts | `docker run --restart=always` | Docker daemon handles it |
| Secret injection | Baking secrets into image layers | `docker run -e GOOGLE_API_KEY=...` | Follows DEP-03; secrets never in image |
| Health monitoring | Custom watchdog script | Docker HEALTHCHECK instruction | Built into Docker engine |
| Image transfer to server | Custom rsync approach | `docker save \| gzip \| ssh \| docker load` | Standard Docker pattern, no registry required |

**Key insight:** For a competition submission, Docker's built-in mechanisms (--restart=always, env injection, HEALTHCHECK) cover all operational needs without custom infrastructure.

---

## Common Pitfalls

### Pitfall 1: pyproject.toml missing [project] section breaks pip install

**What goes wrong:** `pip install -e .` in the Dockerfile (or README quickstart) fails with "No pyproject.toml found" or "Could not build wheels" because `pyproject.toml` only contains `[tool.ruff]`.
**Why it happens:** `pyproject.toml` was created for linting config only; the `[project]` section with package metadata was never added.
**How to avoid:** Use `ENV PYTHONPATH=/app/src` in the Dockerfile instead of `pip install -e .`. This makes `python -m palimpsest.app` work without any pyproject.toml changes.
**Warning signs:** Build fails with "pip: ERROR: File 'setup.py' or 'pyproject.toml' not found".

### Pitfall 2: FastMCP stdio subprocess fails silently in Docker

**What goes wrong:** After deploying, uploading a manuscript processes through Transcription and Cleaning, but the Context Agent returns empty results or hangs at the MCP tool call stage. No error is shown.
**Why it happens:** Known issue (fastmcp #507) — stdio transport can fail in Docker if Python output is buffered or if subprocess stdin/stdout are not properly connected. When the JSON-RPC stream is corrupted, the ADK `McpToolset` may time out silently.
**How to avoid:**
1. Set `ENV PYTHONUNBUFFERED=1` in Dockerfile (prevents stdout buffering).
2. The MCP server.py already avoids `print()` — do not add any print statements.
3. Smoke test: after `docker run`, execute a manuscript that triggers the Context Agent and verify the historical notes table populates.
4. If stdio fails: fallback is to switch `StdioConnectionParams` in `context.py` to an HTTP transport (run MCP server separately on a fixed port).
**Warning signs:** Context Notes panel shows "No historical entities found" for a manuscript with obvious entities (persons, places).

### Pitfall 3: Oracle VM firewall has two independent layers

**What goes wrong:** Port 7860 is opened in the OCI Console security list, but requests still time out. Container is running and accessible on localhost.
**Why it happens:** Oracle Linux's OS-level firewall (firewalld/iptables) is an independent layer from the OCI VCN security list. Both must be configured.
**How to avoid:** After opening the OCI security list, run on the Oracle VM:
```bash
sudo firewall-cmd --zone=public --permanent --add-port=7860/tcp
sudo firewall-cmd --reload
```
**Warning signs:** `curl http://localhost:7860` works on the VM but `curl http://<oracle-ip>:7860` from another machine times out.

### Pitfall 4: Gradio defaults to 127.0.0.1 (not 0.0.0.0)

**What goes wrong:** Container starts, Gradio starts on `http://0.0.0.0:7860` is shown in logs, but no external connection can reach it.
**Why it happens:** Gradio's default `server_name` is `127.0.0.1` (loopback only). Even with port mapping (`-p 7860:7860`), Docker forwards to the container's IP, not loopback.
**How to avoid:** Set `ENV GRADIO_SERVER_NAME=0.0.0.0` in Dockerfile.
**Warning signs:** Docker logs show "Running on local URL: http://127.0.0.1:7860" instead of "http://0.0.0.0:7860".

### Pitfall 5: GOOGLE_API_KEY vs GEMINI_API_KEY mismatch

**What goes wrong:** Container starts, Gradio loads, but pipeline fails immediately with an authentication error or "GOOGLE_API_KEY not set" even though `GEMINI_API_KEY` was injected.
**Why it happens:** The code checks `os.environ.get("GOOGLE_API_KEY")` in `run.py` and the google-adk SDK reads `GOOGLE_API_KEY`. If the Docker run command injects `GEMINI_API_KEY=...`, it is not read.
**How to avoid:** Always use `GOOGLE_API_KEY` as the env var name in Docker run commands, `.env.example`, and documentation.
**Warning signs:** `run.py` error: "GOOGLE_API_KEY environment variable is not set" despite having passed a key.

### Pitfall 6: Kaggle writeup saved but not submitted

**What goes wrong:** Writeup is complete, cover image and video are attached, but judges do not see it.
**Why it happens:** Kaggle has a two-step flow: Save (creates draft) and Submit (makes it eligible). Draft writeups are explicitly excluded from judging.
**How to avoid:** After saving, look for the "Submit" button in the top-right corner of the Kaggle writeup page and click it before the deadline (July 6, 2026 at 11:59 PM PT).
**Warning signs:** The writeup status shows "Draft" rather than "Submitted".

### Pitfall 7: Cover image not attached = cannot submit

**What goes wrong:** Attempting to click Submit fails with a validation error.
**Why it happens:** Kaggle requires a cover image to be attached to the Media Gallery before submission. The Submit button may not appear or may be disabled without it.
**How to avoid:** Attach the cover image (screenshot of Gradio UI with pares_easy_18c.jpg result) to the Media Gallery first, before attempting to submit.

---

## Code Examples

### Minimal Dockerfile (verified pattern)

```dockerfile
# Source: gradio.app/guides/deploying-gradio-with-docker [CITED]
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY data/samples/ ./data/samples/

ENV PYTHONPATH=/app/src
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

CMD ["python", "-m", "palimpsest.app"]
```

### Optional HEALTHCHECK (requires curl in container)

```dockerfile
# Add before CMD if curl is available
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1
```

Note: `start-period=90s` accounts for Gradio startup time + first `load_dotenv()` call. Adjust if needed.

### .env.example content (correct env var names)

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

### Oracle VM firewall commands

```bash
# Source: docs.oracle.com/en-us/iaas/Content/Network/Concepts/securitylists.htm [CITED]

# Check current firewall state
sudo firewall-cmd --list-ports

# Open port 7860 permanently
sudo firewall-cmd --zone=public --permanent --add-port=7860/tcp
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-ports  # should include 7860/tcp
```

### README architecture diagram (updated for Phase 3 additions)

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

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Cloud Run deploy (D-04 originally) | Oracle VM Docker | No cold start, no GCP billing, existing infra |
| `pip install -e .` in Dockerfile | `ENV PYTHONPATH=/app/src` | No pyproject.toml [project] section needed |
| Manual server_name="0.0.0.0" in code | `GRADIO_SERVER_NAME=0.0.0.0` env var | No app.py modification required |
| Single OCI firewall rule | OCI security list + OS firewalld | Two layers required on Oracle Linux |

**Deprecated/outdated:**
- `CMD python app.py` (flat layout): Requires `WORKDIR /app/src` and breaks imports. Use `-m` flag with `PYTHONPATH` instead.
- `GRADIO_ANALYTICS_ENABLED=False` as privacy consideration: Still valid but not required for competition submission.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Oracle VM runs Oracle Linux 8.x (uses firewalld, not ufw) | Common Pitfalls #3, Code Examples | If Ubuntu: use `sudo ufw allow 7860/tcp` instead |
| A2 | Docker is already installed on the Oracle VM | Common Pitfalls #3, Oracle VM workflow | Need to install Docker Engine first |
| A3 | `GEMINI_API_KEY` in CONTEXT.md D-09/D-10 is a naming error; the correct name is `GOOGLE_API_KEY` per codebase | Critical Findings #1 | If SDK was updated to read GEMINI_API_KEY, planner must update codebase too |
| A4 | Custom domain DNS A record is already pointing to Oracle VM IP (CONTEXT.md D-03) | Architecture Patterns | If not configured: use `http://oracle-ip:7860` as Public Project Link |
| A5 | FastMCP stdio subprocess will work in Docker with PYTHONUNBUFFERED=1 | Common Pitfalls #2 | If stdio fails: fallback is HTTP transport for MCP (requires context.py modification) |
| A6 | The pares_easy_18c.jpg demo manuscript produces clean output for the before/after excerpt | Phase Requirements DOC-03 | Need to run pipeline on the image before recording video to verify |

---

## Open Questions

1. **Does the Oracle VM already have Docker installed?**
   - What we know: VM exists and is accessible. Context says "existing server".
   - What's unclear: Whether Docker Engine is installed and running.
   - Recommendation: First task in deployment wave should verify `docker --version` and install if missing.

2. **Is the OCI security list rule for port 7860 already configured?**
   - What we know: VM was provisioned for other uses.
   - What's unclear: Whether port 7860 was opened in OCI Console previously.
   - Recommendation: Include OCI security list verification step in the deploy plan.

3. **Does pares_easy_18c.jpg produce a clean, complete transcription?**
   - What we know: It was selected as "easier cursive" (D-11). The pipeline is complete from Phase 3.
   - What's unclear: Actual output quality. The before/after excerpt in the Writeup depends on a real pipeline run.
   - Recommendation: Run `python -m palimpsest.run data/samples/pares_easy_18c.jpg` immediately after Docker smoke test to capture the output for the Writeup excerpt.

4. **Is a Docker Hub account available for image transfer, or is the direct SSH pipe method preferred?**
   - What we know: Both methods work. Direct SSH pipe (docker save | gzip | ssh | docker load) requires no registry.
   - Recommendation: Use direct SSH pipe method to avoid creating a public Docker Hub repo that might expose image layers.

---

## Environment Availability

| Dependency | Required By | Available | Fallback |
|------------|------------|-----------|----------|
| Docker Engine (local) | Build image | [ASSUMED] check with `docker --version` | Install Docker Desktop |
| SSH access to Oracle VM | Transfer image, run container | [ASSUMED] per "existing server" in CONTEXT.md | — |
| Docker Engine (Oracle VM) | Run container | [ASSUMED] — needs verification | `curl -fsSL https://get.docker.com \| sh` |
| Port 7860 OCI security list | External access | [ASSUMED] — needs OCI Console check | Add ingress rule |
| Port 7860 OS firewall (Oracle VM) | External access | [ASSUMED] — needs `firewall-cmd --list-ports` | `firewall-cmd --add-port=7860/tcp` |
| OBS Studio | Video recording | [ASSUMED] — user confirmed in CONTEXT.md D-14 | — |
| YouTube account | Video upload | [ASSUMED] | — |
| Kaggle account with writeup rights | Submission | [ASSUMED] | — |

**Missing dependencies with no fallback:** None identified (all have either confirmed alternatives or are user-controlled).

---

## Security Domain

`security_enforcement: true`, `security_asvs_level: 1`

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V1 Architecture | yes | Single-container pattern; no privileged mode |
| V2 Authentication | no | No user auth in this phase |
| V5 Input Validation | yes | GOOGLE_API_KEY presence check at startup |
| V10 Malicious Code | yes | No secrets baked in image layers; .dockerignore covers .env |
| V14 Configuration | yes | PYTHONUNBUFFERED, no debug mode, no Gradio share=True |

### Known Threat Patterns for Docker + Gradio

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Secret in Docker layer (API key via ARG/ENV at build time) | Information disclosure | Inject at runtime via `docker run -e` only; never in Dockerfile |
| .env file copied into image | Information disclosure | `.dockerignore` must exclude `.env` |
| Gradio share=True in production | Spoofing / exposure | share=False (default); never set True in Dockerfile CMD |
| Container running as root | Elevation of privilege | Consider adding `USER 1001` before CMD; not required for competition |
| PYTHONPATH traversal | Tampering | PYTHONPATH scoped to /app/src only; no user-controlled path components |

**DEP-03 verification gate:** After `docker build`, run `docker history <image>` and confirm no env layer contains `GOOGLE_API_KEY`. The key must only appear at container runtime.

---

## Sources

### Primary (MEDIUM confidence — official documentation)
- [gradio.app/guides/deploying-gradio-with-docker](https://gradio.app/guides/deploying-gradio-with-docker) — GRADIO_SERVER_NAME env var, Dockerfile pattern
- [gradio.app/guides/environment-variables](https://gradio.app/guides/environment-variables) — GRADIO_SERVER_NAME/GRADIO_SERVER_PORT defaults and behavior
- [docs.oracle.com — Security Lists](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securitylists.htm) — OCI security list ingress rules
- [adk.dev/agents/models/google-gemini/](https://adk.dev/agents/models/google-gemini/) — GOOGLE_API_KEY env var for Python ADK
- `docs/rules.md` (in-repo) — Kaggle submission requirements, word limits, deadlines

### Secondary (LOW confidence — community sources, cross-checked with codebase)
- [github.com/jlowin/fastmcp/issues/507](https://github.com/jlowin/fastmcp/issues/507) — FastMCP stdio Docker failure, closed as not planned
- [snyk.io/blog/best-practices-containerizing-python-docker/](https://snyk.io/blog/best-practices-containerizing-python-docker/) — Python Docker layer ordering
- [marcinmitruk.link/posts/how-to-open-ports-80-and-443-on-an-oracle-cloud-instance/](https://marcinmitruk.link/posts/how-to-open-ports-80-and-443-on-an-oracle-cloud-instance/) — Oracle Linux two-layer firewall

### Codebase inspection (HIGH confidence — directly read)
- `src/palimpsest/app.py` — Confirmed: no server_name/server_port in demo.launch()
- `src/palimpsest/mcp/server.py` — Confirmed: no print() calls; uses `if __name__ == "__main__": mcp.run()`
- `src/palimpsest/agents/context.py` — Confirmed: sys.executable + StdioServerParameters subprocess pattern
- `src/palimpsest/run.py` — Confirmed: reads GOOGLE_API_KEY (not GEMINI_API_KEY)
- `requirements.txt` — Confirmed: 7 packages, no new packages needed for Phase 4
- `pyproject.toml` — Confirmed: only [tool.ruff], no [project] section

---

## Metadata

**Confidence breakdown:**
- Dockerfile pattern: MEDIUM — verified against official Python and Gradio Docker docs
- Gradio env vars: MEDIUM — confirmed from official gradio.app documentation
- Oracle VM firewall: LOW — community source (marcinmitruk.link) cross-checked with OCI official docs; specific OS flavor assumed
- FastMCP stdio Docker: LOW — single issue report, closed; actual behavior depends on Docker version and FastMCP version in container
- Kaggle submission steps: MEDIUM — sourced directly from `docs/rules.md` in the repo (the official competition rules text)
- Codebase findings (gaps): HIGH — directly inspected source files

**Research date:** 2026-06-28
**Valid until:** 2026-07-06 (competition deadline; Kaggle submission rules may be updated)

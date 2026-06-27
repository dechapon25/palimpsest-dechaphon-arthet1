---
phase: 04-deploy-submission-artifacts
plan: "01"
subsystem: container-foundation
tags:
  - docker
  - gradio
  - deployment
  - security
dependency_graph:
  requires:
    - 03-03-SUMMARY.md
  provides:
    - Dockerfile
    - .dockerignore
    - .env.example
    - app.py (server_name/server_port)
  affects:
    - Oracle VM deployment (Plan 04-02)
tech_stack:
  added:
    - python:3.11-slim (Docker base image)
    - Docker HEALTHCHECK with curl
  patterns:
    - PYTHONPATH=/app/src (no pyproject.toml [project] section)
    - GRADIO_SERVER_NAME=0.0.0.0 (container port binding)
    - PYTHONUNBUFFERED=1 (FastMCP stdio subprocess safety)
    - Runtime credential injection via docker run -e
key_files:
  created:
    - Dockerfile
    - .dockerignore
  modified:
    - .env.example (updated from 3-line stub to full 4-var documentation)
    - src/palimpsest/app.py (demo.launch() gains server_name and server_port)
decisions:
  - "D-05 (python:3.11-slim) followed exactly"
  - "D-06 (server_port=int(os.environ.get('PORT', 7860))) implemented in app.py"
  - "D-07 (PYTHONUNBUFFERED=1) implemented in Dockerfile"
  - "D-10 (credentials at runtime only) enforced — zero credential ENV in Dockerfile"
  - "GOOGLE_API_KEY used (corrected from CONTEXT.md D-09 GEMINI_API_KEY per codebase)"
  - "HEALTHCHECK with curl added (Claude discretion — 90s start-period for Gradio)"
metrics:
  duration: "~3 minutes"
  completed: "2026-06-27"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 2
status: complete
requirements:
  - DEP-01
  - DEP-03
  - DEP-04
---

# Phase 04 Plan 01: Container Foundation Summary

**One-liner:** Dockerfile + .dockerignore + .env.example + app.py launch fix with PYTHONPATH, GRADIO_SERVER_NAME, PYTHONUNBUFFERED, and zero credentials baked in.

## What Was Built

Created the container foundation for the Palimpsest Kaggle submission deployment:

1. **Dockerfile** — python:3.11-slim base; requirements.txt cached in Layer 1 before source copy; three critical ENV vars (PYTHONPATH, GRADIO_SERVER_NAME, PYTHONUNBUFFERED); curl installed for HEALTHCHECK; CMD runs `python -m palimpsest.app`; no credentials baked in any layer.

2. **.dockerignore** — excludes `.env` and `.env.*` from build context (T-04-02 mitigation); also excludes `.git/`, `__pycache__/`, `.venv/`, `.planning/`, `docs/`, `tests/`, `*.md`.

3. **.env.example** — updated from the prior 3-line stub to full 4-variable documentation with correct env var names: `GOOGLE_API_KEY` (not `GEMINI_API_KEY`), `PALIMPSEST_MAX_UPLOAD_MB`, `PALIMPSEST_CONFIDENCE_THRESHOLD`, `PORT`.

4. **src/palimpsest/app.py** — `demo.launch()` updated to add `server_name="0.0.0.0"` and `server_port=int(os.environ.get("PORT", 7860))` with explanatory comments. `import os` was already present (line 32).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write Dockerfile, .dockerignore, .env.example | 5740544 | Dockerfile (new), .dockerignore (new), .env.example (modified) |
| 2 | Fix app.py demo.launch() + verify static content | 2fd9aa0 | src/palimpsest/app.py |

## Deviations from Plan

### Environment Limitation — Docker not available in execution environment

**Found during:** Task 2  
**Issue:** The execution environment (WSL2 with Claude Code) does not have Docker Engine installed. `docker build` and the smoke test commands returned `command not found`.  
**Resolution:** All Dockerfile content was verified via static analysis (grep checks on ENV vars, CMD, COPY paths). The `app.py` change was verified with Python AST parsing. The Docker build and smoke test (acceptance criteria steps 3-6) must be run by the user on a machine with Docker or directly on the Oracle VM.  
**Impact:** No code impact. All artifacts are complete and correct. Manual verification required before Oracle VM deploy.  
**Files modified:** None (environment constraint, not code fix).

### Auto-fix: .env.example existed but was outdated (Rule 2)

**Found during:** Task 1  
**Issue:** `.env.example` already existed (created 2026-06-21) with only `GOOGLE_API_KEY=<your-key-here>` — missing `PALIMPSEST_MAX_UPLOAD_MB`, `PALIMPSEST_CONFIDENCE_THRESHOLD`, and `PORT`.  
**Fix:** Replaced content with full 4-variable documentation per plan specification.  
**Files modified:** `.env.example`

### Naming correction: GEMINI_API_KEY → GOOGLE_API_KEY (Rule 1)

**Found during:** Task 1 research review  
**Issue:** CONTEXT.md D-09/D-10 specified `GEMINI_API_KEY` but `src/palimpsest/run.py` lines 28-31 read `GOOGLE_API_KEY`. The plan explicitly corrected this.  
**Fix:** `.env.example` uses `GOOGLE_API_KEY=` with a comment explaining the correct name.  
**Files modified:** `.env.example`

## Security Verification

| Threat | Mitigation | Status |
|--------|-----------|--------|
| T-04-01: Credentials in Dockerfile ENV | No `ENV GOOGLE_API_KEY` in Dockerfile; only PYTHONPATH/GRADIO_SERVER_NAME/PYTHONUNBUFFERED | VERIFIED |
| T-04-02: .env in Docker build context | `.env` listed first in .dockerignore | VERIFIED |
| T-04-03: API key in container logs | app.py never logs env var values; greeting and error messages contain no key values | VERIFIED |
| T-04-04: Container running as root | Accepted (per plan; competition submission, no multi-tenancy) | ACCEPTED |
| T-04-06: Gradio share=True | `grep 'share=True'` returns empty — confirmed absent | VERIFIED |

## Manual Verification Steps Required

Since Docker is not available in the execution environment, the following must be run by the user before deploying to Oracle VM:

```bash
# From repo root with Docker installed:
docker build -t palimpsest .

# Smoke test:
docker run --rm -d --name palimpsest_smoke -e GOOGLE_API_KEY=smoke_test -p 7861:7860 palimpsest
sleep 15
curl -s -o /dev/null -w "%{http_code}" http://localhost:7861/
# Expected: 200

# Verify container logs show 0.0.0.0 binding (not 127.0.0.1):
docker logs palimpsest_smoke 2>&1 | grep "Running on"

# Verify no credentials in image ENV layer:
docker inspect palimpsest --format='{{range .Config.Env}}{{println .}}{{end}}'
# Expected: exactly 3 lines (PYTHONPATH, GRADIO_SERVER_NAME, PYTHONUNBUFFERED)

docker stop palimpsest_smoke
```

## Known Stubs

None. All env vars documented in `.env.example` are functional. The `PORT` default of 7860 is correct for Oracle VM.

## Threat Flags

No new threat surface introduced beyond what is documented in the plan's threat model.

## Self-Check: PASSED

- [x] Dockerfile exists at /home/carlosapsa/palimpsest/Dockerfile
- [x] .dockerignore exists at /home/carlosapsa/palimpsest/.dockerignore
- [x] .env.example updated at /home/carlosapsa/palimpsest/.env.example
- [x] src/palimpsest/app.py modified with server_name and server_port
- [x] Commit 5740544 — Task 1 artifacts
- [x] Commit 2fd9aa0 — Task 2 app.py fix
- [x] PYTHONPATH=/app/src in Dockerfile ✓
- [x] GRADIO_SERVER_NAME=0.0.0.0 in Dockerfile ✓
- [x] PYTHONUNBUFFERED=1 in Dockerfile ✓
- [x] .env in .dockerignore ✓
- [x] GOOGLE_API_KEY= in .env.example ✓
- [x] server_name="0.0.0.0" in app.py ✓
- [x] server_port=int(os.environ.get("PORT", 7860)) in app.py ✓
- [x] No credentials in Dockerfile ENV/ARG ✓
- [x] No share=True in app.py ✓

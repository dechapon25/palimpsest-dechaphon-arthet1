# Walking Skeleton — Palimpsest

**Phase:** 1
**Generated:** 2026-06-21

## Capability Proven End-to-End

A researcher runs `python -m palimpsest.run <image_path>` with a JPG or PNG manuscript scan and receives a structured JSON dict containing the raw Gemini transcription — passing through security validation, EXIF stripping, and the ADK pipeline in a single command.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Agent framework | Google ADK 2.3.0 — `SequentialAgent` + `LlmAgent` | Required by competition; declarative pipeline clearly demonstrates multi-agent concept to judges; handles session state, invocation context, and event streaming out of the box |
| Vision model | `gemini-2.5-pro` (fallback for "Gemini 3 Pro") | D-01: only model that passed 3/4 cursive manuscript pages in field tests; Flash failed; `maxOutputTokens=65536` mandatory or silent truncation |
| API client | `google-genai` 2.9.0 — `genai.Client(api_key=...)` | New unified Google Gen AI SDK; required by ADK 2.x; the deprecated `google-generativeai` / `genai.configure()` pattern must not be used |
| Security intake | `filetype` (magic bytes) + `Pillow` (EXIF strip) | Zero system dependencies (vs `python-magic` which needs `libmagic`); pure Python; correct for Docker slim images |
| Prompt injection defense | Double barrier: `response_mime_type="application/json"` in `GenerateContentConfig` + explicit "data, not instructions" system prompt | D-18: defense-in-depth for OWASP LLM01:2025; structured output prevents fence wrapping; system prompt boundary extends to downstream agents in Phase 2 |
| Package layout | `src/palimpsest/` with `agents/`, `security/`, `mcp/` sub-packages | D-12: clean separation; `mcp/` created empty to avoid Phase 2 restructuring; Phase 3 Gradio UI imports `security/intake.py` without modification |
| Dependency manager | `pip` + `requirements.txt` | D-14: explicit choice over uv/poetry; simpler CI for competition timeline |
| Python version | 3.11 (Docker target) / 3.12 (local dev compatible) | D-15: `python:3.11-slim` for Phase 4 Docker base; ADK 2.3.0 confirmed compatible with 3.12 for local dev |
| Linting | Ruff — `ruff check .` + `ruff format .` | D-16: single fast tool; configured in `pyproject.toml` (tool config only, no build system) |
| Environment loading | `python-dotenv` — `load_dotenv()` called once in `run.py` entry point | D-19: standard env pattern; `.env` gitignored; `.env.example` documents variable names only |
| Output schema | Frozen Python dict: `{status, raw_transcription, metadata:{filename, model, tokens_used}, errors:[]}` | D-11: Phase 2 agents extend `metadata` but must not remove existing keys; Phase 3 Gradio consumes this schema directly |
| Test runner | `pytest` — unit tests only in Phase 1 (no API calls) | D-17: SEC-01 through SEC-04 are pure Python logic; integration tests deferred to Phase 2 |
| Deployment target | Local CLI only in Phase 1; Cloud Run in Phase 4 | D-15, DEP-02: Docker base image locked now; actual deployment deferred to Day 14 |

## Stack Touched in Phase 1

- [x] Project scaffold — `src/palimpsest/` package, `requirements.txt`, `pyproject.toml`, `.gitignore`, `.env.example`
- [x] Security layer — `security/intake.py` with file-type validation (magic bytes), size check, and EXIF stripping
- [x] Agent pipeline — `agents/transcription.py` (LlmAgent) + `agents/orchestrator.py` (SequentialAgent + Runner)
- [x] CLI entry point — `run.py` wires load_dotenv + security gate + ADK pipeline + structured output
- [x] Real Gemini API call — `gemini-2.5-pro` vision call on a real PARES manuscript scan
- [x] Unit tests — `tests/test_intake.py` covers SEC-01 through SEC-04 with no API calls
- [ ] Database — not applicable; stateless pipeline
- [ ] Deployment — documented local run command; Cloud Run deferred to Phase 4

## Out of Scope (Deferred to Later Slices)

- Cleaning agent and paleographic abbreviation expansion (Phase 2 — CLN-01 through CLN-03)
- FastMCP server and historical context tools (Phase 2 — MCP-01 through MCP-06)
- Context enrichment agent for named entities (Phase 2 — CTX-01 through CTX-03)
- Confidence scoring and uncertainty highlights (Phase 3 — VER-01 through VER-03)
- Gradio demo interface (Phase 3 — UI-01 through UI-05)
- Docker containerization and Cloud Run deploy (Phase 4 — DEP-01, DEP-02)
- README, Kaggle Writeup, and video (Phase 4 — DOC-01 through DOC-04)
- Image preprocessing (contrast/deskew) — deferred per D-08; revisit in Phase 2 only if quality requires it
- Retry logic — deferred per D-10; Phase 1 uses simple error propagation
- Integration tests — deferred to Phase 2 when pipeline has more layers

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering its architectural decisions:

- Phase 2: Raw transcription passes through cleaning agent (Agent Skill) and context agent querying FastMCP for historical enrichment
- Phase 3: Researcher sees confidence-scored, highlighted transcription and historical notes in a Gradio interface
- Phase 4: Application runs as a publicly accessible Cloud Run container; all Kaggle submission artifacts ready

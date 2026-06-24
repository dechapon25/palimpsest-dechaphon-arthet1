---
phase: 01
slug: mvp-linear-pipeline
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-25
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| filesystem → security intake | User-supplied file path; any content could be malicious | Raw file bytes (untrusted) |
| security intake → Pillow | Raw bytes cross into parsing library before EXIF strip | Image bytes (magic-byte validated) |
| CLI args → run.py | User-controlled image_path | String path (no shell interpolation) |
| clean bytes → ADK Session | EXIF-stripped bytes enter ADK runner | Clean image bytes + MIME type |
| ADK Session → Gemini API | Agent instruction + image sent to Google infrastructure | Prompt + image bytes |
| Gemini response → output dict | Raw transcription treated as data only | JSON string (never executed) |
| GOOGLE_API_KEY → process env | Loaded via python-dotenv from .env | Secret credential |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-01-01 | Tampering | `security/intake.py` — file type check | mitigate | `filetype.guess()` magic bytes — never trusts extension | closed |
| T-01-02 | Denial of Service | `security/intake.py` — file size | mitigate | `stat().st_size` check before reading; 20 MB limit + decompression bomb guard | closed |
| T-01-03 | Information Disclosure | `security/intake.py` — EXIF metadata | mitigate | `Image.new()` + pixel copy — no metadata carried over | closed |
| T-01-04 | Elevation of Privilege | `agents/transcription.py` — prompt injection | mitigate | Barrier 1: system prompt labels content as data; Barrier 2: `response_mime_type="application/json"` | closed |
| T-01-05 | Information Disclosure | `.env` / `GOOGLE_API_KEY` | mitigate | `.gitignore` excludes `.env`; `.env.example` has placeholders only | closed |
| T-01-06 | Tampering | Package legitimacy | mitigate | All 5 packages verified in RESEARCH.md audit; pinned versions | closed |
| T-02-01 | Elevation of Privilege | `agents/transcription.py` — prompt injection via manuscript | mitigate | `TRANSCRIPTION_INSTRUCTION` labels document text as historical data; `response_mime_type` enforces JSON | closed |
| T-02-02 | Elevation of Privilege | `agents/orchestrator.py` — downstream consumption | mitigate | Phase 2+ agents must include system prompt boundary (documented) | closed |
| T-02-03 | Information Disclosure | `run.py` — API key in output | mitigate | Key loaded from env, never in output dict or printed | closed |
| T-02-04 | Denial of Service | `run.py` — Gemini API timeout | accept | No timeout in Phase 1 CLI; deferred to Phase 2 per D-10 | closed |
| T-02-05 | Integrity | `agents/orchestrator.py` — partial transcription | mitigate | None/empty check returns error; finish_reason deferred to Phase 2 | closed |
| T-02-06 | Tampering | `run.py` — CLI arg as filesystem path | mitigate | `pathlib.Path()` only — no shell, no eval, no subprocess | closed |
| T-02-07 | Tampering | Package legitimacy | mitigate | All packages pre-verified; no new packages in Plan 02 | closed |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | T-02-04 | Phase 1 is CLI-only; no user-facing timeout needed; deferred to Phase 2 | Developer | 2026-06-25 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-25 | 13 | 13 | 0 | gsd-secure-phase |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-25

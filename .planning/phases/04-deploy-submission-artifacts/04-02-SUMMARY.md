---
phase: 04-deploy-submission-artifacts
plan: "02"
subsystem: deployment
tags:
  - docker
  - oracle-vm
  - firewall
  - gradio
  - public-url

requires:
  - phase: 04-01
    provides: Dockerfile + image artifact (palimpsest:latest)
provides:
  - Running container palimpsest-prod on Oracle VM (palimpsest.cpaz.es)
  - OS-level firewall rule: 7860/tcp via firewalld (permanent)
  - OCI Console VCN security list: TCP 7860 ingress rule
  - Public URL: http://palimpsest.cpaz.es:7860/
  - Full pipeline smoke test (pares_easy_18c.jpg end-to-end with Historical Notes)
affects:
  - 04-03 (Kaggle Writeup + video — needs the confirmed public URL)

tech-stack:
  added:
    - Docker Engine on Oracle VM (Oracle Linux / Oracle Cloud)
    - firewalld (OS-level port management)
    - OCI Console VCN security list (cloud-level port management)
  patterns:
    - Oracle VM requires TWO independent firewall layers: OS firewalld + OCI Console security list
    - docker run --restart=always for auto-start on VM reboot
    - GOOGLE_API_KEY injected at runtime (never baked into image)

key-files:
  created: []
  modified: []

key-decisions:
  - "Public URL confirmed as http://palimpsest.cpaz.es:7860/ (IP-based, no custom domain required for Kaggle submission)"
  - "Both firewall layers mandatory: opening OCI Console only is insufficient (OS firewalld blocks even if OCI allows)"
  - "GOOGLE_API_KEY injected via -e flag at docker run time to avoid shell history exposure risk"
  - "FastMCP stdio subprocess confirmed working — Context Agent populates Historical Notes correctly"

patterns-established:
  - "Oracle dual-firewall pattern: always open both OCI Console security list AND OS firewalld for any new port"

requirements-completed:
  - DEP-02

coverage:
  - id: D1
    description: "Container palimpsest-prod running on Oracle VM with restart=always, binding 0.0.0.0:7860"
    requirement: DEP-02
    verification:
      - kind: manual_procedural
        ref: "ssh oracle-vm 'docker ps --filter name=palimpsest-prod' → Up status confirmed"
        status: pass
      - kind: manual_procedural
        ref: "ssh oracle-vm 'curl localhost:7860' → HTTP 200"
        status: pass
    human_judgment: false
  - id: D2
    description: "OS-level firewall (firewalld) permanently allows TCP 7860"
    requirement: DEP-02
    verification:
      - kind: manual_procedural
        ref: "ssh oracle-vm 'sudo firewall-cmd --list-ports' → includes 7860/tcp"
        status: pass
    human_judgment: false
  - id: D3
    description: "OCI Console VCN security list TCP 7860 ingress rule active"
    requirement: DEP-02
    verification:
      - kind: manual_procedural
        ref: "OCI Console → Security Lists → Default → Ingress Rules: TCP 7860 from 0.0.0.0/0 confirmed"
        status: pass
    human_judgment: true
    rationale: "Browser-only OCI Console action — no CLI path available without OCI CLI setup; human verified visually"
  - id: D4
    description: "Public URL http://palimpsest.cpaz.es:7860/ reachable from external network with HTTP 200"
    requirement: DEP-02
    verification:
      - kind: manual_procedural
        ref: "curl -s -o /dev/null -w '%{http_code}' http://palimpsest.cpaz.es:7860/ → 200 from external network"
        status: pass
    human_judgment: false
  - id: D5
    description: "Full end-to-end pipeline smoke test: pares_easy_18c.jpg uploaded via Gradio UI, all 4 panels populate including Historical Notes"
    requirement: DEP-02
    verification:
      - kind: manual_procedural
        ref: "Browser: http://palimpsest.cpaz.es:7860/ → upload pares_easy_18c.jpg → Raw/Clean/Historical Notes/Confidence all populated"
        status: pass
    human_judgment: true
    rationale: "End-to-end visual verification of all Gradio UI panels requires human judgment; FastMCP context agent correctness must be assessed by reviewer"

duration: "~60 minutes (user-executed infrastructure tasks + OCI Console configuration)"
completed: "2026-06-27"
status: complete
---

# Phase 04 Plan 02: Oracle VM Deploy + Public Access Summary

**Docker container palimpsest-prod deployed to Oracle VM at http://palimpsest.cpaz.es:7860/ with dual-layer firewall (OS firewalld + OCI Console) open and full pipeline verified end-to-end including FastMCP Context Agent.**

## Performance

- **Duration:** ~60 minutes (user-executed infrastructure + OCI Console browser steps)
- **Completed:** 2026-06-27
- **Tasks:** 2/2
- **Files modified:** 0 (pure infrastructure deployment — no repository files changed)

## Accomplishments

- Container `palimpsest-prod` running on Oracle Cloud VM (palimpsest.cpaz.es) with `--restart=always`, surviving reboots
- OS firewall permanently opened: `sudo firewall-cmd --zone=public --permanent --add-port=7860/tcp`
- OCI Console VCN security list ingress rule added: TCP port 7860 from 0.0.0.0/0
- Public URL `http://palimpsest.cpaz.es:7860/` confirmed accessible from external network (HTTP 200)
- Full pipeline smoke test completed: `pares_easy_18c.jpg` processed with all 4 Gradio panels populated, Historical Notes confirmed (Context Agent / FastMCP stdio subprocess working correctly)
- `GOOGLE_API_KEY` injected at runtime via `-e` flag — no credentials baked into image or shell history

## Task Commits

This plan modified no repository files. Both tasks were pure infrastructure operations performed on Oracle VM and OCI Console:

1. **Task 1: Transfer image + OS firewall + deploy container** — infrastructure-only (no git commit)
2. **Task 2: OCI Console security list + full public access verification** — human-verified checkpoint (no git commit)

**Plan metadata commit:** (see final commit hash below)

## Files Created/Modified

None. This plan is a pure infrastructure deployment plan. All artifacts are live running services:

- Running Docker container on Oracle VM (palimpsest-prod)
- Permanent OS firewall rule (survives reboots via firewalld --permanent)
- OCI Console VCN security list ingress rule (persists in OCI network configuration)

## Deployment Details

| Component | Value |
|-----------|-------|
| Oracle VM IP | palimpsest.cpaz.es |
| Public URL | http://palimpsest.cpaz.es:7860/ |
| Container name | palimpsest-prod |
| Restart policy | always |
| Port binding | 0.0.0.0:7860→7860/tcp |
| OS firewall | firewalld — 7860/tcp permanent |
| OCI Console | VCN security list — TCP 7860 ingress from 0.0.0.0/0 |
| Pipeline smoke test | pares_easy_18c.jpg — all 4 panels populated |

## Decisions Made

- **IP-based URL (no custom domain):** http://palimpsest.cpaz.es:7860/ is sufficient for Kaggle judge access. Custom domain (D-03 option) not required within the competition timeline.
- **Both firewall layers required:** Oracle VM has two independent firewall layers. Opening OCI Console security list alone does NOT allow traffic — OS firewalld must also be opened. This was the documented Pitfall 3 in RESEARCH.md; applied correctly.
- **API key via -e flag at runtime:** Avoids key in shell history. Consistent with T-04-D-01 mitigation from the plan's threat model.
- **FastMCP stdio subprocess confirmed working:** `PYTHONUNBUFFERED=1` set in Dockerfile (Plan 01) ensured the MCP server subprocess doesn't buffer output silently. Validated by Historical Notes populating correctly during smoke test.

## Deviations from Plan

None — plan executed exactly as written. Both firewall layers were opened in the documented order (OS firewall in Task 1, OCI Console in Task 2). The FastMCP subprocess worked on first try with no debugging required.

## Issues Encountered

None. The dual-firewall configuration matched RESEARCH.md documentation exactly. FastMCP Context Agent required no additional troubleshooting.

## Security Verification

| Threat | Mitigation | Status |
|--------|------------|--------|
| T-04-D-01: GOOGLE_API_KEY in docker run command / shell history | Key passed via `-e GOOGLE_API_KEY=...` in SSH session (not committed or stored in repo) | APPLIED |
| T-04-D-02: DoS via public Gradio endpoint | Accepted — short-lived competition deployment, no rate limiting needed | ACCEPTED |
| T-04-D-03: Wikidata/Wikipedia external calls | Informational only, no PII, public domain data | ACCEPTED |

## Known Stubs

None.

## Threat Flags

No new threat surface beyond what is documented in the plan's threat model.

## Next Phase Readiness

- Plan 04-03 (README + Writeup + video) can proceed immediately
- Public URL for inclusion in Writeup and video: **http://palimpsest.cpaz.es:7860/**
- All pipeline functionality confirmed working on the live deployment
- No blockers

## Self-Check: PASSED

- [x] Public URL confirmed reachable: http://palimpsest.cpaz.es:7860/
- [x] Container palimpsest-prod running with restart=always
- [x] OS firewall (firewalld) permanently allows 7860/tcp
- [x] OCI Console security list TCP 7860 ingress rule active
- [x] Full pipeline smoke test passed (pares_easy_18c.jpg, all 4 panels)
- [x] FastMCP Context Agent (Historical Notes) confirmed working
- [x] No credentials in repository

---
*Phase: 04-deploy-submission-artifacts*
*Completed: 2026-06-27*

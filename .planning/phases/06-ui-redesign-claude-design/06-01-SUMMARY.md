---
phase: "06"
plan: "06-01"
subsystem: ui
tags: [css, gradio, parchment-theme, design-tokens, fonts]
title: "CSS Theme Overhaul — Parchment Light Design"
status: complete

key-decisions:
  - "Replaced dark glassmorphism (#0F172A slate) with parchment light theme (#F1EADA)"
  - "Changed status_md from gr.Markdown to gr.HTML to enable metadata bar HTML injection in Wave 2"
  - "view_toggle choices reordered to Limpiada|Original per design spec; toggle_view() updated accordingly"
  - "body::before watermark uses rgba(35,25,15,0.038) to stay barely visible over parchment"

key-files:
  modified:
    - src/palimpsest/app.py

metrics:
  completed: "2026-07-01"
  tasks_completed: 2
  files_modified: 1
  commit: "eddeb21"
---

# Phase 06 Plan 01: CSS Theme Overhaul — Parchment Light Design Summary

## One-liner

Replaced dark glassmorphism Gradio UI with a parchment light theme using Spectral serif fonts, terracotta accent (#AE3B2C), and Claude Design handoff tokens — all in `src/palimpsest/app.py`.

## What was done

### Task 1 — CUSTOM_CSS replacement (lines 49–167 → new block)

The entire `CUSTOM_CSS` constant was replaced. Old theme: dark slate `#0F172A` background, amber `#C9A84C` accent, glassmorphism `backdrop-filter: blur`, `overflow: hidden` on body (no scrolling).

New theme includes:
- `@import` for Spectral / Hanken Grotesk / IBM Plex Mono from Google Fonts
- `:root` block with all `--pal-*` design tokens from Claude Design handoff
- `body, html`: `background-color: #F1EADA !important` + `overflow-x: hidden` only (natural scroll preserved)
- `body::before`: fixed italic Spectral watermark at `rgba(35,25,15,0.038)`, 40px, -1deg rotation
- `.gradio-container`: parchment bg + all Gradio CSS variable overrides (`--loader-color`, `--block-background-fill`, `--body-text-color`, etc.) in single rule block
- `.pal-header`, `.pal-logo-mark` (48px dark box + terracotta bottom shadow), `.pal-header-title`, `.pal-header-sub`
- `.pal-upload-zone`: dashed `rgba(174,59,44,0.40)` border on `#FBF8F0` card
- `.pal-card`: 16px radius, `var(--pal-shadow)`, `#FBF8F0` background
- `.pal-results-grid`: `1.55fr 1fr` CSS grid with `grid-template-areas`
- `.pal-notes-grid`: `repeat(auto-fill, minmax(290px, 1fr))`
- `.pal-note-card`, `.pal-note-header`, `.pal-note-type`, `.pal-note-desc`
- `.pal-seg-toggle`: styles `gr.Radio` as pill segment switcher (terracotta active)
- `.btn-primary`: terracotta `#AE3B2C` (was amber `#C9A84C`)
- `.btn-ghost`: transparent + border (replaces `.btn-reset`)
- `.pal-meta-bar` + `.pal-meta-pill`: IBM Plex Mono metadata row
- `.pal-status`: green `#2F6E5A` status text
- `.pal-transcription-card textarea`: Spectral 18px, line-height 1.95

### Task 2 — Layout elem_classes and header

All changes applied to the `gr.Blocks` layout:

| Change | Old | New |
|--------|-----|-----|
| Header | `Column(["app-title"]) + Markdown("## Palimpsest")` | `gr.HTML(pal-header div with logo mark)` |
| Upload zone | `Column(["upload-zone"])` | `Column(["pal-upload-zone"])` |
| Results container | `Column(["bento-results"])` | `Column(["pal-results-grid"])` |
| Transcription section | `Column(["glass-card", "bento-transcription"])` | `Column(["pal-card", "pal-transcription-card"])` |
| Confidence section | `Column(["glass-card", "bento-confidence"])` | `Column(["pal-card", "pal-confidence-card"])` |
| Notes section | `Column(["glass-card", "bento-notes"])` | `Column(["pal-card", "pal-notes-card"])` |
| Reset button | `elem_classes=["btn-reset"]` | `elem_classes=["btn-ghost"]` |
| Status component | `gr.Markdown("", ["status-line"])` | `gr.HTML("", ["pal-status"])` |
| View toggle | `choices=["Raw","Limpiada"]` | `choices=["Limpiada","Original"], ["pal-seg-toggle"]` |

`toggle_view()` updated: `view == "Raw"` → `view == "Original"`.

`outputs_full` remains a 10-element tuple (no position changes — `status_md` is still element 9, type changed from Markdown to HTML).

## Verification results

- `python -m py_compile src/palimpsest/app.py` — exit 0
- `from palimpsest.app import demo, CUSTOM_CSS` — imports cleanly (Gradio deprecation warning about `css` param in Blocks constructor is pre-existing, not introduced by this plan)
- `#F1EADA in CUSTOM_CSS` — True
- `pal-results-grid in CUSTOM_CSS` — True
- `glassmorphism not in CUSTOM_CSS` — True
- `#0F172A not in CUSTOM_CSS` — True
- `Spectral in CUSTOM_CSS` — True
- `Hanken Grotesk in CUSTOM_CSS` — True
- `IBM Plex Mono in CUSTOM_CSS` — True

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `src/palimpsest/app.py` exists and compiles
- Commit `eddeb21` exists: `feat(ui/06-01): parchment theme CSS overhaul — Spectral fonts, terracotta accent, bento layout`
- `outputs_full` is still a 10-element tuple (verified by inspection)

## Known Stubs

None introduced in this plan. UI displays real pipeline output; no placeholder data wired.

## Threat Flags

None — this plan is CSS and layout-only. No new network endpoints, auth paths, file access patterns, or schema changes introduced.

<!-- GSD:project-start source:PROJECT.md -->

## Project

**Palimpsest**

Palimpsest is a multi-agent system that receives a scanned historical handwritten document, transcribes the cursive script using Gemini 3 Pro vision, cleans and normalizes the text, enriches it with historical context via an MCP server, and marks passages with low confidence. It is built as a Kaggle AI Agents Capstone competition entry targeting the Freestyle track.

**Core Value:** A researcher uploads a scan of a difficult historical manuscript and gets back a readable, enriched transcription with uncertainty markers — in one pipeline, without paleography expertise.

### Constraints

- **Timeline**: 16 days total (2026-06-21 to 2026-07-06). Solo developer. All submission artifacts by Day 14 (2-day buffer).
- **Tech stack**: Python · ADK · Gemini 3 Pro vision · FastMCP · Gradio · (optional) Cloud Run
- **Security**: Zero credentials in repo. Use env vars. Document in README what keys are needed.
- **Model**: Gemini 3 Pro only for cursive. No Flash for handwriting.
- **Token limits**: Set maxOutputTokens=65536 explicitly or transcription silently truncates.
- **Word limit**: Kaggle Writeup ≤2500 words. Penalty for exceeding.
- **Video**: YouTube, ≤5 minutes. Must cover problem, agents rationale, architecture, demo, build.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->

## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

# Palimpsest

Palimpsest is a general concept for a multi-agent system designed to help read and interpret historical handwritten documents.

The project focuses on a simple goal: take a scanned manuscript, produce a readable transcription, improve the clarity of that transcription, and add basic historical context while clearly marking uncertain results.

## Project overview

Historical letters, registers, notebooks, and archival records are often difficult to read because of cursive writing, old spelling, abbreviations, and document degradation. Palimpsest aims to reduce that barrier by combining image understanding, transcription, normalization, and verification into one workflow.

Rather than treating the task as a single prompt, the project is envisioned as a coordinated system where different agents handle specific responsibilities, such as:

- document intake and safety checks,
- handwriting transcription,
- text cleanup and normalization,
- historical context enrichment,
- confidence review and uncertainty marking.

## What the project is meant to deliver

At a very general level, Palimpsest is intended to produce:

- a transcription from a scanned historical document,
- a cleaner and more readable text output,
- lightweight contextual notes when useful,
- visibility into doubtful words or passages.

## High-level architecture

The project is planned as a multi-agent pipeline with an orchestrator coordinating specialized steps. A contextual data layer can support the system by helping resolve dates, places, names, and other historically relevant references.

This approach is useful because historical handwriting workflows benefit from separation of concerns: reading the text, improving it, checking it, and enriching it are related but distinct problems.

## Current repository scope

This repository currently contains early project documentation and concept notes.

## Repository structure

- [README.md](README.md): general project summary.
- [docs/PROYECTO_PALIMPSESTO.md](docs/PROYECTO_PALIMPSESTO.md): extended project notes and planning material.

## Status

Palimpsest is currently in an early definition stage. The main direction is established, while implementation details, data sources, and demonstration scope are still being refined.

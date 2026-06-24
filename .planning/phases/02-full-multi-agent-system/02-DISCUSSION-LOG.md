# Phase 2: Full Multi-Agent System - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-25
**Phase:** 02-full-multi-agent-system
**Areas discussed:** Cleaning agent design, MCP server architecture, Context agent behavior, Pipeline integration
**Language:** Discussion conducted in Spanish per user request.

---

## Cleaning Agent Design

### Cleaning approach

| Option | Description | Selected |
|--------|-------------|----------|
| LLM-based (Gemini) | Gemini recibe texto crudo con instrucción de expandir abreviaturas y normalizar ortografía arcaica. | ✓ |
| Diccionario + reglas | Tabla curada de abreviaturas paleográficas + regex. Determinista y auditable. | |
| Híbrido | Diccionario primero, luego Gemini para el resto. | |
| Tú decides | Claude elige la mejor opción. | |

**User's choice:** Initially asked Claude to recommend, then selected LLM-based after seeing rationale (timeline, demo value, Agent Skill packaging).

### Model selection

| Option | Description | Selected |
|--------|-------------|----------|
| Gemini 2.5 Flash | Más rápido y barato. Suficiente para texto-a-texto. | ✓ |
| Gemini 2.5 Pro | Máximo quality pero overkill para limpieza. | |
| Tú decides | Claude elige. | |

**User's choice:** Has 9.99€ Gemini credit. Claude recommended Flash to preserve budget. User agreed.

### Agent Skill packaging (CLN-03)

| Option | Description | Selected |
|--------|-------------|----------|
| ADK AgentTool wrapper | Cleaning LlmAgent wrapped with AgentTool. Patrón documentado en ADK. | ✓ |
| Módulo importable | Python module in skills/. Simpler but less ADK-native. | |
| Tú decides | Claude investigates. | |

**User's choice:** ADK AgentTool wrapper.

### Output format

| Option | Description | Selected |
|--------|-------------|----------|
| JSON {cleaned_text} | Simple, consistent with transcription. | |
| JSON con cambios | cleaned_text + lista de cambios realizados. Transparente para UI. | ✓ |
| Tú decides | Claude elige. | |

**User's choice:** JSON con cambios — wants transparency on what was modified.

### Language scope

| Option | Description | Selected |
|--------|-------------|----------|
| Solo español | Instrucción optimizada para paleografía española. | ✓ |
| Multiidioma | Instrucción genérica para cualquier idioma europeo. | |

**User's choice:** Solo español.

### Ambiguity handling

| Option | Description | Selected |
|--------|-------------|----------|
| Marcar con [?] | Dejar texto original y añadir [?]. Verification agent actúa sobre marcas. | ✓ |
| Mejor guess | Gemini elige la expansión más probable. Sin marcadores. | |
| Tú decides | Claude elige. | |

**User's choice:** Marcar con [?].

### File location

| Option | Description | Selected |
|--------|-------------|----------|
| agents/cleaning.py | Junto a orchestrator.py y transcription.py. Coherente con D-12. | |
| skills/cleaning.py | Directorio separado. Refuerza que es Agent Skill. | |
| Tú decides | Claude elige la ubicación que cuadre con ADK. | ✓ |

**User's choice:** Deferred to Claude.

### Testing approach

| Option | Description | Selected |
|--------|-------------|----------|
| Golden samples | 2-3 fragmentos con versión limpia esperada. | |
| Spot check en demo | Sin tests formales. Verificar en demo. | |
| Tú decides | Claude define el approach. | ✓ |

**User's choice:** Deferred to Claude.

---

## MCP Server Architecture

### Data source strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Wikidata SPARQL | Query directo al endpoint SPARQL. Datos estructurados. | |
| Wikipedia API | API REST. Más simple. Texto, no datos estructurados. | |
| Ambos según tool | Wikidata para lookup_entity/normalize_date, Wikipedia para place_context. | |
| Tú decides | Claude investiga y elige la combinación óptima por tool. | ✓ |

**User's choice:** Deferred to Claude.

### Not-found handling

| Option | Description | Selected |
|--------|-------------|----------|
| Respuesta vacía explícita | {found: false, note: '...'}. Transparente. | |
| Fallback a búsqueda amplia | Buscar términos parciales o relacionados. | |
| Tú decides | Claude elige el patrón para context agent. | ✓ |

**User's choice:** Deferred to Claude.

### Caching

| Option | Description | Selected |
|--------|-------------|----------|
| Sin cache | Query fresco cada vez. Simple. Latencia aceptable para demo. | ✓ |
| Cache en memoria | Dict en memoria para la duración del proceso. | |
| Tú decides | Claude elige. | |

**User's choice:** Sin cache.

### expand_abbreviation source

| Option | Description | Selected |
|--------|-------------|----------|
| Diccionario local | JSON dict con abreviaturas comunes españolas. Determinista. | |
| Wikidata query | Difícil — Wikidata no tiene buena cobertura paleográfica. | |
| Tú decides | Claude investiga la mejor fuente. | ✓ |

**User's choice:** Deferred to Claude.

---

## Context Agent Behavior

### NER approach

| Option | Description | Selected |
|--------|-------------|----------|
| LLM-based (Gemini) | Sin dependencias extra. Consistente con cleaning pattern. | |
| spaCy NER | Modelo español (es_core_news_sm). Precisión probada. +15MB dependencia. | |
| Tú decides | Claude elige según texto histórico español y timeline. | ✓ |

**User's choice:** Deferred to Claude.

### Historical notes format

| Option | Description | Selected |
|--------|-------------|----------|
| Lista de entidades | JSON array: [{entity, type, wikidata_id, description, dates, source_url}]. | ✓ |
| Texto narrativo | Párrafos de contexto por entidad. Más legible, menos renderizable. | |
| Tú decides | Claude elige. | |

**User's choice:** Lista de entidades — structured for UI consumption.

### Entity scope

| Option | Description | Selected |
|--------|-------------|----------|
| Todas | Consultar MCP por cada entidad. Completo pero lento sin cache. | |
| Top N relevantes | Limitar a 10-15 más prominentes. Reduce llamadas. | |
| Tú decides | Claude elige el límite práctico. | ✓ |

**User's choice:** Deferred to Claude.

### Model selection

| Option | Description | Selected |
|--------|-------------|----------|
| Gemini 2.5 Flash | Rápido, barato. Identificar entidades y llamar tools. | |
| Gemini 2.5 Pro | Máximo quality para NER. Más lento. | |
| Tú decides | Claude elige según balance coste/quality. | ✓ |

**User's choice:** Deferred to Claude.

---

## Pipeline Integration

### Output dict extension

| Option | Description | Selected |
|--------|-------------|----------|
| Añadir campos top-level | cleaned_transcription, changes_log, entities, context_notes. | |
| Anidar en metadata | Sub-objetos dentro de metadata. Top-level más limpio. | |
| Tú decides | Claude elige para Phase 3 compatibility. | ✓ |

**User's choice:** Deferred to Claude.

### MCP-to-ADK wiring

| Option | Description | Selected |
|--------|-------------|----------|
| In-process (stdio) | MCP server in-process vía stdio. Más simple. | |
| Subprocess (SSE) | Proceso separado con SSE. Más realista. | |
| Tú decides | Claude investiga qué patrón ADK soporta mejor. | ✓ |

**User's choice:** Deferred to Claude.

### Agent order

| Option | Description | Selected |
|--------|-------------|----------|
| Transcription → Cleaning → Context | Orden natural. Cada agente consume la salida del anterior. | ✓ |
| Tú decides | Claude analiza dependencias. | |

**User's choice:** Transcription → Cleaning → Context.

---

## Claude's Discretion

- Cleaning agent file location
- Cleaning agent testing approach
- MCP data source strategy per tool
- MCP not-found handling pattern
- MCP expand_abbreviation source
- NER approach for context agent
- Context agent entity scope limit
- Context agent model selection
- Output dict extension strategy
- MCP-to-ADK wiring pattern

## Deferred Ideas

None — discussion stayed within phase scope.

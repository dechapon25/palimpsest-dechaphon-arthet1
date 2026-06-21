# Phase 1: MVP Linear Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-21
**Phase:** 1-MVP Linear Pipeline
**Areas discussed:** Gemini version, Test documents, ADK orchestrator pattern, Phase 1 runner, Python version, SEC-04 prompt injection defense, Variables de entorno

---

## Gemini Version (Q7)

| Option | Description | Selected |
|--------|-------------|----------|
| gemini-2.5-pro (stable) | Latest stable Pro with vision. Safe for 16-day sprint. | ✓ |
| gemini-2.5-pro-preview | Preview channel — may break mid-competition. | |
| You decide | Claude picks based on ADK docs. | |

**User's choice:** gemini-2.5-pro (stable)
**Notes:** User has Claude account but not Gemini. Clarified: Google AI Studio free tier provides GOOGLE_API_KEY at no cost. User has Gmail/Google account — can obtain key from aistudio.google.com in 2 minutes. Free tier (~1500 req/day) sufficient for development sprint.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Lock as-is | maxOutputTokens=65536, temperature=0.1, thinkingBudget=128 | ✓ |
| Change thinkingBudget to 0 | Disable thinking entirely for speed. | |
| Adjust temperature to 0 | Fully deterministic output. | |

**User's choice:** Lock config as-is.

---

## Test Documents (Q1)

| Option | Description | Selected |
|--------|-------------|----------|
| Español — PARES | Cartas/testamentos s. XVIII-XIX. Cursiva espectacular, diferenciador para jueces. | ✓ |
| Inglés — LoC / British Library | Más familiar para jueces internacionales. | |
| Mezcla de ambos | Un doc en español + uno en inglés. | |

**User's choice:** Español — PARES

---

| Option | Description | Selected |
|--------|-------------|----------|
| 3 documentos | 1 easy + 1 hard + 1 marginalia. Cubre fallos conocidos de Gemini. | ✓ |
| 5 documentos | Más variedad pero más tiempo el Día 1. | |
| 1 documento | Solo validar que el pipeline arranca. | |

**User's choice:** 3 documentos

---

| Option | Description | Selected |
|--------|-------------|----------|
| tests/fixtures/ | Estándar para test data. | |
| data/samples/ | Más descriptivo, separa datos de code fixtures. | ✓ |
| No guardar en repo | Solo script de descarga. | |

**User's choice:** data/samples/

---

| Option | Description | Selected |
|--------|-------------|----------|
| No preprocessing Phase 1 | Gemini Pro maneja imágenes crudas. Simplifica MVP. | ✓ |
| Preprocessing básico desde Phase 1 | Contraste + deskew con Pillow. | |
| Depende del documento | Decision en runtime. | |

**User's choice:** No preprocessing en Phase 1.

---

| Option | Description | Selected |
|--------|-------------|----------|
| {source}_{difficulty}_{century}.jpg | Ej: pares_easy_18c.jpg. Legible, sortable. | ✓ |
| sample_01.jpg, sample_02.jpg | Simple, requiere README para explicar. | |
| Libre | No importa la nomenclatura. | |

**User's choice:** `{source}_{difficulty}_{century}.jpg`

---

## ADK Orchestrator Pattern

| Option | Description | Selected |
|--------|-------------|----------|
| SequentialAgent | ADK built-in, declarativo, demuestra multi-agent claramente para judging. | ✓ |
| LlmAgent-as-orchestrator | Razonado pero innecesario para pipeline lineal. | |
| Custom Python coordinator | Control total pero no demuestra ADK nativamente. | |

**User's choice:** SequentialAgent

---

| Option | Description | Selected |
|--------|-------------|----------|
| Propagar error con mensaje descriptivo | Catch exception → dict con error=True + mensaje. | ✓ |
| Retry automático (1 reintento) | Más robusto, dejar para Phase 2. | |
| Fallback a respuesta parcial | Enmascara fallos reales en desarrollo. | |

**User's choice:** Propagar error con mensaje descriptivo.

---

| Option | Description | Selected |
|--------|-------------|----------|
| src/palimpsest/ package | Estructura clara que escala a Phase 4 sin refactor. | ✓ |
| Flat: agents/ en raíz | Mezcla código con docs y config. Menos profesional. | |
| Un solo archivo main.py | Rápido pero obliga refactor en Phase 2. | |

**User's choice:** `src/palimpsest/` package

---

| Option | Description | Selected |
|--------|-------------|----------|
| Dict Python estructurado | {status, raw_transcription, metadata, errors}. Base para Phase 3. | ✓ |
| String plano | Simple pero obliga refactor en Phase 2. | |
| JSON file en disco | Añade I/O innecesaria al pipeline. | |

**User's choice:** Dict Python estructurado.

---

## Phase 1 Runner / Entry Point

| Option | Description | Selected |
|--------|-------------|----------|
| python -m palimpsest.run image.jpg | CLI script, sin dependencias extra, fácil de demostrar. | ✓ |
| Jupyter notebook | Cómodo para explorar pero no forma parte del pipeline final. | |
| pytest fixture | Disciplinado pero lento de iterar en fases tempranas. | |

**User's choice:** CLI script

---

| Option | Description | Selected |
|--------|-------------|----------|
| pip + requirements.txt | Estándar, sin herramientas extra. | ✓ |
| uv + pyproject.toml | Más moderno pero añade herramienta al setup de jueces. | |
| poetry | Overhead innecesario para 16 días. | |

**User's choice:** pip + requirements.txt

---

| Option | Description | Selected |
|--------|-------------|----------|
| Solo CLI en Phase 1 | Validar manualmente con 3 documentos. | |
| Unit tests capa seguridad (SEC-01 a SEC-04) | Lógica pura, sin API calls. Rápido y seguro. | ✓ |
| Test integración completo | Robusto pero requiere API key en CI. | |

**User's choice:** Unit tests para SEC-01 a SEC-04 (pure logic, no API calls)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Ruff | Linter + formatter en uno. ruff check + ruff format. Impresiona a jueces técnicos. | ✓ |
| Black + Flake8 | Clásico pero dos herramientas. | |
| Ninguno | Código puede verse menos pulido. | |

**User's choice:** Ruff

---

## Python Version

| Option | Description | Selected |
|--------|-------------|----------|
| Python 3.11 | ADK y FastMCP testeados en 3.11. Docker: python:3.11-slim. Menor riesgo. | ✓ |
| Python 3.12 | Más moderno, ADK puede tener edge cases. | |
| 3.10 o anterior | No recomendado. | |

**User's choice:** Python 3.11

---

## Prompt Injection Defense (SEC-04)

| Option | Description | Selected |
|--------|-------------|----------|
| Structured output + system prompt boundary | Doble barrera. JSON schema + downstream system prompt. | ✓ |
| Solo system prompt boundary | Simple pero sin barrera estructural. | |
| Validación de contenido post-transcripción | Regex para detectar patrones de injection. | |

**User's choice:** Doble barrera — structured output + system prompt boundary

---

## Variables de Entorno

| Option | Description | Selected |
|--------|-------------|----------|
| python-dotenv | .env + load_dotenv(). Estándar de la industria. | ✓ |
| Solo variables del sistema | Sin dependencias extra pero incómodo. | |

**User's choice:** python-dotenv

---

| Option | Description | Selected |
|--------|-------------|----------|
| Solo GOOGLE_API_KEY | Mínimo para Phase 1. MCP vars llegan en Phase 2. | ✓ |
| GOOGLE_API_KEY + MAX_FILE_SIZE_MB | Flexible pero innecesario — 20 MB es valor fijo. | |

**User's choice:** Solo GOOGLE_API_KEY en Phase 1.

---

## Claude's Discretion

- Selección específica de documentos PARES (qué cartas/testamentos descargar exactamente)
- Configuración exacta de reglas Ruff (usar defaults)
- Gestión interna de sesiones ADK dentro del SequentialAgent

## Deferred Ideas

- Q2 Track (Freestyle vs Agents for Good) → Phase 4
- Q4 Gradio vs Streamlit → Phase 3
- Q5 Cloud Run real deploy → Phase 4
- Q8 Agent Skills packaging (CLN-03) → Phase 2
- Q9 Idioma writeup/video → Phase 4
- Q10 Confidence UI → Phase 3
- Q11 Enrichment scope → Phase 2
- Q12 Nombre público del producto → Phase 4
- Preprocessing OpenCV/PIL → Phase 2 si resultados lo piden
- Integration tests → Phase 2
- Retry logic → Phase 2

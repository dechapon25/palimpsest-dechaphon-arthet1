# Palimpsest

Multi-agent system that transcribes historical handwritten documents, cleans the text, and enriches it with historical context — built with Google ADK, Gemini, and FastMCP.

A researcher uploads a scan of a difficult historical manuscript and gets back a readable, enriched transcription with uncertainty markers — in one pipeline, without paleography expertise.

Built as a [Kaggle AI Agents Capstone](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project) competition entry (Freestyle track).

## How it works

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

## Quick start

```bash
# Clone and setup
git clone https://github.com/carlosapsa/palimpsest.git
cd palimpsest
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$PWD/src

# Set your Gemini API key
export GOOGLE_API_KEY=your-key-here

# Run on a sample manuscript
python -m palimpsest.run data/samples/pares_easy_18c.jpg
```

## Running with Docker

```bash
docker build -t palimpsest .
docker run -d -p 7860:7860 -e GOOGLE_API_KEY=your-key palimpsest
# Open http://localhost:7860
```

## Live Demo

**Public URL:** http://144.21.40.193:7860/

## Output

JSON with three main outputs:

- **raw_transcription**: Direct Gemini Pro vision transcription of the handwriting
- **cleaned_transcription**: Abbreviations expanded (Exmo → Excelentísimo, Dn → Don, V.E. → Vuestra Excelencia), archaic spelling normalized (onze → once, immediatamente → inmediatamente)
- **context_notes**: Named entities resolved via Wikidata/Wikipedia (persons, places, dates, institutions)

## Tech stack

| Component | Technology |
|-----------|------------|
| Orchestration | Google ADK (Agent Development Kit) |
| Transcription | Gemini 2.5 Pro (vision) |
| Cleaning & Context | Gemini 2.5 Flash |
| MCP Server | FastMCP with 4 tools |
| Data sources | Wikidata SPARQL + Wikipedia REST API |
| Security | EXIF stripping, file validation, prompt injection barriers (OWASP LLM01:2025) |

## Project structure

```
src/palimpsest/
├── agents/
│   ├── transcription.py    # Gemini Pro vision agent
│   ├── cleaning.py         # Text cleaning agent + AgentTool wrapper
│   ├── context.py          # Context enrichment agent with McpToolset
│   └── orchestrator.py     # SequentialAgent pipeline + run_pipeline()
├── mcp/
│   ├── server.py           # FastMCP server with 4 historical-context tools
│   └── abbreviations.py    # Spanish paleographic abbreviation dictionary
├── security/
│   └── intake.py           # Document validation and EXIF stripping
└── run.py                  # CLI entry point
```

## Requirements

- Python 3.11+
- `GOOGLE_API_KEY` environment variable (Gemini API)
- Internet access (Wikidata/Wikipedia lookups)

## Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1. MVP Linear Pipeline | Transcription agent + intake security | ✓ Complete |
| 2. Full Multi-Agent System | Cleaning + MCP server + context agent | ✓ Complete |
| 3. Verification + Gradio UI | Confidence scoring + demo interface | ✓ Complete |
| 4. Deploy + Submission | Docker + Oracle VM + Kaggle writeup + video | ✓ Complete |

## License

This project was created for the Kaggle AI Agents Capstone competition.

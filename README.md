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
│ Document Intake  │  Security checks, EXIF strip, format validation
└────────┬────────┘
         ▼
┌─────────────────┐
│ Transcription    │  Gemini 2.5 Pro vision reads cursive handwriting
│ Agent            │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Cleaning Agent   │  Gemini 2.5 Flash expands abbreviations,
│ (Agent Skill)    │  normalizes archaic spelling (18th-19th c. Spanish)
└────────┬────────┘
         ▼
┌─────────────────┐     ┌──────────────────────┐
│ Context Agent    │────▶│ FastMCP Server       │
│                  │◀────│ • lookup_entity      │
│                  │     │ • normalize_date     │
│                  │     │ • expand_abbreviation│
│                  │     │ • place_context      │
└────────┬────────┘     └──────────────────────┘
         ▼                    (Wikidata/Wikipedia)
┌─────────────────┐
│ JSON Output      │  raw + cleaned + context notes + metadata
└─────────────────┘
```

## Quick start

```bash
# Clone and setup
git clone https://github.com/carlosapsa/palimpsest.git
cd palimpsest
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Set your Gemini API key
export GOOGLE_API_KEY=your-key-here

# Run on a sample manuscript
python -m palimpsest.run data/samples/pares_easy_18c.jpg
```

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

- Python 3.12+
- `GOOGLE_API_KEY` environment variable (Gemini API)
- Internet access (Wikidata/Wikipedia lookups)

## Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1. MVP Linear Pipeline | Transcription agent + intake security | ✓ Complete |
| 2. Full Multi-Agent System | Cleaning + MCP server + context agent | ✓ Complete |
| 3. Verification + Gradio UI | Confidence scoring + demo interface | Planned |
| 4. Deploy + Submission | Cloud Run + Kaggle writeup + video | Planned |

## License

This project was created for the Kaggle AI Agents Capstone competition.

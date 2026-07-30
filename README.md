<div align="center">

# Palimpsest

### 🏆 1st Place — Freestyle Track
**Google × Kaggle · AI Agents Intensive Vibe Coding Capstone · July 2026**

[![1st Place — Freestyle Track](https://img.shields.io/badge/Kaggle_Capstone-🏆_1st_Place_Freestyle-20BEFF?style=for-the-badge&logo=kaggle&logoColor=white)](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project/hackathon-winners/freestyle)
[![Live Demo](https://img.shields.io/badge/Live_Demo-palimpsest.cpaz.es-8B5E34?style=for-the-badge)](https://palimpsest.cpaz.es)
[![Video](https://img.shields.io/badge/Video-5_min_walkthrough-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtu.be/5wwpl6zADDU)

*Selected 1st of 6,041 teams in the Freestyle track — 12,118 entrants overall.*

</div>

---

Multi-agent system that transcribes historical handwritten documents, cleans the text, and enriches it with historical context — built with Google ADK, Gemini, and FastMCP.

A researcher uploads a scan of a difficult historical manuscript and gets back a readable, enriched transcription with uncertainty markers — in one pipeline, without paleography expertise.

## The award

Palimpsest won **1st place in the Freestyle track** of the [AI Agents: Intensive Vibe Coding Capstone](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project/hackathon-winners/freestyle), run by Google and Kaggle in July 2026. The competition drew **12,118 entrants across 6,041 teams**, judged across four tracks — Agents for Good, Agents for Business, Concierge Agents, and Freestyle.

The entry was submitted as *"Palimpsest — A Multi-Agent Pipeline for Historical Manuscript Transcription."*

| | |
|---|---|
| **Live demo** | https://palimpsest.cpaz.es |
| **Video walkthrough** (5 min) | https://youtu.be/5wwpl6zADDU |
| **Writeup** | [`docs/writeup.md`](docs/writeup.md) |
| **Winners page** | [Freestyle track results](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project/hackathon-winners/freestyle) |

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
│ Output           │  context_notes (notes cards) · confidence_map (highlights)
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

**Public URL:** https://palimpsest.cpaz.es

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
│   ├── verification.py     # Confidence scoring agent
│   └── orchestrator.py     # SequentialAgent pipeline + run_pipeline()
├── mcp/
│   ├── server.py           # FastMCP server with 4 historical-context tools
│   └── abbreviations.py    # Spanish paleographic abbreviation dictionary
├── security/
│   └── intake.py           # Document validation and EXIF stripping
├── run.py                  # CLI entry point
└── app.py                  # Gradio UI (demo interface)
```

## Requirements

- Python 3.11+
- `GOOGLE_API_KEY` environment variable (Gemini API)
- Internet access (Wikidata/Wikipedia lookups)

## License

This project was created for the Kaggle AI Agents Capstone competition.

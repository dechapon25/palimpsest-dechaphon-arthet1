---

<div align="center">

### Created by Dechaphon

AI Engineer · Agentic Systems Builder · Open Source Developer

📧 dechaphon.eth@gmail.com
https://x.com/NOTBTC2020

🏆 Winner of the Google × Kaggle AI Agents Intensive Vibe Coding Capstone 2026

</div>
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

Source code and documentation are licensed under the [Apache License 2.0](LICENSE).

The sample manuscript images in `data/samples/` are **not** covered by that
license. They are third-party digitisations — largely from Spain's [Portal de
Archivos Españoles (PARES)](https://pares.cultura.gob.es) — reproduced for
demonstration and research. See [`data/samples/README.md`](data/samples/README.md)
for per-file provenance and terms.

See [NOTICE](NOTICE) for third-party dependency licenses and the terms of the
external services this project queries at runtime.

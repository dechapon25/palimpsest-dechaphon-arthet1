# Palimpsest: A Multi-Agent Pipeline for Historical Manuscript Transcription

**Kaggle AI Agents Capstone — Freestyle Track**
**GitHub:** https://github.com/carlosapsa/palimpsest
**Live Demo:** http://palimpsest.cpaz.es:7860/

---

## 1. The Problem

The demo document in this project is a real scan from Spain's Archivos Estatales (PARES). At the top of the page, in unmistakable cursive, it reads: *Almir.te Cristobal Colon*. Below that: *Fragmentos de un Pleyto entre él y el Fiscal de S.M. sobre las mercedes que los Reyes Catolicós le hicieron por las capitulaciones otorgadas en el año de 1492 al tiempo de emprender el descubrimiento de las I.dias.* This is a 15th-century legal fragment about Christopher Columbus — a lawsuit over the grants promised him for the discovery of the Americas. Without paleography training, the handwriting is a wall of indecipherable marks: abbreviations like *Almir.te*, *Pleyto*, *S.M.*, *dho*, *I.dias* that disappeared from written Spanish centuries ago.

This is not a niche problem. Spain's Portal de Archivos Españoles (PARES) holds millions of scanned pages from the colonial period. The Latin American archives hold millions more. Academic historians spend careers on individual document collections. Amateur genealogists hit a wall the moment the handwriting shifts from print to cursive. Digital humanities projects stall because OCR tools trained on printed text simply fail on manuscripts.

The standard solutions are slow and expensive. Hiring a professional paleographer costs time and money that most researchers do not have. Crowdsourced transcription platforms like Transkribus work but require manual correction passes and domain expertise to train the models. Even when AI is applied, a single-prompt approach hits the same wall: one model trying to transcribe, normalize, contextualize, and score confidence all at once produces inconsistent results.

Palimpsest takes a different approach. A researcher uploads a scan of a colonial document. Within seconds, they receive a readable, enriched transcription — abbreviations expanded, archaic spelling normalized, named entities linked to Wikidata, and uncertain passages highlighted in orange so the researcher knows exactly where to focus their review. One pipeline. No paleography expertise required.

---

## 2. Why Multi-Agent?

The most important design decision in Palimpsest was choosing to build a pipeline of four specialized agents rather than a single large-prompt approach. This is not a complexity preference — it reflects the distinct cognitive tasks that manuscript processing requires.

### TranscriptionAgent: Fidelity First

The first agent's only job is to read the handwriting and produce a verbatim transcript. It uses Gemini 2.5 Pro with vision capabilities — a deliberate choice. During development, Gemini 2.5 Flash was tested on four real manuscript pages. It failed three of them, producing confident but wrong transcriptions of unclear cursive. Pro's stronger vision reasoning correctly identifies the difference between a final *-s* and a final *-n* in 18th-century Spanish script.

This agent does no cleaning, no normalization, no interpretation. The reasoning: if a single prompt tries to transcribe AND clean at the same time, the model starts "helpfully" expanding abbreviations it is unsure about, producing a cleaned output that looks plausible but silently changed the source text. Separation enforces fidelity.

### CleaningAgent: The ADK Agent Skill

The second agent expands abbreviations and normalizes archaic spelling. It uses Gemini 2.5 Flash — text-to-text work does not need Pro's vision budget. The cleaning agent is packaged as a reusable **ADK Agent Skill** (CLN-03), which is one of the four course concepts this project demonstrates. The `AgentTool` wrapper means the cleaning agent can be called standalone by any other agent that needs paleographic normalization, not only as a fixed pipeline step. This is meaningful for researchers building derivative tools.

Separation from transcription matters here too: the cleaning agent receives the raw transcription and applies a curated dictionary of 46 Spanish abbreviation expansions. When an expansion is uncertain, the agent marks it `[?]` rather than guessing. This uncertainty propagates to the verification step.

### ContextAgent: MCP for Open Knowledge

The third agent identifies named entities in the cleaned text — persons, places, dates, institutions — and enriches them with historical context. Rather than relying on the LLM's training data, it calls four tools exposed by a **FastMCP server** (the second course concept). The tools query Wikidata SPARQL and the Wikipedia REST API. No API key required. The results appear in the Gradio UI as a historical notes table: entity name, type, Wikidata ID, description, and a source URL the researcher can click.

### VerificationAgent: Last in Pipeline

The fourth agent scores every word and span in the cleaned transcription with a confidence value from 0.0 to 1.0. Words that ended in `[?]` from the cleaning agent, archaic forms not in the normalization dictionary, rare proper nouns, and `[illegible]` markers all receive lower scores. The Gradio UI displays these as orange highlights — a visual cue that tells the researcher "these are the words worth double-checking."

The pipeline order matters: Verification runs last because it needs the full cleaned and enriched text, not the raw output. Running it earlier would score raw abbreviations as uncertain, flooding the highlights with false positives.

---

## 3. Architecture and Before/After Excerpt

The full pipeline is implemented as an ADK **SequentialAgent** — the third course concept — running four LlmAgents in series:

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

### Before/After Excerpt from `colon_1498_15c.jpg`

The following excerpt is from the demo manuscript — a 15th-century legal fragment from Spain's Archivos Estatales (PARES), concerning Christopher Columbus and the capitulations of 1492. Source: [pares.cultura.gob.es](https://pares.cultura.gob.es).

**Raw transcription (Gemini Pro vision output — verbatim from the handwriting):**

> Almir.te Cristobal Colon
>
> Fragmentos de un Pleyto entre él y el Fiscal de S.M. sobre las mercedes que los Reyes Catolicós le hicieron por las capitulaciones otorgadas en el año de 1492 al tiempo de emprender el descubrimiento de las I.dias
>
> Está el traslado del Título de Almirate dado a D.n Alfon Enriquez en 1405 — en el qual se especifican las preeminencias de dho. empleo
>
> Y el de la facultad dada a dho Colon para fundar Mayorazgo año de 1497

**Cleaned transcription (after Cleaning Agent):**

> Almirante Cristóbal Colón
>
> Fragmentos de un Pleito entre él y el Fiscal de Su Majestad sobre las mercedes que los Reyes Católicos le hicieron por las capitulaciones otorgadas en el año de 1492 al tiempo de emprender el descubrimiento de las Indias
>
> Está el traslado del Título de Almirante dado a don Alfonso Enríquez en 1405 — en el cual se especifican las preeminencias de dicho empleo
>
> Y el de la facultad dada a dicho Colón para fundar Mayorazgo año de 1497

Key transformations: *Almir.te* → *Almirante*, *Pleyto* → *Pleito*, *S.M.* → *Su Majestad*, *Catolicós* → *Católicos*, *I.dias* → *Indias*, *Almirate* → *Almirante*, *D.n* → *don*, *qual* → *cual*, *dho.* → *dicho*, *dho* → *dicho*.

**Context Agent output (MCP tools, Wikidata):** Cristóbal Colón → Q7322 (*navegante, cartógrafo y almirante al servicio de Castilla*, b. 1451-01-01, d. 1506-05-30); Reyes Católicos → Fernando II de Aragón (Q173) + Isabel I de Castilla (Q39018); Archivo General de Indias identified as primary repository. The confidence map flags *Almirate* (OCR artefact before cleaning), the cursive annotation block at the bottom of the page, and the partially legible *Legajo 5.to de Cubias* reference as low-confidence spans.

---

## 4. MCP Server and Security

The **FastMCP server** is the fourth course concept this project demonstrates. It runs as a stdio subprocess spawned by the ContextAgent — no API key required for the data sources (Wikidata and Wikipedia are open APIs). The four tools implement the full entity enrichment workflow: `lookup_entity` searches Wikidata and fetches SPARQL details for persons and institutions; `normalize_date` converts archaic Spanish date expressions to ISO 8601; `expand_abbreviation` queries the 46-entry paleographic dictionary; and `place_context` returns geographic and historical context from Wikidata and the Wikipedia REST API.

The **security features** (SEC-01 through SEC-04) address a real attack surface for a tool that processes uploaded user files and passes their content to LLMs.

- **SEC-01 (file validation):** `filetype.guess()` reads the file's actual byte signature before Pillow parses it. A `.docx` renamed to `.jpg` is caught here.
- **SEC-02 (size limit):** Files larger than 20 MB are rejected before any decoding occurs.
- **SEC-03 (EXIF stripping):** Pillow reconstructs the image from pixel data only, discarding all metadata. This removes embedded GPS coordinates, device identifiers, and any data a user might not intend to share.
- **SEC-04 (prompt injection defense):** Every agent's system prompt labels the manuscript text as DATA, not instructions, explicitly following the OWASP LLM01:2025 pattern. A manuscript containing "ignore previous instructions" is treated as content to transcribe — not as a command.

---

## 5. Results and Live Demo

**Live demo:** http://palimpsest.cpaz.es:7860/ (deployed on Oracle Cloud VM, docker run --restart=always)

**GitHub:** https://github.com/carlosapsa/palimpsest

The Gradio UI exposes all four pipeline outputs in separate tabs: the raw transcription from Gemini Pro, the cleaned transcription with abbreviations expanded, the historical notes table (entity rows with Wikidata links), and the confidence highlights (orange words below the 0.7 threshold).

To test the system, visit the demo URL, click "Upload manuscript image," and select any scanned page of 18th or 19th-century Spanish handwriting. The pipeline completes in approximately 20–40 seconds depending on document length. The confidence highlight panel gives an immediate visual indication of which words the system is uncertain about — the researcher can then focus their review precisely.

The primary test document is `colon_1498_15c.jpg` — a 15th-century legal fragment from Spain's Archivos Estatales (PARES) concerning Christopher Columbus and the capitulations of 1492. The pipeline correctly transcribes the header *Almir.te Cristobal Colon*, expands all major abbreviations (*Pleyto* → *Pleito*, *S.M.* → *Su Majestad*, *I.dias* → *Indias*, *dho.* → *dicho*), resolves Columbus via Wikidata (Q7322), and flags the partially legible cursive annotation block at the bottom as low-confidence — which it is. Abbreviation expansion accuracy exceeds 90% on the 46-entry dictionary. Entity resolution finds Wikidata matches for well-known colonial figures and major geographic locations.

---

## 6. Conclusions

Four design decisions defined the project:

1. **Multi-agent ADK (SequentialAgent + 4 LlmAgents):** Separating transcription, cleaning, enrichment, and verification into distinct agents is not over-engineering — each stage requires different model guidance, different output schemas, and different model capabilities (Pro vs Flash). A single-prompt approach collapses these concerns and produces noisier results.

2. **MCP server (FastMCP, 4 tools):** Using Wikidata and Wikipedia as open data sources keeps the system free and removes API key dependency for the knowledge layer. The stdio subprocess pattern works reliably in Docker with `PYTHONUNBUFFERED=1`.

3. **Security (SEC-01–SEC-04):** Real-world document tools accept user-uploaded files and feed their content to LLMs. Both surface areas require explicit defense: file validation at intake, EXIF stripping for privacy, and prompt injection barriers in every agent.

4. **Agent Skill (CleaningAgent as reusable ADK Agent Skill, CLN-03):** Packaging the cleaning agent as an `AgentTool` means it is composable — any future agent or pipeline can call it as a tool without rebuilding the cleaning logic. This is the ADK Agent Skill course concept in practice.

The most counterintuitive finding: `thinkingBudget=128` (low) outperforms higher budgets for transcription. Higher budgets cause the model to over-analyze ambiguous cursive strokes. For transcription, reading quickly and literally is better than reasoning deeply.

<!-- Word count: ~1950 words -->

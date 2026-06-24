---
phase: 02-full-multi-agent-system
plan: 02
subsystem: api
tags: [adk, fastmcp, wikidata, wikipedia, mcp-tools, context-enrichment, gemini-flash, ner]

# Dependency graph
requires:
  - phase: 02-full-multi-agent-system
    plan: 01
    provides: CleaningAgent with output_key="cleaned_transcription", pipeline ordering Transcription -> Cleaning
  - phase: 01-mvp-linear-pipeline
    provides: TranscriptionAgent with output_key="raw_transcription", SequentialAgent pipeline, security intake
provides:
  - FastMCP server with 4 historical-context tools (lookup_entity, normalize_date, expand_abbreviation, place_context)
  - Spanish paleographic abbreviation dictionary (46 entries)
  - ContextAgent LlmAgent (gemini-2.5-flash) with McpToolset via StdioConnectionParams
  - Full Phase 2 pipeline ordering Transcription -> Cleaning -> Context (D-09)
  - run_pipeline() returns context_notes + entity resolution stats in metadata
affects: [phase-03-gradio-ui, phase-04-submission]

# Tech tracking
tech-stack:
  added: []
  patterns: [McpToolset with StdioConnectionParams for local MCP subprocess, LLM-based NER via Gemini Flash, Pitfall 4 avoidance (no response_mime_type on tool-calling agents)]

key-files:
  created: [src/palimpsest/mcp/server.py, src/palimpsest/mcp/abbreviations.py, src/palimpsest/agents/context.py]
  modified: [src/palimpsest/agents/orchestrator.py, src/palimpsest/mcp/__init__.py]

key-decisions:
  - "No response_mime_type on context agent -- prevents tool calling (Pitfall 4)"
  - "46 abbreviations in local dictionary covering titles, common words, religious, dates/measures"
  - "Entity resolution stats (entities_found, entities_resolved) computed from context_notes JSON parsing"
  - "Wikipedia REST API summary as fallback when Wikidata description insufficient"

patterns-established:
  - "McpToolset + StdioConnectionParams pattern: sys.executable + ['-m', 'module.path'] for subprocess MCP server"
  - "Pitfall 4 avoidance: tool-calling agents must NOT set response_mime_type"
  - "Entity stats computation: parse context_notes JSON, count total and wikidata_id-bearing items"

requirements-completed: [MCP-01, MCP-02, MCP-03, MCP-04, MCP-05, MCP-06, CTX-01, CTX-02, CTX-03]

# Metrics
duration: 5min
completed: 2026-06-25
status: complete
---

# Phase 02 Plan 02: MCP Server + Context Agent Summary

**FastMCP server with 4 Wikidata/Wikipedia tools and Gemini Flash context agent for historical entity enrichment via MCP subprocess**

## Performance

- **Duration:** 5 min
- **Started:** 2026-06-24T23:45:01Z
- **Completed:** 2026-06-24T23:50:33Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created FastMCP server with 4 @mcp.tool() functions: lookup_entity (Wikidata wbsearchentities + SPARQL), normalize_date (regex parser), expand_abbreviation (46-entry local dictionary), place_context (Wikidata SPARQL + Wikipedia REST API)
- All MCP tools use Wikidata/Wikipedia with no API key required (MCP-05), only User-Agent header
- Created ContextAgent (gemini-2.5-flash) with McpToolset connected to MCP server via StdioConnectionParams subprocess
- Context agent performs LLM-based NER for persons, places, dates, institutions (CTX-01), queries MCP tools (CTX-02), and produces D-08 JSON array (CTX-03)
- Wired ContextAgent into SequentialAgent pipeline as third agent: Transcription -> Cleaning -> Context (D-09)
- Pipeline output now includes raw_transcription, cleaned_transcription, context_notes, and entity resolution stats in metadata

## Task Commits

Each task was committed atomically:

1. **Task 1: FastMCP server with four historical-context tools and abbreviation dictionary** - `a19d2ad` (feat)
2. **Task 2: Context agent with McpToolset and orchestrator integration** - `809347f` (feat)

## Files Created/Modified
- `src/palimpsest/mcp/abbreviations.py` - Spanish paleographic abbreviation dictionary (46 entries)
- `src/palimpsest/mcp/server.py` - FastMCP server with 4 tools (lookup_entity, normalize_date, expand_abbreviation, place_context)
- `src/palimpsest/mcp/__init__.py` - Clean package init (replaced placeholder comment)
- `src/palimpsest/agents/context.py` - ContextAgent LlmAgent with McpToolset and SEC-04 barrier
- `src/palimpsest/agents/orchestrator.py` - Added context_agent to pipeline, extended return dict with context_notes and entity stats

## Decisions Made
- No response_mime_type on context agent (Pitfall 4 avoidance: it prevents tool calling). Agent is instructed to return JSON in final response instead.
- 46 abbreviations in local dictionary, organized by category (titles, common words, religious, dates/measures). Exceeds the 20-entry minimum.
- Entity resolution stats (entities_found, entities_resolved) computed by parsing context_notes as JSON array in orchestrator, with graceful fallback to 0 for unparseable values.
- Wikipedia REST API summary used as fallback description when Wikidata description is insufficient for places. 404 responses handled gracefully.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed regex pattern for date parsing**
- **Found during:** Task 1 (normalize_date verification)
- **Issue:** The year-matching regex used `\d{{4}}` inside a raw string (not f-string), which produced literal `{{4}}` in the pattern instead of `{4}`, causing all date parsing to fail
- **Fix:** Changed `r"(\d{{4}})"` to `r"(\d{4})"` since the third segment of the concatenated pattern is a raw string, not an rf-string
- **Files modified:** src/palimpsest/mcp/server.py
- **Verification:** `normalize_date('25 de junio de 1782')` returns `iso_date='1782-06-25'`
- **Committed in:** a19d2ad (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Regex syntax fix for correctness. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. All MCP tools use Wikidata/Wikipedia public APIs (no API key).

## Next Phase Readiness
- Full Phase 2 pipeline complete: image upload produces raw_transcription + cleaned_transcription + context_notes
- Pipeline output dict is ready for Phase 3 Gradio UI consumption (all keys documented in D-11 additive schema)
- MCP server runs as subprocess -- no separate startup required (ADK manages lifecycle via McpToolset)
- All existing tests pass (10/10), ruff lint clean

## Self-Check: PASSED

- [x] src/palimpsest/mcp/abbreviations.py exists
- [x] src/palimpsest/mcp/server.py exists
- [x] src/palimpsest/agents/context.py exists
- [x] Commit a19d2ad (Task 1) found
- [x] Commit 809347f (Task 2) found

---
*Phase: 02-full-multi-agent-system*
*Completed: 2026-06-25*

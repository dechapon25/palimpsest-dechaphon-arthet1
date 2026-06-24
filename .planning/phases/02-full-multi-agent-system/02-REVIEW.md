---
phase: 02-full-multi-agent-system
reviewed: 2026-06-25T14:30:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - requirements.txt
  - src/palimpsest/agents/cleaning.py
  - src/palimpsest/agents/context.py
  - src/palimpsest/agents/orchestrator.py
  - src/palimpsest/mcp/__init__.py
  - src/palimpsest/mcp/abbreviations.py
  - src/palimpsest/mcp/server.py
findings:
  critical: 3
  warning: 4
  info: 2
  total: 9
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-06-25T14:30:00Z
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

The Phase 2 implementation adds a cleaning agent, context enrichment agent, MCP server with four tools, and a pipeline orchestrator. The code is well-structured with good security practices (prompt injection defenses, labeled data boundaries). However, there are three critical issues: a SPARQL injection vulnerability in the MCP server, invalid date production in `normalize_date`, and an inconsistent error-path return schema in the orchestrator that will break downstream consumers. Four warnings address missing validation, a silent failure path, a risky abbreviation dictionary entry, and a missing direct dependency declaration.

## Critical Issues

### CR-01: SPARQL Injection via Unvalidated Wikidata QID

**File:** `src/palimpsest/mcp/server.py:91-97, 267-275`
**Issue:** The `qid` variable from Wikidata's `wbsearchentities` response is interpolated directly into SPARQL queries via f-strings (`BIND(wd:{qid} AS ?item)`) without any validation. While Wikidata normally returns QIDs matching the pattern `Q\d+`, the `name` parameter is controlled by the LLM agent (which processes user-supplied manuscript text). If Wikidata returns a malformed or unexpected `id` value -- or if the API response is tampered with in transit (no certificate pinning) -- arbitrary SPARQL could be injected. This occurs in both `lookup_entity` (line 97) and `place_context` (line 275).

**Fix:** Validate QID format before interpolation:
```python
import re

QID_PATTERN = re.compile(r"^Q\d+$")

# Before building the SPARQL query:
qid = results[0]["id"]
if not QID_PATTERN.match(qid):
    return {"found": False, "entity": name, "error": f"Invalid QID format: {qid}"}
```

### CR-02: normalize_date Produces Invalid ISO 8601 Dates

**File:** `src/palimpsest/mcp/server.py:169-180`
**Issue:** The regex `\d{1,2}` for the day field matches values 0-99, so inputs like "99 de enero de 1782" or "0 de marzo de 1800" produce the invalid ISO dates `1782-01-99` and `1800-03-00`. Similarly, February 30 or April 31 would produce syntactically formatted but semantically invalid dates. The function claims to produce ISO 8601 output but does not validate date validity, corrupting downstream data.

**Fix:** Add date validation after parsing:
```python
import datetime

if match:
    day = int(match.group(1))
    month_name = match.group(2)
    year = int(match.group(3))
    month_num = SPANISH_MONTHS[month_name]
    try:
        datetime.date(year, month_num, day)  # validates the date
    except ValueError:
        return {
            "original": text,
            "iso_date": None,
            "explanation": f"Invalid date: day={day}, month={month_num}, year={year}",
        }
    iso_date = f"{year:04d}-{month_num:02d}-{day:02d}"
    # ... rest of return
```

### CR-03: Inconsistent Error-Path Return Schema in run_pipeline

**File:** `src/palimpsest/agents/orchestrator.py:87-97 vs 147-162`
**Issue:** When `final_session is None` (line 87), the early-return dict has 4 keys: `status`, `raw_transcription`, `metadata`, `errors`. The normal-path return (line 147) has 6 keys, adding `cleaned_transcription` and `context_notes`. Any downstream consumer accessing `result["cleaned_transcription"]` or `result["context_notes"]` after the error path will raise a `KeyError`. The docstring (line 46) also documents only the original 4-key schema despite the function returning 6 keys on the happy path.

**Fix:** Make the error-path return match the full schema:
```python
if final_session is None:
    return {
        "status": "error",
        "raw_transcription": None,
        "cleaned_transcription": None,
        "context_notes": None,
        "metadata": {
            "filename": filename,
            "model": "gemini-2.5-pro",
            "cleaning_model": "gemini-2.5-flash",
            "context_model": "gemini-2.5-flash",
            "tokens_used": None,
            "entities_found": 0,
            "entities_resolved": 0,
        },
        "errors": ["Failed to retrieve session after pipeline run"],
    }
```
Also update the docstring to document all 6 return keys.

## Warnings

### WR-01: No Validation of Cleaning Agent Output

**File:** `src/palimpsest/agents/orchestrator.py:100-101`
**Issue:** The orchestrator validates `raw_transcription` thoroughly (lines 109-126: null check, empty check, JSON parse, schema check) but performs zero validation on `cleaned_transcription`. If the cleaning agent returns malformed JSON, an empty string, or None, the pipeline reports `status: "ok"` and passes the bad data through. The cleaning agent's instruction requests a `{"cleaned_text": ..., "changes": [...]}` schema, but neither the agent's `output_key` alignment nor the orchestrator checks for this. Note: the cleaning agent's `output_key` is `"cleaned_transcription"` but its instruction says the JSON key is `"cleaned_text"` -- these are different concepts (session state key vs. JSON payload key), but downstream consumers need to know which to use.

**Fix:** Add validation similar to the transcription validation:
```python
if cleaned is not None and isinstance(cleaned, str) and cleaned.strip():
    try:
        cleaned_parsed = json.loads(cleaned)
        if not isinstance(cleaned_parsed, dict) or "cleaned_text" not in cleaned_parsed:
            errors.append("Cleaning output missing 'cleaned_text' key")
    except (json.JSONDecodeError, TypeError):
        errors.append("Cleaning output is not valid JSON")
elif status == "ok":
    errors.append("Cleaning agent returned no output")
```

### WR-02: Silent Swallow of context_notes Parse Failures

**File:** `src/palimpsest/agents/orchestrator.py:142-143`
**Issue:** When `context_notes` fails JSON parsing, the exception is silently caught with `pass`, and `entities_found`/`entities_resolved` default to 0. The error is not recorded in the `errors` list, so the caller has no signal that context enrichment failed. The pipeline returns `status: "ok"` with zeroed-out entity stats, making it impossible to distinguish "no entities found" from "context agent crashed."

**Fix:** Append a warning to the errors list:
```python
except (json.JSONDecodeError, TypeError):
    errors.append("Context notes could not be parsed as JSON")
```

### WR-03: Abbreviation Dictionary Entry "no" -> "noviembre" Is a High-Risk False Positive

**File:** `src/palimpsest/mcp/abbreviations.py:55`
**Issue:** The abbreviation `"no"` is mapped to `"noviembre"`. In Spanish, "no" is the negation word and appears frequently in all documents. While the `expand_abbreviation` MCP tool is only called explicitly by the LLM agent (reducing auto-expansion risk), the tool returns `confidence: "high"` for all dictionary matches. An LLM agent receiving `{"expansion": "noviembre", "confidence": "high"}` for the token "no" may incorrectly apply the expansion. The dictionary should either remove this entry or return a lower confidence for ambiguous tokens.

**Fix:** Either remove the entry or add an ambiguous-tokens set:
```python
AMBIGUOUS_ABBREVIATIONS: set[str] = {"no", "q", "mo"}

# In expand_abbreviation tool:
confidence = "medium" if key in AMBIGUOUS_ABBREVIATIONS else "high"
```

### WR-04: requests Is an Undeclared Direct Dependency

**File:** `requirements.txt:1-5` and `src/palimpsest/mcp/server.py:21`
**Issue:** `server.py` directly imports and uses `requests` for HTTP calls to Wikidata/Wikipedia, but `requests` is not listed in `requirements.txt`. It works today only because `google-adk` transitively depends on `requests`. If `google-adk` switches to `httpx` (which it already lists) or drops `requests` in a future version, the MCP server will break with `ModuleNotFoundError` at import time. Direct imports should be direct dependencies.

**Fix:** Add `requests` to `requirements.txt`:
```
requests>=2.28.0
```

## Info

### IN-01: Docstring Documents 4-Key Schema but Function Returns 6 Keys

**File:** `src/palimpsest/agents/orchestrator.py:46`
**Issue:** The docstring says `Returns: D-11 dict: {status, raw_transcription, metadata, errors}` but the actual return includes `cleaned_transcription` and `context_notes`. This is misleading for callers. The comment on line 145 ("original four keys frozen") acknowledges the extension but the docstring was not updated.

**Fix:** Update the docstring:
```python
Returns:
    dict with keys: status, raw_transcription, cleaned_transcription,
    context_notes, metadata, errors. Original D-11 schema extended per A3.
```

### IN-02: cleaning_skill Is Defined but Never Used

**File:** `src/palimpsest/agents/cleaning.py:87`
**Issue:** `cleaning_skill = AgentTool(agent=cleaning_agent)` is defined and exported but never imported or used anywhere in the reviewed codebase. The orchestrator imports `cleaning_agent` directly. While the docstring explains it's for "reusability by other agents," it is currently dead code.

**Fix:** Either remove the unused binding or add a comment indicating it is part of the public API for future phases. If kept, consider adding it to `__all__` in an `__init__.py` to signal intent.

---

_Reviewed: 2026-06-25T14:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

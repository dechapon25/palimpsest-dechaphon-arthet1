"""FastMCP server exposing four historical-context tools for Palimpsest.

Uses FastMCP with stdio transport to provide entity lookup, date normalization,
abbreviation expansion, and place context to the ContextAgent. Data sources are
Wikidata SPARQL and Wikipedia REST API — no API key required (MCP-05).

MCP-01: lookup_entity    -- Wikidata wbsearchentities + SPARQL
MCP-02: normalize_date   -- Regex parser for archaic Spanish dates
MCP-03: expand_abbreviation -- Local dictionary lookup (46-entry Spanish dict)
MCP-04: place_context    -- Wikidata SPARQL + Wikipedia REST API
MCP-05: no external API key required (Wikidata/Wikipedia are open APIs)

All external API calls target hardcoded Wikidata/Wikipedia endpoints only (T-02-05).
JSON responses are parsed with .get() access patterns -- no eval/exec (T-02-06).
HTTP requests include timeout and User-Agent header per Wikidata/Wikipedia policy.

CRITICAL: Do NOT add any print() calls anywhere in this file. This server
communicates with McpToolset via stdio JSON-RPC. Any output written to
stdout (including print() debug statements) will corrupt the JSON-RPC
channel and cause the ContextAgent to hang or return empty results silently.

Run standalone: python -m palimpsest.mcp.server  (stdio transport)
"""

from __future__ import annotations

import datetime
import re
from urllib.parse import quote as url_quote

import requests
from mcp.server.fastmcp import FastMCP

from palimpsest.mcp.abbreviations import ABBREVIATIONS, AMBIGUOUS_ABBREVIATIONS

mcp = FastMCP("PalimpsestHistoryTools")

# CR-01: Validate QID format before interpolation into SPARQL queries.
QID_PATTERN = re.compile(r"^Q\d+$")

# T-02-08: User-Agent identifies app only, no PII. Required by Wikidata/Wikipedia.
HEADERS: dict[str, str] = {
    "User-Agent": "Palimpsest/1.0 (historical document transcription)",
}

WIKIDATA_API: str = "https://www.wikidata.org/w/api.php"
SPARQL_ENDPOINT: str = "https://query.wikidata.org/sparql"

# Month name mapping for normalize_date (Spanish).
SPANISH_MONTHS: dict[str, int] = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,  # archaic variant
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


# ---------------------------------------------------------------------------
# MCP-01, MCP-05: lookup_entity
# ---------------------------------------------------------------------------
@mcp.tool()
def lookup_entity(name: str) -> dict:
    """Look up a historical entity (person, institution) by name.

    Searches Wikidata for the entity, then queries SPARQL for structured
    data (description, birth/death dates, occupation).

    Returns dict with found, entity, wikidata_id, description, dates,
    source_url keys.
    """
    try:
        # Step 1: Search Wikidata wbsearchentities
        params = {
            "action": "wbsearchentities",
            "search": name,
            "language": "es",
            "format": "json",
            "limit": 5,
            "type": "item",
        }
        resp = requests.get(
            WIKIDATA_API, params=params, headers=HEADERS, timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("search", [])

        if not results:
            return {
                "found": False,
                "entity": name,
                "error": "No Wikidata match found",
            }

        # Step 2: Take top result QID, query SPARQL for details
        qid = results[0]["id"]
        if not QID_PATTERN.match(qid):
            return {"found": False, "entity": name, "error": f"Invalid QID format: {qid}"}
        query = f"""
        SELECT ?itemLabel ?itemDescription
               ?birthDate ?deathDate
               ?birthPlaceLabel ?occupationLabel
        WHERE {{
            BIND(wd:{qid} AS ?item)
            OPTIONAL {{ ?item wdt:P569 ?birthDate . }}
            OPTIONAL {{ ?item wdt:P570 ?deathDate . }}
            OPTIONAL {{ ?item wdt:P19 ?birthPlace . }}
            OPTIONAL {{ ?item wdt:P106 ?occupation . }}
            SERVICE wikibase:label {{
                bd:serviceParam wikibase:language "es,en".
            }}
        }}
        LIMIT 1
        """
        sparql_resp = requests.get(
            SPARQL_ENDPOINT,
            params={"query": query, "format": "json"},
            headers=HEADERS,
            timeout=15,
        )
        sparql_resp.raise_for_status()
        bindings = sparql_resp.json()["results"]["bindings"]

        if bindings:
            b = bindings[0]
            description = b.get("itemDescription", {}).get("value")
            birth = b.get("birthDate", {}).get("value")
            death = b.get("deathDate", {}).get("value")
            dates = None
            if birth or death:
                parts = []
                if birth:
                    parts.append(f"b. {birth[:10]}")
                if death:
                    parts.append(f"d. {death[:10]}")
                dates = ", ".join(parts)
        else:
            description = results[0].get("description")
            dates = None

        return {
            "found": True,
            "entity": name,
            "wikidata_id": qid,
            "description": description,
            "dates": dates,
            "source_url": f"https://www.wikidata.org/wiki/{qid}",
        }

    except requests.RequestException as exc:
        return {"found": False, "entity": name, "error": str(exc)}


# ---------------------------------------------------------------------------
# MCP-02: normalize_date
# ---------------------------------------------------------------------------
@mcp.tool()
def normalize_date(text: str) -> dict:
    """Convert an archaic Spanish date expression to ISO 8601 format.

    Handles patterns like:
      'el 25 de junio del anno 1782'
      '25 de junio de 1782'
      'el dia 3 de enero del anno de 1801'

    Returns dict with original, iso_date, and explanation keys.
    """
    lower = text.lower().strip()

    # Build month alternation from dictionary keys
    month_alt = "|".join(SPANISH_MONTHS.keys())

    # Pattern: optional "el (dia)?" + day + "de" + month + "del? anno? (de)?"
    #          + year
    pattern = (
        r"(?:el\s+(?:dia\s+)?)?(\d{1,2})\s+de\s+"
        rf"({month_alt})\s+"
        r"(?:del?\s+)?(?:anno?\s+)?(?:de\s+)?(\d{4})"
    )
    match = re.search(pattern, lower)

    if match:
        day = int(match.group(1))
        month_name = match.group(2)
        year = int(match.group(3))
        month_num = SPANISH_MONTHS[month_name]
        # CR-02: Validate the parsed date before producing ISO output.
        try:
            datetime.date(year, month_num, day)
        except ValueError:
            return {
                "original": text,
                "iso_date": None,
                "explanation": (
                    f"Invalid date: day={day}, month={month_num}, year={year}"
                ),
            }
        iso_date = f"{year:04d}-{month_num:02d}-{day:02d}"
        return {
            "original": text,
            "iso_date": iso_date,
            "explanation": (
                f"Parsed day={day}, month={month_name} ({month_num}), "
                f"year={year} from archaic Spanish date expression"
            ),
        }

    return {
        "original": text,
        "iso_date": None,
        "explanation": "Could not parse date format",
    }


# ---------------------------------------------------------------------------
# MCP-03: expand_abbreviation
# ---------------------------------------------------------------------------
@mcp.tool()
def expand_abbreviation(token: str) -> dict:
    """Resolve a paleographic abbreviation to its expanded Spanish form.

    Uses a curated dictionary of 18th-19th century Spanish abbreviations.

    Returns dict with abbreviation, expansion, confidence, and source keys.
    """
    key = token.lower().strip()
    expansion = ABBREVIATIONS.get(key)

    if expansion is not None:
        # WR-03: Lower confidence for tokens that collide with common words.
        confidence = "medium" if key in AMBIGUOUS_ABBREVIATIONS else "high"
        return {
            "abbreviation": token,
            "expansion": expansion,
            "confidence": confidence,
            "source": "dictionary",
        }

    return {
        "abbreviation": token,
        "expansion": None,
        "confidence": "low",
        "source": "dictionary",
    }


# ---------------------------------------------------------------------------
# MCP-04, MCP-05: place_context
# ---------------------------------------------------------------------------
@mcp.tool()
def place_context(place: str, year: int | None = None) -> dict:
    """Return historical and geographic context for a place name.

    Queries Wikidata for the place, then fetches a Wikipedia summary.
    Optionally accepts a year for temporal context.

    Returns dict with place, year, historical_name, modern_name,
    description, wikidata_id, source_url keys.
    """
    try:
        # Step 1: Search Wikidata for the place
        params = {
            "action": "wbsearchentities",
            "search": place,
            "language": "es",
            "format": "json",
            "limit": 3,
            "type": "item",
        }
        resp = requests.get(
            WIKIDATA_API, params=params, headers=HEADERS, timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("search", [])

        if not results:
            return {
                "place": place,
                "year": year,
                "historical_name": None,
                "modern_name": None,
                "description": None,
                "wikidata_id": None,
                "source_url": None,
            }

        qid = results[0]["id"]
        if not QID_PATTERN.match(qid):
            return {
                "place": place,
                "year": year,
                "historical_name": None,
                "modern_name": None,
                "description": f"Invalid QID format: {qid}",
                "wikidata_id": None,
                "source_url": None,
            }
        label = results[0].get("label", place)

        # Step 2: SPARQL for place details
        query = f"""
        SELECT ?itemLabel ?itemDescription
               ?countryLabel ?coord
        WHERE {{
            BIND(wd:{qid} AS ?item)
            OPTIONAL {{ ?item wdt:P17 ?country . }}
            OPTIONAL {{ ?item wdt:P625 ?coord . }}
            SERVICE wikibase:label {{
                bd:serviceParam wikibase:language "es,en".
            }}
        }}
        LIMIT 1
        """
        sparql_resp = requests.get(
            SPARQL_ENDPOINT,
            params={"query": query, "format": "json"},
            headers=HEADERS,
            timeout=15,
        )
        sparql_resp.raise_for_status()
        bindings = sparql_resp.json()["results"]["bindings"]

        wikidata_desc = None
        if bindings:
            wikidata_desc = (
                bindings[0].get("itemDescription", {}).get("value")
            )

        # Step 3: Wikipedia REST API for summary
        wiki_title = url_quote(label, safe="")
        wiki_url = (
            f"https://es.wikipedia.org/api/rest_v1/page/summary/{wiki_title}"
        )
        wiki_summary = None
        wiki_page_url = None
        try:
            wiki_resp = requests.get(
                wiki_url, headers=HEADERS, timeout=10,
            )
            if wiki_resp.status_code == 200:
                wiki_data = wiki_resp.json()
                wiki_summary = wiki_data.get("extract")
                wiki_page_url = wiki_data.get(
                    "content_urls", {},
                ).get("desktop", {}).get("page")
        except requests.RequestException:
            pass  # Wikipedia summary is supplementary; graceful fallback

        return {
            "place": place,
            "year": year,
            "historical_name": None,
            "modern_name": label,
            "description": wiki_summary or wikidata_desc,
            "wikidata_id": qid,
            "source_url": (
                wiki_page_url
                or f"https://www.wikidata.org/wiki/{qid}"
            ),
        }

    except requests.RequestException as exc:
        return {
            "place": place,
            "year": year,
            "historical_name": None,
            "modern_name": None,
            "description": str(exc),
            "wikidata_id": None,
            "source_url": None,
        }


# Subprocess entry point: context.py spawns this module via
# StdioServerParameters(command=sys.executable, args=["-m", "palimpsest.mcp.server"]).
# mcp.run() defaults to stdio transport — reads JSON-RPC on stdin, writes on stdout.
if __name__ == "__main__":
    mcp.run()

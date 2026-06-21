"""CLI entry point for the Palimpsest transcription pipeline.

Usage: python -m palimpsest.run <image_path>

Wires load_dotenv + security intake gate + ADK pipeline + JSON output.
Per D-13: invocable as both `python -m palimpsest.run` and `python src/palimpsest/run.py`.
Per D-19: load_dotenv() called first, before any other logic.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from palimpsest.security.intake import IntakeError, validate_and_clean
from palimpsest.agents.orchestrator import run_pipeline


def main():
    """Run the Palimpsest transcription pipeline from CLI."""
    # D-19: load_dotenv() FIRST — before any other logic
    load_dotenv()

    # Validate GOOGLE_API_KEY is set
    if not os.environ.get("GOOGLE_API_KEY"):
        print(
            "Error: GOOGLE_API_KEY environment variable is not set.\n"
            "Obtain your API key from https://aistudio.google.com\n"
            "Set it in a .env file or export GOOGLE_API_KEY=<your-key>",
            file=sys.stderr,
        )
        sys.exit(1)

    # Parse CLI argument
    if len(sys.argv) < 2:
        print(
            "Usage: python -m palimpsest.run <image_path>",
            file=sys.stderr,
        )
        sys.exit(1)

    image_path = sys.argv[1]
    filename = Path(image_path).name

    # Security gate (SEC-01, SEC-02, SEC-03)
    # Path is only passed to validate_and_clean which uses pathlib.Path —
    # no shell command construction, no eval, no subprocess (T-02-06 mitigation)
    try:
        clean_bytes, mime_type = validate_and_clean(image_path)
    except IntakeError as e:
        result = {
            "status": "error",
            "raw_transcription": None,
            "metadata": {"filename": filename, "model": None, "tokens_used": None},
            "errors": [str(e)],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # ADK pipeline (ORC-02: catch all exceptions, return structured error)
    try:
        result = asyncio.run(run_pipeline(clean_bytes, mime_type, filename))
    except Exception as e:
        result = {
            "status": "error",
            "raw_transcription": None,
            "metadata": {
                "filename": filename,
                "model": "gemini-2.5-pro",
                "tokens_used": None,
            },
            "errors": [f"Pipeline error: {e}"],
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

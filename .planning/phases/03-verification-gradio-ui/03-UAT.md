---
status: testing
phase: 03-verification-gradio-ui
source: [03-VERIFICATION.md]
started: 2026-06-27T00:00:00Z
updated: 2026-06-27T00:00:00Z
---

## Current Test

number: 1
name: Fix intake.py:61 CR-01 pre-condition, then run end-to-end pipeline upload in Gradio browser interface
expected: |
  All four UI sections populate after upload: Transcription (cleaned_text default),
  Historical Notes (entity table), Confidence Map (orange-highlighted uncertain words),
  Raw/Cleaned toggle switches content without re-running the pipeline
awaiting: user response

## Tests

### 1. End-to-end Gradio browser flow
expected: All four UI sections populate after upload: Transcription (cleaned_text default), Historical Notes (entity table), Confidence Map (orange-highlighted uncertain words), Raw/Cleaned toggle switches content without re-running the pipeline
result: [pending]
notes: Pre-condition — fix intake.py:61 AttributeError (get_flattened_data() should be getdata()). Set GOOGLE_API_KEY. Run `python -m palimpsest.app`, open browser, upload a manuscript image.

### 2. Confidence scoring completeness on a real manuscript (50+ words)
expected: confidence_map JSON array contains exactly one entry per space-separated token in cleaned_text; all scores are floats in [0.0, 1.0]; tokens ending in [?] score <= 0.5; common Spanish function words (el, la, de, que, y) score >= 0.85
result: [pending]
notes: Requires live GOOGLE_API_KEY and a 50+ word manuscript scan. Run after test 1 passes.

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps

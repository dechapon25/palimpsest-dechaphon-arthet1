---
status: testing
phase: 01-mvp-linear-pipeline
source: [01-VERIFICATION.md]
started: 2026-06-21T08:25:00Z
updated: 2026-06-21T08:25:00Z
---

## Current Test

number: 1
name: End-to-end Gemini transcription on easy sample
expected: |
  JSON dict with status='ok', non-empty raw_transcription containing Spanish cursive text, metadata.model='gemini-2.5-pro'
awaiting: user response

## Tests

### 1. End-to-end Gemini transcription on easy sample
expected: JSON dict with status='ok', non-empty raw_transcription containing Spanish cursive text, metadata.model='gemini-2.5-pro'
result: [pending]

### 2. Multi-sample diversity (hard + margins)
expected: Both pares_hard_19c.jpg and pares_margins_18c.jpg return status='ok' with transcribed text (quality may vary)
result: [pending]

### 3. Partial transcription graceful handling
expected: If Gemini truncates, output should not crash and should return whatever text was produced
result: [pending]

### 4. SEC-04 prompt injection defense
expected: Document text containing 'ignore previous instructions' should be transcribed verbatim as data, not followed as an instruction
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps

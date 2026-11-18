# AIESEC Assistant

Bilingual (Macedonian/English) Q&A assistant for the AIESEC in North Macedonia website.
Learning project for the CCDV-F exam: explain *why* when making changes.

## Stack
- Python 3.14, managed with uv. Windows + PowerShell.
- Run scripts: `uv run <file>.py`. Add packages: `uv add <pkg>`. Never use pip.

## Files
- `chat.py`: streaming CLI chat with history, error handling, cost counter
- `pricing.py`: per-model prices; the only place prices live
- `compare.py`: Haiku vs Sonnet vs Opus comparison
- `prompts.py`: BASE/RULES/EXAMPLES from the Week 1 few-shot experiment (kept verbatim)
- `checks.py`: deterministic answer checks, reused by the evals
- `grounding.py`: builds the grounded system prompt from `data/pages.json` + optional `data/local_facts.md`
- `grounded_demo.py`: first look at grounded answers with checks and cost

## Conventions
- Default model: `claude-haiku-5-5`. Do not change models without asking.
- Parse response content by block `type`, never by index.
- Always check `stop_reason`; never fail silently.
- Never read, print or commit `.env` or the API key.

## Facts about AIESEC
Do not invent programme names. Current exchange programmes: Global Volunteer,
Global Talent, Global Teacher. Verify anything else against the site.
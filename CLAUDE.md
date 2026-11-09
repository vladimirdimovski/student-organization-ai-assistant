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

## Conventions
- Default model: `claude-haiku-5-5`. Do not change models without asking.
- Parse response content by block `type`, never by index.
- Always check `stop_reason`; never fail silently.
- Never read, print or commit `.env` or the API key.

## Facts about AIESEC
Do not invent programme names. Current exchange programmes: Global Volunteer,
Global Talent, Global Teacher. Verify anything else against the site.
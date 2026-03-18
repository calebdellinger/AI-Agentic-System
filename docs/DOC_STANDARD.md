# Documentation Standard (Why Behind the How)

This repo uses a doc-first standard so the codebase remains transferable across
agentic frameworks without losing the "why" context.

## Applies to
- Every source file we generate (`.py`, `.js`, workflow templates, Dockerfiles)

## File-level rationale header
At the top of each file include:
- `Rationale:` why the file exists (tie to sovereignty boundary or Decision DNA)
- `How:` what the file provides/implements (high level)
- `Contracts:` what it consumes and produces (types, file paths, env vars, network boundaries)
- `Sovereignty Notes:` whether it may touch externals and where logs are written

## Public API docstrings
Document:
- Public functions and classes (FastAPI routes, orchestration loops)
- Pydantic models (especially required `rationale` fields)
- Non-trivial validation/fallback behavior

Avoid:
- Verbose narration of one-off helpers
- Copy/paste documentation without a real maintenance purpose

Rationale: This ensures auditors (or future framework swaps) can answer
"why this exists" and "how it works" by scanning the files themselves.


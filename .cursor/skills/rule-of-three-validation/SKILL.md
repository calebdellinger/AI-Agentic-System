---
alwaysApply: true
name: rule-of-three-validation
description: Track repeated error signatures across Cursor attempts, and after the same error occurs 3 times, append that error's specific correction to `.cursorrules`. Use when debugging, fixing build/test failures, resolving lint/diagnostics, or responding to runtime/exception errors.
---

# Rule-of-Three Validation

## Objective
Make the system "evolve" by learning from repeated failures: if the agent hits the same error signature three times, it must permanently record the correct resolution in `.cursorrules` so future attempts avoid the mistake.

## When to run this skill
Trigger on any *failure event* you encounter while working in this repo, including:
- Build/compile errors
- Linter/IDE diagnostics
- Test failures
- Runtime/exception traces
- HTTP/API errors that block progress

## Core loop
1. Capture the error text (verbatim as provided in logs/diagnostics) and compute an `error_signature`:
   - Prefer the exception type + the first stable message line.
   - For compiler/linter diagnostics, prefer the first line of the diagnostic message.
   - For stack traces, ignore file paths/line numbers and keep the exception type + top message.
   - For HTTP errors, use `status_code + short_error_string`.
2. Normalize the signature to reduce false mismatches:
   - Remove/ignore file paths, line/column numbers, and long IDs.
   - Keep stable wording and punctuation.
3. Load persistent counters from `.cursor/state/rule-of-three-state.json`.
4. Increment `errors[error_signature].count` (create the entry if missing).
5. If `count` is now `< 3`, keep working normally.
6. If `count` is now `>= 3`:
   - Derive a concrete `correction` that would prevent recurrence (not just “fix the bug”).
   - Update `.cursorrules` immediately under `## Rule-of-Three: Learned Corrections`:
     - If an entry for this `error_signature` already exists, update it (no duplicates).
     - Otherwise, append a new learned bullet in the form:
       - `<error_signature>`: `<correction>`
   - Reset the counter for this signature (set `count` back to `0`) and record that it was learned (so it doesn't spam).
7. After updating `.cursorrules`, follow the newly learned correction in the remainder of the task.

## Required file targets
- `.cursorrules`: store learned correction bullets under the “Rule-of-Three: Learned Corrections” section.
- `.cursor/state/rule-of-three-state.json`: store counts keyed by `error_signature`.

## Update rules for safety
- Never delete unrelated `.cursorrules` content.
- Never add vague corrections; require something actionable (e.g., “Use X type”, “Handle null”, “Use async/await here”, “Match schema field names”).
- Do not duplicate learned entries for the same `error_signature`.


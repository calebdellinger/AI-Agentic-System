---
alwaysApply: true
name: log-driven-debugging
description: Analyze the most recent RD-Lab rhythm entries (last 10 lines of `/rhythms/lab.jsonl`) to find logic bottlenecks instead of asking generic "why isn't it working?" questions. Use when debugging failures in this repo and when rhythm logs are available.
---

# Log-Driven Debugging

## Core idea
When something fails, do not ask "Why isn't it working?".
Instead, immediately switch to a log-first debug: focus only on the latest rhythm context and extract bottlenecks from it.

## When to use this skill
Use this skill when the user (or the agent) indicates one of the following:
- Debugging a failing run / stuck loop / unexpected output
- The lab run produced errors, validation failures, timeouts, or exceptions
- The agent would normally ask "why isn't it working?"

## Required inputs (prefer this order)
1. The last 10 lines of the lab rhythm file: `/rhythms/lab.jsonl`
   - If you are in RD-Lab Docker, that is the canonical location.
   - If the user has a local copy, use that local `lab.jsonl` instead.
2. If the user already pasted those last 10 lines, analyze them directly.

## Cursor interaction (so you get the right slice)
Ask the user to:
1. Open `lab.jsonl`
2. Highlight the last 10 lines
3. Press `Cmd+L` to send the selection and ask the agent with exactly:
   - `Analyze these rhythms for logic bottlenecks.`

Note: on Windows, Cursor keybindings are often `Ctrl+L` instead of `Cmd+L`. If `Cmd+L` doesn’t work, use `Ctrl+L` with the same prompt.

## Analysis method
Given the last 10 lines, identify bottlenecks by looking for (as applicable):
- Repeated/oscillating states (retry loops, repeated actor handoffs, repeated validation passes)
- Validation or schema failure markers (for example `#SYSTEM_VALIDATION_FAILURE`)
- Missing transitions (an expected event does not appear after a related one)
- Order-of-operations problems (an action happens before required prerequisites)
- Timeout / resource / dependency errors

## Output format (what you must return)
Return:
1. `Bottleneck:` (short label)
2. `Evidence:` (quote 1-3 short fragments from those last 10 lines)
3. `Why it bottlenecks:` (one sentence)
4. `Correction to try next:` (one concrete next step or code change)

Provide up to 3 bottlenecks, ranked by likelihood.


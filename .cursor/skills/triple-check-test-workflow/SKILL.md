---
name: triple-check-test-workflow
description: Runs the same test command three times to confirm stability and catch flaky/race-condition failures. Use when the user says "run a test" or "test this", especially for Python tests under tests/**/*.py or **/test_*.py.
globs: ["tests/**/*.py", "**/test_*.py"]
---

# Triple-Check Test Workflow

## When to use
Use when the user says **"run a test"** or **"test this"**.

## Workflow
1. **Iteration 1**: Run the specified test command.
2. **Iteration 2**: If successful, immediately run the exact same test again.
3. **Iteration 3**: If successful, run it a final time to confirm 3/3 stability.

## Error Handling
- If ANY iteration fails, stop the sequence immediately.
- Analyze the failure logs and suggest a fix.
- Do NOT proceed to the next iteration until the current failure is resolved.

## Output Requirement
Report the final status as: `Test Stability: [X]/3 Passes`.


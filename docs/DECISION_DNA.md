# Decision DNA (Rationale-first Bridge)

## Core rule
Every schema record that represents a decision or discovery must include:
- `rationale`: why the system chose the plan/action, written in a
  framework-agnostic way.

## What is preserved across hemispheres
Only schema-validated records may cross the hemisphere boundary via the
`spinalcord` volume.

This preserves:
- intent context (`correlation_id`, linked record ids)
- the "why" behind each step (`rationale`)

And prevents:
- raw agent chat logs
- hidden chain-of-thought artifacts

## Enforcement approach (scaffolding)
The shared Pydantic models must:
- make `rationale` required
- validate schema versions

## Escalation observability
When local validation fails repeatedly and a cloud escalation occurs:
- write a local rhythm event `#SYSTEM_ESCALATION`
- include: `task_id`, `correlation_id`, failure count, and provider transition

Rationale: This keeps sovereignty and auditability intact even when a
fallback provider is used.


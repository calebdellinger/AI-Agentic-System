# File Manifest (Scaffolding Inventory)

This is an audit-friendly inventory of the files generated for the initial
scaffolding.

Update this manifest when we add implementation code so new files always
have an explicit "why".

## Root
- `docker-compose.yml` — Rationale: wire hemispheres and n8n with separated
  networks; Sovereignty: Lab air-gapped via `internal: true` network.
- `.env.example` — Rationale: document provider selection and escalation
  contract; Sovereignty: keep secrets external to shared volumes.
- `.gitignore` — Rationale: keep local rhythms/spinalcord artifacts out of VCS.

## Docs
- `docs/DOC_STANDARD.md` — Rationale: enforce "why behind the how" in every
  file.
- `docs/DECISION_DNA.md` — Rationale: define the decision-rationale bridge
  contract and escalation observability.

## Next (to be expanded)
- `business-trinity/` — CrewAI-based orchestration scaffold and n8n
  WorkOrder dispatch stubs.
- `rd-lab/` — AutoGen-in-DinD scaffold and file-based spinalcord inbox/outbox
  stubs with local-only rhythm logging.
- `shared-schemas/` + `shared/` — shared Pydantic schema + provider-mode
  config + escalation policy (the Spinal Cord bridge).

Rationale: The manifest is meant to be quickly scannable during audits; it is
intentionally not exhaustive down to every stub module.


---
name: Doc-First Attack
overview: Provide a documentation-first implementation plan for the Sovereign Dual-Hemisphere AI OS, including a per-file “why behind the how” standard and the shared `config.py` provider/fallback design.
todos:
  - id: doc-standard
    content: Create `docs/` with `DOC_STANDARD.md`, `FILE_MANIFEST.md`, and `DECISION_DNA.md`, and define the exact “Rationale Contract” template for every file.
    status: pending
  - id: scaffold-structure
    content: "Generate the root scaffolding: `business-trinity/`, `rd-lab/`, `shared-schemas/`, `infrastructure/`, `docker-compose.yml`, `.env.example`, and docs placeholders."
    status: pending
  - id: config-contract
    content: In `shared-schemas/`, define `shared_schemas/config.py` that reads `.env`, supports `PROVIDER_MODE` (LOCAL/GEMINI/ANTHROPIC), sets vLLM base_url for LOCAL, and implements 3x Pydantic validation failure escalation with `#SYSTEM_ESCALATION` rhythm logging.
    status: pending
  - id: constitution-schemas
    content: Implement initial Pydantic schemas in `shared-schemas/` with required `rationale` fields and versioning; document each model’s rationale and constraints.
    status: pending
  - id: spinalcord-bridge
    content: Specify and implement file/volume bridge contract under `spinalcord` (`requests/`, `discoveries/`), including atomic JSON conventions and rhythm events.
    status: pending
  - id: trinity-integration
    content: "Outline and then implement Trinity’s orchestration loop: consume `ResearchDiscovery`, validate outputs via Pydantic, write `DecisionRecord` rationale rhythms before execution, create `WorkOrder` for n8n."
    status: pending
  - id: rd-lab-integration
    content: "Outline and then implement Lab’s AutoGen DinD worker: consume requests offline, produce schema-validated discoveries and decision records, write local rhythms only."
    status: pending
  - id: n8n-workorder-gateway
    content: Create the n8n webhook contract and workflow blueprint to execute Notion/Slack actions based on `WorkOrder`, with idempotency and local-only logging assumptions.
    status: pending
  - id: contract-tests-docs
    content: Add contract tests ensuring `rationale` is present and all bridge records validate against `shared-schemas`; ensure test failures capture why/how in docs.
    status: pending
isProject: false
---

# Sovereign Dual-Hemisphere AI OS (Plan of Attack, Doc-First)

## 0. Current repo state (what exists)

- This workspace currently contains only a nested project placeholder at `[research-&-development/README.md](research-&-development/README.md)` and the active plan file at `/.cursor/plans/AI OS Plan.md`.
- There is no existing `docker-compose.yml`, no `business-trinity/`, `rd-lab/`, or `shared-schemas/` code yet.

Rationale: We can safely design a clean initial structure without migrating unknown legacy code.

## 1. Documentation Standard (Your “Why behind the How” requirement)

Applies to every file we create (including `Dockerfile`s, workflow JSON, and any generated modules).

### 1.1 File-level “Rationale Contract” (in-code, not just prose)

For every new source file, include at the very top:

- A module docstring or header block containing:
  - `Rationale:` why this file exists (tie back to sovereignty, boundary, or decision DNA)
  - `How:` what it provides/implements at a high level
  - `Contracts:` what it consumes and produces (types, file paths, env vars, network boundaries)
  - `Sovereignty Notes:` whether it may touch externals and where logs are written

Rationale: If you switch agent frameworks later, the “why” stays attached to the code artifacts themselves.

### 1.2 Function/Class docstrings (hybrid rule)

Doc every:

- Public API entrypoints (FastAPI routes, orchestration loops, webhook handlers)
- “Decision DNA” critical logic (anything that writes/reads `DecisionRecord`, `ResearchDiscovery`, or `WorkOrder`)
- Pydantic models and their non-trivial constraints/validators (especially those enforcing `rationale` presence)

Rationale: This preserves handoff quality while avoiding doc bloat for one-time utilities.

### 1.3 “Decision DNA” before execution (per your rule)

Define a single internal policy helper (conceptually) used by both hemispheres:

- Before any external action or task execution that mutates state:
  - write rationale to local JSONL rhythms (include `correlation_id`, record ids, and a reason code)

Rationale: This makes the audit chain deterministic and future-proof.

### 1.4 Generated documentation artifacts

Create/update the following docs at scaffold time:

- `docs/DOC_STANDARD.md` (the rules above)
- `docs/FILE_MANIFEST.md` (a human-readable inventory of files generated, mapped to their rationale)
- `docs/DECISION_DNA.md` (how `DecisionRecord.rationale` is enforced and propagated)

Rationale: In audits, you should be able to answer “why does this exist” without reading the entire codebase.

## 2. Phase 1 — Project scaffolding (structure + sovereign defaults)

### 2.1 Directory structure to generate

At workspace root:

- `business-trinity/`
- `rd-lab/`
- `shared-schemas/`
- `infrastructure/`
- `docker-compose.yml`
- `.env.example`
- `.gitignore`
- `docs/`

Rationale: Keeping “shared bridge” isolated prevents accidental cross-hemisphere coupling.

### 2.2 Docker Compose + air-gap networking plan

In `docker-compose.yml` (root):

- Services: `trinity-api`, `rd-lab-worker`, `n8n`
- Networks:
  - `net_internal` for Trinity <-> n8n only
  - `net_lab` with `internal: true` so Lab has no path to external networks
- Volumes:
  - `spinalcord` (shared exchange volume between hemispheres)
  - hemisphere-local rhythm volumes (e.g., `trinity_rhythms`, `lab_rhythms`)

Rationale: This enforces “Lab air-gapped” at the Docker boundary, not by convention.

### 2.3 Sovereignty defaults for logs and telemetry

- Ensure containers default to local-only logs/rhythms stored in mounted volumes.
- Disable remote telemetry and cloud logging where possible.

Rationale: Sovereignty-by-default avoids “one missing env var” mistakes.

## 3. Phase 1.5 — `shared_schemas/config.py` (env-driven provider + fallback)

Implement the config module as part of the bridge library so both hemispheres compile against the same provider contract.

### 3.1 Location + purpose

- Create `shared-schemas/src/shared_schemas/config.py`.
- It reads from `.env`.

Rationale: Putting provider selection in the shared bridge reduces drift across hemispheres.

### 3.2 Provider mode contract

Use:

- `PROVIDER_MODE` in `{LOCAL, GEMINI, ANTHROPIC}`

Rules:

- If `PROVIDER_MODE=LOCAL`:
  - set `base_url` to `http://vllm-server:8000/v1`
- If `PROVIDER_MODE=GEMINI`:
  - use the LangChain Google GenAI connector (conceptually, configured by the config module)
- If `PROVIDER_MODE=ANTHROPIC`:
  - use an appropriate LangChain Anthropics connector (left as a confirm-later item if needed, but design the config to be connector-pluggable)

Rationale: A single provider contract keeps model routing framework-agnostic.

### 3.3 Fallback escalation rule (after validation failures)

Requirement:

- Always implement fallback logic conceptually as:
  - On the orchestrator side, when using LOCAL provider output:
    - attempt Pydantic validation
    - if Pydantic validation fails, retry up to 3 times
    - on the 3rd consecutive validation failure, allow escalation to a cloud model for that specific task

Config variables:

- Use `FALLBACK_PROVIDER_MODE` (env-driven) to choose the cloud provider for escalation (initially GEMINI per your direction).

Audit behavior:

- When escalation happens, write a local rhythm event: `#SYSTEM_ESCALATION` (include `task_id`, `correlation_id`, provider transition, and failure count).

Rationale: This makes the system robust while preserving “Decision DNA” and keeping escalation observable.

### 3.4 Documentation requirements for config

In `shared_schemas/config.py` and the docs:

- Document the exact meaning of every env var.
- Include a “Why this escalation exists” rationale block.

Rationale: Provider-routing bugs are high impact; this must be auditable.

## 4. Phase 2 — Pydantic Constitution (schemas)

Implement in `shared-schemas/`:

- `DecisionRecord` (must include required `rationale`)
- `ResearchDiscovery` (must include required `rationale`)
- Add helper types:
  - `WorkOrder` (for n8n intent payload)
  - versioning utilities

Rationale: The bridge is the sovereignty boundary; schema-level constraints prevent silent drift.

## 5. Phase 3 — Integration logic (n8n + handoff)

### 5.1 n8n webhook listener strategy

Trinity sends work orders to n8n; n8n performs external side effects.

- Standardize webhook payload as `WorkOrder`.
- Include idempotency and a reference to relevant `DecisionRecord`.

Rationale: External world-actions should not be executed by autonomous hemispheres.

### 5.2 Handoff from R&D (AutoGen) to Trinity (CrewAI)

- Only exchange schema-validated records via the `spinalcord` volume.
- Lab writes `ResearchDiscovery` + any associated `DecisionRecord`.
- Trinity consumes and turns discoveries into CrewAI tasks.

Rationale: File/volume exchange provides deterministic sovereignty boundaries.

## 6. Milestones (doc-first deliverables)

1. Scaffold directories + Docker + docs (`docs/DOC_STANDARD.md`, `docs/FILE_MANIFEST.md`, `docs/DECISION_DNA.md`).
2. Implement `shared_schemas/config.py` provider/fallback contract + document all env vars.
3. Implement schemas (`DecisionRecord`, `ResearchDiscovery`, `WorkOrder`) with `rationale` required and versioning included.
4. Implement file-bridge semantics for `spinalcord` (atomic JSON write/read conventions).
5. Implement Trinity orchestration loop: consumes discoveries, writes rationale rhythms, validates with Pydantic, creates work orders.
6. Implement Lab worker: consumes spinalcord requests, runs AutoGen in DinD sandbox with no-network, writes discoveries/decision records + rhythms.
7. Implement n8n webhook + workflow blueprint for Notion actions.

Rationale: Each milestone preserves “Decision DNA” and the sovereignty boundary.

## 7. Open items (to lock before implementation code)

- Confirm the exact LangChain connector choice for `PROVIDER_MODE=ANTHROPIC` (design should allow swapping connectors without changing core contracts).

Rationale: Connector selection is implementation detail; architecture should remain stable.
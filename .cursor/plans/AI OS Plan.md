---
name: Dual-Hemisphere Plan
overview: Scaffold a Sovereign AI OS with business-trinity (CrewAI/LangChain), rd-lab (AutoGen in DinD, air-gapped), and a shared Pydantic “decision DNA” schema bridged via a local volume; wire n8n as the external-action gateway via webhooks.
todos:
  - id: scaffold-monorepo
    content: Create root folders `business-trinity/`, `rd-lab/`, `shared-schemas/`, `infrastructure/` plus root `docker-compose.yml` and `.env.example` skeletons.
    status: pending
  - id: docker-compose-networking
    content: Draft `docker-compose.yml` with two networks (`net_internal`, `net_lab internal:true`), mount local volumes for spinalcord and rhythms, and attach n8n + trinity to `net_internal` while attaching lab only to `net_lab`.
    status: pending
  - id: shared-schemas-package
    content: "Implement `shared-schemas/` as a Python package with initial Pydantic models: `DecisionRecord`, `ResearchDiscovery`, plus `WorkOrder` and minimal constitutional check scaffolding."
    status: pending
  - id: spinalcord-bridge-contract
    content: Define file-based bridge layout under `spinalcord` volume (`requests/`, `discoveries/`) and specify atomic JSON write/read semantics for record exchange.
    status: pending
  - id: trinity-api-and-orchestrator
    content: Implement Trinity orchestrator loop that watches `spinalcord/discoveries/`, creates CrewAI execution tasks, emits `WorkOrder` intents, writes local rhythms, and updates `DecisionRecord` status.
    status: pending
  - id: rd-lab-autogen-dind
    content: Implement Lab worker that consumes `spinalcord/requests/`, runs AutoGen inside DinD with no-network policy, and writes `ResearchDiscovery` + `DecisionRecord` outputs + lab rhythms.
    status: pending
  - id: n8n-workflow-blueprint
    content: Add an n8n webhook-driven workflow blueprint to accept `WorkOrder` JSON and perform Notion actions using n8n’s local `n8n_data` credentials storage.
    status: pending
  - id: sovereignty-and-secrets
    content: "Add a sovereignty checklist: local-only rhythm logs, secret redaction, disable telemetry, and enforce that hemispheres never directly call Notion/Slack (only n8n executes externals)."
    status: pending
  - id: tests-and-contract-checks
    content: Add contract tests to ensure every exchanged record validates against shared-schemas and that `rationale` is always present.
    status: pending
isProject: false
---

# Sovereign Dual-Hemisphere AI OS (Plan)

## Current repo state (discovered)

- The workspace root appears to contain a nested project folder: `[x:/AI Agentic System/research-&-development/README.md](x:/AI Agentic System/research-&-development/README.md)` (content: `# AI-OS`) plus `[x:/AI Agentic System/research-&-development/nexus-4d.html](x:/AI Agentic System/research-&-development/nexus-4d.html)`.
- No existing `docker-compose.yml`, no `business-trinity/`, `rd-lab/`, `shared-schemas/`, or `infrastructure/` directories are present.
- No existing code for CrewAI, LangChain, AutoGen, or Pydantic is present yet.

## Confirmed assumptions from clarifications

- Stack: Python-only for Trinity/R&D/bridge (CrewAI + LangChain + AutoGen + Pydantic); n8n uses its official container image.
- Air-gapped Lab: Lab has no internet/egress, but Trinity/internal Docker networking is allowed for other services.
- LLM runtime: use a local OpenAI-compatible endpoint (vLLM).
- n8n egress: n8n is allowed outbound internet to reach Notion/Slack.

## Architecture (high-level)

```mermaid
graph TD
  UserOrExternal[User / External Trigger] -->|webhook/task| n8n[Nervous System: n8n]

  n8n -->|WorkOrder intent| Trinity[Business Trinity: CrewAI + LangChain]
  Trinity -->|ResearchRequest/continuation| BridgeVol[(Spinal Cord Volume)]
  BridgeVol -->|ResearchDiscovery| Lab[RD Lab: AutoGen in DinD sandbox]

  Lab -->|ResearchDiscovery JSON (schema)| BridgeVol
  BridgeVol -->|discovery| Trinity

  Trinity -->|WorkOrder JSON| n8n
  n8n -->|Notion/Slack actions| ExternalWorld[(Notion/Slack)]
```



Rationale: This keeps external side-effects isolated in n8n while hemispheres communicate only through schema-validated “Decision DNA”.

## Phase 1: Project scaffolding

### Proposed directory structure

At workspace root:

- `/business-trinity`
- `/rd-lab`
- `/shared-schemas`
- `/infrastructure`
- `docker-compose.yml`
- `.env.example`
- `.gitignore`

#### `shared-schemas/`

- `pyproject.toml`
- `src/shared_schemas/`
  - `__init__.py`
  - `decision_record.py`
  - `research_discovery.py`
  - `work_order.py`
  - `rhythm_event.py`
  - `constitution.py`
  - `versioning.py`
- `tests/`



#### `business-trinity/`

- `pyproject.toml`
- `src/business_trinity/`
  - `api/` (FastAPI webhook endpoints)
    - `__init__.py`
    - `work_orders.py`
  - `orchestrator/`
    - `main_loop.py` (monitors spinal cord volume)
    - `state_store.py`
  - `crew_execution/`
    - `crews.py` (CrewAI configuration)
    - `tasks.py`
  - `tooling/`
    - `langchain_connectors.py` (tool connectors that produce intents, not direct external calls)
  - `storage/`
    - `log_writer.py` (local JSONL rhythms)
- `Dockerfile`
- `tests/`



#### `rd-lab/`

- `pyproject.toml`
- `src/rd_lab/`
  - `autogen_runner.py`
  - `dinD_executor/`
    - `sandbox_runner.py` (policy for running code without internet)
  - `bridge/`
    - `inbox.py` (reads ResearchRequests)
    - `outbox.py` (writes ResearchDiscovery + DecisionRecord)
  - `storage/`
    - `log_writer.py` (local JSONL rhythms)
- `Dockerfile`
- `tests/`



#### `infrastructure/`

- `n8n/`
  - `docker-compose.override.yml` (optional)
  - `workflows/`
    - `trinity-workorder-to-notion.json` (workflow blueprint to import)
  - `hooks/`
    - `verify-signature.js` (optional, if used)
- `policy/`
  - `egress-block.md`
  - `volume-layout.md`



### Docker Compose plan (networking + volumes + air-gap)

Single `docker-compose.yml` at root with these services (minimum):

- `trinity-api` (Python service)
- `trinity-orchestrator` (can be same image as `trinity-api`)
- `rd-lab-worker` (AutoGen + DinD sandbox runner)
- `n8n` (official `n8nio/n8n` image)

#### Networks

- `net_internal` (for Trinity<->n8n private calls)
- `net_lab` with `internal: true` (Lab has no path to external networks)

Rationale: Docker’s `internal: true` prevents routing to outside the Docker host for that network attachment.

#### Keeping the Lab air-gapped

- Attach `rd-lab-worker` only to `net_lab`.
- Do not attach `rd-lab-worker` to `net_internal`.
- Use a file/volume bridge (`spinalcord` volume) for all handoffs, so Lab never needs to call Trinity over the network.
- In the DinD sandbox runner, execute inner containers with `--network none` or an internal-only network created inside the lab daemon (no default route).

Rationale: The safest approach is to remove the need for inter-service network access and enforce no-network at runtime for DinD.

#### Volumes (so logs never leave the host)

- `spinalcord` (shared volume mounted into Trinity + Lab)
  - `requests/`, `discoveries/`, `results/`, `errors/`
- `trinity_rhythms` (local JSONL)
- `lab_rhythms` (local JSONL)
- `n8n_data` (n8n persistent storage)
- `model_cache` (local if vLLM/weights are co-located)

Rationale: Local volumes provide explicit control, auditability, and easy backup/retention without cloud telemetry.

### Sovereignty-focused logging (“Rhythms”)

- Implement a local-only rhythm writer in both hemispheres:
  - Append JSON Lines per event (time, record_id, event_type, payload redacted)
  - Enforce secret redaction before writing
- Disable remote logging/telemetry in all containers.

Rationale: A deterministic local event log is the backbone for compliance and debugging.

## Phase 2: The Pydantic Constitution (initial schemas)

All schemas live in `shared-schemas/` and are versioned.

### `DecisionRecord` (initial)

Fields (Pydantic model):

- `record_id`: UUID
- `schema_version`: semver string
- `timestamp_utc`: datetime
- `hemisphere`: enum(`trinity`,`lab`)
- `correlation_id`: UUID (threads request/discovery/decisions)
- `decision_type`: enum (e.g., `research`, `execution`, `tool_intent`, `validation`)
- `rationale`: string (required) describing why the decision/plan was made
- `inputs_summary`: object (strictly typed summary; no raw secrets)
- `decision_payload`: object (strictly typed union by decision_type)
- `outputs_summary`: object (strictly typed summary)
- `constitutional_checks`: list of
  - `rule_id`: string
  - `passed`: boolean
  - `evidence_summary`: string
- `status`: enum(`pending`,`completed`,`failed`)
- `artifact_refs`: list of
  - `ref_id`: string
  - `volume_path`: string (relative to mounted volume roots)
- `error`: optional structured error

Rationale: `rationale` is the “Decision DNA” anchor, while summaries and artifact refs prevent schema drift and secret leakage.

### `ResearchDiscovery` (initial)

Fields (Pydantic model):

- `discovery_id`: UUID
- `schema_version`: semver string
- `timestamp_utc`: datetime
- `correlation_id`: UUID
- `hypothesis`: string
- `methods`: list of structured method descriptors (no hidden tool secrets)
- `findings`: list of structured findings
  - each finding can include: `claim`, `support_summary`, `confidence` (0..1)
- `next_questions`: list of strings
- `rationale`: string (required) explaining why these findings are the “next best” output
- `linked_decision_record_id`: UUID (optional but encouraged)
- `artifact_refs`: list of local-volume refs (e.g., code outputs, diffs)

Rationale: By making `rationale` required at the discovery layer too, downstream execution can be purely “schema-guided” rather than agent-chained.

### Versioning + compatibility

- Add a `schema_version` to every record.
- Provide a `versioning.py` helper that:
  - validates version compatibility
  - provides conversion stubs later

Rationale: Schema evolution is inevitable; explicit versioning prevents silent interpretation errors.

## Phase 3: Integration logic (n8n + hemisphere handoff)

### n8n webhook strategy (Trinity -> Notion)

Goal: Trinity submits work orders; n8n performs external side-effects.

#### n8n endpoint model

- Trinity sends `POST` to an n8n webhook URL:
  - `POST /webhook/trinity-workorder` (path defined by imported workflow)
- Payload is a `WorkOrder` schema (from `shared-schemas`) containing:
  - `work_order_id` UUID
  - `correlation_id` UUID
  - `operation` enum(`notion_create`,`notion_update`,`slack_post`, ...)
  - `payload` typed per operation
  - `decision_dna_ref` pointing at relevant `DecisionRecord.record_id`
  - `idempotency_key` (so retries are safe)

Rationale: Centralizing side-effects in n8n guarantees we can enforce “Sovereignty First” at the boundary.

#### Workflow responsibilities

- Verify inbound signature from Trinity (shared secret)
- Validate payload shape (either n8n-side strict checks or rely on schema in Trinity)
- Execute Notion/Slack actions using n8n credentials stored in local `n8n_data`
- Return a structured `WorkOrderResult` to Trinity

Rationale: Signature + idempotency makes automation reliable and reduces accidental duplicates.

### Handoff: AutoGen (R&D) -> CrewAI (Execution) via the Spinal Cord

#### What travels across hemispheres

- Never raw agent chat logs.
- Only schema-validated records written to the `spinalcord` volume:
  - Lab writes `ResearchDiscovery` + associated `DecisionRecord`
  - Trinity reads them and constructs CrewAI tasks

Rationale: “Decision DNA” is preserved without transferring transient reasoning or leaking sensitive runtime artifacts.

#### Execution loop (Trinity)

- Trinity orchestrator watches `spinalcord/discoveries/`.
- For each new discovery:
  - Create a CrewAI run plan using LangChain connectors that output `WorkOrder` intents (not direct Notion calls)
  - Write a `DecisionRecord` for the execution rationale
  - Send WorkOrder to n8n
  - Store `WorkOrderResult` and mark the corresponding `DecisionRecord` completed

Rationale: This creates a closed-loop audit trail from discovery rationale to action outcomes.

#### R&D loop (Lab)

- Lab watches `spinalcord/requests/`.
- For each request:
  - Run AutoGen debate inside DinD sandbox with no-network
  - Produce `ResearchDiscovery` + `DecisionRecord` with required `rationale`
  - Write outputs to `spinalcord/discoveries/` and local lab rhythms logs

Rationale: Deterministic file-based handoffs avoid network coupling and reinforce air-gap guarantees.

## Implementation milestones (no code yet)

1. Scaffolding
  - Create the 4 directories with Python package skeletons and Dockerfiles.
  - Add root `docker-compose.yml` wiring networks + volumes.
2. Constitution + schema validation tests
  - Implement `DecisionRecord` and `ResearchDiscovery` in `shared-schemas`.
  - Add unit tests for required `rationale` and version fields.
3. Spinal Cord bridge (file-based)
  - Implement directory layout and atomic JSON write/read conventions.
  - Add basic “record appears -> orchestrator consumes” logic.
4. Trinity integration
  - Implement FastAPI endpoints for receiving inbound triggers (optional) and for sending work orders to n8n.
  - Implement CrewAI execution that outputs `WorkOrder` intents.
5. Lab integration (AutoGen + DinD)
  - Implement request consumption and discovery emission.
  - Enforce no-network execution policy for DinD.
6. n8n workflow blueprint
  - Prepare and document the workflow import JSON for webhook-to-Notion.
  - Document environment variables and local volume requirements.
7. Sovereignty checklist
  - Ensure all rhythms/logs are written to mounted local volumes.
  - Ensure no cloud telemetry env vars are enabled.

Rationale: Milestones align with the phases you specified while keeping air-gap and “Decision DNA” constraints foundational from day one.

## Open (non-blocking) engineering decisions to finalize during implementation

- Where exactly vLLM runs (separate container vs external service) and how model endpoints are configured.
- Whether we include a lightweight local queue (sqlite) in the spinalcord volume or keep pure file-based semantics.

Rationale: These can be finalized once we add the first working end-to-end loop, but the plan above keeps them isolated behind the bridge interface.
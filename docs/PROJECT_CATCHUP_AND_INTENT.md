# Project Catch-up and Original Intent

Last updated: 2026-04-15

## Why this doc exists

This is a memory-refresh document to reconstruct your original design intent and compare it with what is currently implemented, so you can restart quickly without rereading the whole repo.

---

## Original thought process (from planning docs)

The core architecture idea was:

- Build a **sovereign dual-hemisphere system**:
  - `rd-lab` does constrained research/exploration.
  - `business-trinity` does orchestration/execution planning.
- Exchange structured records through a shared **Spinal Cord** (volume/file handoff), not ad-hoc agent chat.
- Make Pydantic schemas the constitutional boundary ("Decision DNA"), especially required rationale fields.
- Keep external side effects **outside** of agent code and route them through **n8n**.
- Preserve auditability with local rhythm logs and explicit rationale before execution/escalation.

In short: deterministic contracts + local observability + strict boundary between reasoning and side effects.

---

## What has been implemented so far

## 1) n8n is wired into infrastructure

- `docker-compose.yml` contains an `n8n` service (`n8nio/n8n`) on port `5678`.
- Persistent storage is configured via `n8n_data` volume.
- Trinity container env includes:
  - `N8N_WORKORDER_WEBHOOK_URL`
  - `N8N_WORKORDER_WEBHOOK_SECRET`
- `.env.example` defines the corresponding n8n variables, including `N8N_ENCRYPTION_KEY`.
- `scripts/daddies-home.ps1 -FullStack` starts `trinity-api` + `n8n` in addition to the UI/lab stack.

Status: **present and runnable as infrastructure scaffolding**.

## 2) Bridge contract exists for Trinity -> n8n

- `shared-schemas/src/shared_schemas/work_order.py` defines `WorkOrder` with:
  - `operation` (`notion_create`, `notion_update`, `slack_post`, `noop`)
  - `payload`
  - `decision_dna_ref`
  - `idempotency_key`
- `business-trinity/src/business_trinity/api/work_orders.py` has `post_work_order_to_n8n(...)`:
  - sends JSON payload to webhook
  - supports `X-WorkOrder-Secret` header

Status: **contract and sender function implemented**.

## 3) n8n workflow/hook artifacts exist, but are placeholders

- `infrastructure/n8n/workflows/trinity-workorder-to-notion.json` explicitly marks:
  - `"scaffold_only": true`
- `infrastructure/n8n/hooks/verify-signature.js` currently accepts everything (`return true`).

Status: **blueprint only; no production-grade verification/logic yet**.

## 4) Trinity orchestration loop is still scaffold stage

- `business-trinity/src/business_trinity/orchestrator/main_loop.py`:
  - ensures spinalcord dirs exist
  - writes startup rhythm events
  - stays alive in a loop
- No real discovery consumption -> decisioning -> work order emission loop yet.

Status: **bootstrapped runtime shell, not full behavior**.

---

## Plan docs vs current repo (important context)

Some plan docs still include historical "starting from zero" notes (for example, stating key directories/files did not exist at plan time). The repo has since progressed beyond that scaffold baseline.

Interpretation:

- The **architecture intent is still valid**.
- The **status markers in the plan files are stale** and should not be treated as current completion tracking.

---

## What you likely intended next (inferred from plans + current code)

This appears to be the intended next sequence:

1. Implement real Trinity execution loop behavior:
   - consume discoveries from spinalcord
   - validate with shared schemas
   - emit rationale/decision rhythms
   - generate and dispatch `WorkOrder`s
2. Complete n8n workflow:
   - import/build actual webhook flow
   - map `operation` + `payload` to Notion/Slack actions
   - return structured result payload back to Trinity
3. Implement request authenticity and idempotency:
   - replace placeholder signature check
   - enforce secret validation and replay-safe behavior
4. Close the loop with contract tests:
   - schema conformance across handoff artifacts
   - required rationale fields and retry-safe semantics
5. Refresh docs/manifests to match current state:
   - convert stale "todo/pending" markers into accurate progress snapshots

---

## Current gap map (quick scan)

- **Done**
  - Compose/service wiring for n8n
  - Env contract for webhook + secret + encryption key
  - Shared `WorkOrder` schema
  - Trinity HTTP sender helper for work orders
  - n8n workflow and signature files created

- **Partially done**
  - Trinity orchestrator loop (runtime shell exists, behavior missing)
  - Documentation coverage (good rationale style, but status freshness varies)

- **Not done yet**
  - Real n8n workflow actions and result contract handling
  - Real signature verification enforcement
  - End-to-end run proving discovery -> work order -> external action -> result ack
  - Comprehensive contract/integration tests for this flow

---

## Suggested "restart here" checklist

If you are jumping back in after time away, this order should minimize context switching:

1. Validate stack boots:
   - run `scripts/daddies-home.ps1 -FullStack`
   - verify UI, Trinity API health, and n8n UI are reachable
2. Finalize n8n workflow JSON from scaffold to executable flow.
3. Wire Trinity orchestrator to actually produce and post one concrete `WorkOrder` from a controlled input.
4. Replace `verify-signature.js` placeholder with real check and fail-closed behavior.
5. Add one happy-path E2E test and one rejection-path test (bad secret / duplicate idempotency).
6. Update planning docs with a "current state" section so this memory gap does not happen again.

---

## One-line project summary

You already built the boundary contracts and infrastructure shape; the remaining work is to turn scaffolded loop/workflow pieces into a verified end-to-end execution path.

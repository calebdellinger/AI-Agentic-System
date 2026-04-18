# n8n -> Notion Automation Setup

This project now includes an importable n8n workflow at:

- `infrastructure/n8n/workflows/trinity-workorder-to-notion.json`

It consumes Trinity `WorkOrder` payloads from:

- `POST /webhook/trinity-workorder`

## What the workflow does

- Validates required `WorkOrder` fields.
- Verifies `X-WorkOrder-Secret` against `N8N_WORKORDER_WEBHOOK_SECRET`.
- Enforces idempotency using `idempotency_key` (duplicate requests are ignored with an `ok` response).
- Routes by operation:
  - `notion_create`
  - `notion_update`
  - `noop`
  - unsupported operations return a structured error response.
- Calls Notion REST API using `NOTION_API_TOKEN`.
- Returns a structured JSON result payload to Trinity.

## Required environment variables

Set these in your `.env` before starting `n8n`:

- `N8N_WORKORDER_WEBHOOK_SECRET`
- `NOTION_API_TOKEN`
- `NOTION_API_VERSION` (defaults to `2022-06-28`)
- `NOTION_DATABASE_ID` (optional fallback for `notion_create`)

`docker-compose.yml` passes these into the `n8n` container.

## Import into n8n

1. Open n8n UI at `http://localhost:5678`.
2. Create/import workflow from JSON.
3. Import `infrastructure/n8n/workflows/trinity-workorder-to-notion.json`.
4. Save and activate workflow.

## Expected WorkOrder payloads

### notion_create

`payload` should include:

- `database_id` (optional if `NOTION_DATABASE_ID` env is set)
- `properties` (Notion page properties object)
- `children` (optional block array)

### notion_update

`payload` should include:

- `page_id` (required)
- `properties` (optional)
- `archived` (optional boolean)
- `icon` / `cover` (optional)

## Quick test (manual webhook)

Send a POST to:

- `http://localhost:5678/webhook/trinity-workorder`

with header:

- `X-WorkOrder-Secret: <your-secret>`

and a JSON body matching `shared_schemas.work_order.WorkOrder`.

## Notes

- Signature helper code also exists at `infrastructure/n8n/hooks/verify-signature.js` for reuse in custom n8n code nodes.
- This workflow uses HTTP Request nodes so it does not require an n8n-specific Notion credential object.

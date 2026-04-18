# Company knowledge (shared across hemispheres)

**Rationale:** Long-lived reference material (SOPs, glossaries, process notes) is **not** pushed through `spinalcord` JSON. Both **RD-Lab** and **Trinity** mount the same tree read/write (vector index may write under `vector-index/`).

**Contracts:**

- **Framework** lives under `framework/` (schemas, conventions). It is **industry-agnostic**. See **[Knowledge best practices & templates](framework/KNOWLEDGE_BEST_PRACTICES.md)**.
- **Tenant content** lives under `companies/<slug>/`. Only that subtree changes when you “plug in” another company.
- **Spinalcord** remains the channel for schema-validated **handoffs** (requests, discoveries, decisions). This tree is for **human-curated knowledge** and future **RAG**.

## Active company

Set at runtime (Docker / `.env`):

| Variable | Default | Meaning |
|----------|---------|--------|
| `COMPANY_KNOWLEDGE_ROOT` | `/company-knowledge` | Root of this repo on the host/container |
| `COMPANY_KNOWLEDGE_SLUG` | `example-regional-concrete` | Subfolder under `companies/` |

Python: `from shared.company_knowledge.paths import company_doc_root, iter_document_files`.

## Layout (per company)

```
companies/<slug>/
  manifest.json          # Company metadata (see framework/manifest.schema.json)
  operations/            # How work gets done (field + back office)
  reference/             # Glossaries, policies, links to authority docs
  strategy/              # Optional: positioning, growth notes (non-binding)
```

Swap **industry** by replacing `companies/<slug>/` content and `manifest.json` — **no code changes** required.

## Vector index (scaffolding)

Source docs stay in `companies/`. Embeddings / ANN index live under `vector-index/` (see `vector-index/README.md`). Ingestion jobs will read from `companies/<slug>/` and write derived artifacts there.

## Example tenant

`companies/example-regional-concrete/` is a **fictional** small subcontractor used for integration tests. Content may mention concrete construction **as sample text only**; product code must remain domain-neutral unless you add an explicit industry feature.

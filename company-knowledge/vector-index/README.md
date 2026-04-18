# Vector index (scaffolding)

**Rationale:** Source-of-truth documents live in `../companies/<slug>/`. This directory holds **derived** artifacts (chunk manifests, embedding stores) produced by future ingestion pipelines.

## Planned layout

```
vector-index/
  README.md                 # this file
  by-company/
    <slug>/                 # per-tenant derived data
      chunks.jsonl          # optional: stable chunk IDs + source paths + hashes
      store/                # optional: Chroma / Qdrant snapshot / pgvector dump metadata
```

## Integration rules

1. **Never** treat the vector store as authoritative; re-build from `companies/` when in doubt.
2. Ingestion should record **source path + content hash** per chunk for auditability.
3. Hemispheres resolve paths via `shared.company_knowledge.paths` — add a retriever implementation later without changing container mount contracts.

## Future stack (pick one later)

- Embedded: Chroma / sqlite under `by-company/<slug>/store/`
- Service: Qdrant / pgvector with connection string in env (out of tree)

.gitignore in repo root excludes large binary index blobs once you add them.

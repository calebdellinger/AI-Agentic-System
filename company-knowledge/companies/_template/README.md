# Template: new company slug

1. Copy this folder to `../<your-slug>/` (lowercase, hyphens).
2. Edit `manifest.json` (see `../../framework/manifest.schema.json`).
3. Fill `operations/`, `reference/`, `strategy/` with your curated markdown.
4. Set `COMPANY_KNOWLEDGE_SLUG=<your-slug>` for Lab + Trinity containers.
5. (Later) Run vector ingest to populate `../../vector-index/by-company/<your-slug>/`.

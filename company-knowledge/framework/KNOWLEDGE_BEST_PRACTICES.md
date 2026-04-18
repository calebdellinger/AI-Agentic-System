# Knowledge best practices (for RAG & agent systems)

This document is **framework-level**: it applies to any industry or company using the shared `company-knowledge/` tree with RD-Lab and Trinity.

---

## Core idea: **curated signal > raw volume**

Agents see **only what you put in context** (prompt + retrieved chunks). More documents usually mean **noisier retrieval** unless you **govern** what exists, how it’s titled, and what’s authoritative.

| Priority | What it fixes |
|--------|----------------|
| **Quality** | Correct, current, non-contradictory text → consistent “how we work” behavior. |
| **Quantity** (after quality) | Broader coverage **without** duplicating or contradicting primaries. |

**Rule of thumb:** If adding a doc doesn’t change a real decision or answer a real question, **don’t add it** (or merge it into an existing canonical page).

---

## When to **focus on quality** (do this first)

1. **Early deployment** — You’re defining how agents should sound and what they’re allowed to assume.
2. **Contradictions appear** — Outputs flip between “risk-first” and “speed-first” because docs disagree.
3. **Retrieval feels random** — Wrong chunks surface; often duplicate or vague sources are the cause.
4. **Compliance / safety** — One wrong or stale instruction is worse than missing optional detail.
5. **Small team** — You can’t babysit a huge corpus; a tight set of **canonical** pages wins.

**Quality work =** one owner per topic, explicit “source of truth,” dates/owners, retire old versions.

---

## When **quantity** helps (after quality is under control)

1. **Stable canon exists** — You have 10–30 strong pages and clear folder rules; now you **extend** edge cases.
2. **Specialized depth** — e.g. regional regs, client-specific addenda **as separate, labeled** docs (not pasted into random notes).
3. **Auditable history** — You need **append-only** decision logs or RFIs **cross-linked** to the canon (not conflicting with it).
4. **Measured gaps** — You log “agent couldn’t answer X” and **add one targeted** doc or section—not 100 generic exports.

**Quantity without curation =** more chunks competing for the same query → **worse** answers.

---

## Practices that improve both quality *and* retrieval

1. **Single source of truth** per topic — Link out; don’t copy-paste the same policy in five files.
2. **Title + first paragraph = intent** — Retrieval often keys off headings and lead sentences.
3. **Stable slugs & paths** — Move rarely; if you move, update links and ingestion (future vector indexes).
4. **Front-matter (optional)** — `status: canonical | draft | archived`, `owner`, `last_reviewed` (see template below).
5. **Glossary** — Define org-specific terms once; agents stop inventing definitions.
6. **“Operating model” page** — Short description of how decisions are made (see template). Highest ROI for “company brain” feel.
7. **Version discipline** — Archive superseded docs (`archive/` or `status: archived`) instead of deleting without trace.

---

## Anti-patterns

- Dumping **entire email exports** or **wiki dumps** without cleanup.
- **Duplicate** policies with tiny wording differences (pick one; diff the rest).
- **Stale** docs that contradict the current `manifest` or strategy page.
- **Secrets** in knowledge trees (credentials, unreleased bids)—use redacted bundles and separate secret stores.

---

## Review cadence (suggested)

| Frequency | Action |
|-----------|--------|
| **Each change** | Update one canonical doc; note `last_reviewed`. |
| **Monthly** (active org) | Scan `draft` / conflicting sections; archive noise. |
| **Per “plug-in”** | New `company_slug`: fill manifest + operating model + one ops + one reference doc before scaling volume. |

---

## Templates

### A. New markdown doc (copy-paste)

```markdown
---
status: canonical
owner: "Team or person"
last_reviewed: YYYY-MM-DD
tags: [operations, field]   # optional: for humans / future filters
---

# <Title — specific outcome or question this page answers>

**Purpose:** One sentence — why this doc exists.  
**Scope:** What is / isn’t covered.  
**Authority:** Canonical / draft / supersedes: [link or "none"]

## When to use this
- Bullet: scenario A
- Bullet: scenario B

## Decisions & rules
- Clear, testable statements (avoid vague “usually” unless you define it).

## Links
- Related: [other doc path]
```

### B. Operating model (“how the company brain works”) — 1–2 pages

```markdown
# Operating model (example template)

## What we optimize for
- Primary: (e.g. predictable delivery, margin, safety, reputation — pick and rank)
- Secondary:
- We explicitly do **not** optimize for: (e.g. winning every bid at any price)

## How decisions get made
- **Fast vs slow paths:** what can field decide vs what needs office/GC?
- **Data vs judgment:** when numbers are required before acting
- **Innovation:** where experimentation is encouraged vs where process is fixed

## How we communicate
- Channels, escalation, “single coordinator” rules if relevant

## Risk & stop-work
- Conditions that halt work until resolved

## Document hygiene
- Where the **canonical** copies live; how to propose changes

*Keep this short. Link out to long SOPs.*
```

### C. `manifest.json` (already schema-backed)

Use `companies/<slug>/manifest.json` for **identity and human labels**, not for encoding secret logic. Optional future tags (e.g. `operating_tags`) can stay **descriptive** only unless you add generic code that reads them.

---

## Quick decision: “Should I add this document?”

Ask:

1. **Does it answer a repeated question** or prevent a **class of mistakes**?  
2. **Is it duplicative?** Can you add a **section** to an existing canonical page instead?  
3. **Will it stay true** for 90+ days? If not, `draft` or link to a ticket, not the canon.  
4. **Can retrieval find it** from a realistic user question? (Title + first § matter.)

If yes / no / yes / yes → good candidate. If duplicate or stale-prone → fix quality first.

---

## Where this lives in your repo

- **Framework (this file):** `company-knowledge/framework/KNOWLEDGE_BEST_PRACTICES.md`  
- **Tenant content:** `company-knowledge/companies/<slug>/`  
- **Future vectors:** `company-knowledge/vector-index/` — still treat **files under `companies/`** as source of truth.

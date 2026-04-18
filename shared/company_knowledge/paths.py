"""
Rationale: Canonical path resolution for the company knowledge tree.

How:
- `COMPANY_KNOWLEDGE_ROOT` — mount point (default `/company-knowledge`).
- `COMPANY_KNOWLEDGE_SLUG` — active tenant under `companies/<slug>/`.

Contracts:
- Pure filesystem; safe to import from both hemispheres.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Generator

DEFAULT_KNOWLEDGE_ROOT = "/company-knowledge"
DEFAULT_COMPANY_SLUG = "example-regional-concrete"


def knowledge_root() -> Path:
    return Path(os.getenv("COMPANY_KNOWLEDGE_ROOT", DEFAULT_KNOWLEDGE_ROOT))


def active_company_slug() -> str:
    return os.getenv("COMPANY_KNOWLEDGE_SLUG", DEFAULT_COMPANY_SLUG)


def company_doc_root(company_slug: str | None = None) -> Path:
    slug = company_slug or active_company_slug()
    return knowledge_root() / "companies" / slug


def vector_index_root() -> Path:
    return knowledge_root() / "vector-index"


def company_vector_index_dir(company_slug: str | None = None) -> Path:
    slug = company_slug or active_company_slug()
    return vector_index_root() / "by-company" / slug


def iter_document_files(
    company_slug: str | None = None,
    *,
    patterns: tuple[str, ...] = ("**/*.md", "**/*.mdx", "**/*.txt"),
) -> Generator[Path, None, None]:
    """
    Yield curated text documents under the company tree (non-recursive glob per pattern).
    """

    root = company_doc_root(company_slug)
    if not root.is_dir():
        return
    seen: set[Path] = set()
    for pattern in patterns:
        for p in root.glob(pattern):
            if p.is_file() and p not in seen:
                seen.add(p)
                yield p


def iter_document_files_sorted(
    company_slug: str | None = None,
    *,
    patterns: tuple[str, ...] = ("**/*.md", "**/*.mdx", "**/*.txt"),
) -> list[Path]:
    return sorted(iter_document_files(company_slug, patterns=patterns), key=lambda x: str(x))


def load_manifest_dict(company_slug: str | None = None) -> dict[str, Any] | None:
    """
    Best-effort read of companies/<slug>/manifest.json (no schema validation here).
    """

    path = company_doc_root(company_slug) / "manifest.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def summarize_knowledge_mount(company_slug: str | None = None) -> dict[str, Any]:
    """
    Small dict for rhythm/debug logs (no file contents).
    """

    slug = company_slug or active_company_slug()
    root = company_doc_root(slug)
    docs = iter_document_files_sorted(slug) if root.is_dir() else []
    return {
        "company_knowledge_root": str(knowledge_root()),
        "company_slug": slug,
        "company_doc_root": str(root),
        "company_doc_exists": root.is_dir(),
        "document_file_count": len(docs),
        "vector_index_dir": str(company_vector_index_dir(slug)),
    }

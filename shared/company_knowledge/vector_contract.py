"""
Rationale: Future vector/RAG backends implement a single protocol.

How:
- `StubCompanyKnowledgeRetriever` returns no chunks until you wire Chroma/Qdrant/etc.
- Call sites (Lab / Trinity) depend on `CompanyKnowledgeRetriever`, not a vendor SDK.

Contracts:
- Chunks must carry `source_path` for audit trails linking back to `companies/<slug>/`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence, runtime_checkable


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source_path: str
    chunk_id: str = ""


@runtime_checkable
class CompanyKnowledgeRetriever(Protocol):
    def query(self, query: str, *, top_k: int = 5) -> Sequence[RetrievedChunk]: ...


class StubCompanyKnowledgeRetriever:
    """
    Rationale: Safe default — no network, no embeddings.

    Replace via DI / factory when `vector-index/` is populated.
    """

    def query(self, query: str, *, top_k: int = 5) -> Sequence[RetrievedChunk]:  # noqa: ARG002
        return ()

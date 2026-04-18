"""
Rationale: Company-scoped knowledge is shared by RD-Lab and Trinity via a
mounted filesystem tree — separate from `spinalcord` message artifacts.

Contracts:
- Path helpers only; no industry-specific branching.
- Vector/RAG implementations plug in behind `vector_contract` later.
"""

from shared.company_knowledge.paths import (
    active_company_slug,
    company_doc_root,
    company_vector_index_dir,
    iter_document_files,
    iter_document_files_sorted,
    knowledge_root,
    load_manifest_dict,
    summarize_knowledge_mount,
    vector_index_root,
)
from shared.company_knowledge.vector_contract import (
    CompanyKnowledgeRetriever,
    RetrievedChunk,
    StubCompanyKnowledgeRetriever,
)

__all__ = [
    "active_company_slug",
    "company_doc_root",
    "company_vector_index_dir",
    "iter_document_files",
    "iter_document_files_sorted",
    "knowledge_root",
    "load_manifest_dict",
    "summarize_knowledge_mount",
    "vector_index_root",
    "CompanyKnowledgeRetriever",
    "RetrievedChunk",
    "StubCompanyKnowledgeRetriever",
]

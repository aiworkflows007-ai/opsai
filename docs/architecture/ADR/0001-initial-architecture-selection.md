# ADR 0001: Initial Architecture and Technology Stack Selection

- **Status:** Accepted
- **Date:** 2026-09-14
- **Deciders:** Product & Engineering Lead

---

## Context

OpsAI is envisioned as an enterprise-grade, multi-tenant AI business operating system. The platform must safely connect unstructured company knowledge, structured business data, and workflow actions while strictly isolating tenants and protecting against prompt injection, privilege escalation, and hallucinated transactional state.

---

## Decision

We have adopted the following core architecture and stack:

1. **Backend Framework:** **Python + FastAPI**
   - *Rationale:* High performance async I/O, native integration with AI/ML ecosystems, robust Pydantic data validation, and automated OpenAPI documentation.
2. **Database & Vector Storage:** **PostgreSQL + pgvector**
   - *Rationale:* Single proven engine providing ACID guarantees, relational joins (tenants, users, roles, documents), and vector indexing (HNSW/IVFFlat). Eliminates multi-database consistency overhead for Phase 1.
3. **Frontend:** **Next.js + TypeScript**
   - *Rationale:* Modern React ecosystem, typed contracts, SSR/streaming support, enterprise UI readiness.
4. **Package Management & Tooling:** **uv + Ruff + Pytest**
   - *Rationale:* Blazing-fast virtual environment management and package resolution via `uv`, instant linting/formatting via `ruff`, standard testing with `pytest`.
5. **Agent Orchestration:** **Core RAG implementation first, transitioning to LangGraph**
   - *Rationale:* PRD Section 14 mandates building the foundational knowledge and retrieval primitives from scratch first to master the concepts, then adopting LangGraph for stateful agent workflows, retries, and human approvals.

---

## Consequences

- **Positive:**
  - Unified database simplifies multi-tenant backups, transactions, and foreign-key integrity between vector embeddings and source documents.
  - Type safety from Pydantic in Python and TypeScript in Next.js minimizes runtime schema errors.
- **Negative / Trade-offs:**
  - Dedicated vector databases (e.g. Qdrant / Milvus) may offer specialized filtering at extreme scale (100M+ vectors); pgvector will be benchmarked as volume scales.

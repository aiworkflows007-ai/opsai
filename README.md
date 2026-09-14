# OpsAI — AI Business Operating System

> **Ask → Understand → Find → Decide → Act**

[![CI](https://github.com/aiworkflows007-ai/opsai/actions/workflows/ci.yml/badge.svg)](https://github.com/aiworkflows007-ai/opsai/actions)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

OpsAI is a multi-tenant AI operating layer for companies. It provides employees and managers with a single interface to query enterprise knowledge, inspect structured business data, and execute approved workflows through controlled, authorized tools.

---

## 🎯 Core Principles

1. **RAG retrieves knowledge** — Never treated as the single source of truth for transactional state.
2. **DB/API provides structured business state** — Transactional queries always resolve to deterministic backends.
3. **Backend enforces authorization** — All RBAC and tenant boundaries are enforced in code, never delegated to LLMs.
4. **Retrieved content is untrusted data** — Strict prompt boundaries protect against direct and indirect injection.
5. **Human approval for high-risk actions** — Irreversible operations require explicit multi-factor or human approval.
6. **Measurable AI quality** — All retrieval, generation, and agent workflows are benchmarked against golden datasets.

---

## 📁 Repository Structure

```text
opsai/
├── docs/
│   ├── product/             # Master PRD and product decisions
│   │   └── MASTER_PRD.md
│   ├── architecture/        # Architecture diagrams & Decision Records (ADRs)
│   │   ├── ARCHITECTURE.md
│   │   └── ADR/
│   ├── learning/            # Concept explanations & engineering notes
│   ├── evaluation/          # Benchmark methodology & golden datasets
│   ├── operations/          # Deployment, runbooks, and configurations
│   └── evidence/            # Resume Evidence Bank (PRD Section 21)
├── src/                     # Application source code (FastAPI backend)
├── tests/                   # Unit and integration test suite
├── evals/                   # Automated RAG and agent evaluation harnesses
├── data/                    # Sample documents and test corpora
├── scripts/                 # Migration, ingestion, and maintenance scripts
├── pyproject.toml           # Python dependencies and tool configs (uv)
├── CHANGELOG.md             # Project changelog
└── README.md                # Project documentation
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+ (or 3.14)
- [`uv`](https://github.com/astral-sh/uv) package manager
- PostgreSQL with `pgvector`
- Redis

### Setup
```bash
# 1. Clone repository
git clone https://github.com/aiworkflows007-ai/opsai.git
cd opsai

# 2. Set up virtual environment and dependencies using uv
uv sync

# 3. Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL, Redis, and LLM provider credentials

# 4. Run tests & linting
uv run pytest
uv run ruff check .
```

---

## 🗺️ 6-Month Roadmap

- [x] **Phase 0:** Project Scaffolding & Governance Spec
- [ ] **Phase 1:** Knowledge Foundation (Chunking, Embeddings, pgvector, Baseline RAG)
- [ ] **Phase 2:** Advanced RAG (BM25, Hybrid RRF, Reranking, Citations)
- [ ] **Phase 3:** Business Data + Tools (Structured outputs, Tool calling, RBAC)
- [ ] **Phase 4:** Agent Workflows (State graphs, LangGraph, Human approval gates)
- [ ] **Phase 5:** Interoperability + Reliability (MCP, Guardrails, OpenTelemetry)
- [ ] **Phase 6:** Production Hardening (Caching, Queues, Resilience, Cloud Deploy)

---

## 📄 Documentation Links

- [Master PRD v1.0](docs/product/MASTER_PRD.md)
- [Architecture & Data Flows](docs/architecture/ARCHITECTURE.md)
- [ADR Index](docs/architecture/ADR/)
- [Resume Evidence Bank](docs/evidence/RESUME_EVIDENCE_BANK.md)
- [Changelog](CHANGELOG.md)

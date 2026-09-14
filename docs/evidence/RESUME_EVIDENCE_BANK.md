# OpsAI — Resume Evidence Bank

> **PRD Section 21 Compliance:** Maintain a separate evidence log during development. Only verified outcomes and reproducible measurements go onto the final engineering resume / portfolio summary.

---

## Verified Architecture Capabilities Implemented

| Milestone | Capability | PRD Phase | Verification Method | Date Verified |
| :--- | :--- | :---: | :--- | :--- |
| **0.1.0** | Project Scaffolding & Governance Spec | Setup | Git repository, directory structure, PRD v1.0 | 2026-09-14 |
| **0.2.0** | Multi-Tenant Data Layer & pgvector Schema (#1) | Phase 1 | 16 Pytest automated tests, Alembic schema migration | 2026-09-14 |

---

## Retrieval & Generation Quality Benchmarks

| Metric | Baseline | Target | Verified Score | Evaluation Dataset | Date |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Recall@5 (Dense)** | TBD | > 85% | | | |
| **Recall@5 (Hybrid RRF)** | TBD | > 92% | | | |
| **Groundedness / Faithfulness** | TBD | > 95% | | | |
| **Citation Accuracy** | TBD | > 98% | | | |

---

## Security & Guardrail Outcomes

| Security Test Category | Test Cases Executed | Blocked Attack Rate | Notes |
| :--- | :--- | :--- | :--- |
| **Direct Prompt Injection** | 0 | - | |
| **Indirect Prompt Injection** | 0 | - | |
| **Cross-Tenant Isolation** | 0 | - | |
| **Tool Privilege Escalation** | 0 | - | |

---

## Production Reliability & Latency

- **P50 Latency:** TBD
- **P95 Latency:** TBD
- **P99 Latency:** TBD
- **Error Rate:** TBD
- **Cost per 1k queries:** TBD

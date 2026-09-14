# Changelog

All notable changes to the OpsAI Business Operating System will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Multi-Tenant Data Layer (#1)**:
  - Base declarative models and mixins (`UUIDPrimaryKeyMixin`, `TimestampMixin`, `TenantScopedMixin`) enforcing multi-tenant isolation.
  - SQLAlchemy models for `Tenant`, `User` (with `employee`, `manager`, `admin` roles), `KnowledgeSource`, `Document`, `DocumentChunk` with `pgvector` (`Vector(1536)`), `Conversation`, `Message` (with citation metadata), and `AuditEvent`.
  - Pydantic v2 schemas across all domain entities with validation rules (slug formatting, email validation).
  - Initial Alembic migration script (`fe9965af8a7d_create_initial_multi_tenant_schema.py`) with PostgreSQL and `pgvector` extension setup.
  - Test suites in `tests/test_models.py` and `tests/test_schemas.py` verifying multi-tenant isolation, cascading deletions, and schema validation.

---

## [0.1.0] - 2026-09-14

### Added
- Initialized OpsAI project repository.
- Published `docs/product/MASTER_PRD.md` based on Master PRD v1.0.
- Established system architecture documentation and diagrams in `docs/architecture/ARCHITECTURE.md`.
- Created ADR 0001: Initial Architecture and Technology Stack Selection.
- Created learning, evaluation, and operational runbook foundations.
- Initialized Section 21 Resume Evidence Bank in `docs/evidence/RESUME_EVIDENCE_BANK.md`.
- Configured Python environment with `uv`, FastAPI, Pydantic, Ruff, and Pytest.

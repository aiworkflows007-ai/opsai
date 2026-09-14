# Operations & Runbooks

Operational runbooks, deployment guides, environment variable configurations, and incident response procedures for OpsAI.

---

## Environments

- **Local Development:**
  - Python 3.14 + `uv`
  - PostgreSQL 16+ with `pgvector`
  - Redis 7+
- **CI / Automated Testing:**
  - GitHub Actions running linting (`ruff`), unit tests (`pytest`), and smoke evaluation tests.
- **Production / Staging:**
  - Dockerized container services with reverse proxy (Caddy / Nginx).

---

## Configuration & Environment Variables

Refer to `.env.example` at the repository root for all required environment variables:
- Database connection strings (`DATABASE_URL`)
- Vector dimensions and embedding provider keys
- JWT secrets and auth configurations
- LLM API keys and model parameters

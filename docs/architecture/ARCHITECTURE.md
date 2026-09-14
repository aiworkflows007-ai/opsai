# OpsAI Architecture Overview

OpsAI is an AI business operating system built on a multi-tenant foundation. It connects company knowledge, structured business data, company policies, and authorized business tools while enforcing strict security and tenant boundaries outside of the LLM context.

---

## 1. System Architecture Diagram

```mermaid
flowchart TD
    subgraph Client ["Client Layer"]
        FE["Next.js Web UI / Client"]
    end

    subgraph Gateway ["API & Auth Gateway"]
        API["FastAPI Application"]
        AUTH["Auth & Tenant Context Provider (JWT / RBAC)"]
    end

    subgraph Core ["OpsAI Orchestrator"]
        ROUTER["Request Classifier & Intent Router"]
        ORCH["Workflow & Execution Engine"]
    end

    subgraph Subsystems ["Specialized Execution Paths"]
        direction TB
        RAG["RAG Engine<br/>(Dense + Sparse + RRF + Reranker)"]
        DATA["Business Data Service<br/>(Transactional DB / Read APIs)"]
        AGENT["LangGraph Agent Workflows<br/>(Multi-step, State persistence)"]
    end

    subgraph Models ["Foundation Models & Embeddings"]
        LLM["LLM (Reasoning, Extraction, Synthesis)"]
        EMB["Embedding Model (Vector generation)"]
    end

    subgraph Storage ["Persistence & State Layer"]
        PG[("PostgreSQL + pgvector<br/>(Tenants, Users, Docs, Vectors)")]
        REDIS[("Redis<br/>(Cache, Sessions, Rate Limits)")]
    end

    subgraph SecurityAudit ["Governance & Observability"]
        POLICY["Backend Policy & Approval Gate"]
        AUDIT["Audit Logger"]
        OTEL["OpenTelemetry Telemetry (Traces/Metrics)"]
    end

    FE -->|HTTP/REST / SSE Stream| API
    API --> AUTH
    AUTH --> ROUTER
    ROUTER -->|Knowledge Query| RAG
    ROUTER -->|Structured Data Query| DATA
    ROUTER -->|Action / Multi-step Workflow| AGENT

    RAG --> EMB
    RAG --> PG
    DATA --> PG
    AGENT --> LLM

    RAG --> LLM
    AGENT --> POLICY
    POLICY -->|High-risk Action| FE
    POLICY -->|Approved Execution| PG
    
    API -.-> AUDIT
    API -.-> OTEL
    AGENT -.-> REDIS
```

---

## 2. Request Lifecycle & Routing

```mermaid
sequenceDiagram
    autonumber
    actor User as Employee / Manager
    participant UI as Frontend (Next.js)
    participant API as FastAPI / Auth
    participant Router as OpsAI Orchestrator
    participant RAG as RAG Service
    participant DB as Postgres (pgvector)
    participant LLM as Language Model

    User->>UI: Submit query ("What is our travel reimbursement policy?")
    UI->>API: POST /api/v1/chat (with Tenant & Auth Token)
    API->>API: Authenticate & extract tenant_id + user_role
    API->>Router: Route validated request
    Router->>RAG: Knowledge retrieval path
    RAG->>DB: Dense + Sparse search (strictly scoped to tenant_id)
    DB-->>RAG: Matched document chunks + scores
    RAG->>RAG: Hybrid RRF Fusion + Reranking + Context compression
    RAG->>LLM: Grounded prompt (Context treated as untrusted data)
    LLM-->>RAG: Grounded response + citations
    RAG-->>API: Stream tokens + citations metadata
    API-->>UI: Server-Sent Events (SSE) stream
    UI-->>User: Rendered response with verified citations
```

---

## 3. Core Principles

1. **RAG Retrieves Knowledge:** RAG is never used as the single source of truth for transactional business state (e.g. ticket count, order status, inventory).
2. **DB / API Provides Structured State:** Transactional information comes from deterministic database queries or internal APIs.
3. **Backend Enforces Authorization:** All permission checks (RBAC, object-level tenancy) are handled in Python backend code, not delegated to LLM decision-making.
4. **Untrusted Content:** Ingested documents and retrieved passages are treated as untrusted input. Directives inside documents must never grant administrative privileges.
5. **Human-in-the-Loop:** Irreversible or high-risk tool operations trigger explicit approval requests before execution.

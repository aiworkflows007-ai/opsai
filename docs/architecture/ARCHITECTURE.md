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

---

## 4. Authentication, Tenant Context & Authorization Architecture

OpsAI enforces a strict three-tier security model on every incoming request:

```mermaid
flowchart TD
    REQ["Incoming HTTP Request<br/>(Authorization: Bearer &lt;JWT&gt;)"] --> D1["1. Token Extraction & Validation<br/>(Signature, Expiration, Claims: sub, tenant_id, role)"]
    D1 -->|Invalid / Expired| ERR1["HTTP 401 Unauthorized<br/>(WWW-Authenticate: Bearer)"]
    D1 -->|Valid Payload| D2["2. Server-Side Identity & Tenant Resolution<br/>(Query DB for active User & active Tenant)"]
    D2 -->|User / Tenant Inactive| ERR2["HTTP 401 Unauthorized"]
    D2 -->|Active User + Tenant| D3["3. TenantContext Injection<br/>(Frozen TenantContext: tenant, user, role)"]
    D3 --> D4{"4. Role-based Authorization<br/>(require_roles guard)"}
    D4 -->|Insufficient Role| ERR3["HTTP 403 Forbidden"]
    D4 -->|Authorized| D5["5. Tenant-Scoped Execution<br/>(Queries strictly filtered by context.tenant_id)"]
    D5 --> D6{"6. Object-Level Access Check<br/>(verify_tenant_access)"}
    D6 -->|Cross-Tenant Resource| ERR4["HTTP 404 Not Found<br/>(Prevents enumeration attacks)"]
    D6 -->|Owned Resource| SUCCESS["Successful Execution & Response"]
```

### Key Security Guarantees

1. **Server-Side Authority for Tenant Identity:**
   The application never trusts `tenant_id` supplied in client headers, query parameters, or request payloads. The tenant identity is strictly established from the authenticated user record in PostgreSQL via `get_current_tenant` and `get_tenant_context`.
2. **Anti-Enumeration via 404:**
   When an authenticated user requests a resource ID belonging to another tenant, the server returns `404 Not Found` (rather than `403 Forbidden`) to avoid leaking the existence of sensitive entities across tenant boundaries.
3. **Decoupled Roles & Extensibility:**
   Roles (`employee`, `manager`, `admin`) govern capability access through FastAPI dependency guards (`require_roles`), preserving a clean boundary between *Authentication* (identity verification) and *Authorization* (action permissioning).

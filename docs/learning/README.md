# Learning & Engineering Notes

This directory stores engineering notes, concept explanations, and implementation walkthroughs throughout the six-month AI-native development journey of OpsAI.

## Roadmap & Topics

- **Phase 1: Knowledge Foundation**
  - Context engineering & window limits
  - Ingestion pipelines & document parsing
  - Chunking strategies (fixed size, recursive, semantic)
  - Embedding models & vector mathematics
  - Vector indexing (HNSW vs IVFFlat in pgvector)
- **Phase 2: Advanced RAG**
  - BM25 sparse retrieval
  - Reciprocal Rank Fusion (RRF)
  - Cross-encoder reranking
  - Query expansion & hyde
  - Citation attribution mechanics
- **Phase 3: Business Data & Tool Calling**
  - Structured outputs & Pydantic validation
  - Function calling protocol
  - Backend authorization boundaries
- **Phase 4: Agent Workflows**
  - State graphs with LangGraph
  - Human-in-the-loop approval gates
  - Memory architectures
- **Phase 5: Interoperability & Reliability**
  - Model Context Protocol (MCP)
  - Guardrails & prompt injection mitigation
  - OpenTelemetry tracing
- **Phase 6: Production Hardening**
  - Redis caching & rate limiting
  - Distributed queueing
  - Cloud / Docker deployment

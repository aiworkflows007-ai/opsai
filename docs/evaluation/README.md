# Evaluation & Benchmarking Methodology

OpsAI quality and performance are measured as a system, not by model output alone. Every architectural change (retriever adjustments, prompt modifications, model routing) is measured against established golden datasets.

---

## Metric Suite

| Area | Primary Metrics | Description |
| :--- | :--- | :--- |
| **Retrieval** | Recall@K, Precision@K, MRR, nDCG | Measures whether the ground-truth chunks appear in the top-K retrieved context. |
| **Generation** | Correctness, Groundedness / Faithfulness, Citation Recall | Measures whether claims in generated answers are directly supported by retrieved chunks. |
| **Tool Calling** | Selection Accuracy, Parameter Validity, Execution Success | Verifies that the correct tools are invoked with valid arguments according to RBAC. |
| **Security** | Injection Block Rate, Privilege Escalation Resistance | Measures system defenses against direct and indirect prompt injections. |
| **Performance** | Latency (P50, P95, P99), Cost per query, Token efficiency | Ensures system changes remain cost-effective and low latency. |

---

## Directory Structure
- `datasets/`: Golden evaluation query sets (`golden_retrieval_v1.json`, `golden_e2e_v1.json`).
- `benchmarks/`: Automated harness scripts and runners.
- `reports/`: Versioned evaluation run summaries and regression comparisons.

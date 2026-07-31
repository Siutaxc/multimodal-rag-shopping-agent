# Stage 6 bounded-agent and evidence evaluation

- Dataset: `shoplens-stage6-bounded-agent` / `stage6-agent-v1`
- Corpus: 24 synthetic CC0 fixtures
- Cases: 15
- Generated: `2026-07-22T06:26:00.467183+00:00`

| Metric | Value |
|---|---:|
| Task completion | 1.0000 |
| Tool selection accuracy | 1.0000 |
| Citation precision | 1.0000 |
| Citation coverage | 1.0000 |
| Structured fact claims | 384 |
| Structured fact hallucination rate | 0.0000 |
| Condition mutation accuracy | 1.0000 |
| Average tool calls | 2.200 |
| Maximum tool calls | 3 |
| Invalid loop rate | 0.0000 |
| Full answer P50 ms | 26.303 |
| Full answer P95 ms | 138.085 |

## Per-case results

| ID | Conversation | Status | Task | Conditions | Tools | Facts | Hallucinations | Degraded |
|---|---|---|---:|---:|---:|---:|---:|---|
| agent-01 | conversation-a | completed | 1 | 1 | 1 | 24 | 0 | - |
| agent-02 | conversation-a | completed | 1 | 1 | 1 | 24 | 0 | - |
| agent-03 | conversation-a | completed | 1 | 1 | 1 | 24 | 0 | - |
| agent-04 | conversation-a | completed | 1 | 1 | 1 | 36 | 0 | - |
| agent-05 | conversation-a | needs_clarification | 1 | 1 | 1 | 0 | 0 | - |
| agent-06 | conversation-b | completed | 1 | 1 | 1 | 24 | 0 | - |
| agent-07 | conversation-b | completed | 1 | 1 | 1 | 24 | 0 | - |
| agent-08 | conversation-b | completed | 1 | 1 | 1 | 36 | 0 | - |
| agent-09 | conversation-b | needs_clarification | 1 | 1 | 1 | 0 | 0 | - |
| agent-10 | conversation-c | completed | 1 | 1 | 1 | 36 | 0 | - |
| agent-11 | conversation-c | completed | 1 | 1 | 1 | 36 | 0 | - |
| agent-12 | conversation-d | completed | 1 | 1 | 1 | 48 | 0 | - |
| agent-13 | conversation-e | completed | 1 | 1 | 1 | 36 | 0 | - |
| agent-14 | conversation-e | completed | 1 | 1 | 1 | 36 | 0 | - |
| agent-15 | conversation-e | needs_clarification | 1 | 1 | 1 | 0 | 0 | - |

## Limitations

- The corpus contains only 24 synthetic CC0 fixture products.
- The deterministic agent provider proves schemas and control flow, not LLM quality.
- Product prompt injection and model timeouts are covered by adversarial unit tests.

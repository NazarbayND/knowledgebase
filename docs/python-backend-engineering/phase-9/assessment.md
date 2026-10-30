# Phase 9 — Architectural judgment assessment

Review week 15 using all earlier correctness, security and operations concepts.
Prepare written notification, rate-limiter and event-ingestion designs. Practical
implementations and the capstone architecture project remain deferred.

## Tasks and scoring

| Dimension | Evidence | Points |
| --- | --- | ---: |
| Concepts | Explain contexts, invariants, scaling, consistency, durability and recovery | 25 |
| Correctness | Give coherent requirements, APIs, data models and acceptance boundaries for three designs | 30 |
| Debugging | Analyze hot partitions, duplicate effects, overload and region failure | 20 |
| Tradeoffs | Justify modularity, storage/broker choice, scale triggers and cost | 15 |
| Communication | Present estimates/diagrams and an ADR with assumptions/revisit triggers | 10 |

## Model review

Start with scale and user-visible semantics. Keep orders/stock inside an explicit
consistency boundary, define accepted durability and tolerate messaging redelivery.
Use partitioning/hashing only after explaining ownership and hot keys. Record
identity/tenant checks, bounded resources and recovery for every major path.

Compare the chosen architecture with a simpler alternative. Explain why any
microservice, multi-region writer or event-sourcing mechanism is worth its cost.
Capacity numbers must have units, peak factors and overhead; they are planning
assumptions until measured.

Target 80/100. A diagram without failure behavior or a scale claim without arithmetic
needs revision. Record designs, ADR, score and weak areas in [progress](../progress.md).
Use the other [five design studies](module-18/design-studies.md) for transfer practice.

[Overview](index.md) · [Project placeholder](project.md) · [Next phase](../phase-10/index.md)

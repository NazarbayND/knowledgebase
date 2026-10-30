# Phase 10 — Final cumulative assessment

**Week 16 checkpoint:** use the [full simulation](module-20/practice.md) and the
[competency review](competency-review.md). Practical projects are intentionally
deferred; no passing score can be claimed without an independent assessment.

## Assessment package

1. A timed Python algorithm/problem with edge cases and complexity.
2. A SQL correctness/indexing discussion with required evidence, not invented plans.
3. A concurrency/backend debugging reproduction or precise interleaving.
4. An API/transaction/security boundary review.
5. A system design including requirements, estimates, data, failure/recovery and cost.
6. Two truthful STAR stories and a review of uncertain/deferred capability.

## Scoring

| Dimension | Evidence | Points |
| --- | --- | ---: |
| Concepts | Explain mechanisms across language, networking, persistence and production | 25 |
| Correctness | Supply coherent bounded solutions/contracts preserving key invariants | 30 |
| Debugging | Reproduce/diagnose failures and propose checks that distinguish hypotheses | 20 |
| Tradeoffs | Compare alternatives with workload, cost, team and recovery assumptions | 15 |
| Communication | Explain clearly, respond to changed requirements and separate facts from claims | 10 |

Target 80/100. Revise cross-tenant access, unsafe concurrent stock, swallowed
cancellation and unbounded duplicate effects regardless of the numerical score.

## Final report

Record scores, timeboxes, hints, evidence and weak areas. Distinguish written/design
competency, the existing Phase 1–2 example behavior and the deferred Phase 3–10
practical implementation. Use the original eighteen competencies to choose the
next concrete revision or project action rather than marking everything complete.

A useful final decision is specific: “I can explain the transaction and retry model;
I still need a PostgreSQL concurrent integration result.” This is more informative
than a single unqualified readiness percentage.

[Overview](index.md) · [Competency checklist](competency-review.md) ·
[Project placeholder](project.md) · [Progress](../progress.md)

# Phase 8 — Delivery and infrastructure assessment

Review weeks 13–14 with earlier API, persistence, queue and reliability decisions.
Submit delivery/network diagrams and a runbook; implementation is deferred.

## Scenario

An image works locally but uses localhost for its database in deployment. Every
new pod attempts the same migration. HPA adds replicas during pool exhaustion;
rollout 503s rise and rollback cannot run against the newly removed column.

## Tasks and scoring

| Dimension | Evidence | Points |
| --- | --- | ---: |
| Concepts | Explain images/namespaces, controller roles, IAM and state ownership | 25 |
| Correctness | Specify reproducible build/promotion, networking, lifecycle and migration compatibility | 30 |
| Debugging | Distinguish connectivity, readiness, pool saturation and schema incompatibility | 20 |
| Tradeoffs | Compare compute platforms, scaling signals, release strategy and total cost | 15 |
| Communication | Produce an actionable rollout/rollback and restore runbook | 10 |

## Model review

Resolve connectivity using correct namespace/DNS/routes/permissions/TLS rather
than widening everything. Coordinate migrations and use expand/contract while
old/new binaries coexist. Compute scaling must remain inside dependency budgets.
Readiness/drain and surge capacity affect 503s. Rollback requires schema/message
compatibility and cannot reverse every external business effect.

Include Terraform state protection/locking and an AWS alternative justified by
team capability and cost. A Kubernetes requirement must be earned, not assumed.

Target 80/100. Deployment/restore capability remains pending until artifacts are
actually built, deployed and recovered. Record written results in
[progress](../progress.md) separately from [deferred practical work](project.md).

[Overview](index.md) · [Next phase](../phase-9/index.md)

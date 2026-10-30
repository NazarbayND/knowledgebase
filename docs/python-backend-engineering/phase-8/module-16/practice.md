# Module 16 — Practice and assessment

## Exercises

1. Draw Deployment/ReplicaSet/Pod/Service/Ingress ownership and traffic. Diagnose
   a selector/targetPort mismatch separately from an application crash.
2. Specify ConfigMap/Secret/service-account roles and rotation adoption without
   confusing base64 encoding with encryption.
3. Choose measured requests/limits and HPA signals for API and queue workers.
   Calculate how maximum replicas affect database pool demand.
4. Design startup/readiness/liveness and a graceful termination timeline with
   routing propagation, slow requests and cancelled jobs.
5. Compare rolling, canary and blue-green release. Include surge capacity,
   representative traffic, abort criteria and schema/message compatibility.
6. Explain GitOps reconciliation during an emergency fix and migration ordering.
7. Write a 503 rollout runbook distinguishing pending, crashing, not-ready and
   ready-but-unreachable pods, followed by recovery and cost considerations.

??? note "Model reasoning"
    Controllers reconcile desired state, but traffic depends on actual selectors,
    ports and ready endpoints. Config updates require process adoption. HPA can
    amplify dependency pressure. Drain timing must overlap routing propagation
    under a bounded grace period. Rollback needs compatible schema/messages and
    cannot undo arbitrary effects. A GitOps source of truth and incident changes
    require coordinated ownership.

## Interview questions

- Why can an HPA fail to help a low-CPU overloaded service?
- What causes 503s while a Deployment reports a rollout in progress?
- Does rolling back an image roll back its database migration?
- How do startup, readiness and liveness serve different decisions?
- Why is a running database pod not a recovery plan?

??? note "Answer guide"
    Bottlenecks may be queues, pools or vendors; the signal can miss them. Bad
    endpoints, premature readiness, drain gaps, capacity or incompatibility cause
    rollout failures. Image rollback does not reverse schema/effects. Probes govern
    initialization, routing and restart. Durable recovery needs replication,
    backups, restoration and promotion procedures beyond process scheduling.

## Self-check before the assessment

Five pods may each run two processes with a pool of ten. The database budget is 80, of which 20 must remain for other work. What is potential demand and a simple per-process cap?

??? note "Model answer and a five-point check"
    Potential demand is 5 × 2 × 10 = 100. The simplified API allowance is 60, so ten processes imply at most six per process before extra overflow/other consumers. This arithmetic is a capacity ceiling assumption, not evidence six is optimal. Autoscaling and rollout surge must preserve the aggregate budget.

    Award up to two points for the correct outcome, two for the mechanism, and
    one for a relevant limit or counterexample. Record hints honestly. This is
    a retrieval drill, not a replacement for the full module assessment.

Use the [assessment guide](../../assessment-guide.md) for the shared scoring
anchors and evidence rules.

## Mastery assessment

Use 25 for Kubernetes mechanisms, 30 for coherent rollout/lifecycle contracts,
20 for 503/resource diagnosis, 15 for scaling/GitOps/cost choices and 10 for
communication. Target 80/100. No cluster, manifests or deployment results are
claimed while the practical project remains deferred.

[Module 16](index.md) · [Phase assessment](../assessment.md)

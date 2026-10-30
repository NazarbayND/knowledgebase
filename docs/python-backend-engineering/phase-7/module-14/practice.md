# Module 14 — Practice and assessment

## Exercises

1. Specify safe structured fields and trace propagation across API → outbox →
   worker. Distinguish request correlation, parent-child timing and causal links.
2. Design request/dependency/pool/queue metrics with bounded labels. Explain why
   raw order id and request URL are poor Prometheus labels.
3. Define event-based success and latency SLIs, an SLO window and a budget for
   one million requests. Include caller-error and partial-failure policy.
4. Diagnose low-CPU high-p99 latency using three competing hypotheses. Name a
   measurement that would disprove each rather than selecting a favorite immediately.
5. Design liveness/readiness/startup behavior during a database outage and deploy.
6. Plan expected-load, stress and soak experiments, including offered vs completed
   load, slow clients, cache state and correctness checks.
7. Write a postmortem for a leaked-session export with mitigation, contributing
   conditions, owners and a regression scenario.

??? note "Model reasoning"
    IDs can belong in controlled logs/traces, while metric dimensions must remain
    bounded. Global quantiles require valid distribution aggregation. User SLIs
    count eligible successful outcomes under explicit semantics. Pool waits, locks
    and downstream delays can explain low-CPU tails. Probe actions differ, and
    dependency-driven restart storms worsen incidents. A recovery report needs
    evidence, not a chart that happened to improve after several simultaneous changes.

## Interview questions

- Why can averaging p99 per pod misrepresent global p99?
- What is a useful alert versus a noisy symptom alert?
- Why might liveness depending on Redis worsen a Redis outage?
- How can a closed-loop load test hide overload?
- What distinguishes a memory leak from allocator-retained RSS?

??? note "Answer guide"
    Quantiles are not linearly composable. Actionable alerts tie to user impact or
    budget burn. Restarting healthy applications adds churn without repairing Redis.
    Slowing clients can lower demand as latency grows. Retained live references,
    traced allocations and process memory must be compared separately.

## Self-check before the assessment

An SLO permits a bad-event fraction of 0.001. A compatible short window contains 100 bad events out of 10,000 eligible requests. What is burn rate and what does it not tell you by itself?

??? note "Model answer and a five-point check"
    Observed fraction is 0.01, so burn rate is 10. It is a ratio, not failures per minute. Exact time to exhaustion additionally depends on the remaining long-window budget, request rate/distribution and whether this behavior persists. Do not count fast errors as good latency outcomes or change the eligible definition between windows.

    Award up to two points for the correct outcome, two for the mechanism, and
    one for a relevant limit or counterexample. Record hints honestly. This is
    a retrieval drill, not a replacement for the full module assessment.

Use the [assessment guide](../../assessment-guide.md) for the shared scoring
anchors and evidence rules.

## Mastery assessment

Use 25 for observability/SLO mechanisms, 30 for coherent instrumentation/probe
contracts, 20 for evidence-driven incident diagnosis, 15 for sampling/load/recovery
tradeoffs and 10 for explanation. Target 80/100. Dashboards, injected incidents and
load-test numbers are planned work, not results claimed by this text.

[Module 14](index.md) · [Cumulative review](../assessment.md)

# Phase 7 — Security and incident assessment

**Week 12 cumulative checkpoint:** combine API, transactions, caching, messaging,
security and reliability. Implementation and incident injection are deferred.

## Scenario

A valid JWT reads another tenant's orders. An export holds connections during
slow downloads. p99 climbs with low CPU, readiness removes all pods, and liveness
restarts them because Redis is down. Logs contain raw bearer tokens.

## Tasks and scoring

| Dimension | Evidence | Points |
| --- | --- | ---: |
| Concepts | Explain identity vs object permission, resource lifetimes and user SLIs | 25 |
| Correctness | Specify verifier/tenant/field checks, negative cases and safe telemetry | 30 |
| Debugging | Compare pool/lock/dependency evidence and explain probe restart amplification | 20 |
| Tradeoffs | Choose outage policy, sampling, cardinality and token/key rotation behavior | 15 |
| Communication | Produce an incident timeline, mitigation and preventive follow-up | 10 |

## Model review

Fix object authorization independently of token cryptography; review list/export
and write paths too. Redact credentials and investigate exposure under an owned
response process. Track pool waits/transaction age and stream resource ownership.
Separate probe actions so a recoverable dependency problem does not restart every
healthy process. Define success/latency SLIs and report evidence without inventing
a measured improvement.

Include outbox/consumer consequences if retries occur during the incident. Safe
recovery must preserve tenant and duplicate-effect invariants, not merely return
the dashboard to green.

Target 80/100. Cross-tenant access, accepting arbitrary signed audiences and logging
secrets require revision regardless of score. Record written evidence separately
from pending integration/load-test evidence in [progress](../progress.md).

[Overview](index.md) · [Project placeholder](project.md)

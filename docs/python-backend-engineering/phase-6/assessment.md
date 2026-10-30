# Phase 6 — Distributed-workflow assessment

Review weeks 9–10 with earlier transaction, API and concurrency concepts. Submit
written state machines and failure matrices; practical services are deferred.

## Scenario

A cache outage floods PostgreSQL. Some committed orders produce no event, and
others send duplicate emails. Workers retry invalid messages forever. A lock lease
expires during a pause and two holders write conflicting state.

## Tasks and scoring

| Dimension | Evidence | Points |
| --- | --- | ---: |
| Concepts | Explain cache freshness, leases, acknowledgements and partial failures | 25 |
| Correctness | Specify bounded fallback, outbox intent, consumer dedup and external-effect reconciliation | 30 |
| Debugging | Trace stale fill, publish/commit gaps, replay and expired-holder effects | 20 |
| Tradeoffs | Choose broker, retry/DLQ, fencing and partition policies | 15 |
| Communication | Show a state/sequence diagram with assumptions and remaining limits | 10 |

## Model review

Bound/coalesce cache misses and preserve source-of-truth writes. Commit order and
outbox together; assume relay/consumer redelivery. Atomically deduplicate local
effects and handle remote side effects through a supported idempotency or repair
contract. Use bounded classified retries and an owned DLQ. Lease release tokens
do not prevent stale effects unless the protected resource enforces fencing or
another matching concurrency protocol.

Target 80/100. Revise any “exactly once everywhere” claim that omits an external
effect boundary, or any cache design making authoritative stock depend on freshness.
Record the written assessment separately from unrun recovery tests in
[progress](../progress.md).

[Overview](index.md) · [Project placeholder](project.md)

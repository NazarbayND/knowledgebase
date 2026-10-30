# Module 18 — Design practice and assessment

## Eight exercises

Attempt each before reading its [worked study](design-studies.md):

1. **URL shortener:** design creation/redirects, expiry, malicious links and viral keys.
2. **Notifications:** design preferences, provider quotas, retries and unknown send outcomes.
3. **Rate limiter:** choose exact vs approximate tenant limits under hot keys/outages.
4. **Event ingestion:** define durable acceptance, partitions, poison data and replay.
5. **Order processing:** preserve stock and retry/payment behavior under contention.
6. **Real-time messaging:** define delivery semantics, offline resume and slow clients.
7. **Document search/RAG:** preserve tenant/ACL/deletion lineage through derived indexes.
8. **Multi-tenant SaaS:** choose isolation, noisy-neighbor limits and recovery boundaries.

## Required answer structure

For every exercise provide:

- Functional/nonfunctional requirements and explicit exclusions.
- Capacity assumptions: average/peak throughput, payload, retention and skew.
- API and data model with identities, invariants and security context.
- Architecture with ownership, durability point and consistency per operation.
- First bottleneck and an incremental scaling step justified by a metric.
- Failure recovery, timeouts/retry owner, duplicate handling and RPO/RTO.
- Tradeoffs across latency, correctness, cost and operating complexity.

These are written exercises; implementing eight applications is not required now.
For week 15, choose notifications, rate limiting and ingestion for three deeper
design reviews, matching the original roadmap. Use the other studies for revision.

??? note "Model review principles"
    Start simple and compute units explicitly. A cache is not a source-of-truth
    reservation system; a queue is not an exactly-once remote-effect guarantee.
    Partition order is not global order, consistent hashing does not split a hot
    key, and a second region is not a tested failover protocol. For each arrow
    identify identity, timeout, retry, resource and recovery ownership. Acknowledge
    uncertainty and state which observation would change the design.

## Interview questions

- When should this design shard, and why that key?
- What is acknowledged before the caller receives success?
- Which reads can be stale, and how would users notice?
- What happens when one region remains writable after failover?
- How does your proposed improvement affect cost and the support team?

## Mastery assessment

Use 25 for mechanisms/requirements, 30 for coherent APIs/data/invariants, 20 for
failure and bottleneck analysis, 15 for justified tradeoffs and 10 for communication.
Target 80/100. Evaluate estimates as assumptions, not fabricated benchmarks. Record
design evidence separately from deferred implementation in [progress](../../progress.md).

[Module 18](index.md) · [Design studies](design-studies.md) · [Phase review](../assessment.md)

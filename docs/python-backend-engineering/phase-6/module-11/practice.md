# Module 11 — Practice and assessment

## Exercises

1. Design tenant-aware catalogue cache keys and define acceptable staleness,
   representation versioning, TTL/eviction and negative-cache behavior.
2. Draw the stale-fill race around a commit and invalidation. Compare bounded
   staleness with a version-aware fill protocol.
3. Plan a cold-cache recovery with single-flight, global refill bounds and source
   admission. Explain why adding TTL jitter alone is insufficient during restart.
4. Compare fixed/sliding windows and token buckets. Make count/expiry updates
   atomic and define outage behavior for a tenant rate limiter.
5. Choose Pub/Sub or Streams for presence updates vs recoverable background work.
   Explain what happens while a consumer is disconnected.
6. Draw an expired lease holder resuming after a replacement holder writes.
   Distinguish release-owner tokens from resource-enforced fencing.

??? note "Model reasoning"
    Cache keys include every dimension affecting representation/permission.
    Deleting after commit does not stop an older in-flight reader from refilling.
    A cache restart needs bounded misses; TTL jitter addresses a different expiry
    pattern. Combined limiter operations must preserve expiry under crashes.
    Pub/Sub has no recovery history; Streams need retention/ack/reclaim policies.
    A stale owner is stopped only if the protected resource enforces ownership
    versioning, not merely because release compares a random token.

## Interview questions

- Can TTL guarantee current inventory?
- How can the cache fail while the hit ratio remains excellent?
- Why does a distributed lock need more than expiry and unlock?
- How can a fail-open cache fallback create a larger outage?
- What does a rate limiter protect that a connection pool does not?

??? note "Answer guide"
    TTL bounds some residence, not transactional truth. Hit ratios hide skew and
    correctness. Expiry permits old/new holders to overlap unless effects are
    fenced. Unbounded fallback floods the source. Rate limiting bounds admission
    over time while pools bound connection concurrency.

## Mastery assessment

Use 25 for Redis/consistency mechanisms, 30 for cache/limiter contracts, 20 for
stampede/stale-holder diagnosis, 15 for outage tradeoffs and 10 for explanation.
Target 80/100. Runtime hit/miss metrics and outage tests remain deferred project
evidence, not observed results in these notes.

[Module 11](index.md) · [Next: Module 12](../module-12/index.md)

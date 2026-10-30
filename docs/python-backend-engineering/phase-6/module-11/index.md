# Module 11 — Caching and coordination

**P0/P1 · prerequisite: persistence consistency and failure boundaries**

A cache stores a derived answer to reduce latency or source load. Its design
must define freshness, keys, eviction and failure behavior. Redis can also provide
atomic coordination primitives, but using one server does not turn a multi-system
business operation into a transaction.

## Chapter navigation

1. [Redis execution and data structures](#redis-execution-and-data-structures)
2. [Cache placement strategies](#cache-placement-strategies)
3. [Freshness and invalidation](#freshness-and-invalidation)
4. [Stampedes, hot keys and penetration](#stampedes-hot-keys-and-penetration)
5. [Rate limits and atomic updates](#rate-limits-and-atomic-updates)
6. [PubSub and Streams](#pubsub-and-streams)
7. [Locks, leases and fencing](#locks-leases-and-fencing)
8. [Outage behavior](#outage-behavior)

## Redis execution and data structures

Redis serves in-memory structures with persistence/replication options. Commands
have defined atomic execution behavior, while slow or large commands can still
hurt other clients. Modern versions can use threads for some work; do not reduce
the architecture to “every byte is handled by one thread.” Know the commands and
deployment mode you rely on.

Strings fit scalar values/counters, hashes fit field collections, sets fit unique
membership, sorted sets fit score-ordered data, lists fit simple sequences and
Streams fit retained message entries with consumer-group mechanics. Choose based
on operations and bounded cardinality. Unbounded keys or values can make eviction,
replication and failover painful even if average command latency looks low.

Namespace keys by environment, tenant, resource and representation version where
required. `catalog:{tenant}:v2:{product}` communicates more than an ambiguous product
id alone. Never let unrelated tenants share an authorization-sensitive cache key.

## Cache placement strategies

| Strategy | Flow | Tradeoff |
| --- | --- | --- |
| Cache-aside | Read cache; on miss read source and populate | Simple ownership, but stale fills and stampedes need policy |
| Write-through | Write through a component updating cache/source | Centralized path; failure ordering still matters |
| Write-behind | Buffer writes before source persistence | Lower apparent latency with durability/replay/ordering complexity |

PostgreSQL remains FulfillHub's source of truth for orders/stock. A cached stock
display can be stale; final reservation must use the authoritative transaction.
Write-behind is a poor default for business data whose loss is unacceptable.

## Freshness and invalidation

Define acceptable staleness, not simply “cache for five minutes.” TTL limits some
stale residence but does not prove immediate consistency. Invalidate after a
committed write or use a versioned representation/change feed under an explicit
ordering policy. Add TTL jitter to avoid synchronized expiry where suitable.

There is a subtle race: reader A reads old DB state; writer B commits and invalidates;
A then populates the cache with old data. Delete-after-write alone does not prevent
this. Version checks, coordinated fill/update protocols or accepting bounded
staleness can be appropriate; choose against the actual consistency requirement.

Negative caching can store “absent” briefly to protect the source, but tenant/auth
context and creation behavior affect the key and TTL. Cache eviction is a capacity
policy, not an invalidation guarantee.

## Stampedes, hot keys and penetration

A stampede occurs when many misses refill together. Use single-flight/coalesced
fills, bounded refill concurrency, jitter or stale-while-revalidate where stale
data is acceptable. Protect the database during cold start and mass invalidation.

A hot key concentrates traffic on one shard/node. Client-local caches or replicated
read patterns can help under explicit freshness limits; adding unrelated shards
does not distribute one key's load automatically. Cache penetration sends requests
for non-existent/un-cacheable values to the source repeatedly; validate input and
consider bounded negative caching or probabilistic filters with understood errors.

## Rate limits and atomic updates

Fixed windows are simple but burst near boundaries. Sliding windows smooth timing
at greater state/compute cost; token buckets allow a configured burst and sustained
refill rate. State whether the policy limits callers, tenants, IPs or operations,
and whether a cache outage should reject or degrade.

INCR is atomic, but INCR followed by EXPIRE as separate operations can leave a
counter without expiry if the client crashes between them. Use a suitable atomic
script/transactional protocol for the combined rule. Redis scripts should be short
and bounded; Redis Cluster multi-key operations require attention to key slots.

```text
atomic decision:
    identify current window/bucket
    update state
    set/retain expiry
    return allowed/retry information
```

This is an algorithm contract, not a new installed limiter. A connection pool cap
or semaphore limits concurrent work; it does not impose requests per second.

## PubSub and Streams

Redis Pub/Sub delivers to currently connected subscribers without a retained
consumer recovery log. It fits ephemeral notifications where loss is acceptable.
Streams retain entries and support groups, pending entries, acknowledgement and
reclaiming work; retention, duplicate handling and consumer recovery still need
explicit policies. Neither feature alone proves exactly-once business effects.

Do not choose Pub/Sub for a durable order workflow merely because a demonstration
message arrived. Inspect disconnect/restart behavior and retention capacity.

## Locks, leases and fencing

A distributed lease can expire while its holder is paused. Another worker may
acquire it, then the old worker resumes and writes stale state. A unique owner
token used for conditional release prevents deleting another holder's lease,
but does not itself stop the stale holder from writing.

A fencing token is a monotonic ownership/version value that the protected resource
actually validates, rejecting older holders. The token source and resource-side
check must support the intended consistency. A randomly generated lock token is
not automatically a fencing token.

Prefer a database transaction/constraint when it naturally owns the invariant.
Distributed lock algorithms have topology/failure assumptions; document them
instead of presenting a SET-with-expiry call as universal correctness.

## Outage behavior

For a derived catalogue cache, degrading to the source can preserve correctness
but overload the database. Bound fallback concurrency, use a circuit breaker and
consider serving permitted stale data. Security/rate-limit coordination may need
a different fail-open/fail-closed decision than catalogue reads.

Observe hit/miss/error rates, refill concurrency, evictions, latency and source
load. A high hit ratio can hide one expensive miss path or a stale-data bug.
Never make authoritative stock writes depend on a cached count being current.

## Worked failure analysis

After Redis restarts, the database collapses under refill traffic. Identify the
unbounded miss fan-out, not just Redis uptime. Coalesce identical fills, bound
overall source admission and recover cache capacity gradually. Then test that
cache errors cannot alter order/stock invariants.

[Redis data types](https://redis.io/docs/latest/develop/data-types/) and
[distributed locks](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)
provide detailed command and failure assumptions.

[Practice](practice.md) · [Next: messaging](../module-12/index.md)

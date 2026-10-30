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

### Example — a key must identify the representation, not just the object

Suppose tenants A and B both have product 7. A cache key product:7 can return A's
representation to B if the lookup path ignores tenant context. A safer key
includes tenant, representation version and any other dimension that changes
the permitted result.

Choose structures from operations: a string for one serialized response, a hash
for selected fields, a sorted set for ordered scores, or a Stream for retained
entries. A hash with a million unbounded fields is still an unbounded data
structure, and one hot key is still concentrated work.

Caching removes repeated source work only if key cardinality, value size, TTL and
eviction policy fit the workload. It is not just replacing a database call with
a Redis command.

## Cache placement strategies

| Strategy | Flow | Tradeoff |
| --- | --- | --- |
| Cache-aside | Read cache; on miss read source and populate | Simple ownership, but stale fills and stampedes need policy |
| Write-through | Write through a component updating cache/source | Centralized path; failure ordering still matters |
| Write-behind | Buffer writes before source persistence | Lower apparent latency with durability/replay/ordering complexity |

PostgreSQL remains FulfillHub's source of truth for orders/stock. A cached stock
display can be stale; final reservation must use the authoritative transaction.
Write-behind is a poor default for business data whose loss is unacceptable.

### Example — cache-aside has two owners and a failure gap

```text
GET cache → miss
READ database → product version 8
SET cache → product version 8 with TTL
RETURN product
```

The database owns truth; the cache owns a derived representation. On a write,
decide when/how that representation is invalidated or replaced. Cache-aside is
simple but has races with concurrent readers; write-through centralizes write
paths but still has multi-system failure ordering.

Write-behind acknowledges before source persistence under a buffering contract.
If the buffer is not durably recoverable, acknowledged writes can disappear.
That is a materially different promise from a derived catalogue cache. Do not
choose write-behind for authoritative order/stock data just because its apparent
latency is lower.

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

### Example — deleting after a write does not stop a stale refill

```text
Reader A: cache miss; reads old price 100 from database
Writer B: commits price 90; deletes cached value
Reader A: fills cache with its earlier price 100
```

The final cache is stale even though B invalidated after commit. A TTL can bound
some residence, but does not prove immediate consistency. Version-aware writes,
coordinated fills or an explicit bounded-staleness contract address different needs.

For stock display, bounded staleness may be acceptable while checkout always
uses authoritative transactional state. For permissions, a long stale allowance
may violate the contract. Define freshness per use case, not one global cache
duration. Negative caching similarly needs a short, scoped absence policy that
does not mask newly created or differently authorized resources indefinitely.

## Stampedes, hot keys and penetration

A stampede occurs when many misses refill together. Use single-flight/coalesced
fills, bounded refill concurrency, jitter or stale-while-revalidate where stale
data is acceptable. Protect the database during cold start and mass invalidation.

A hot key concentrates traffic on one shard/node. Client-local caches or replicated
read patterns can help under explicit freshness limits; adding unrelated shards
does not distribute one key's load automatically. Cache penetration sends requests
for non-existent/un-cacheable values to the source repeatedly; validate input and
consider bounded negative caching or probabilistic filters with understood errors.

### Example — a cache restart changes load, not only hit ratio

Imagine 1,000 requests for the same missing expensive report. Without coalescing,
all 1,000 can query the database before any one fills the cache. A single-flight
mechanism lets one owned fill run while compatible callers await its result.

Also bound fills across different keys; per-key coalescing alone cannot protect
a source against 1,000 distinct misses. TTL jitter spreads some expiry traffic
but does not fix a completely cold cache after restart.

Hot keys concentrate demand on one owner, while penetration repeatedly requests
non-existent values that never helpfully cache. Validate inputs and choose bounded
negative caching or other filters under clear error/freshness rules. Measure source
load and fill concurrency alongside hit ratio.

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

### Example — atomic count and expiry form one limiter rule

With separate INCR and EXPIRE calls, a client can fail after incrementing but
before setting expiry. The counter may then outlive the intended window. This
illustrative Redis Lua script combines the state rule after validating its TTL:

```lua
local ttl = tonumber(ARGV[1])
if not ttl or ttl < 1 or ttl > 60000 or ttl ~= math.floor(ttl) then
    return redis.error_reply("TTL must be 1..60000 milliseconds")
end
local count = redis.call("INCR", KEYS[1])
if count == 1 then
    redis.call("PEXPIRE", KEYS[1], ttl)
end
return count
```

The trusted caller selects a server-policy window key, then compares count with
the allowed threshold. This shows a fixed-window primitive, not a complete deployed
limiter. Validate before mutation because script errors do not provide arbitrary
rollback semantics.

Window boundaries can permit bursts; token buckets/sliding windows make different
cost/smoothing choices. A local semaphore limits in-flight work, not requests
per second or a global tenant quota.

## PubSub and Streams

Redis Pub/Sub delivers to currently connected subscribers without a retained
consumer recovery log. It fits ephemeral notifications where loss is acceptable.
Streams retain entries and support groups, pending entries, acknowledgement and
reclaiming work; retention, duplicate handling and consumer recovery still need
explicit policies. Neither feature alone proves exactly-once business effects.

Do not choose Pub/Sub for a durable order workflow merely because a demonstration
message arrived. Inspect disconnect/restart behavior and retention capacity.

### Example — reconnection means different things for PubSub and Streams

A subscriber disconnects while order event 42 is published. With ordinary Pub/Sub,
being connected again does not retrieve that missed history. Streams can retain
entries and consumer-group pending state, allowing recovery under retention,
acknowledgement and reclaim policies.

But a retained entry can be delivered again after a consumer crashes. The business
effect still needs idempotency and a durable progress boundary. Retention that
expires before a slow consumer catches up can also remove its recovery source.

Use Pub/Sub for loss-tolerant live signals such as ephemeral presence. Choose a
retained work/event mechanism when business recovery requires history, and specify
capacity/ownership rather than assuming the word "stream" guarantees it.

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

### Example — the old lease holder can wake after its authority expired

Worker A acquires a lease and pauses. Its lease expires; B acquires a new lease
and writes a newer result. A resumes and writes its stale result afterward.

Comparing a random owner token during unlock prevents A from deleting B's lease.
It does not stop A's stale write to the protected resource. A fencing design needs
a monotonic token and resource-side enforcement rejecting an older token.

This distinction matters when the resource is a database, file or external service.
If that resource cannot enforce the intended protocol, "we used a distributed
lock" is not enough proof. Prefer a database transaction/constraint when it naturally
owns the invariant, and document lease timing/topology assumptions.

## Outage behavior

For a derived catalogue cache, degrading to the source can preserve correctness
but overload the database. Bound fallback concurrency, use a circuit breaker and
consider serving permitted stale data. Security/rate-limit coordination may need
a different fail-open/fail-closed decision than catalogue reads.

Observe hit/miss/error rates, refill concurrency, evictions, latency and source
load. A high hit ratio can hide one expensive miss path or a stale-data bug.
Never make authoritative stock writes depend on a cached count being current.

### Example — fail-open fallback can overload the source

A catalogue cache outage triggers direct database reads. Correctness may be
preserved, but the source previously handled only misses and now receives every
request. Its pool saturates, timeouts provoke retries and a cache issue becomes
a database incident.

Use bounded fallback/admission, coalescing, suitable stale serving and an owned
circuit-breaker recovery policy. A rate-limit/security service may require a
different fail-open/fail-closed choice from catalogue data.

Observe errors, latency, evictions, fill concurrency and database load. A high
overall hit ratio can hide a single expensive miss path or an authorization key
bug. Recovery is about preserving both business guarantees and finite capacity.

## Worked failure analysis

After Redis restarts, the database collapses under refill traffic. Identify the
unbounded miss fan-out, not just Redis uptime. Coalesce identical fills, bound
overall source admission and recover cache capacity gradually. Then test that
cache errors cannot alter order/stock invariants.

[Redis data types](https://redis.io/docs/latest/develop/data-types/) and
[distributed locks](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)
provide detailed command and failure assumptions.

[Practice](practice.md) · [Next: messaging](../module-12/index.md)

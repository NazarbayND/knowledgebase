# Module 10 — Transactions, concurrency and scalability

**P0 · prerequisite: schema constraints, SQL and Unit of Work**

Transactions protect an invariant across concurrent operations. “Both requests
returned success” does not mean their combined result is correct. State the
invariant, draw the interleaving and choose the database mechanism matching it.

## Chapter navigation

1. [ACID and MVCC](#acid-and-mvcc)
2. [Isolation and anomalies](#isolation-and-anomalies)
3. [Concurrency-control strategies](#concurrency-control-strategies)
4. [Deadlocks and retries](#deadlocks-and-retries)
5. [Pools and transaction duration](#pools-and-transaction-duration)
6. [Replication and partitioning](#replication-and-partitioning)
7. [WAL, backups and recovery](#wal-backups-and-recovery)
8. [Choosing other data models](#choosing-other-data-models)

## ACID and MVCC

Atomicity keeps transaction effects together; consistency concerns preserved
constraints/invariants; isolation governs interactions; durability describes
committed recovery behavior under the selected storage/replication configuration.
ACID is not a claim that every application invariant is automatically encoded.

PostgreSQL MVCC maintains tuple versions so readers see data according to snapshots
while writers create new versions. Old versions require cleanup once no relevant
snapshot needs them. Long transactions can retain versions, interfere with vacuum
and occupy connections even when application CPU is idle.

## Isolation and anomalies

| PostgreSQL level | Snapshot behavior | Important implication |
| --- | --- | --- |
| Read Committed | A fresh snapshot per statement | Two reads in one transaction can observe different committed data |
| Repeatable Read | Transaction snapshot with snapshot-isolation behavior | Stable reads prevent PostgreSQL phantom/nonrepeatable-read effects, but write skew remains possible |
| Serializable | Detects executions inconsistent with serial order | Transactions may fail and need complete retries |

PostgreSQL treats Read Uncommitted as Read Committed. Product-specific semantics
matter; do not infer every database's behavior from an isolation label alone.

A lost update can occur when both callers compute a replacement from the same old
value without a suitable condition/lock. Write skew occurs when transactions read
a shared invariant but update different rows, such as two on-call engineers each
seeing the other available and both going off call. A per-row nonnegative stock
check cannot express an arbitrary cross-row availability rule.

## Concurrency-control strategies

For a single stock row, an atomic conditional update can enforce availability:

```sql
UPDATE products
SET available = available - :quantity
WHERE tenant_id = :tenant
  AND product_id = :product
  AND :quantity > 0
  AND available >= :quantity
RETURNING available;
```

Zero returned rows requires a defined absent/insufficient/invalid outcome policy.
Place this update and the order write in one transaction; an atomic stock update
alone does not atomically create an order. Keep constraints as a final guard.

Pessimistic control can SELECT ... FOR UPDATE, inspect and change within the same
transaction. It serializes contenders on the locked row and may create waits.
Acquire multiple products in a consistent order. Locks do not protect resources
whose corresponding rows are not part of the chosen protocol.

Optimistic control uses a version precondition, such as UPDATE ... WHERE version =
:observed_version, incrementing version on success. A conflict needs a business
policy: retry after re-evaluating the use case or tell the caller its assumption
changed. Do not silently overwrite the newer value.

Serializable can protect broader read/write invariants by rejecting unsafe
interleavings. It still requires constraints, correct transaction scope and a retry
policy. Choosing it is not permission to ignore external side effects.

## Deadlocks and retries

Deadlock: transaction A holds product one and waits for two; B holds two and waits
for one. PostgreSQL detects and aborts a participant. Consistent acquisition order
and smaller transactions reduce risk; increasing a timeout does not remove a cycle.

On serialization/deadlock failures, roll back and retry the complete transaction
with a fresh snapshot, bounded attempts and backoff/jitter where useful. Retrying
only the last failed statement can preserve invalid assumptions. Avoid retrying
permanent validation/permission failures or blindly wrapping every database error.

If a payment/email is sent before commit and the transaction retries, the external
effect may duplicate. Record durable intent/outbox within the transaction and
process it with idempotent external contracts. A connection loss around commit can
leave an unknown outcome; a durable request identity is needed to reconcile it.

## Pools and transaction duration

A pool bounds connections and reuses them; it does not increase database capacity.
Measure checkout wait, active transaction time, query time and idle-in-transaction
sessions separately. Worker/replica scaling multiplies per-process pool limits.

Do not hold a transaction while waiting on a slow vendor or rendering a large
stream if the invariant does not require it. Ensure rollback/close on cancellation
and failed requests. Apply admission limits and realistic deadlines rather than
making the pool arbitrarily large.

## Replication and partitioning

Read replicas offload reads but introduce lag and read-after-write surprises.
Route consistency-sensitive reads deliberately or expose a stale-read contract.
Synchronous replication trades latency/availability for stronger acknowledgement
properties; asynchronous replication can lose recent acknowledged writes during
some failovers depending on topology/recovery policy.

Partitioning divides a logical table for pruning, lifecycle management and
maintenance; it is not automatic cross-machine sharding. Choose keys from access
and retention patterns. Too many partitions, skewed keys and incompatible unique
constraints create new costs. Replication copies data; sharding distributes ownership.

## WAL, backups and recovery

WAL records changes needed for recovery. Backups plus continuous WAL archiving
can support point-in-time recovery under an appropriate configuration. A replica
is not a backup: accidental deletes/corruption can propagate. Test restoration,
permissions, retention and recovery time, not merely whether a backup job exists.

Define RPO (acceptable data loss window) and RTO (acceptable recovery duration).
High availability reduces outage probability/duration through redundancy/failover;
it does not prove correctness or replace a recovery drill. Prevent split-brain
writers and understand which component owns promotion/routing.

## Choosing other data models

Document stores fit aggregate documents and flexible shapes; key-value systems fit
direct key access; wide-column systems fit partition-oriented high-volume access;
graphs fit relationship traversal. Evaluate query patterns, transaction boundaries,
consistency, scale, operations and cost. “NoSQL” does not mean schema-free business
data or no transactions, nor does a relational database fit every workload.

## Worked failure analysis

Two customers buy the last unit. A SELECT then application-computed SET uses a
stale value under concurrency. Reproduce the interleaving, choose an atomic update,
row lock/version or appropriate serializable transaction, and preserve order/stock
in one boundary. The eventual integration test must coordinate concurrent clients
and assert business invariants, not just count HTTP 200 responses.

[PostgreSQL concurrency control](https://www.postgresql.org/docs/current/mvcc.html),
[locking](https://www.postgresql.org/docs/current/explicit-locking.html) and
[backup/recovery](https://www.postgresql.org/docs/current/backup.html) are the references.

[Practice](practice.md) · [Phase assessment](../assessment.md) ·
[Next: caching](../../phase-6/module-11/index.md)

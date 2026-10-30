# Module 10 — Practice and assessment

## Exercises

1. Draw two last-item purchases under read-then-write logic. Show an atomic guarded
   UPDATE, a row-lock strategy and a version-precondition strategy; compare conflicts.
2. Construct a two-row write-skew example and explain why stable snapshot reads
   alone do not preserve the cross-row invariant.
3. Draw opposite-order locks on two products. Specify lock order, rollback and
   bounded complete-transaction retry, including nonretryable failures.
4. Explain how cancellation and a lost connection around commit differ. Design
   a reconciliation identity without pretending a timeout proves rollback.
5. Model workers × pools against a database connection budget. Diagnose long
   transactions, retained versions and replica-lag read-after-write failures.
6. Specify a restore drill with RPO/RTO and explain why a read replica is not a backup.
7. Compare relational, document, key-value, wide-column and graph choices for
   orders, sessions, telemetry and relationship traversal.

??? note "Model reasoning"
    Guarded updates decide the predicate and mutation together; use-case effects
    still need one transaction. Snapshot isolation can allow writers of different
    rows to violate a shared read invariant. Retry a rolled-back complete unit,
    not only its last statement, and keep external effects idempotent/durable.
    Unknown commit outcomes need reconciliation. Pool waits and long snapshots
    can explain low-CPU latency. Restore evidence, not replica existence, establishes
    recovery capability.

## Interview questions

- Does PostgreSQL Repeatable Read permit the classic phantom-read behavior?
- Why can Serializable require retries?
- When would optimistic control be better than a row lock?
- Can a retry duplicate a payment even if the database transaction rolled back?
- How do replication, partitioning and backups solve different problems?

??? note "Answer guide"
    PostgreSQL's snapshot behavior prevents classic phantom reads at Repeatable
    Read, but write skew remains. Serializable rejects unsafe histories. Optimistic
    control avoids holding locks during independent work but needs conflicts to
    be tolerable. External effects are outside rollback unless a protocol addresses
    them. Replicas copy state, partitions divide a table's data organization, and
    backups support historical recovery.

## Mastery assessment

Use 25 for isolation mechanisms, 30 for a correct transaction/concurrency contract,
20 for anomaly/retry diagnosis, 15 for scale/recovery tradeoffs and 10 for explanation.
Target 80/100. Actual concurrent correctness/performance remains unverified until
the [deferred project](../project.md) is run against PostgreSQL.

[Module 10](index.md) · [Cumulative review](../assessment.md)

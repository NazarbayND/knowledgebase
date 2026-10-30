# Phase 5 — Persistence and concurrency assessment

**Week 8 cumulative checkpoint:** review Python ownership, API contracts, Unit of
Work and PostgreSQL together. Projects are deferred; submit written evidence.

## Scenario

A reporting endpoint became slow and double-counts revenue after joining audit
events. Concurrent checkout sometimes oversells. Adding API workers increased
pool waits, and customers read stale orders from a replica after writing.

## Tasks and scoring

| Dimension | Evidence | Points |
| --- | --- | ---: |
| Concepts | Explain keys, MVCC, snapshots, index/planner decisions and replica lag | 25 |
| Correctness | Write grain-correct SQL and a transaction preserving stock/order invariants | 30 |
| Debugging | Show join multiplication, unsafe interleaving and a pool-budget investigation | 20 |
| Tradeoffs | Compare locks/versioning/Serializable and indexing/migration/recovery choices | 15 |
| Communication | Present hypotheses, expected evidence and assumptions clearly | 10 |

## Model review

Correct query grain before optimizing it. Inspect rows/loops/buffers on realistic
data and preserve equivalent totals. Choose a stock mutation protocol and combine
order/outbox effects in one transaction. Complete retries need fresh assumptions
and idempotent external behavior. Worker growth multiplies pool demand; a larger
pool does not create database capacity. Route immediate consistency-sensitive
reads appropriately rather than assuming replicas are current.

Include an expand/contract migration plan and a restore drill with explicit
RPO/RTO. A backup without restored evidence and an index without a measured plan
remain hypotheses, not completed operational work.

## Pass and revision

Target 80/100. Revise wrong totals, negative stock, retrying only a failed final
statement, or claims that every isolation level prevents every anomaly. Record
written results in [progress](../progress.md); leave concurrent test and measured
query-performance evidence pending until practical implementation resumes.

[Overview](index.md) · [Project placeholder](project.md)

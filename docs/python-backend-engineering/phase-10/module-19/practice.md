# Module 19 — Timed practice and assessment

These are exercise prompts and answer guides. The practical portfolio project is
deferred; small code/SQL answers can be written independently without building it.

## Challenge set

| Timebox | Challenge | Required evidence |
| --- | --- | --- |
| 20 min | First position >= target in sorted data | Interval invariant, duplicates/empty edges, O(log n) explanation |
| 25 min | Longest substring with distinct code points | Monotonic window, overlap cases, O(n) average time/space analysis |
| 25 min | Shortest path distances in an unweighted graph | Queue/visited semantics, cycles/disconnected nodes, O(V+E) |
| 25 min | Top k frequent SKUs | Counting, tie policy, heap vs full sort costs |
| 30 min | Minimum coins for an amount | State/base/transition, unreachable case and why greedy can fail |
| 30 min | Rank tenant customers by spend | Correct join grain, ties/nulls, query/index reasoning |
| 30 min | Diagnose blocked event loop and lost counter updates | Reproduction timeline, scope-correct correction and cleanup |
| 45 min | Specify/outline a create-order API | Validation/auth/tenant/idempotency/error contract and negative cases |
| 30 min | Review unfamiliar persistence code | Commit/rollback/resource boundary, regression and safe refactor |

## Model reasoning and edges

??? note "Algorithm guide"
    Binary search needs sorted input and a strictly shrinking half-open interval.
    Sliding-window start must never move backwards on an older duplicate. BFS
    records discovery before enqueuing repeatedly. Heap entries need tie-breaking
    compatible with payloads. DP requires a defined unreachable state; denominations
    such as 1, 3, 4 defeat a naive largest-first greedy answer for amount 6.

??? note "Backend guide"
    State grain and invariants first. Queries must not multiply totals through
    unrelated one-to-many joins. API success needs an explicit durable effect
    boundary. Process-local dictionaries/locks cannot prove multi-worker stock
    or idempotency correctness. Async wrappers do not make blocking calls nonblocking.

## Review questions

- What is your precondition, invariant and termination argument?
- Which edge case would break your first approach?
- What are time, extra memory and output costs?
- Which behavior is promised and which production capability is deferred?
- How would you test a failure instead of only the happy path?

## Mastery assessment

Use 25 for problem/mechanism understanding, 30 for a correct bounded solution,
20 for debugging and edges, 15 for alternatives/complexity and 10 for communication.
Target 80/100. Capture actual independent results and timeboxes in
[progress](../../progress.md); reading the supplied algorithm is not a completed attempt.

[Module 19](index.md) · [Next: Module 20](../module-20/index.md)

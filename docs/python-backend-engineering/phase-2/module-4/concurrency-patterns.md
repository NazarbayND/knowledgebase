# Module 4 — Failure, cancellation, and backpressure in practice

**P0/P1 · use after the [execution-model chapters](index.md)**

A useful concurrency design answers four questions: who owns the work, what can
run simultaneously, how long callers may wait, and what happens when one operation
fails. This walkthrough makes those contracts observable rather than relying on
sleep durations or the presence of an `async` keyword.

## A workload selection interview

You need to process 100 vendor responses, calculate a pure-Python report, and save
a file through a blocking SDK. A single blanket answer such as “make it async”
misses the different bottlenecks.

| Operation | Initial choice | Evidence that could change it |
| --- | --- | --- |
| Many independent HTTP waits with an async client | Bounded asyncio workers | Vendor capacity, latency, rate limits, response sizes |
| Pure Python CPU calculation on ordinary CPython | Bounded process pool if large enough | Serialization/startup costs and actual CPU profile |
| Blocking SDK call | Bounded threads, with SDK timeouts | SDK thread safety, native GIL release, cancellation requirements |
| Existing native numeric kernel | Measure its implementation first | It may already release the GIL or own an internal thread pool |

The GIL limits simultaneous Python execution in standard CPython, but does not
prevent I/O overlap or protect multi-step application invariants. Free-threaded
builds change the parallelism opportunity; they do not remove shared-state races
or make every dependency compatible.

## Worked experiment 1 — Make a lost update deterministic

Consider two tasks incrementing a shared count across an await:

```text
Task A reads 0
Task B reads 0
Task A writes 1
Task B writes 1
```

There were two completed operations but the count is one. The same shape appears
when two requests each read the last inventory unit before either commits.

The reference `async_patterns.py` uses an `asyncio.Barrier`, so every unsafe worker
reads before any writes. It does not hope that a short sleep happens to expose
the failure. With twenty workers the unsafe result is one; with a shared
`asyncio.Lock` around the read/await/write operation the result is twenty.

```bash
# Working directory: examples/python-backend-engineering/
uv run --frozen python -m fulfillhub.async_patterns
```

The first line is:

```text
unsafe and locked counts: (1, 20)
```

### What the lock actually guarantees

Every task in this experiment shares one event loop, state object and lock. Only
tasks using that same lock participate in its mutual exclusion. A second process
has a different memory space and cannot be coordinated by this object. Database
invariants need an appropriate transaction/locking strategy in later phases.

The lab keeps the await inside the lock to show that the protected operation stays
exclusive. Real code should minimize time holding a lock. Do not hold a global
inventory lock around slow HTTP calls if an ownership or transaction boundary can
be made smaller. A `threading.Lock` used synchronously on the event-loop thread can
block that loop and is not an interchangeable fix.

## Worked experiment 2 — Observe sibling behavior after failure

The lab uses two children: a sibling announces it has started and waits on an
event; the other waits for that announcement and raises a deliberate error. This
removes any race about whether the sibling ran before the failure.

### Gather with an explicit owner

The parent awaits `gather`. When a child raises a normal RuntimeError, the await
raises but the waiting sibling is still live. The parent catches the error,
releases the sibling, and explicitly awaits it. Its finally block still cancels
and awaits unfinished children on any other exit.

```text
sibling started
parent caught failure
sibling completed
sibling cleaned
```

If the parent instead returned and let `asyncio.run()` shut down, the runner might
cancel the remaining task. That would be **runner shutdown behavior**, not proof
that gather cancelled siblings on the child's error. Preserve ownership long
enough to observe the distinction.

### TaskGroup owns a failure scope

For the same failure under TaskGroup, the sibling is cancelled and cleaned before
the parent handles the group's error:

```text
sibling started
sibling cancelled
sibling cleaned
parent caught failure
```

`except* RuntimeError` handles matching leaves of an ExceptionGroup. It is not
permission to swallow every unexpected failure; unmatched errors still need a
policy. `CancelledError` propagates out of the child after its cleanup.

### When to choose each

TaskGroup fits a set of operations with one shared lifetime and failure scope.
Gather can be useful when collecting independently managed awaitables and when
its exact error contract suits the caller. `return_exceptions=True` turns errors
into values; each must be inspected. Neither API chooses the business meaning of
partial success for you.

## Worked experiment 3 — Read the aggregator as a lifecycle

The existing `aggregation.py` has one producer, a bounded queue, a fixed worker
set, and one shared HTTP client. Walk through the scope in this order:

1. Validate positive integer worker/queue limits and a positive finite timeout
   before opening the client or creating workers. Reject bool counts, fractional
   counts, NaN and infinity rather than discovering them inside child tasks.
2. Allocate a bounded pending queue and finite result slots.
3. Enter the shared client's lifetime; configure connection limits.
4. Enter TaskGroup and start producer/workers.
5. Each worker owns a dequeued item and records exactly one outcome.
6. Workers acknowledge every successful queue get, including sentinels.
7. The group waits for completion, or cancels/awaits children on failure.
8. The client closes after workers no longer use it.

The nesting is part of correctness. Closing the client while unowned workers are
still running would create shutdown errors that look like network failures.

### Expected endpoint failures vs unexpected defects

| Event | Reference behavior | Why |
| --- | --- | --- |
| Request deadline expires | Result with `error="timeout"` | One endpoint's failure is an expected batch outcome |
| Remote status is 503 | Result with status 503 and `error="http_status"` | Caller can distinguish a received response from connection failure |
| Transport fails | Result with `error="request_error"` | The client failed to complete the request |
| Unexpected programming error | TaskGroup fails and cancels siblings | Do not disguise a defect as a successful partial batch |
| Parent is cancelled | Cancellation propagates after worker cleanup | Caller owns the lifetime of the batch |

The client accepts trusted URLs and full response bodies. It is not an untrusted
URL-fetching production endpoint. Destination validation, payload limits and
network policy would be additional contracts, not hidden benefits of asyncio.

## Deadlines are a budget, not one timeout number

A request can wait in the application queue, wait for a connection, connect,
exchange data, process a body, and wait for the result consumer. The reference's
per-request timeout starts **after dequeue**, and its HTTPX client also has transport
timeouts. A whole batch may take much longer than one per-request deadline.

For a caller-owned batch budget, wrap the entire operation:

```python
import asyncio
from fulfillhub.aggregation import aggregate

async def fetch_with_budget(urls: list[str]):
    try:
        async with asyncio.timeout(2.0):
            return await aggregate(urls, concurrency=4, request_timeout=0.5, queue_size=8)
    except TimeoutError:
        raise RuntimeError("whole batch exceeded its budget") from None
```

This is a contract illustration: it discards partial results when the overall
budget expires and translates the timeout into a caller-facing error. If partial
output must survive cancellation, define a streaming/result persistence boundary
instead of pretending a list-returning function has already returned it.

Timeouts are cooperative. They cannot immediately interrupt a CPU loop that does
not yield or kill a thread already executing a blocking SDK call. A native blocking
operation needs its own deadline/stop mechanism. `shield()` changes cancellation
propagation; it does not create a free detached lifecycle or remove ownership.

## Capacity math that reveals overload

For a rough steady-state estimate, throughput is about concurrency divided by
average operation time when there is enough demand and no other bottleneck. Four
in-flight calls taking 100 ms each suggest an upper scale near forty calls/second,
before overhead, variance, vendor limits and queuing. This is an estimate, not a
load-test result or a guaranteed rate limit.

| Mechanism | Bounds | Does not bound |
| --- | --- | --- |
| Fixed worker set | Number of active worker tasks | Body size or total output storage |
| Bounded queue | Pending admitted items | Complete batch input already retained by the caller |
| Semaphore | Concurrent entry to a region | Number of pre-created tasks waiting to enter |
| HTTP connection pool | Connections used by that client | Calls per second or every dependency's capacity |
| Per-request timeout | Waiting within its defined scope | Queue time excluded from that scope |
| Rate limiter | Admission rate under a chosen policy | How long already admitted work occupies resources |

With 10,000 inputs, four workers and queue capacity eight, the queued item count
is bounded, but the reference still holds the caller's finite URL sequence and
10,000 result slots. Full response bodies can dominate memory. Backpressure is
effective only when you identify every unbounded buffer, including output.

Increasing worker count against a saturated downstream can increase queue time
and errors while reducing useful throughput. Record p95/p99 latency, failure rate,
pool wait and queue occupancy when choosing a limit; a fast average hides tail risk.

## A disciplined debugging sequence

**Symptom: unrelated requests pause.** Measure heartbeat/loop lag, then inspect for
synchronous HTTP, `time.sleep`, blocking SDK calls and long CPU work. Try the
existing blocking/cooperative/thread comparison. Choose an async library for async
I/O, bounded threads for blocking I/O, and measured process offload for pure-Python
CPU work. Do not simply add more async tasks.

**Symptom: cancellation appears ignored.** Find broad catches, cleanup awaits,
threads still doing work, or a scope that never yields. Reproduce with an event
that confirms the child started; cancel the parent and assert child cleanup
completed. A task disappearing from a log is weaker evidence than its finally
block running and the owner awaiting completion.

**Symptom: count or stock is wrong.** Draw the read/await/write timeline, reproduce
with a barrier, identify the scope of the shared state, then choose a lock,
single-owner design, or transaction mechanism with the matching scope.

## Verification and extensions

```bash
# Working directory: examples/python-backend-engineering/
uv run --frozen pytest tests/test_async_patterns.py tests/test_aggregation.py -v
uv run --frozen python -m fulfillhub.async_patterns
uv run --frozen python -m fulfillhub.concurrency_lab
```

The deterministic tests check race outcomes and sibling lifecycle ordering; the
aggregation tests check limits, errors, cancellation and real HTTP. Speed ratios
remain observations. Extend the batch API with one explicitly chosen policy—such
as an overall deadline or output byte cap—and write the acceptance tests before
changing behavior. Retries require a separate load and idempotency discussion.

[Core chapters](index.md) · [Practice](practice.md) ·
[Phase 2 cumulative review](../assessment.md)

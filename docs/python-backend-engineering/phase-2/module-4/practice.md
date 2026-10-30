# Module 4 — Practice and assessment

Use the [concurrency chapters](index.md) and [phase project](../project.md).

## Exercises

1. **Choose a model:** classify waiting for 100 HTTP responses, computing pure-Python
   hashes, reading files with a blocking library, and a native numeric operation.
   Justify asyncio/threads/processes and identify where measurement could change it.
2. **Inspect the runtime:** report build and current GIL status. Explain how a
   free-threaded interpreter changes parallelism possibilities without proving
   business-state safety. Running a free-threaded build is optional P2 work.
3. **Scheduling:** compare two sequential awaits with TaskGroup-owned concurrent
   tasks. Explain coroutine objects, Tasks and Futures; deliberately create and then
   repair an unawaited-coroutine mistake in scratch code.
4. **Task behavior:** fail one child under `gather` and under `TaskGroup`. Observe
   whether siblings finish or cancel; explicitly await/clean up every child in your
   experiment. Do not assume gather cancels siblings on a normal child exception.
5. **Cancellation and timeout:** cancel the aggregation parent while a request is
   waiting. Prove workers terminate and cleanup runs. Classify endpoint timeout as
   an expected result while a programming error fails the batch.
6. **Executors:** run equal CPU work through threads/processes, then adapt a blocking
   I/O function using `to_thread`. Report startup/serialization costs and explain
   why cancelling the await does not stop an already-running thread.
7. **Loop blocking:** run the deliberate `time.sleep` defect beside a heartbeat,
   diagnose the symptom and compare an async sleep and threaded adaptation. Report
   observations without a fixed performance assertion.
8. **Races:** run 20 unsafe increment coroutines with an await between read/write.
   Show a lost update; repair with `asyncio.Lock` or a single state owner. Explain
   why this does not coordinate separate API worker processes.
9. **Backpressure:** aggregate a batch with a fixed worker count and queue capacity
   one. Verify peak in-flight operations never exceeds the limit, output order is
   preserved and a slow consumer does not create one task per input. Explain the
   difference between this, a semaphore, a connection pool and a rate limiter.

## Reference commands

Working directory: `examples/python-backend-engineering/`.

```bash
uv run --frozen python -m fulfillhub.concurrency_lab
uv run --frozen python -m fulfillhub.concurrency_lab --executors
uv run --frozen pytest tests/test_aggregation.py -v
```

The tests cover a bounded worker set, input-order results, endpoint timeouts,
transport and HTTP errors, parent cancellation, unexpected child failure, invalid
limits, empty input, and a real loopback HTTP boundary. Timing comparisons are lab
observations, not speed assertions. Gather semantics and the lost-update repair
now have reference implementations in `fulfillhub.async_patterns` and behavioral
tests in `tests/test_async_patterns.py`. Attempt them independently before opening
the [lifecycle walkthrough](concurrency-patterns.md).

## Interview practice

- Why can an `async def` endpoint be slower than a synchronous endpoint?
- When do threads improve Python throughput despite the GIL?
- Does every `await` yield? What happens to a timeout around blocking Python code?
- How do TaskGroup and gather differ on a child's unexpected exception?
- Why does a semaphore around a million created tasks still use excessive memory?
- Which time does a per-request timeout exclude? How would you add a batch deadline?
- Why can increasing pool size make a downstream service less reliable?
- How do you safely stop work during shutdown, including blocking library calls?

??? note "Expected reasoning"
    Async endpoints still block if their bodies call blocking code. Threads overlap
    I/O and may parallelize native code that releases the GIL. Awaiting an already
    completed operation need not suspend. Timeouts are cooperative. TaskGroup
    owns/cancels/awaits children; gather has different failure semantics. Queue
    bounds limit pending admission; pool bounds limit connections; neither is a
    rate limit. Shutdown requires deadlines, task ownership and operation-specific
    stopping rather than assuming cancellation kills threads.

## Mastery assessment

Timebox: **75 minutes implementation/diagnosis + 20 minutes explanation**.

| Dimension | Evidence | Points |
| --- | --- | ---: |
| Concepts | Choose execution models and explain loop/GIL/cancellation behavior | 25 |
| Correctness | Ordered bounded aggregator with timeout/error/cancellation tests | 30 |
| Debugging | Demonstrate and diagnose loop blocking and a shared-state race | 20 |
| Decisions | Explain capacity, deadline, pool and partial-failure tradeoffs | 15 |
| Communication | Show reproducible results, measured limits and production gaps | 10 |

Target **80/100**. Do not mark mastery while parent cancellation leaks workers,
the concurrency limit is violated, or failures are silently reported as success.
Record evidence in [progress](../../progress.md).

[Module 4](index.md) · [Concurrency project](../project.md) ·
[Phase overview](../index.md)

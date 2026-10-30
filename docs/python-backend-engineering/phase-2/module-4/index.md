# Module 4 — Concurrency and asynchronous execution

**P0/P1 · free-threaded internals are P2**

Concurrency means multiple activities can make progress during overlapping periods;
parallelism means execution at the same instant. Choose an execution model from the
workload, isolation needs, dependency support and failure behavior—not from whether
the API happens to have an `async` keyword.

## Chapter navigation

1. [Processes, threads and coroutines](#processes-threads-and-coroutines)
2. [The GIL and free-threading](#the-gil-and-free-threading)
3. [Workload selection](#workload-selection)
4. [Event-loop scheduling](#event-loop-scheduling)
5. [Structured tasks and cancellation](#structured-tasks-and-cancellation)
6. [Executors and blocking libraries](#executors-and-blocking-libraries)
7. [Diagnosing loop blocking](#diagnosing-loop-blocking)
8. [Races and synchronization](#races-and-synchronization)
9. [Pools, limits and backpressure](#pools-limits-and-backpressure)

## Processes, threads and coroutines

Processes have separate address spaces and communicate through serialization,
shared memory or IPC. They provide stronger memory isolation and incur startup,
transfer and coordination costs. Threads share process memory and are scheduled
by the OS; blocking I/O can leave other threads able to run. Coroutines are
cooperatively scheduled execution contexts, usually on one event-loop thread.

An `async def` call returns a coroutine object; it does not execute to completion
or automatically start in the background. Await it directly or schedule it as a
task owned by a clear scope. A thousand waiting coroutines can be cheaper than a
thousand threads, but a thousand live network requests can still exhaust a service.

```python
import asyncio

async def value() -> int:
    await asyncio.sleep(0)
    return 42

async def main() -> None:
    task = asyncio.create_task(value())
    print(await task)

if __name__ == "__main__":
    asyncio.run(main())
```

Unlike an automatically launched JavaScript promise-producing operation, merely
creating a Python coroutine object does not drive it. Unawaited coroutines can
produce warnings and silently omit intended work.

## The GIL and free-threading

In a standard GIL-enabled CPython build, one thread at a time executes Python
bytecode in an interpreter. This protects interpreter state, not your application's
multi-step invariants. Threads remain useful for I/O, and native code can release
the GIL during expensive work.

Free-threaded CPython builds can run Python code concurrently across threads.
That does not make shared mutable business data race-free or remove synchronization
costs. Extension compatibility and whether importing an extension enables the GIL
must be checked on the actual runtime. Package support, memory overhead and workload
shape affect the benefit.

```python
import sys
import sysconfig

print("free-threaded build:", bool(sysconfig.get_config_var("Py_GIL_DISABLED")))
probe = getattr(sys, "_is_gil_enabled", None)
print("GIL currently enabled:", probe() if probe is not None else "unknown")
```

`_is_gil_enabled` is implementation-specific; absence is not proof the GIL is off.
The course's reference validation uses ordinary CPython 3.14, not a free-threaded
build. Free-threaded benchmarking is optional P2 work; do not generalize its results
to a different interpreter or extension stack.

## Workload selection

| Workload | Starting choice | Why and tradeoff |
| --- | --- | --- |
| Many waits with async-capable clients | asyncio | Low waiting-task overhead; every blocking call needs scrutiny |
| Blocking I/O library | bounded thread pool | Reuses existing API; shared state and cancellation limits remain |
| Pure Python CPU work on standard CPython | bounded process pool | Parallel execution; startup, pickling, memory costs |
| CPU-heavy native library releasing GIL | measure threads first | Native execution may parallelize; library's own threads can oversubscribe |
| Untrusted or unstable isolated work | process boundary | Better fault isolation, but explicit IPC and lifecycle management |

First ask whether the bottleneck is CPU, remote latency, disk, a database lock,
or a saturated connection pool. Asyncio improves overlap of waits, not the CPU cost
of a calculation. Adding workers to a saturated database can worsen latency.
For tiny jobs, serialization and process startup can outweigh parallel gains.

## Event-loop scheduling

The loop drives ready callbacks and tasks, checks I/O readiness and timers, and
resumes suspended coroutines. A task runs until it completes or actually suspends.
`await` is a potential suspension point; awaiting an already-complete operation
need not yield a meaningful scheduling opportunity.

A Future represents an eventual result/error and is mainly a lower-level bridge
for transports and callback APIs. A Task drives a coroutine and is also awaitable.
Application code normally composes tasks rather than manually setting Futures.

```python
async def fetch_pair(client, first: str, second: str):
    async with asyncio.TaskGroup() as group:
        left = group.create_task(client.get(first))
        right = group.create_task(client.get(second))
    return left.result(), right.result()
```

This illustration assumes imports and a shared async client. Two sequential
`await client.get(...)` calls are sequential requests; the keyword alone does not
create overlap. Never run `asyncio.run()` inside an already-running loop; expose
an async function for that caller to await.

## Structured tasks and cancellation

`TaskGroup` owns its children: leaving its scope waits for them; an unexpected
child failure cancels siblings and raises grouped errors after cleanup. `gather`
collects results in input order, but with default settings one failing awaitable
does not automatically cancel every sibling. `return_exceptions=True` changes
exceptions into results and requires deliberate inspection.

```python
import asyncio

async def bounded_wait() -> None:
    try:
        async with asyncio.timeout(0.1):
            await asyncio.sleep(10)
    except TimeoutError:
        print("deadline exceeded")
```

Cancellation is a request delivered at an await point, typically as
`CancelledError`. Use `try/finally` and `async with` for cleanup, then propagate it.
Do not catch `BaseException` and turn cancellation into success. `asyncio.timeout`
translates its own cancellation into `TimeoutError` outside the timeout context.
A timeout cannot interrupt a CPU loop that never yields.

An `asyncio.Queue` coordinates producers/workers; call `task_done()` once for every
successful `get()` if using join accounting. A semaphore bounds simultaneous entry
to a region, but creating a task for every item first can still allocate millions
of waiting tasks. A fixed worker set plus a bounded queue limits pending work too.
Use expected endpoint failures as explicit results only when the batch contract
allows partial success; let programming errors fail the TaskGroup.

## Executors and blocking libraries

`asyncio.to_thread()` is convenient for blocking I/O. `ThreadPoolExecutor` gives
explicit pool/lifetime control; `ProcessPoolExecutor` supports CPU work in separate
processes. Keep process functions importable at module scope, send picklable data,
and guard executable startup with `if __name__ == "__main__":`.

```python
import asyncio
from pathlib import Path

async def load_text(path: Path) -> str:
    return await asyncio.to_thread(path.read_text, encoding="utf-8")
```

Cancelling this await does not forcibly stop a thread already reading. Set
timeouts/cooperative stopping in the underlying operation where supported and
account for shutdown. A process boundary also has cancellation and ownership
costs; cancelling a Future is not a guarantee that running work was terminated.

From `examples/python-backend-engineering/`, run:

```bash
uv run --frozen python -m fulfillhub.concurrency_lab --executors
```

The lab verifies equal results and reports elapsed times for a bounded CPU job.
It makes no promise the process pool is faster for this small input; vary task size
to explain the crossover while keeping total resource use bounded.

## Diagnosing loop blocking

`time.sleep`, synchronous HTTP clients, long JSON processing, CPU loops and blocking
database calls can monopolize an event-loop thread. An `async def` wrapper does not
change their implementation. A symptom is increased latency for unrelated requests
while the loop cannot schedule them, even when remote services are healthy.

```python
import asyncio
import time

async def wrong() -> None:
    time.sleep(0.1)  # deliberately blocks the loop

async def cooperative() -> None:
    await asyncio.sleep(0.1)

async def adapted_blocking_api() -> None:
    await asyncio.to_thread(time.sleep, 0.1)
```

The lab runs a heartbeat alongside each mode. Fewer heartbeat turns in blocking
mode expose lack of scheduling progress. Use loop lag/slow callback observations
and CPU profiling to identify the responsible call. For async I/O choose the async
client; for blocking I/O use bounded threads; for pure Python CPU work consider
processes. Offloading CPU work to threads on a GIL-enabled interpreter may still
cause contention. No fixed speed ratio is a correctness assertion.

## Races and synchronization

A race occurs when correctness depends on execution ordering. Even on one loop,
an invariant can be broken across an `await` between reading and writing state:

```python
async def unsafe_increment(state: dict[str, int]) -> None:
    before = state["count"]
    await asyncio.sleep(0)
    state["count"] = before + 1

async def safe_increment(state: dict[str, int], lock: asyncio.Lock) -> None:
    async with lock:
        before = state["count"]
        await asyncio.sleep(0)
        state["count"] = before + 1
```

This lock protects tasks using the same loop/lock. It does not coordinate another
process or a database transaction. Thread code needs thread-safe primitives such
as `threading.Lock`; blocking on a threading lock in the event-loop thread can
deadlock it. Keep critical sections small and lock acquisition order consistent.

A single loop does not interleave tasks during ordinary non-suspending Python
code, but relying on that detail can hide invariants when code later gains awaits
or threads. The GIL is not a transaction mechanism. Prefer immutable messages and
one owner for mutable state; use a database's transactional tools for multi-worker
inventory correctness in later phases.

## Pools, limits and backpressure

A connection pool reuses connections and caps socket usage. Match application
concurrency to downstream capacity, and distinguish queue wait, pool wait, connect,
read, and whole-request deadlines. A semaphore of 100 with a connection pool of
10 mostly creates another queue; neither sets a requests-per-second rate limit.

```mermaid
flowchart LR
    Producer[Finite URL batch] --> Queue[Bounded queue]
    Queue --> Workers[Fixed worker tasks]
    Workers --> Pool[Shared HTTP connection pool]
    Pool --> API[Local controlled API]
```

Backpressure makes the producer wait when the queue is full instead of accumulating
unbounded tasks. In `fulfillhub.aggregation`, one producer feeds a bounded queue;
a fixed TaskGroup worker set shares an HTTPX client whose pool limit matches the
worker count. Per-request deadlines start after dequeueing. Results preserve input
order; timeout, HTTP status and transport failure are distinct outcomes.

The reference still retains the finite input/results and full response bodies.
A streaming production design would also bound payload bytes, output buffering,
batch duration and input admission. Retrying can multiply load; retries, URL trust,
rate limits and response-size policies need explicit contracts rather than hidden
defaults. Parent cancellation cancels and awaits workers before the client closes.

## Engineering decisions and common mistakes

Use structured ownership, bounded work, shared clients, deadline budgets and
observable failure results. Avoid unowned fire-and-forget tasks, per-request client
creation, blanket exception handling, blocking loop calls, sleeps as synchronization,
and a “the GIL makes this safe” explanation. The right design can be slower for a
tiny benchmark while being more predictable under real resource constraints.

[Exercises, interview and mastery assessment](practice.md) ·
[Concurrency project](../project.md) · [Phase overview](../index.md) ·
[Full course roadmap](../../course-plan.md)

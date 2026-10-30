# Module 4 — Concurrency and asynchronous execution

**P0/P1 · free-threaded internals are P2**

Concurrency means multiple activities can make progress during overlapping periods;
parallelism means execution at the same instant. Choose an execution model from the
workload, isolation needs, dependency support and failure behavior—not from whether
the API happens to have an `async` keyword.

## Chapter navigation

Continue with the [failure and backpressure walkthrough](concurrency-patterns.md)
for deterministic experiments, lifecycle traces and capacity/deadline reasoning.

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

### Example — overlap waiting without adding Python execution lanes

```python
import asyncio

async def fetch(label):
    print("start", label)
    await asyncio.sleep(0)
    print("finish", label)
    return label

async def main():
    async with asyncio.TaskGroup() as group:
        first = group.create_task(fetch("A"))
        second = group.create_task(fetch("B"))
    print(sorted([first.result(), second.result()]))

asyncio.run(main())
```

Both calls start, suspend and finish, and the last line is ['A', 'B']. Exact
interleaving is a scheduler detail; the invariant is that both results exist when
the group exits successfully. sleep(0) is a teaching suspension, not network I/O.

A process normally has separate memory and an interpreter; threads share process
memory and use OS scheduling; coroutines share a loop and cooperate at suspension
points. Asyncio overlaps waits rather than executing two Python bodies at once
on the same loop thread. If each body instead computes for a second without
suspending, adding tasks does not turn two seconds of computation into one.

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

### Example — explain why threads help one workload but not another

Consider two tasks that each spend 10 ms in Python and 200 ms waiting on a remote
service. Sequential execution is roughly 420 ms. Threads can overlap much of the
waiting because blocking I/O can release the GIL. Async-capable clients can overlap
it without dedicating a thread to each request. These are illustrative durations,
not a speed guarantee.

Now consider two pure-Python calculations each requiring 200 ms of CPU. Ordinary
GIL-enabled threads compete for execution in one interpreter, so a second core
does not automatically halve elapsed time. A process pool can use separate cores,
but startup, transfer, scheduling and memory may outweigh gains for small jobs.
Native libraries may release the GIL and need different measurement.

The GIL protects interpreter machinery; it does not promise your read/check/write
business sequence is atomic. Free-threaded builds change parallelism possibilities,
not the need for synchronization. Inspect the actual build, active GIL state,
extensions and workload before using a benchmark to choose an execution model.

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

### Example — an endpoint's waiting time reveals the useful optimization

Imagine this sequential request path:

| Step | Illustrative elapsed time |
| --- | ---: |
| Validate input | 2 ms |
| Query PostgreSQL | 100 ms |
| Call vendor | 200 ms |
| Compute domain result | 3 ms |
| Serialize | 2 ms |

The total is 307 ms if these intervals do not overlap. Most time is waiting.
Async I/O can let other requests progress while this one waits; it does not make
PostgreSQL execute its query in 2 ms.

If the vendor request depends on the database result, those two operations cannot
simply run together. If independent, structured concurrent tasks may overlap their
waits. Check the dependency graph before promising lower single-request latency.

An existing blocking SDK can use bounded threads. A large pure-Python transform
may need a process or durable worker. Increasing all concurrency limits can
overload a finite database, making throughput worse and queues longer. Identify
the constraint and the desired metric: one request's duration, aggregate throughput,
tail latency and correctness are related but distinct goals.

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

### Example — a coroutine object is not a running operation

```python
import asyncio

async def fetch():
    print("body")
    await asyncio.sleep(0)
    return "done"

async def main():
    operation = fetch()
    print("created")
    result = await operation
    print(result)

asyncio.run(main())
```

Expected output:

```text
created
body
done
```

Calling fetch creates a coroutine object. Its body starts when main awaits it.
create_task instead schedules the coroutine on the running loop, and the returned
Task owns completion/result/cancellation state. A Future represents a later result,
often used by lower-level I/O integration. All these are awaitable, but not identical.

For three independent 100 ms waits, sequential awaits take roughly 300 ms;
scheduled overlapping waits can take roughly 100 ms plus overhead. Those numbers
are a model, not a performance assertion. Awaiting an already-finished operation
may not suspend at all, so count actual waiting opportunities rather than the
number of await keywords in a function.

### Python 3.14 detail — task startup can be eager

Creating a coroutine object does not run its body. Task creation is a separate
operation, and Python 3.14 supports explicit eager startup:

```python
import asyncio

async def main():
    events = []

    async def immediate():
        events.append("body")
        return 1

    task = asyncio.create_task(immediate(), eager_start=True)
    events.append("after create_task")
    print(events)
    print(await task)

asyncio.run(main())
```

On the course's CPython 3.14 runtime this prints ['body', 'after create_task'],
then 1. The coroutine completed without suspending during task creation. Default
or configured task factories can produce other startup scheduling behavior.

Do not rely on a particular interleaving for correctness. Use explicit events,
locks or ownership when ordering matters. See the
[Python 3.14 create_task contract](https://docs.python.org/3.14/library/asyncio-task.html#asyncio.create_task).

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

### Example — failure stops siblings and cleanup precedes the parent's handler

```python
import asyncio

async def main():
    events = []
    started = asyncio.Event()

    async def waiting():
        events.append("started")
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            events.append("cleaned")

    async def failing():
        await started.wait()
        raise ValueError("deliberate failure")

    try:
        async with asyncio.TaskGroup() as group:
            group.create_task(waiting())
            group.create_task(failing())
    except* ValueError:
        events.append("caught")
    print(events)

asyncio.run(main())
```

Expected output is ['started', 'cleaned', 'caught']. The event ensures the sibling
started before failure. TaskGroup requests sibling cancellation and waits for its
finally block before control reaches the parent handler.

Default gather behaves differently on a child's ordinary exception: it propagates
the exception without automatically cancelling every sibling. The caller must
still own unfinished tasks. Runner shutdown can later cancel them, which must
not be mistaken for gather's failure semantics.

Timeouts also use cancellation under a defined scope. Catch TimeoutError outside
asyncio.timeout, and preserve unrelated caller cancellation. A CPU loop that
never yields cannot be interrupted promptly by a cooperative deadline. Cancelling
an await on running thread work does not kill that thread.

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

### Example — choose the offload boundary, not just a new keyword

```python
import asyncio
import time

def blocking_sdk(value):
    time.sleep(0.01)
    return value * 2

async def main():
    result = await asyncio.to_thread(blocking_sdk, 3)
    print(result)

asyncio.run(main())
```

The final line prints 6. blocking_sdk executes in a worker thread while the loop
can schedule other work. Calling blocking_sdk(3) directly inside main would block
the loop despite main being async. to_thread takes the function and its arguments,
not the already-computed result.

Thread pools suit blocking I/O with explicit capacity/timeouts. Process pools
isolate memory and can parallelize pure-Python CPU work; callable importability,
picklable arguments/results and guarded startup matter. Passing a huge object may
make serialization dominate the calculation.

Python 3.14 also provides InterpreterPoolExecutor in supported CPython builds.
Each worker has isolated interpreter state and a separate GIL, with compatibility
and transfer constraints. Treat it as a P2 alternative after mastering processes,
threads and asyncio; it does not make mutable application objects freely shared
between interpreters.

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

### Example — one blocking handler delays unrelated work

Imagine a single worker receives a five-second blocking operation and a quick
health request immediately afterward. If the first handler calls time.sleep(5)
on the loop thread, the second request's Python code cannot run there until that
thread becomes available. The health handler can be trivial and still look slow.

Replacing a simulated wait with await asyncio.sleep allows scheduling progress.
For a real blocking SDK, use a supported async implementation or bounded offload.
For CPU work, a sleep substitution is not a fix: move or reduce the computation.

FastAPI can offload a normal def path operation through its framework thread
pool. A synchronous helper directly called by an async def path operation is not
automatically offloaded. The execution boundary, not the function's file or name,
determines where it runs.

Diagnose with loop lag, slow callback evidence, CPU and dependency traces.
A healthy downstream plus high loop lag suggests local blocking/CPU work.
Low loop lag plus large pool wait suggests another bottleneck. The existing
heartbeat lab demonstrates the distinction without claiming fixed speed ratios.

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

### Example — show the lost update as a timeline

| Step | Task A | Task B | Shared count |
| --- | --- | --- | ---: |
| 1 | Read 0 | — | 0 |
| 2 | Suspend | Read 0 | 0 |
| 3 | Write 1 | Suspend | 1 |
| 4 | — | Write 1 | 1 |

Both tasks completed, but there was only one effective increment. One loop thread
can have races because the logical operation spans a suspension. This does not
require simultaneous machine instructions.

An asyncio.Lock around the whole read/await/write region coordinates tasks using
that same lock on the same loop. A second API worker has another process and
another lock; it can still race on shared database state. Use a matching database
transaction/constraint/guarded update for that resource.

Keep critical sections small and use a consistent lock order. Holding a lock
while waiting for another task that needs it can deadlock. In the existing
async_patterns lab a barrier makes every unsafe reader observe zero before
writing, so the lost update is reproduced deterministically rather than by hoping
a short sleep yields a particular schedule.

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

### Example — account for every buffer and every owner

Suppose there are 100 jobs, five workers, a queue capacity of ten and an HTTP pool
of five. At most five workers perform calls and at most ten items wait in that
queue. The producer waits when it tries to enqueue more. That is backpressure.

But a list containing all 100 inputs and all completed response bodies still
occupies memory. A bounded queue does not bound arbitrary retained results.
A semaphore around a million already-created tasks limits entry to a region,
not the million task objects themselves.

If there are four API processes each with that pool, potential connections become
twenty. With three replicas they become sixty. Compare the aggregate with the
downstream's real capacity and other clients, not just one process's setting.

Own resources in nested scopes: the application/request owns the client, a task
group owns children, and each worker owns its dequeued item. Await worker cleanup
before closing resources they use. Work that must survive process restart needs
durable acceptance/queue semantics; an unowned create_task call is not that
guarantee. Semaphore, pool, queue, rate limiter and deadline each bound different
dimensions, so describe their combined contract explicitly.

### Validate capacity configuration before creating child work

A positive-value check alone is insufficient. bool subclasses int; fractional
worker counts cannot drive range; NaN does not behave like an ordinary ordered
number; infinity removes the intended finite deadline.

The reference aggregator now requires positive integer worker/queue counts and
a positive finite timeout, rejecting invalid configuration with ValueError before
opening the client or creating workers. Its regression cases cover bool/fractional
counts, strings, NaN/infinity and an unrepresentably large timeout. Validation
does not choose a safe maximum for your deployment: admission/body/output limits
and downstream capacity still need an explicit policy.

## Engineering decisions and common mistakes

Use structured ownership, bounded work, shared clients, deadline budgets and
observable failure results. Avoid unowned fire-and-forget tasks, per-request client
creation, blanket exception handling, blocking loop calls, sleeps as synchronization,
and a “the GIL makes this safe” explanation. The right design can be slower for a
tiny benchmark while being more predictable under real resource constraints.

[Exercises, interview and mastery assessment](practice.md) ·
[Concurrency project](../project.md) · [Phase overview](../index.md) ·
[Full course roadmap](../../course-plan.md)

Continue with [Module 5 — Networking and HTTP](../../phase-3/module-5/index.md).

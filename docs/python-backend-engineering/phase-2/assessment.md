# Phase 2 — Cumulative assessment and model review

**Goal:** connect runtime mechanisms to correct concurrency and defensible
performance decisions. Prerequisites: [Module 3](module-3/index.md),
[Module 4](module-4/index.md), and the [concurrency project](project.md).

Allocate about **100 minutes**: 20 concepts, 35 implementation, 20 debugging,
15 design/measurement and 10 explanation. Use the existing weekly study budget.
Take a first attempt without opening the model answers.

## A. Explain mechanisms — 25 points

Each question is worth five points: correct claim, mechanism, and a concrete limit.

1. A closure and a traceback both retain a large record list. Why might repeated
   collection fail to reduce its memory? What observation distinguishes live owners
   from unreachable cycles or native allocations?
2. A class has a property named `stock` and the instance dictionary also contains
   `stock`. Which wins ordinary lookup, and how is that different from a plain
   function descriptor used to create a bound method?
3. In a diamond hierarchy, why can `super()` inside Left call Right? What fails if
   some classes use cooperative calls and others directly invoke Root?
4. Why is `Sequence[Cat]` usable where a read-only sequence of Animal is required,
   while treating `list[Cat]` as mutable `list[Animal]` is unsafe?
5. One child raises under gather and under TaskGroup. What happens to a waiting
   sibling in each case, and why can `asyncio.run()` shutdown confuse the observation?

??? note "Concept model answers"
    1. Reachable references are still owners; collecting cycles cannot free them.
       Compare retained Python allocations, inspect long-lived holders, and
       separate traced allocation measurements from RSS/native memory.
    2. A property is a data descriptor and precedes the instance dictionary.
       Ordinary functions are non-data descriptors: instance attributes can
       shadow them, and method access binds the instance through `__get__`.
    3. `super()` continues along the actual instance's C3 MRO, not a named parent.
       Direct calls can skip or duplicate cooperative behavior/initialization.
    4. Reading Cats as Animals is safe; appending a non-Cat Animal through a mutable
       alias would violate the original list's contract. Mutation changes variance.
    5. Default gather propagates the child's exception without automatically
       cancelling every sibling. TaskGroup cancels/awaits siblings before leaving
       its failure scope. Runner shutdown can later cancel an unowned task; that
       does not mean gather performed that cancellation.

## B. Add a caller-owned batch deadline — 30 points

Create a wrapper around the existing aggregator in your own solution:

```python
async def aggregate_with_budget(urls, *, budget, transport=None):
    ...
```

Requirements:

- Annotate the interface using `Sequence[str]`, `list[Result]` and the optional
  HTTPX async transport type.
- Require a positive budget. Use the existing aggregator with a per-request
  timeout of ten seconds, so tests can distinguish the shorter batch deadline.
- Include queue wait and worker completion in the total budget scope.
- On batch expiry, raise TimeoutError rather than returning a partial success list.
- Preserve TaskGroup cleanup and parent cancellation propagation.
- Prove a successful ordered batch and a batch whose transport waits indefinitely.

Scoring: **10** for typed API/validation, **10** for deadline and result semantics,
**10** for tests proving cleanup and distinct caller cancellation.

??? note "Reference implementation and test strategy"
    ```python
    import asyncio
    from collections.abc import Sequence
    import httpx
    from fulfillhub.aggregation import Result, aggregate

    async def aggregate_with_budget(
        urls: Sequence[str], *, budget: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> list[Result]:
        if budget <= 0:
            raise ValueError("budget must be positive")
        async with asyncio.timeout(budget):
            return await aggregate(urls, request_timeout=10, transport=transport)
    ```

    A test transport can signal an `asyncio.Event` on entry, increment an active
    count, await an unreleased event, and decrement in `finally`. Batch expiry
    must raise TimeoutError after active work unwinds. For caller cancellation,
    start the wrapper as a task, wait for entry, cancel it, and assert
    CancelledError instead of a successful list or translated timeout.

    Use events to coordinate startup rather than assuming a sleep duration proves
    the request began. Timing supplies the deadline trigger, not a fixed speed
    assertion. Existing aggregation tests demonstrate the cleanup pattern.

    This small solution assumes the annotated numeric caller contract. A public
    configuration boundary would additionally validate non-numeric values, NaN,
    infinity and any bool policy before calling it. State that scope explicitly.

## C. Diagnose two failures — 20 points

**Ten points — Lost update:** twenty successful tasks leave a counter at one.
Reproduce the read/await/write interleaving with a barrier, repair it using a shared
async lock or single-owner design, and show the count becomes twenty. Explain why
this does not fix two independent API worker processes.

**Ten points — Event-loop blocking:** unrelated requests stop making progress
while one coroutine calls a synchronous SDK. Show the heartbeat symptom, identify
the blocking operation and choose a correction. Bounded threads fit blocking I/O;
pure Python CPU work may need processes on standard CPython. Explain why cancellation
of the await cannot forcibly stop an already-running thread.

Full credit requires a reproduction, a matching-scope correction and a limitation.
“Add async” or “add a lock” without identifying the execution model is insufficient.

## D. Evaluate design and performance — 15 points

- **Five points:** choose worker, queue and pool limits for a vendor client. State
  what remains unbounded: retained input/results, full response bytes and total
  batch time unless separately capped. Distinguish limits from a rate limiter.
- **Five points:** compare list membership vs an index with equivalent outputs,
  input sizes, repeated measurements and construction cost included. Interpret
  incremental traced allocations separately from RSS.
- **Five points:** decide whether a descriptor, property, class decorator,
  subclass hook or metaclass fits a reusable attribute/registration requirement.
  Prefer the smallest mechanism that satisfies the actual requirement.

Do not award speed points for a noisy single run or for a candidate that drops
duplicate queries and therefore computes a different result.

## E. Explain the investigation — 10 points

Present **symptom → hypothesis → reproduction → evidence → correction → remaining
limits**. State interpreter/version/GIL context when relevant. Acknowledge what you
have not measured. Explain your deadline/error/partial-success contract in terms
the calling service can act on.

## Completion and revision

Target **80/100**. Concurrency bound violations, leaked child tasks, swallowed
cancellation, or incorrect state require revision regardless of the numerical
total. Record score and evidence in [progress](../progress.md), including which
cases you implemented yourself rather than only running supplied examples.

For weak runtime explanations, repeat the
[runtime investigations](module-3/runtime-investigations.md). For unclear lifecycle
behavior, trace the [failure walkthrough](module-4/concurrency-patterns.md) before
adding more features. Use the [debugging playbook](debugging-playbook.md) to organize
your next experiment.

[Phase overview](index.md) · [Project](project.md) · [Full roadmap](../course-plan.md)

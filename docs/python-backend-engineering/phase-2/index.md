# Phase 2 — Advanced Python and internals

**Weeks 2–3 · P0/P1, selected P2** · Prerequisite: [Phase 1](../phase-1/index.md).

Connect language behavior to runtime mechanisms, then choose concurrency based on
workload and ownership. Descriptors and profiling are practical P1 skills;
metaclass machinery and free-threaded internals are a conceptual P2 first pass.

| Module | Chapters | Deliverable |
| --- | --- | --- |
| [3 — Python data model and runtime](module-3/index.md) | Lifecycle, CPython, memory, descriptors/MRO, class creation, typing, functional style, serialization, profiling | [Service interface, runtime investigation, refactor](module-3/practice.md) |
| [4 — Concurrency and asynchronous execution](module-4/index.md) | Execution models, GIL, workloads, scheduling, structured tasks, executors, blocking, races, backpressure | [Bounded API aggregator and diagnosis](module-4/practice.md) |

## Worked study route

1. [Runtime investigations](module-3/runtime-investigations.md): connect retained
   references, code objects, descriptors, MRO, decorators, and measured complexity.
2. [Failure, cancellation, and backpressure](module-4/concurrency-patterns.md):
   reproduce races and compare gather/TaskGroup with deterministic coordination.
3. Use the [debugging playbook](debugging-playbook.md) to plan experiments, then
   attempt the [cumulative assessment](assessment.md) before opening its solutions.

## Practical project

Complete the [concurrency and performance project](project.md). Extend Phase 1's
service interface, profile a bounded workload, and build an HTTP aggregation client
against a controlled local API. Demonstrate timeout behavior, cancellation, bounded
in-flight work, and deliberate event-loop blocking.

## Checkpoint

- [ ] Explain object lifetime without treating reference counts as a language guarantee.
- [ ] Trace descriptor precedence, method binding, and cooperative MRO.
- [ ] Substitute two repositories and pass strict typing plus contract tests.
- [ ] Record profiler evidence and distinguish allocation peaks from process RSS.
- [ ] Select threads, processes, or asyncio for a concrete workload.
- [ ] Prove timeout, failure, and parent cancellation behavior with tests.
- [ ] Demonstrate event-loop blocking and the appropriate correction.
- [ ] Score at least 80/100 and record evidence in [progress](../progress.md).

[Subject overview](../index.md) · [Previous: Phase 1](../phase-1/index.md) ·
[Full roadmap](../course-plan.md)

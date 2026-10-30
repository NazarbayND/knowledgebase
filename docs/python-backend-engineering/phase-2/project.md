# Phase 2 project — Runtime diagnosis and concurrent API aggregation

Extend the [inventory package](../phase-1/project.md) with a reusable typed boundary
and a runtime investigation, then build a bounded aggregation client. The local
API is a controlled fixture; implementing FastAPI endpoints belongs to later phases.

## Part A — Interface and profiling

Keep the two inventory adapters substitutable. Draw their import dependencies,
explain ownership and run strict mypy plus the shared contract tests. Use
`fulfillhub.runtime_lab` to inspect the actual interpreter and allocations. Add a
small repeated-membership benchmark and compare list scans against a set, including
set construction. Preserve equivalent outputs and record repeated measurements.

Deliver a short profile report, one justified refactor, and the regression test
that protects behavior. A speed claim without measurements is not an acceptance result.

## Part B — Aggregation contract

- Accept a finite ordered sequence of trusted URLs.
- Limit worker count, queue capacity and HTTP connection pool size.
- Reuse one async HTTP client and preserve result order.
- Apply a per-request deadline and distinguish timeout, transport, and HTTP errors.
- Return explicit per-endpoint failure results while allowing unexpected defects
  to fail the batch and cancel siblings.
- Propagate parent cancellation after awaited worker cleanup.
- Demonstrate a blocked event loop and compare the appropriate nonblocking approach.
- Test real HTTP on loopback as well as deterministic transport scenarios.

The reference lives in `aggregation.py` and `concurrency_lab.py` under
`examples/python-backend-engineering/src/fulfillhub/`.

## Run the reference

Working directory: `examples/python-backend-engineering/`.

```bash
uv sync --frozen
uv run --frozen python -m fulfillhub.runtime_lab
uv run --frozen python -m fulfillhub.concurrency_lab
uv run --frozen python -m fulfillhub.concurrency_lab --executors
uv run --frozen pytest
uv run --frozen mypy
uv run --frozen ruff check .
uv run --frozen ruff format --check .
```

The HTTP lab starts/shuts down its own temporary loopback server. Expected behavior:
both worker settings return eight successful results; the deliberate slow endpoint
becomes `timeout`, the failure endpoint becomes status 503/`http_status`; blocking
mode permits substantially less heartbeat progress. Exact elapsed times and turn
counts depend on the machine and are observations. The executor lab checks equal
results and reports timing without assuming a process-speed advantage.

## Acceptance and failure experiments

| Experiment | Evidence |
| --- | --- |
| Queue capacity one, multiple workers | Peak active requests stays within worker bound; every result remains ordered |
| Endpoint waits forever | Per-request timeout completes with an explicit timeout result |
| HTTP 503 or connect error | Distinct status/transport results; no silent success |
| Parent cancelled while workers wait | CancelledError propagates, active requests unwind, worker tasks finish |
| Unexpected handler defect | TaskGroup raises an ExceptionGroup and cancels siblings |
| Blocking work next to a heartbeat | Observable scheduling loss; async/threaded correction explained |
| CPU workload in thread/process pools | Same output; report overhead and runtime/GIL context |
| Read/await/write shared counter | Reproduce race, repair with appropriate ownership/lock, explain cross-process limit |

The suite implements the aggregator contract and local HTTP integration checks.
The membership benchmark and race repair are explicit learner extensions. Do not
claim them complete just because the reference suite passes.

## Capacity and deadline review

The queue bounds pending work, not retained output bytes. The reference loads full
responses and keeps the finite batch/results in memory. Its request timeout begins
after dequeue, so total batch time can exceed one request timeout. Cancellation
cannot immediately interrupt non-yielding CPU code or kill a running thread.

Propose production limits for allowed destinations, response sizes, batch deadlines,
streamed results, rate limiting, retries and observability. Explain the cost of
each; do not add unrelated infrastructure to this phase's demonstration.

Deliver tests, a before/after diagnosis report, commands/results, resource limits,
and open risks. Assess using [Module 4's rubric](module-4/practice.md#mastery-assessment)
and record evidence in [progress](../progress.md).

[Phase 2 overview](index.md) · [Whole-course plan](../course-plan.md)

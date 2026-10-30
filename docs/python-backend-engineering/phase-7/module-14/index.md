# Module 14 — Operational reliability

**P1 with P0 debugging foundations · prerequisite: request and dependency lifetimes**

Reliability engineering connects user-visible outcomes to measurements and recovery.
Collecting telemetry is only useful if it helps distinguish hypotheses and decide
what to do. A dashboard full of averages cannot explain every tail-latency incident.

## Chapter navigation

1. [Logs, metrics and traces](#logs-metrics-and-traces)
2. [Instrumentation and propagation](#instrumentation-and-propagation)
3. [Latency and capacity](#latency-and-capacity)
4. [SLIs, SLOs and error budgets](#slis-slos-and-error-budgets)
5. [Health probes](#health-probes)
6. [Load tests and resource exhaustion](#load-tests-and-resource-exhaustion)
7. [Incident response and prevention](#incident-response-and-prevention)

## Logs, metrics and traces

Structured logs record events with stable fields; metrics aggregate measurements;
traces connect timed operations across boundaries. Correlation/request ids help
search logs; trace/span context explains parent-child timing. A trace does not
automatically include every asynchronous hop or show unsampled failures.

Use logs for relevant transitions/errors, metrics for rates/distributions and
traces for causal paths. Preserve error causes internally while returning safe
public detail. Avoid logging access tokens, raw secrets or unbounded bodies.
Choose retention and access permissions based on sensitivity and usefulness.

## Instrumentation and propagation

OpenTelemetry provides instrumentation and export conventions; collectors can
process/route telemetry to storage backends. Propagate supported trace context
through HTTP and message metadata. A new background task may need an explicit
causal link rather than pretending its lifetime is a synchronous child request.

Prometheus collects time-series metrics; Grafana visualizes sources. Instrument
request rate/errors/duration and dependency/pool/queue signals. Labels such as
raw user ids, order ids or arbitrary paths create high cardinality and cost.
Prefer route templates and bounded dimensions; detailed identities belong in
controlled logs/traces rather than unlimited metric label sets.

Sampling can reduce volume but changes which traces are visible. Record policy
and understand head/tail sampling tradeoffs. Telemetry exporters need bounded
queues and failure behavior so monitoring outages do not exhaust the service.

## Latency and capacity

The median describes a typical request; p95/p99 describe tail thresholds. Do not
average instance-level p99 values to claim a global p99. Use aggregatable histograms
with appropriate buckets or a backend supporting the required distribution merge.
Quantile accuracy depends on the measurement model and bucket resolution.

Separate queue/pool wait, connection setup, remote work, database time, CPU and
serialization. Throughput can stop increasing while latency explodes near a
bottleneck. Low CPU is consistent with lock, pool or downstream waiting.

Little's Law, L = arrival rate × average time in system, is useful for stable
steady-state reasoning with compatible boundaries. It is not an excuse to infer
tail latency or ignore overload. Record offered load and completed throughput.

## SLIs, SLOs and error budgets

An SLI measures a user-relevant outcome. Define good/eligible events and exclusions
explicitly. An SLO sets a target over a window. For an event-based 99.9% success
target over one million eligible requests, the allowed bad-event budget is 1,000.
That calculation is not automatically a time-based availability allowance.

Latency SLIs might count requests completed correctly under a threshold, avoiding
the mistake of calling fast errors good. Distinguish expected caller errors from
server failures under an explicit policy; excluding all inconvenient events can
make the objective meaningless.

Alert on actionable user impact and budget burn. Multi-window burn-rate alerts
can distinguish fast catastrophic consumption from slower sustained degradation.
Avoid paging for every CPU fluctuation without evidence it threatens the service.
An error budget supports release/reliability decisions; it is not permission to
ignore recurring harms until a threshold is crossed.

## Health probes

Liveness asks whether restart may help a stuck process. Readiness asks whether a
workload should receive traffic. Startup probes give initialization a separate
window before normal checks apply. These signals serve different actions.

Making liveness fail whenever PostgreSQL is unavailable can restart every healthy
application during a database incident. Readiness that checks every dependency
can also remove all instances when a service could degrade usefully. Define the
dependency and routing policy rather than copy one endpoint into all probes.

Graceful shutdown withdraws readiness, drains work under a budget and closes
resources. Health checks should be cheap, bounded and reflect the action they cause.

## Load tests and resource exhaustion

Choose realistic distributions: request mix, payload sizes, hot tenants, cache
state and failure rates. Closed-loop clients can reduce offered load as responses
slow, hiding overload; open arrival models reveal different capacity behavior.
Avoid coordinated-omission interpretations that understate time users would wait.

Load tests estimate behavior under expected traffic; stress tests explore limits;
soak tests expose accumulation; profiling investigates causes. Track correctness
as well as latency. A faster run that drops half the work is not an improvement.

Common exhaustion modes include leaked connections, long transactions, retained
task results, unbounded queues, open file descriptors and oversized caches. Compare
live resource ownership and temporal growth. Python allocations, allocator reuse
and process RSS answer different questions, as studied in Phase 2.

## Incident response and prevention

Start with user impact, timeline, recent changes and a bounded mitigation. Gather
evidence before restarting everything and erasing the clues, while prioritizing
safe recovery. Assign communication and decision ownership. Avoid unsupported
causal claims from correlation alone.

A useful postmortem records impact, detection, timeline, contributing conditions,
root-cause reasoning, mitigation and concrete follow-up owners/dates. Include a
regression check or operational guard that would detect/prevent recurrence.
Blaming the last operator does not explain why the system permitted the failure.

## Worked failure analysis

p99 rises while CPU stays low after an export feature. Compare database pool wait,
transaction age and query duration. A stream retaining a session/transaction can
occupy every connection while ordinary queries remain fast once admitted. Bound
export concurrency, shorten persistence lifetime and remeasure the user SLI. Then
test slow clients and cancellation, not only fast local downloads.

[OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/),
[Prometheus practices](https://prometheus.io/docs/practices/) and
[SRE Workbook](https://sre.google/workbook/table-of-contents/) support deeper study.

[Practice](practice.md) · [Phase assessment](../assessment.md) ·
[Next: containers and AWS](../../phase-8/module-15/index.md)

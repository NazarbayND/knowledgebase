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

### Example — three telemetry types answer different questions

For one slow checkout, a metric can show the route's latency/error distribution,
a trace can show pool wait followed by a vendor span, and a log can explain the
specific safe failure code and request identity.

A request id helps find related records; a trace id/span relationship helps
reconstruct timing/causality. A background event may need a link to the originating
trace rather than a fictional synchronous parent that lasted hours.

Do not copy the complete payload into every signal. Use bounded metrics for
aggregate behavior and controlled logs/traces for detail. Sampling means a missing
trace is not proof an operation never happened; retention and access policies
affect what investigators can establish.

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

### Example — label cardinality grows multiplicatively

A request metric labelled by 100 routes, 5 status classes and 10 regions already
has up to 5,000 combinations before method/instance dimensions. Adding an unbounded
order_id can make the series count explode with traffic.

Prefer route templates such as /orders/{id}, not each concrete URL. Put detailed
identities in appropriately controlled logs/traces. Even tenant labels need a
deliberate cardinality/cost decision rather than an assumption that every useful
business field belongs in Prometheus.

OpenTelemetry exporters/collectors also need bounded buffers and outage behavior.
Telemetry must help diagnose a failure, not become an unbounded queue that causes
one. State sampling and propagation policies when interpreting a trace.

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

### Example — a global percentile is not the average of local percentiles

This tiny calculation uses the empirical nearest-rank definition for illustration:

```python
from math import ceil

def p99(samples):
    ordered = sorted(samples)
    return ordered[ceil(0.99 * len(ordered)) - 1]

fast = [10] * 1000
slow = [1000] * 10
print(p99(fast), p99(slow))
print(p99(fast + slow))
```

Expected output is 10 1000, then 10. Averaging the two local p99 values gives
505, which is not the pooled p99. Actual backends/histograms have their own
aggregation/estimation details and bucket accuracy, but quantiles are not
linearly composable.

Also separate queue/pool wait from useful work. Low CPU and high p99 are entirely
compatible with requests waiting on connections, locks or downstream services.
Choose the distribution and boundary before explaining a latency number.

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

### Example — calculate an event budget from an explicit denominator

For 1,000,000 eligible requests and a 99.9% success target, 1,000 bad events fit
the budget. If 750 have already failed under the SLI definition, 250 remain.
That is an event-based calculation, not automatically a time-based outage allowance.

Define whether validation errors, rejected unauthorized actions or partial results
count as eligible/good. A fast 500 should not count as a good latency outcome just
because it was fast. Excluding every inconvenient event makes the target meaningless.

Alert on actionable impact/budget consumption with suitable windows. A CPU
threshold can be useful context but need not justify paging if user outcomes are
healthy. Conversely, low CPU does not make exhausted connection pools acceptable.

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

### Example — one dependency outage should not restart every healthy process

Redis becomes unavailable. The application process is healthy and can serve a
bounded uncached catalogue path. If liveness depends directly on Redis, every
instance may restart, losing warm state and increasing recovery traffic.

Readiness asks whether routing should send work here under the chosen degradation
policy; liveness asks whether restarting this process may help. Startup probes
give initialization a separate allowance. Copying the same remote dependency
check into all three confuses their actions.

Keep checks cheap/bounded and coordinate readiness withdrawal with draining.
An always-green probe that ignores a genuinely unusable listener is also wrong:
the condition must match the operational action, not a universal preference for
green or red.

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

### Example — offered load and completed throughput can diverge

Imagine arrivals stay at 1,000 requests/second while the system completes only
500/second. Pending work grows by roughly 500/second until admission rejects it,
callers abandon it or a resource runs out. Buffering buys time; it does not create
processing capacity.

A closed-loop load generator can send less traffic as responses slow because
its fixed clients wait longer. That may hide overload compared with an open
arrival model. Report offered/accepted/completed work and correctness alongside
latency.

A soak test looks for growth in retained tasks, sessions, queues and memory.
A faster run that silently drops work is not an optimization. Use comparable
input distributions, cache state and measurement boundaries.

## Incident response and prevention

Start with user impact, timeline, recent changes and a bounded mitigation. Gather
evidence before restarting everything and erasing the clues, while prioritizing
safe recovery. Assign communication and decision ownership. Avoid unsupported
causal claims from correlation alone.

A useful postmortem records impact, detection, timeline, contributing conditions,
root-cause reasoning, mitigation and concrete follow-up owners/dates. Include a
regression check or operational guard that would detect/prevent recurrence.
Blaming the last operator does not explain why the system permitted the failure.

### Example — turn an incident explanation into a falsifiable hypothesis

Observation: export traffic increased p99 while CPU stayed low.
Hypotheses: long transactions hold connections; a vendor slowed; the thread pool
is full. Compare transaction age/checkout wait, downstream spans and thread wait
instead of changing all settings at once.

If slow downloads retain sessions, a mitigation can bound export admission.
A correction can shorten persistence lifetime or change the export contract.
Verify with slow consumers/cancellation and resource cleanup, not only a fast
local response.

A postmortem records impact, timeline, contributing conditions, evidence,
mitigation and owned follow-up. "We restarted and it improved" is a useful
observation, not by itself a root-cause proof.

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

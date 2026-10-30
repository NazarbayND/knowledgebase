# Phase 3 — HTTP and request-lifecycle assessment

**Week 4 cumulative checkpoint:** include earlier Python, typing and concurrency
knowledge. Practical project implementation is deferred; this review evaluates
written contracts, mechanisms and debugging reasoning.

## Scenario

A browser submits an order through a TLS proxy. The service commits, its response
is delayed, the browser retries, and two orders appear. During deployment some
streamed responses terminate and database connections remain occupied.

## Tasks and scoring

| Dimension | Evidence | Points |
| --- | --- | ---: |
| Concepts | Explain DNS/TLS/HTTP, ASGI vs WSGI, identity, idempotency and cancellation | 25 |
| Contract correctness | Specify endpoint statuses/errors, durable retry scope, pagination and cache rules | 30 |
| Debugging | Trace duplicate effects and leaked connection lifetimes across commit/disconnect/shutdown | 20 |
| Architecture | Choose proxy trust, worker/pool caps and nested deadlines with assumptions | 15 |
| Communication | Present a request diagram and a concise uncertain-outcome explanation | 10 |

## Model review

A timeout can occur after success, so retry safety belongs at the durable business
boundary. The idempotency claim/outcome and effect must not diverge under concurrency.
Track which hop timed out rather than calling every failure a server timeout.
Sessions/transactions must unwind on failure, and streamed responses need a
termination/resume policy once headers have gone. Withdrawal/draining must precede
resource shutdown, with a bounded cancellation fallback.

Include a Module 1 reference/ownership example and a Module 4 blocking/cancellation
example in your explanation. A process-local dict/lock cannot implement service-wide
idempotency across workers.

## Pass and revision

Target 80/100; correct any claim that a lost response proves no commit or that CORS
authorizes tenant access. Save the diagram, contracts, score and weak topics in
[progress](../progress.md). Keep practical competency pending until a later
implementation supplies observed behavior and tests.

[Phase overview](index.md) · [Project placeholder](project.md)

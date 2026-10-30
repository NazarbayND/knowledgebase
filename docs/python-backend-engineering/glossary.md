# Backend engineering glossary

Use a definition to recover the idea, then follow its lesson for the mechanism
and examples. Similar words often describe different scopes.

## Python and execution

| Term | Meaning |
| --- | --- |
| Binding | Association between a name and an object; rebinding is not mutation |
| Identity | Which particular object a reference denotes, distinct from equal value |
| Ownership | Responsibility for keeping, mutating and releasing a value/resource |
| Iterator | Stateful traversal producing values until exhaustion |
| Generator | A suspended/resumable execution producing iterator values with yield |
| Frame | A call's execution context, including local state and instruction progress |
| Descriptor | Class attribute implementing access hooks such as `__get__`/`__set__` |
| MRO | Method Resolution Order used for inheritance lookup and cooperative super |
| Protocol | Structural static contract for compatible operations |
| Variance | How subtype relationships behave through a generic interface |

Read [Module 1](phase-1/module-1/index.md), [Module 2](phase-1/module-2/index.md)
and [Module 3](phase-2/module-3/index.md).

## Concurrency and resource control

| Term | Meaning |
| --- | --- |
| Concurrency | Overlapping progress of activities, often including waiting |
| Parallelism | Actual simultaneous execution, subject to runtime/resources |
| Coroutine / Task / Future | Async computation / scheduled coroutine owner / eventual result |
| GIL | Interpreter coordination limiting simultaneous Python execution in a conventional CPython interpreter |
| Cancellation | Cooperative request to stop, requiring cleanup and propagation |
| Deadline | End of a defined time budget; distinguish request, queue and batch scopes |
| Backpressure | Downstream capacity limiting upstream admission/production |
| Semaphore | Limit on concurrent entry to a region, not inherently a rate limit |
| Pool | Reused bounded resources such as connections or worker threads |
| Bulkhead | Separate resource budget isolating one workload/failure from others |

Read [Module 4](phase-2/module-4/index.md) and [the debugging playbook](phase-2/debugging-playbook.md).

## HTTP and APIs

| Term | Meaning |
| --- | --- |
| Safe method | Requested semantics do not ask for a state change |
| Idempotent effect | Repeating an operation has the same intended effect under its contract |
| Idempotency key | Durable request identity used to coordinate/recover a repeatable outcome |
| ETag | Representation validator; strong/weak comparison rules depend on the condition |
| Cursor | Continuation state bound to an ordering/filter/access contract |
| WSGI / ASGI | Synchronous web interface / async message-oriented server-application interface |
| Middleware | Behavior around request/application processing with ordering consequences |
| Lifespan | Application startup/shutdown resource scope |
| CORS | Browser cross-origin response-access policy, not object authorization |
| CSRF / XSS | Abuse of automatically attached credentials / execution of injected script in an origin |

Read [Module 5](phase-3/module-5/index.md), [Module 6](phase-3/module-6/index.md)
and [Module 7](phase-4/module-7/index.md).

## Persistence

| Term | Meaning |
| --- | --- |
| Unit of Work | Use-case transaction boundary coordinating related changes |
| Session | Mutable ORM interaction/identity/transaction context, distinct from an engine/pool |
| MVCC | Multi-Version Concurrency Control using versions and visibility rules |
| Snapshot | The database visibility view used by an operation/transaction |
| Lost update | A competing change is overwritten by stale read/compute/write logic |
| Write skew | Writers changing different rows violate a shared read-dependent invariant |
| Selectivity | Fraction/distribution of rows matching a predicate, relevant to access cost |
| Query grain | What one result/intermediate row represents |
| N+1 | Initial query followed by one extra related query per item |
| WAL | Write-Ahead Log used in recovery/replication under configured policies |

Read [Modules 8](phase-4/module-8/index.md), [9](phase-5/module-9/index.md)
and [10](phase-5/module-10/index.md).

## Distributed workflows

| Term | Meaning |
| --- | --- |
| Cache-aside | Read cache; on miss read the source and populate derived data |
| TTL | Time To Live for expiry, not an immediate-consistency guarantee |
| Stampede | Many concurrent misses/refills overload the source |
| Lease | Time-limited authority that can expire while its former holder still runs |
| Fencing token | Ordered authority value enforced by the protected resource |
| Acknowledgement | Confirmation at a specific delivery/processing boundary |
| Visibility timeout | Queue interval after which uncompleted work may be redelivered |
| Outbox | Publication intent committed atomically with a database change |
| DLQ | Dead-letter queue with owned diagnosis and controlled redrive |
| Saga | Durable multi-step local transactions with business compensation |

Read [Modules 11](phase-6/module-11/index.md) and [12](phase-6/module-12/index.md).

## Identity and reliability

| Term | Meaning |
| --- | --- |
| OAuth / OIDC | Delegated access framework / identity layer with defined token semantics |
| PKCE | Proof Key for Code Exchange binding authorization-code redemption to a verifier |
| JWT / JWKS | Signed/encoded token format / published trusted key-set representation |
| Issuer / audience | Authority issuing a token / intended recipient under the verifier policy |
| RBAC / ABAC | Permission decisions based on roles / attributes and policy context |
| SLI / SLO | User-relevant measured indicator / objective over a defined window |
| Error budget | Permitted bad events/time under the explicitly chosen objective |
| Burn rate | Observed bad fraction relative to the allowed fraction, under compatible definitions |
| p99 | 99th-percentile threshold under a specified distribution/estimator |
| Cardinality | Number of distinct metric series/dimension combinations |

Read [Modules 13](phase-7/module-13/index.md) and [14](phase-7/module-14/index.md).

## Delivery and design

| Term | Meaning |
| --- | --- |
| Image / container | Packaged filesystem/configuration artifact / running isolated process set |
| Terraform state | Mapping from configuration identities to remote objects/attributes |
| Pod / Deployment | Replaceable workload unit / controller managing replica and rollout state |
| Readiness / liveness | Routing eligibility / signal that a process restart may help |
| Expand/contract | Staged compatible data/interface evolution before old representation removal |
| Bounded context | Ownership of a domain model and language, not necessarily a process |
| Aggregate | Domain consistency/invariant boundary accessed through a root |
| CQRS / event sourcing | Separation of command/query paths / history as authoritative state basis |
| RPO / RTO | Recovery loss-window objective / useful-service recovery-time objective |
| ADR | Architectural Decision Record preserving context, alternatives and consequences |

Read [Phases 8](phase-8/index.md) and [9](phase-9/index.md). Apply the terms in
[interview practice](phase-10/index.md) through a concrete mechanism, not a list of acronyms.

[Course overview](index.md) · [Curriculum map](curriculum-map.md)

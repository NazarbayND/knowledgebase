# Module 7 — FastAPI application development

**P0 · prerequisite: HTTP semantics, ASGI and typed boundaries**

FastAPI turns typed Python callables into HTTP operations and composes dependency
graphs around them. It helps with validation and documentation; it does not choose
your transaction boundaries, authorize domain objects or make blocking dependencies
asynchronous. The excerpts here explain design and are not a new runnable project.

## Chapter navigation

1. [Routers and dependency graphs](#routers-and-dependency-graphs)
2. [Validation and model boundaries](#validation-and-model-boundaries)
3. [Responses and OpenAPI](#responses-and-openapi)
4. [Middleware and error contracts](#middleware-and-error-contracts)
5. [Lifespan and dependency scopes](#lifespan-and-dependency-scopes)
6. [Execution, authentication and testing seams](#execution-authentication-and-testing-seams)
7. [Large bodies and live connections](#large-bodies-and-live-connections)
8. [Contract evolution](#contract-evolution)

## Routers and dependency graphs

An APIRouter groups operations with a prefix, tags and shared dependencies. Group
by cohesive capability such as orders, not by arbitrary file length. A path
operation declares inputs and delegates application work instead of embedding SQL,
authorization and serialization in one function.

Dependencies form a graph: resolve credentials, construct a trusted principal,
authorize tenant context, acquire request resources and build a service. FastAPI
normally caches a dependency result within the request graph unless configured
otherwise. That is request reuse, not a global singleton or durable cache.

```python
from typing import Annotated
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/v1/orders", tags=["orders"])

def page_limit(limit: int = 20) -> int:
    return min(max(limit, 1), 100)

@router.get("")
async def list_contract(limit: Annotated[int, Depends(page_limit)]):
    return {"limit": limit, "items": []}
```

This small illustration normalizes a limit; a real contract may reject out-of-range
values instead. Choose intentionally and describe it in OpenAPI. Dependencies are
ordinary Python callables; the framework supplies their request-time orchestration.

## Validation and model boundaries

Pydantic v2 models parse/validate external representations. Coercion can be useful
for query strings but dangerous for quantities, identifiers and money. Strictness,
unknown-field policy and constraints are contract choices:

```python
from pydantic import BaseModel, ConfigDict, Field

class CreateOrder(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    product_id: str = Field(min_length=1, max_length=64)
    quantity: int = Field(gt=0, le=1000)
```

Do not assume valid structure proves valid business state. Positive quantity is
input validation; sufficient stock belongs in a transactional domain operation.
Fields can be individually valid while their combination violates a rule.
Untrusted tenant identifiers must be checked against the authenticated principal.

Keep request, domain, persistence and response models distinct when their meanings
diverge. A database password/hash/internal flag must not become a public response
because it exists on an ORM object. Serialization configuration and explicit
response schemas create a reviewable exposure boundary.

## Responses and OpenAPI

Response models specify the shape callers can rely on and can filter fields.
Choose statuses/headers for actual HTTP semantics. Document error responses,
pagination and authentication requirements rather than relying only on happy-path
schema generation.

Generated OpenAPI is an artifact to review, not proof a contract is useful or
backwards compatible. Check nullable vs optional fields, required inputs, enum
values and examples. A response validation failure is usually a server-side
contract defect; do not report it as if the caller submitted invalid input.

## Middleware and error contracts

Middleware surrounds request handling and is appropriate for correlation context,
selected metrics, trusted request metadata and controlled headers. Ordering affects
which exceptions it sees and whether compression/CORS/error headers are applied.
Keep business authorization in explicit dependencies/use cases where resource
context is available.

Translate expected domain errors through handlers into stable public codes.
Preserve internal causes in diagnostic evidence without leaking SQL or traceback
details. Define a consistent structure, for example code, safe message and request
id. Never collapse every exception into HTTP 200 with `success=false`: caches,
clients and monitoring need meaningful status behavior.

## Lifespan and dependency scopes

Application lifespan acquires process-owned resources such as shared HTTP clients
and database engines and closes them during shutdown. Yield dependencies can own
request/use-case resources with cleanup in finally. Each process gets its own
lifespan resources, so deployment scale multiplies pools.

Cleanup timing matters for streaming. FastAPI versions and supported dependency
scope settings affect whether a yield dependency closes around function execution
or the request/response lifetime. Choose supported scope deliberately and verify
it against the eventual pinned version. A stream must not depend on a session
already closed by its owner, and holding a transaction through a slow download can
exhaust a pool.

Do not acquire resources at module import or let a dependency return a global
mutable request session. Importing a module for tests should not connect to a live
database or start a worker.

## Execution, authentication and testing seams

An async route/dependency should use async I/O. Framework-managed sync callables
may be offloaded; ordinary blocking helpers called directly in an async route are
still blocking. Pydantic work, large serialization and domain CPU work also consume
time on an execution path that must be measured.

Authentication dependencies validate credential structure and identity; authorization
dependencies/use cases check scope, tenant membership and object permission. A
dependency override is a useful test seam for identity or a service adapter, but a
test overriding all security behavior cannot prove JWT validation works.

Keep authorization negative cases: absent identity, wrong audience, expired token,
valid identity without role, another tenant's object, and forbidden field changes.
Successful authentication alone proves none of the latter.

## Large bodies and live connections

File uploads need declared size limits at proxy/application boundaries, streaming
or spooling policy, safe filenames and cleanup. Never trust Content-Length alone
or join a caller-supplied filename into an arbitrary writable path. Avoid loading
an unbounded upload into bytes before validating it.

Streaming responses and WebSockets have longer ownership than ordinary handlers.
Bound outbound buffers and message sizes, decide how disconnects cancel producers,
and manage authentication expiry. Once headers are sent, errors need stream-level
termination/resumption behavior rather than a replacement JSON response.

## Contract evolution

Adding a required field breaks old callers; changing validation/coercion can too.
An additive enum value may break exhaustive client matches. Separate internal
refactors from public changes and review schema diffs plus representative client
behavior. Keep old and new application versions compatible with shared database
state during a rolling release.

## Worked failure analysis

A catalogue endpoint now exposes an internal cost field. Check whether the route
returns persistence objects directly and whether its response schema is explicit.
Constrain the response boundary, add a negative exposure assertion, and review
other paths using the same model. Avoid fixing only one sample payload while the
type relationship continues permitting internal fields to escape.

[FastAPI guide](https://fastapi.tiangolo.com/tutorial/),
[dependency scopes](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/)
and [Pydantic validation](https://docs.pydantic.dev/latest/concepts/strict_mode/)
provide version-specific details.

[Practice](practice.md) · [Phase overview](../index.md) ·
[Next: architecture and testing](../module-8/index.md)

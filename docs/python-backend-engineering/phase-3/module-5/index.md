# Module 5 — Networking and HTTP

**P0 · prerequisite: event loops and resource ownership**

HTTP is an application protocol with observable semantics. A reliable API starts
with a contract for requests, responses and retries, then accounts for the network
work required to exchange them. A successful local function call is a much simpler
failure model than a remote operation whose response might be lost.

## Chapter navigation

1. [Connection establishment](#connection-establishment)
2. [Protocol versions and connection reuse](#protocol-versions-and-connection-reuse)
3. [Methods, representations and errors](#methods-representations-and-errors)
4. [Idempotency and caching](#idempotency-and-caching)
5. [Resource contracts and pagination](#resource-contracts-and-pagination)
6. [Identity and browser boundaries](#identity-and-browser-boundaries)
7. [Long-lived communication](#long-lived-communication)

## Connection establishment

A client resolves a hostname through DNS, chooses an address, establishes a
transport connection, negotiates TLS for HTTPS and then exchanges HTTP messages.
DNS caches, connection pools, proxies and resumed TLS sessions can skip/reduce
some work on later requests. A socket is an operating-system endpoint; one Python
coroutine is not necessarily one socket or one connection.

TCP supplies an ordered byte stream with retransmission and congestion control;
it does not preserve your application write boundaries. A receive may contain
part of a message or several messages. Protocol framing tells the receiver where
each HTTP body ends. TLS authenticates the server through certificate validation
and protects data in transit; it does not authorize the caller to view an order.

Investigate DNS, TCP connect, TLS handshake and server response time separately.
“The API is slow” does not identify which boundary is waiting. A connect timeout
differs from a response read timeout, and a timeout does not prove a server did
not perform an operation.

### Example — separate establishing a connection from serving the request

Imagine a cold request with these hypothetical nonoverlapping intervals:

```text
DNS lookup             15 ms
TCP connection         20 ms
TLS negotiation        30 ms
HTTP/application work  80 ms
Total                 145 ms
```

A later request reusing a valid connection might avoid the first three steps, but
the application still needs its 80 ms. DNS caching alone does not reuse a TCP/TLS
session. A pool can also have no free connection, introducing acquisition wait
even when the remote server is fast.

Follow the actual destination through proxies: the browser can negotiate TLS with
an edge while that edge uses another connection/protocol to the application.
A certificate check authenticates the configured server endpoint; it does not
authorize the caller to access an order. This separation prevents "network time"
from becoming an unexplained bucket for database or pool delays.

## Protocol versions and connection reuse

| Protocol | Mechanism | Engineering consequence |
| --- | --- | --- |
| HTTP/1.1 | Persistent connections; typical clients use a pool | Reuse connections; avoid creating a fresh client per request |
| HTTP/2 | Multiplexed streams over one TCP connection | Stream concurrency helps, but TCP packet loss can affect all streams |
| HTTP/3 | HTTP over QUIC, usually over UDP | Independent stream delivery avoids TCP-level cross-stream blocking; deployment support still matters |

Multiplexing does not create unlimited backend capacity. Servers, proxies and
clients set stream/connection limits. HTTP/2 on the browser-to-proxy hop does not
prove the proxy-to-application hop uses HTTP/2. Keep-alive reduces handshake cost
but needs idle timeouts, bounded pools and graceful connection draining.

Do not implement HTTP framing with ad hoc socket string splitting. Use a mature
client/server implementation and understand which hop owns TLS and protocol conversion.

### Example — multiplexing shares a connection, not unlimited capacity

Suppose a browser requests three resources. With HTTP/1.1, a client commonly uses
several pooled connections to overlap requests. With HTTP/2, streams can share
one connection without waiting for the previous response body to finish first.

That does not mean three CPU-heavy handlers execute in parallel on one event-loop
thread. It also does not remove TCP loss effects across that connection. HTTP/3
changes the transport to QUIC and can avoid TCP's cross-stream delivery blocking,
while application limits and downstream waits remain.

When diagnosing a waterfall, identify which hop negotiated which protocol and
whether waiting is at connection acquisition, transport delivery, application
scheduling or the database. "We enabled HTTP/2" is not evidence that the slow
part was on the HTTP/1.1 hop.

## Methods, representations and errors

GET/HEAD are safe: their requested semantics do not ask for a state change.
PUT/DELETE are idempotent in intended effect, though repeated responses can differ.
POST generally creates/processes under server-selected semantics. PATCH applies
a partial modification and is not inherently idempotent. GET requests can still
produce logs/metrics; “safe” describes requested resource semantics.

```http
POST /v1/orders HTTP/1.1
Content-Type: application/json
Accept: application/json
Idempotency-Key: checkout-42

{"product_id":"p-7","quantity":2}
```

Content-Type describes the submitted representation; Accept states what response
types the client can consume. Choose meaningful statuses: 201 for creation, 202
for accepted asynchronous work, 204 for a successful empty response, 400/422 for
the chosen malformed/invalid request policy, 401 for missing/invalid authentication,
403 for denied permission, 404 for absent/concealed resources, 409 for a state
conflict, 429 for rate limits and 5xx for server/dependency failures.

Return a stable error structure with a machine-readable code, safe detail and
request identifier. Avoid leaking stack traces, SQL or credentials. A response
schema must describe failures as deliberately as success.

### Example — status and representation tell the client what happened

```http
POST /v1/orders
Content-Type: application/json
Idempotency-Key: checkout-42

{"product_id":"p-7","quantity":2}
```

An illustrative success is:

```http
HTTP/1.1 201 Created
Location: /v1/orders/o-9
Content-Type: application/json

{"id":"o-9","status":"accepted"}
```

The method requests creation/processing, Content-Type defines the submitted data,
201 says a resource was created, and Location identifies it. A background workflow
may still be pending; created does not mean shipped.

For insufficient stock, choose a documented conflict/domain error rather than
returning the same success shape. Clients, monitoring and caches need meaningful
statuses. Authentication failure, authorization denial and malformed input have
different recovery actions; do not collapse them all into one generic 400.

## Idempotency and caching

If the server commits an order and the response is lost, retrying POST can create
a duplicate. An idempotency key needs a scope, payload fingerprint, retention
policy, atomic claim and stored outcome. Reusing a key with a different payload
should conflict; merely putting a key in a Python dictionary is not a durable
multi-worker guarantee. Idempotency concerns effects, not identical byte responses.

ETags are representation validators. A client can send If-None-Match for a cache
revalidation and receive 304 without a representation body. If-Match can protect
an update from overwriting a representation that has changed; an unmet precondition
can return 412. The validation and update need a matching atomic storage boundary.

Cache-Control distinguishes max-age, public/private, no-cache and no-store.
No-cache permits storage but requires validation before reuse; no-store prohibits
storage by compliant caches. Vary identifies request headers affecting the selected
representation. Personalized responses and authorization need explicit cache-key
and shared-cache policies to avoid cross-user disclosure.

### Example — a timeout can happen after a successful commit

```text
Client          API                Database
POST key=42  →  insert order     →  commit o-9
             × response connection lost
POST key=42  →  recover saved outcome o-9
```

The retry should recover the same intended effect under the idempotency contract.
The key must be scoped, tied to a request fingerprint and claimed/stored atomically
with the relevant business outcome. A new payload under the same key should not
silently reuse an unrelated order. A process-local dictionary cannot cover worker
crashes or concurrent processes.

Caching solves a different problem. GET with If-None-Match can receive 304 when
the representation is unchanged. An update with If-Match can receive 412 when
its observed version is stale. Cache validation and write preconditions use version
knowledge, but neither replaces the transaction enforcing the change. No-cache
allows storage with revalidation; no-store prohibits compliant storage.

### Worked exchange — revalidation differs from a write precondition

A cached representation has a strong validator "product-v8". The client can
revalidate a read:

```http
GET /v1/products/p7
If-None-Match: "product-v8"

HTTP/1.1 304 Not Modified
ETag: "product-v8"
```

No representation body is sent with 304. For a write, If-Match asks the server
to apply the change only if the expected strong validator still matches:

```http
PATCH /v1/products/p7
If-Match: "product-v8"
Content-Type: application/json

{"name":"Updated"}
```

If version 9 is current, the precondition fails with 412 rather than overwriting
it. The storage check and write must share the required atomic boundary.
Idempotency keys solve a different retry/outcome problem.

Weak ETags, such as W/"product-v8", allow weaker representation equivalence for
appropriate cache validation; If-Match uses strong comparison. Do not treat a
weak tag as a valid optimistic-write version just because its text looks familiar.
Malformed syntax, unsupported request media type (415) and unavailable acceptable
response representation (406) also describe different contract failures.

## Resource contracts and pagination

REST-style resources should have stable identifiers and clear relationships.
Define writable fields, immutable fields, filters, sorting, limits and error
semantics. Avoid coupling public schemas directly to ORM models. Versioning may
use paths or negotiated representations; additive changes can still break clients
that incorrectly assume exhaustive enum values or strict unknown-field rejection.

Offset pagination is simple but deep offsets may be costly and concurrent inserts
can shift results. Keyset/cursor pagination continues after a stable ordering key:

```sql
SELECT id, created_at
FROM orders
WHERE tenant_id = :tenant
  AND (created_at, id) < (:last_created_at, :last_id)
ORDER BY created_at DESC, id DESC
LIMIT :page_size;
```

This is an illustrative query: the first page omits the cursor predicate. Use a
tie-breaker such as id and a compatible index. An opaque cursor should bind its
filters/order and validate its structure; signing is useful when integrity matters.
Cursor paging does not itself guarantee a snapshot across many requests.

### Example — pagination needs a tie-breaker and a consistency promise

Suppose orders sort newest first:

```text
id    created_at
o-9   12:00:00
o-8   12:00:00
o-7   11:59:00
```

A cursor containing only 12:00:00 cannot distinguish the first two positions.
Ordering by created_at and id, and carrying both values in the continuation
predicate, makes the next boundary deterministic. Bind the cursor to the tenant,
filters and sort contract; an arbitrary caller-supplied cursor must not escape
authorization.

Offset paging can skip/repeat items if new rows shift earlier pages. Keyset paging
reduces that shifting problem but does not automatically freeze the whole dataset.
If clients require a stable export snapshot, design that separately. The first
page and subsequent cursor pages must use the same ordering and access rules.

## Identity and browser boundaries

A session cookie can identify server-side session state; a bearer token grants
access to whoever presents it. Authentication establishes an identity; authorization
checks whether that identity may perform this action on this resource. A tenant
header or tenant path parameter is a requested context, not trusted permission.

CORS constrains browser cross-origin response access; it is not backend access
control and does not stop non-browser clients. Credentialed browser requests need
specific allowed origins and deliberate cookie settings. CSRF exploits automatically
attached credentials; use appropriate SameSite policies and anti-CSRF mechanisms
for cookie-authenticated state changes. XSS executes script in the application's
origin and can undermine other controls; HttpOnly reduces cookie script access,
not all consequences of script execution.

### Example — a permitted origin is not permission to read an object

A browser at app.example sends a request for tenant B's order using user A's
credentials. The server allows app.example through CORS. That only permits the
browser to expose an allowed cross-origin response; it does not establish that
user A belongs to tenant B.

The backend must verify identity and authorize tenant/object access before
returning data. A non-browser script is not constrained by browser CORS policy.
For cookie-based state changes, automatically attached credentials create a
separate CSRF concern. HttpOnly reduces cookie reading by scripts, but XSS can
still initiate actions in the application's origin.

Trace each control to its threat: CORS, CSRF, XSS, authentication and object
authorization overlap operationally but do not substitute for one another.

## Long-lived communication

| Pattern | Fit | Operational costs |
| --- | --- | --- |
| Long polling | Occasional updates with ordinary HTTP behavior | Repeated requests, reconnect load, timeout coordination |
| SSE | Server-to-client event stream | Reconnect/resume identifiers, buffering, client limits |
| WebSocket | Bidirectional low-latency messages | Connection state, message limits, heartbeat, auth renewal, backpressure |

Streaming is not a reason to omit resource limits. Proxies may buffer, idle timeouts
may cut quiet connections and slow consumers can retain data indefinitely. Define
resume/loss behavior: an SSE event id is not proof the application persisted every
event or the consumer processed it.

### Example — reconnecting is not the same as recovering delivery

For an SSE order-status stream, the client might receive event 17 and disconnect
before processing it. On reconnect it sends its last processed event identity.
The server needs a retention/resume contract to decide which events to replay.

If only an in-memory broadcast exists, reconnect may restore the socket while
lost history remains lost. If processing can repeat, clients need idempotent
application of updates. A WebSocket adds bidirectional messages, but not automatic
durability, ordering across reconnects or unlimited buffers.

Choose SSE for a one-way feed when it fits, and WebSocket when bidirectional
interaction earns the extra connection/message lifecycle. Define idle heartbeats,
authentication expiry, proxy buffering and slow-consumer limits in either case.

## Worked failure analysis

An order exists twice after the client timed out. First separate an unknown outcome
from a confirmed failure. Trace the request id and idempotency key through proxies
and the commit boundary. Check whether retries occurred at several layers and
whether the key and business write were persisted atomically. Correct the effect
contract before increasing timeouts; longer waiting alone cannot make duplicate
side effects safe.

## Sources and next step

Use the [MDN HTTP guide](https://developer.mozilla.org/en-US/docs/Web/HTTP),
[HTTP semantics](https://www.rfc-editor.org/rfc/rfc9110) and
[HTTP caching](https://www.rfc-editor.org/rfc/rfc9111) for precise protocol rules.

[Practice and assessment](practice.md) · [Phase overview](../index.md) ·
[Next: web-server architecture](../module-6/index.md)

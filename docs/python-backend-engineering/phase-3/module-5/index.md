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

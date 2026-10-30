# Module 5 — Practice and assessment

Use the [chapters](index.md) to explain the mechanism before proposing a library.
These are written/design exercises; a running API project is deferred.

## Exercises

1. Draw DNS → connection → TLS → HTTP for a cold request and a pooled request.
   Mark which durations a client might measure and which caches can change them.
2. Specify create/read/update/delete contracts for orders: method, status,
   headers, representation, validation errors and retry behavior.
3. Trace “commit succeeds, response lost, client retries.” Design an idempotency
   key record with tenant scope, payload fingerprint, status and stored result.
4. Design conditional catalogue reads and updates using ETag, If-None-Match and
   If-Match. Explain 304 vs 412 and the required atomic update boundary.
5. Compare offset and cursor pagination while new orders arrive. Include a stable
   tie-breaker and state whether the API promises snapshot consistency.
6. Review cookie-authenticated and bearer-token clients for CORS/CSRF/XSS risks.
   Explain why allowing an origin never authorizes access to another tenant.
7. Choose SSE or WebSocket for order notifications. Specify reconnection,
   authentication expiry, slow consumers and proxy timeout behavior.

??? note "Model reasoning"
    A warm pooled request can avoid DNS/connect/TLS work; those savings do not
    reduce database time. Retry-safe effects require a durable atomic key/write
    relationship. Cache validators identify a representation/version; they are
    neither authentication nor a replacement for a storage precondition. Cursor
    paging needs deterministic order and filter binding but is not automatically
    a multi-page snapshot. SSE fits one-way notifications; WebSockets earn their
    complexity when bidirectional messages are required.

## Interview questions

- Is DELETE idempotent if the second response is 404? Explain effect vs response.
- Can a POST be safely retried? Under what server contract?
- Why does HTTP/2 not remove every head-of-line delay?
- What is the difference between no-cache and no-store?
- Why is CORS neither authentication nor server-to-server protection?

??? note "Answer guide"
    DELETE's intended final effect can remain the same despite different statuses.
    A POST can expose an explicit idempotent contract using stable keys and atomic
    outcomes. HTTP/2 shares TCP delivery across streams. No-cache requires reuse
    validation; no-store disallows storage. CORS is enforced by cooperating browsers
    and does not prove a requester's identity or permission.

## Mastery assessment

Use 25 points for protocol mechanisms, 30 for a precise endpoint/cache/pagination
contract, 20 for duplicate-order diagnosis, 15 for transport/streaming tradeoffs
and 10 for a concise walkthrough. Target 80/100. Do not claim safe retries if you
cannot identify the business write and durable idempotency boundary.

Record written evidence in [progress](../../progress.md). Implementation competency
remains unverified until the deferred project is independently implemented/tested.

[Module 5](index.md) · [Next: Module 6](../module-6/index.md)

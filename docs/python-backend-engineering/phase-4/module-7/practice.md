# Module 7 — Practice and assessment

## Exercises

1. Specify routers/dependencies for tenants, products and orders. Mark which
   dependencies supply identity, authorization, request resources and services.
2. Write request/response schemas on paper for order creation. Reject bool/string
   quantities under an explicit strict policy, unknown writable fields and an
   attempt to supply a server-owned order status.
3. Map invalid input, absent product, insufficient stock, denied tenant and
   unexpected persistence failure to a stable documented error contract.
4. Trace shared-client startup, request-session creation, streaming and shutdown.
   Identify where dependency cleanup timing could invalidate the stream.
5. Plan negative authorization and response-field exposure cases. State which
   tests can override identity and which must exercise real token validation.
6. Review an upload/WebSocket contract for size limits, buffering, cleanup,
   authentication expiry and client disconnects.

??? note "Model reasoning"
    A trusted principal must come from credential validation; a tenant header is
    only requested context. Strict schemas reject unintended coercion but cannot
    establish stock availability. Use explicit response models for exposure and
    expected domain-error translations for stable clients. Resource scope must
    outlive every consumer while avoiding long-held transactions. Override seams
    isolate route behavior, whereas identity integration checks verify the actual
    verifier. Large/long-lived inputs need limits beyond ordinary schema fields.

## Interview questions

- What does FastAPI dependency caching mean, and what does it not mean?
- When should validation happen in Pydantic versus the domain service?
- Why can returning an ORM object create a security/contract risk?
- Is a dependency override enough to test authentication?
- Why can a tiny handler still block its event loop?

??? note "Answer guide"
    Request-graph reuse is not a singleton or distributed cache. Representation
    checks precede domain/state invariants. ORM fields and relationships are not
    automatically a safe public schema. Overrides bypass the replaced behavior.
    Sync helpers, serializers and CPU work remain potential blockers even inside
    an async handler.

## Self-check before the assessment

A streaming response reads from a yield dependency. Compare function and request scope, then explain why a business commit should not be postponed until after a successful response.

??? note "Model answer and a five-point check"
    Function scope closes before response sending; request scope extends through the request/response lifetime in versions supporting that contract. A stream cannot use a closed resource, but retaining transactions for slow consumers can exhaust pools. Commit the use case before reporting successful effects; cleanup still rolls back failures/uncommitted work and releases resources. Check the selected FastAPI version.

    Award up to two points for the correct outcome, two for the mechanism, and
    one for a relevant limit or counterexample. Record hints honestly. This is
    a retrieval drill, not a replacement for the full module assessment.

Use the [assessment guide](../../assessment-guide.md) for the shared scoring
anchors and evidence rules.

## Mastery assessment

Use 25 for framework mechanisms, 30 for schemas/dependency/error correctness,
20 for exposure/cleanup diagnosis, 15 for execution/evolution choices and 10 for
communication. Target 80/100. Submit a reviewed API contract and negative-case
matrix; a running service remains part of the [deferred project](../project.md).

[Module 7](index.md) · [Next: Module 8](../module-8/index.md)

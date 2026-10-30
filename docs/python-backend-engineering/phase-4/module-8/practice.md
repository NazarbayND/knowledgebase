# Module 8 — Practice and assessment

## Exercises

1. Draw domain/API/ORM boundaries for an order. Show one field present only at
   each boundary and justify any shared types rather than copying mechanically.
2. Specify a place-order Unit of Work containing stock, order and event writes.
   Define rollback behavior if each step fails; identify which component commits.
3. Explain Session vs engine/pool and propose lifetimes for sync/async variants.
   Diagnose two concurrent tasks sharing an AsyncSession.
4. Design unit, PostgreSQL integration, contract and end-to-end test cases for
   order creation. Name which guarantee each case can actually establish.
5. Plan isolated configuration and ephemeral-service readiness. Explain why a
   SQLite substitute cannot prove PostgreSQL row-lock or isolation behavior.
6. Write a safe refactoring sequence from a large route handler to a service and
   adapter while preserving status/error/schema behavior.

??? note "Model reasoning"
    The use case owns the multi-effect transaction; repositories should not each
    commit independently. Engines/pools live longer than per-use-case sessions.
    An AsyncSession is mutable transactional state, not a concurrent-query mailbox.
    Unit tests explain decisions; real adapter tests exercise database semantics;
    HTTPX ASGI tests do not prove TLS/proxy behavior. Introduce boundaries under
    characterization tests and retain a representative real integration path.

## Interview questions

- Should a repository commit its own transaction?
- When is a separate domain model worth the mapping code?
- Why can serialization fail after the route already returned an ORM object?
- What can a test with ASGITransport miss?
- How would you refactor safely without building microservices first?

??? note "Answer guide"
    Commit belongs to the use-case invariant, not each storage call. Distinct
    models earn their cost when meaning/exposure/lifecycle differ. Lazy/expired
    ORM attributes may require unavailable I/O during serialization. In-process
    transport bypasses network/proxy behavior and may need explicit lifespan.
    A modular monolith with explicit seams supports incremental refactoring.

## Self-check before the assessment

Repository A commits stock, then repository B fails inserting the order. Can a rollback in B's session restore A, and where should the transaction owner be?

??? note "Model answer and a five-point check"
    No: B cannot undo A's already committed transaction. The use case needs one Unit of Work for the related stock/order/outbox effects, with repository operations inside it. An allocation statement returning no row must abort the order path. External payment remains another boundary requiring its supported idempotency/workflow contract.

    Award up to two points for the correct outcome, two for the mechanism, and
    one for a relevant limit or counterexample. Record hints honestly. This is
    a retrieval drill, not a replacement for the full module assessment.

Use the [assessment guide](../../assessment-guide.md) for the shared scoring
anchors and evidence rules.

## Mastery assessment

Use 25 for ownership/architecture mechanisms, 30 for an internally consistent
transaction and test design, 20 for partial-write diagnosis, 15 for abstraction
tradeoffs and 10 for communication. Target 80/100. A repository diagram alone is
insufficient without failure and commit behavior.

[Module 8](index.md) · [Phase review](../assessment.md)

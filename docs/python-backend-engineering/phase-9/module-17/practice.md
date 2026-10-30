# Module 17 — Practice and assessment

## Exercises

1. Map catalogue, inventory, orders, identity and notifications as capabilities.
   Define their terms, owned data and synchronous/event relationships.
2. Identify stock/order invariants and propose aggregate/transaction boundaries.
   Compare a giant tenant aggregate with smaller contention-aware boundaries.
3. Review a service interface using SOLID with concrete callers and behavioral
   substitution tests. Remove one abstraction that earns no useful isolation.
4. Write an ADR comparing a modular monolith and service extraction for one team.
   Include an evidence-based revisit trigger and data migration consequences.
5. Choose Repository, Strategy, Adapter or Factory for four specific problems.
   Explain when a function is enough and when richer lifecycle/state warrants a type.
6. Compare ordinary state + audit/outbox, CQRS projections and event sourcing.
   Include replay, event evolution, stale reads and retention/privacy concerns.

??? note "Model reasoning"
    Contexts own meanings and data, not just folders. Aggregates should fit actual
    invariants without serializing unrelated work. Substitution requires behavior,
    not only signatures. A modular monolith often preserves local transactions
    while enforcing useful boundaries. Patterns express a need rather than confer
    quality. Outbox events do not automatically make the model event-sourced.

## Interview questions

- When would you choose microservices, and what evidence would change your mind?
- Can two contexts exist in one deployable application?
- Why can a shared database undermine independent service deployment?
- Is CQRS the same as event sourcing?
- What makes an ADR useful six months later?

??? note "Answer guide"
    Scaling/ownership/release isolation can justify services when operating ability
    matches. Contexts and deployments are different boundaries. Shared schemas
    and coordinated changes create coupling. CQRS separates reads/writes; event
    sourcing changes the authoritative state model. ADRs preserve assumptions,
    rejected alternatives, consequences and revisit evidence.

## Mastery assessment

Use 25 for boundary/pattern mechanisms, 30 for invariant/data ownership coherence,
20 for distributed-coupling diagnosis, 15 for architectural tradeoffs and 10 for
communication. Target 80/100. Written design competence does not imply the
deferred architecture project has been implemented or operated.

[Module 17](index.md) · [Next: Module 18](../module-18/index.md)

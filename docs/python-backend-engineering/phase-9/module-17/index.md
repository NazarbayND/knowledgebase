# Module 17 — Software architecture

**P1 · CQRS/event-sourcing implementation is selected P2**

Architecture manages change, invariants and operational ownership. A useful design
explains why a boundary exists, which decisions belong inside it and what evidence
would justify changing it. Folder count and service count are poor proxies for
engineering quality.

## Chapter navigation

1. [Cohesion, coupling and SOLID](#cohesion-coupling-and-solid)
2. [Bounded contexts and domain language](#bounded-contexts-and-domain-language)
3. [Aggregates and consistency](#aggregates-and-consistency)
4. [Deployment boundaries](#deployment-boundaries)
5. [Patterns as local tools](#patterns-as-local-tools)
6. [CQRS and event sourcing](#cqrs-and-event-sourcing)
7. [Decision records and design reviews](#decision-records-and-design-reviews)

## Cohesion, coupling and SOLID

Cohesion means related responsibilities live together; coupling measures how much
one component must know about another. A highly cohesive module can still expose
a badly coupled interface. Look at reasons to change, dependency direction,
shared mutable data and coordination costs.

Single responsibility concerns a coherent reason to change, not “one method per
class.” Open/closed encourages extension through stable seams rather than editing
every caller. Liskov substitution concerns observable behavioral contracts: an
implementation that silently drops saves does not satisfy a repository contract
merely because its method types match.

Interface segregation prefers focused client contracts; dependency inversion
keeps high-level rules from requiring concrete infrastructure. These principles
can conflict with simplicity if applied mechanically. A three-line pure helper
does not need a factory hierarchy; a storage boundary with two real adapters and
contract tests may earn one interface.

## Bounded contexts and domain language

Domain-driven design starts with the business language. A “product” in catalogue
may mean descriptive content, while inventory cares about reservable units and
fulfilment cares about shipment rules. A bounded context owns its model/meaning,
not necessarily a separately deployed process.

Identify context relationships and translation at boundaries. An anti-corruption
adapter can map a vendor's terms into the local domain rather than spreading its
schema through every use case. Shared libraries reduce duplication but can also
create coordinated release coupling; share stable technical concepts deliberately.

Do not create one microservice per database table. First identify capability,
invariant, ownership and change cadence. A modular monolith can express those
contexts while preserving inexpensive calls and local transactions.

## Aggregates and consistency

An aggregate is a boundary for enforcing a set of domain invariants through a
root. Its size affects contention, loading and transaction scope. A giant tenant
aggregate serializing every order is unlikely to scale well; a tiny boundary that
cannot enforce stock rules pushes correctness into accidental coordination.

State which invariants require immediate consistency and which permit asynchronous
propagation. Within one database, a transaction may span the necessary rows. Across
independent services, use durable workflows and compensation where the business
accepts them. Splitting a consistency boundary creates a protocol problem, not just
a deployment improvement.

For inventory, reserving available units and recording a reservation belong under
a defined transaction/concurrency strategy. Updating a search projection can be
eventually consistent if clients understand freshness. Never label every delayed
update harmless simply because a broker is present.

## Deployment boundaries

| Form | Benefits | Costs and constraints |
| --- | --- | --- |
| Monolith | Simple deployment and local interaction | Boundaries can erode; whole-unit release/scale |
| Modular monolith | Explicit internal capabilities with local transactions | Needs enforcement of interfaces and data ownership |
| Microservices | Independent deployment/ownership where boundaries support it | Network failures, data consistency, observability and platform cost |

Independent deployability requires compatible APIs/messages, owned data and a team
able to operate the service. Two processes that share tables and require every
release together may have distributed costs without real independence.

Extract a service when measured scaling, isolation, ownership or release constraints
justify it. A strangler-style migration can route one capability through a new
boundary incrementally, with data migration, consistency and rollback planned.
Measure operational/organizational consequences, not only CPU utilization.

## Patterns as local tools

Repository abstracts meaningful persistence access; Unit of Work owns a transaction.
Strategy selects an interchangeable policy; Adapter translates an external contract;
Factory centralizes construction when construction actually varies. A pattern name
is useful only if it clarifies the decision and failure behavior.

```python
from collections.abc import Callable

def shipping_total(weight: int, policy: Callable[[int], int]) -> int:
    if weight <= 0:
        raise ValueError("weight must be positive")
    return policy(weight)
```

A callable is enough for this small Strategy illustration. A stateful interface
may be warranted for richer policies; choose based on the need. Avoid “generic
repository” APIs that expose every ORM operation while pretending to isolate storage.

## CQRS and event sourcing

CQRS separates command and query models/paths. It can be as small as distinct
read projections in one service; separate databases/brokers are optional decisions.
Async read models introduce projection lag, rebuild and authorization concerns.

Event sourcing stores the domain's event history as the basis for reconstructing
state. It requires event versioning, ordering, replay correctness, snapshots and
long-term privacy/retention policy. It is not the same as adding an audit table
or transactional outbox to a state-based model.

Use these techniques for a demonstrated fit, such as rich temporal reasoning or
very different read/write models. Avoid them when ordinary transactions and an
audit trail solve the requirement with less operational and schema-evolution cost.
Conceptual P2 familiarity includes explaining the failure/rebuild model without
implementing a new event-sourcing framework.

## Decision records and design reviews

A short ADR records context, options, decision, consequences and revisit triggers.
Include assumptions and evidence rather than retrofitting a justification around
a favorite product. For example:

```text
Context: one team, moderate load, stock/order invariants in one database.
Options: modular monolith; separately deployed order/inventory services.
Decision: modular monolith with explicit capability interfaces and outbox.
Consequences: simpler local transactions; shared release and scaling unit.
Revisit: measured independent scaling or ownership constraints justify extraction.
```

A review should challenge requirements, failure boundaries, data ownership,
rollout/recovery, security, observability, cost and team capacity. Record dissent
and uncertainty constructively. “It is industry standard” is not evidence.

## Worked failure analysis

Order and inventory services share tables and must deploy together, while requests
now fail on network timeouts between them. Re-evaluate whether the split achieved
independence. Restore or clarify transaction/data ownership, reduce coupling, and
choose a migration path consistent with the business invariant. Do not fix a
distributed monolith by adding more synchronous hops.

[Cosmic Python](https://www.cosmicpython.com/book/part1.html) provides concrete
repository, Unit of Work and domain examples.

[Practice](practice.md) · [Next: distributed design](../module-18/index.md)

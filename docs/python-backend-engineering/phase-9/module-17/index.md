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

### Example — matching method names do not prove substitution

Suppose Store.save promises that a later get returns the saved value. A replacement
adapter implements save with the same annotated parameters but quietly drops the
write. Static type compatibility can pass while the behavioral contract fails.

Single responsibility asks which decisions change together: reservation rules
and JSON file formatting have different owners. Dependency inversion lets the
rule depend on a useful storage contract rather than on JSON's mechanics.
Interface segregation keeps unrelated clients from depending on operations they
do not need.

Apply the principles to observable problems, not class counts. Splitting a coherent
two-method object into ten interfaces can increase coordination without improving
substitution, ownership or change safety.

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

### Example — the word product can describe several different facts

Catalogue's product has a current description and images. Inventory's product
identity has available/reserved units. A historical invoice line has the purchased
name and price at that time. Changing today's catalogue description should not
rewrite yesterday's invoice.

These are related concepts with different meanings and owners. A bounded context
makes that language explicit; it does not require one process per meaning.
An adapter can translate a supplier's SKU vocabulary without forcing every local
use case to speak the supplier's schema.

Ask which fact is authoritative, which is a projection/snapshot and how changes
propagate. A shared Product class can be convenient initially, but becomes costly
if every team must coordinate unrelated semantic changes through it.

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

### Example — choose the boundary around the invariant

For one reservation, available stock and the reservation record must agree.
An aggregate/use-case boundary should make that rule enforceable through a
defined transaction and concurrency strategy.

Making the entire tenant one aggregate would also serialize unrelated product
work. Making every field independent would push the invariant into accidental
coordination across boundaries. Neither extreme follows merely from the size of
a class.

A search projection can lag under its freshness contract while stock allocation
cannot oversell. Separate immediate invariants from delayed derived updates.
Moving them into separate services does not remove the relationship: it changes
the protocol and failure costs needed to preserve the business promise.

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

### Example — separate processes can still form a distributed monolith

Order and inventory APIs run in different containers, but both edit the same
tables and every release requires simultaneous schema changes. Network calls
now introduce timeouts while data/release ownership remains coupled.

The split may have added operating cost without delivering independent deployment.
A modular monolith can preserve explicit capability boundaries and local transactions
until measured scaling, ownership or fault-isolation needs justify extraction.

When extracting, define owned data, compatible APIs/messages, migration and recovery.
A strangler-style route can move one capability incrementally; it does not excuse
a vague dual-write period. Compare the simpler alternative against the specific
benefit instead of assuming service count measures architectural maturity.

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

### Example — a function can be a sufficient Strategy

```python
def economy(weight):
    return 500 + weight * 2

def express(weight):
    return 900 + weight * 4

def shipping_total(weight, policy):
    if weight <= 0:
        raise ValueError("weight must be positive")
    return policy(weight)

print(shipping_total(10, economy))
print(shipping_total(10, express))
```

Expected output is 520, then 940. The caller chooses a pricing policy without
changing the coordinating function. A stateful policy interface may be justified
later, but a factory hierarchy is not required for these two pure functions.

Repository, Adapter and Unit of Work similarly express particular needs:
persistence access, representation translation and transaction ownership.
A pattern that simply exposes every low-level ORM method has not necessarily
created useful isolation.

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

### Example — event history and an outbox serve different purposes

```python
def rebuild_stock(events):
    stock = 0
    for kind, quantity in events:
        if quantity <= 0:
            raise ValueError("invalid event quantity")
        if kind == "stock_added":
            stock += quantity
        elif kind == "stock_reserved" and quantity <= stock:
            stock -= quantity
        else:
            raise ValueError("invalid event sequence")
    return stock

print(rebuild_stock([("stock_added", 3), ("stock_reserved", 1)]))
```

The result is 2. This tiny reducer illustrates state reconstructed from a defined
ordered event history, not a production event store. Event sourcing needs schema
evolution, replay, ordering, snapshots and retention/privacy decisions.

An outbox alongside current state stores publication intent; it does not make
that history the authority for rebuilding the domain. CQRS separates command/query
paths and need not imply event sourcing or separate databases. Choose the mechanism
whose purpose matches the requirement.

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

### Example — an ADR preserves the assumption that could change

A useful decision might say: one team, moderate load and stock/order invariants
in one database favor a modular monolith. Its costs include a shared release
and scaling unit. A revisit trigger could be measured independent scaling needs
or genuinely separate ownership.

That is more useful than "microservices are modern" because a reviewer can test
the assumption later. Record alternatives, consequences, migration/recovery and
what evidence would change the decision.

Design review should challenge correctness, security, capacity, compatibility,
operations and team support. A diagram may look clean while its transaction
boundary is undefined; an ADR should make that uncertainty visible.

## Worked failure analysis

Order and inventory services share tables and must deploy together, while requests
now fail on network timeouts between them. Re-evaluate whether the split achieved
independence. Restore or clarify transaction/data ownership, reduce coupling, and
choose a migration path consistent with the business invariant. Do not fix a
distributed monolith by adding more synchronous hops.

[Cosmic Python](https://www.cosmicpython.com/book/part1.html) provides concrete
repository, Unit of Work and domain examples.

[Practice](practice.md) · [Next: distributed design](../module-18/index.md)

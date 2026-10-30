# Module 9 — Relational modeling and SQL

**P0 · prerequisite: Unit of Work and request contracts**

A relational schema encodes identities, relationships and constraints so incorrect
state is difficult to store, regardless of which application writes it. SQL query
performance then depends on access patterns, data distribution and the planner—not
on whether an ORM generated the statement.

## Chapter navigation

1. [Model invariants in the schema](#model-invariants-in-the-schema)
2. [Types and representation choices](#types-and-representation-choices)
3. [Joins, aggregation and windows](#joins-aggregation-and-windows)
4. [Indexes and planner decisions](#indexes-and-planner-decisions)
5. [Read execution plans](#read-execution-plans)
6. [SQLAlchemy loading and N+1](#sqlalchemy-loading-and-n1)
7. [Migrations and compatibility](#migrations-and-compatibility)

## Model invariants in the schema

Primary keys identify rows; unique constraints enforce alternative identities;
foreign keys protect relationships; check/not-null constraints protect local values.
Application validation gives useful early errors, while storage constraints protect
against competing writers and forgotten code paths.

For tenant-scoped products, a composite key can express isolation in relationships:

```sql
CREATE TABLE products (
    tenant_id uuid NOT NULL,
    product_id uuid NOT NULL,
    sku text NOT NULL,
    available integer NOT NULL CHECK (available >= 0),
    PRIMARY KEY (tenant_id, product_id),
    UNIQUE (tenant_id, sku)
);

CREATE TABLE order_items (
    tenant_id uuid NOT NULL,
    order_id uuid NOT NULL,
    product_id uuid NOT NULL,
    quantity integer NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (tenant_id, order_id, product_id),
    FOREIGN KEY (tenant_id, product_id)
        REFERENCES products (tenant_id, product_id)
);
```

This partial teaching schema omits order/tenant tables and their foreign keys.
The composite product foreign key prevents an item from referencing a product
under a different tenant key; authorization must still control who can access it.
PostgreSQL does not automatically add every useful index on referencing columns.

Normalize facts to avoid update anomalies: a product name belongs with the product,
not copied into every current catalogue row. Historical order line prices/names
may intentionally be snapshots. Denormalization should define an owner and update
policy, not silently create several conflicting sources of truth.

### Example — integrity still applies when another writer bypasses your API

Consider product (tenant A, id 7) and an order item claiming tenant B/product 7.
A composite foreign key on (tenant_id, product_id) rejects the mismatched relationship,
even if a script bypassed API validation. A foreign key on product_id alone would
not express that tenant relationship.

Likewise, CHECK (available >= 0) rejects a negative stored value. It is a final
data guard, not the entire reservation algorithm: the API must still explain
insufficient stock, combine order/stock effects and authorize the caller.

Normalization keeps each current fact with an owner. Historical order price is
a different fact from the product's current price, so copying it onto an order
line can be intentional. Ask what the value means through time before labelling
every repeated field a mistake.

## Types and representation choices

Use numeric/decimal or integer minor units for money with explicit currency and
rounding rules. UUIDs support distributed identifier generation but are not an
authorization boundary; index locality and payload size remain tradeoffs. Use
timestamptz for instants; it does not retain the original named timezone. Store
the relevant zone separately when business scheduling requires it.

JSONB is useful for flexible structured attributes, with explicit schema/query
expectations. It does not replace relational constraints for core identities.
Arrays fit bounded multi-valued attributes, not arbitrary relationships requiring
independent integrity and access patterns. Every type decision should consider
validation, indexing, evolution and how clients serialize the value.

### Example — representation choices change arithmetic and meaning

```python
from decimal import Decimal
print(0.1 + 0.2 == 0.3)
print(Decimal("0.1") + Decimal("0.2"))
```

Expected output is False, then 0.3. Decimal constructed from decimal strings
avoids first importing the binary float approximation, but currency/rounding rules
still need a contract. Integer minor units are another choice with currency scale.

For timestamps, timestamptz represents an instant; it does not retain the original
named scheduling zone. A recurring 9 AM appointment may need a separate timezone
rule. UUID identifiers help independent generation but do not authorize access.

JSONB can hold variable attributes, while core keys/relationships often benefit
from relational constraints. Flexible storage does not mean undefined semantics;
decide which fields are indexed, validated and evolved.

## Joins, aggregation and windows

Inner joins keep matching rows; left joins preserve unmatched left rows. A WHERE
predicate on a nullable right-side field can accidentally turn a left join's
effective result into an inner join. Joining one-to-many tables before aggregation
can multiply values and inflate totals. Aggregate at the correct grain first.

```sql
WITH totals AS (
    SELECT tenant_id, customer_id, SUM(total_minor) AS spend
    FROM orders
    WHERE status = 'completed'
    GROUP BY tenant_id, customer_id
)
SELECT tenant_id, customer_id, spend,
       DENSE_RANK() OVER (PARTITION BY tenant_id ORDER BY spend DESC) AS rank
FROM totals;
```

A GROUP BY collapses rows; a window function computes over a partition while
retaining rows. ROW_NUMBER chooses distinct sequence positions, RANK leaves gaps
after ties and DENSE_RANK does not. Define tie handling before choosing one.
Subqueries and CTEs can clarify intermediate grain; do not assume a CTE always
forces or always avoids materialization across versions/query forms.

### Example — a valid join can calculate the wrong total

One order has total 100, two item rows and three audit rows. Joining order → items
→ audits produces six combinations. SUM(order.total) over that result yields
600, not 100. Every join can be syntactically correct while the result grain is wrong.

Before joining, state whether a row means one order, one item or one audit event.
Aggregate each relation at the needed grain, or use EXISTS when only existence
matters. A left join followed by WHERE right.status = 'active' also removes the
unmatched rows it originally preserved.

Window functions retain rows rather than collapse them. For spends 100, 100, 80,
ROW_NUMBER gives distinct positions, RANK gives 1,1,3 and DENSE_RANK gives 1,1,2.
Choose tie semantics before optimizing the query or presenting interview output.

## Indexes and planner decisions

| Index shape | Useful case | Cost or caveat |
| --- | --- | --- |
| B-tree | Equality/range/order access | Storage, write amplification and maintenance |
| Composite | Tenant equality plus ordered recent rows | Leading predicates/order determine usefulness |
| Partial | Only active/open rows | Query predicates must support use of the partial condition |
| Expression | Querying a normalized expression | Expression/operator semantics must match |
| Covering with INCLUDE | Return payload without fetching every heap tuple | Index-only scans also depend on visibility and planner choices |

For `WHERE tenant_id = ? ORDER BY created_at DESC, id DESC`, consider
`(tenant_id, created_at DESC, id DESC)`. An index on created_at alone may scan many
other tenants' rows. Column order is about access patterns, not a slogan that the
most selective column is always first.

Planner statistics estimate row counts and value distributions. Low selectivity,
small tables, outdated statistics, mismatched expressions or parameter-sensitive
plans can make a sequential scan sensible or reveal a problem. An unused index
does not prove PostgreSQL is broken. Too many indexes slow writes and increase
vacuum/maintenance work.

### Example — build an index for the actual tenant-and-order access

```sql
CREATE INDEX orders_tenant_recent
ON orders (tenant_id, created_at DESC, id DESC);
```

This illustrative index matches tenant equality followed by deterministic recent
ordering. It can avoid scanning/sorting unrelated tenants when the query and
distribution make that useful. It is not a guarantee the planner must choose it.

An index only on created_at can encounter many other tenants' rows first.
An INCLUDE payload can reduce heap access, but visibility and planner decisions
still affect index-only scans. A partial index on open orders helps queries whose
conditions permit that partial predicate; unrelated status requests need another path.

Every index also adds storage/write/maintenance work. Start with a real access
pattern, compare observed plans and keep the business result unchanged.

## Read execution plans

EXPLAIN reports the planned shape and estimates. EXPLAIN ANALYZE actually executes
the statement and reports observed rows/timing; use an appropriate controlled
environment for mutating statements. BUFFERS helps distinguish cache hits and
reads. Parent/child times are not independent numbers to blindly sum.

Inspect estimated vs actual rows, loops, scan types, sort memory/spills and buffer
activity. A nested loop is reasonable for a small outer side with indexed lookups,
but devastating if a bad estimate produces millions of repetitions. Fix the
cardinality/access issue before toggling planner options to force a preferred logo.

Compare representative datasets and parameters, consistent instrumentation and
equivalent outputs. Record plans and measured results rather than claiming a
speedup because an index was created. Warm caches and EXPLAIN instrumentation
affect timing; distinguish them from actual application latency.

### Example — compare estimates with actual work, not just scan names

Imagine a hypothetical plan estimates 10 outer rows but actually produces 100,000.
A nested indexed inner lookup now loops 100,000 times. The nested-loop operator
is not intrinsically bad; the mistaken cardinality or access pattern made its
cost very different from the estimate.

Inspect actual rows, loops, filter removals, sort spills and buffers. Parent and
child times overlap in plan reporting, so blindly summing them can double-count.
EXPLAIN ANALYZE executes the statement; it is not a harmless preview of a write.

Compare realistic parameters, data and cache conditions. An index can improve
one tenant pattern and be irrelevant for another. "The plan now says Index Scan"
is weaker evidence than equivalent output and measured work under the relevant load.

## SQLAlchemy loading and N+1

SQLAlchemy 2.x select expressions describe SQL; execution and relationship access
determine actual requests. Loading N orders then lazily loading each order's items
can issue N+1 queries. Use explicit projections or eager loading appropriate to
cardinality. selectin loading often batches relationship retrieval; joined loading
can multiply result rows and needs deliberate result handling.

Async relationship access must not trigger surprising implicit I/O outside the
supported context. Inspect emitted SQL and count queries for a bounded fixture.
Avoid “fixing” N+1 by one enormous joined Cartesian result or by fetching every
tenant's data into Python. Apply pagination/filtering in SQL and preserve stable order.

### Example — count requests across the ORM boundary

Fetching 100 orders and then accessing each lazy items collection can perform
one order query plus 100 relationship queries: 101 database round trips.
The Python loop looks small, but remote latency accumulates.

A selectin loading strategy can batch collections; joined loading can reduce
round trips but multiply result rows and transferred data. Projecting the needed
fields can be simpler than loading complete entity graphs. There is no universal
"always eager join everything" rule.

Measure actual statements for a bounded fixture and preserve tenant filters and
pagination. In async code, an ordinary attribute access cannot silently become
arbitrary supported awaitable I/O. Session/loading ownership must match the
serialization path, especially after commit or closure.

## Migrations and compatibility

Alembic records schema evolution, but generated migrations need review. Consider
locks, table rewrites, backfill duration, defaults, indexes and rollback data loss.
Autogeneration cannot infer every rename, business transformation or deployment rule.

Expand/contract separates compatibility stages: add a new optional representation,
deploy code that tolerates both, backfill in bounded batches, validate/enforce the
new invariant, move readers/writers, and remove the old representation only after
old binaries are gone. Some PostgreSQL operations require special transaction
handling, such as concurrent index creation; follow the target version's rules.

### Example — migrate without breaking the old binaries still running

Suppose full_name is replaced by display_name. Dropping full_name immediately
breaks old pods during a rolling deployment and can prevent application rollback.

A staged approach adds the new representation, deploys compatible code, backfills
in bounded batches, verifies data/invariants, moves readers/writers, and removes
the old representation only after old users are gone. Decide how simultaneous
writes are synchronized; a backfill can otherwise overwrite newer data.

Review locks, transaction size and index creation rules against the target
PostgreSQL version. Alembic can describe operations, but autogeneration cannot
infer the business meaning of a rename or prove a deployment is backwards compatible.
The practical migration is deferred; this is the compatibility reasoning it must implement.

### Work the result before discussing the plan

Use the [SQL query workbook](query-workbook.md) for complete fixtures, queries and
expected rows covering left joins/NULLs, tenant-safe aggregation, ties, join
multiplication, cursor boundaries and running window frames.

These examples fill a different need from EXPLAIN: they establish what the query
should return. Only then compare representative PostgreSQL plans, buffers and
query counts. SUM(DISTINCT total) is not a general repair for multiplied joins,
because two different orders may legitimately have equal totals.

## Worked failure analysis

A reporting join doubles revenue when an order has two audit events. Inspect
row grain before/after joining, not only the index plan. Pre-aggregate the relevant
relation or choose an existence predicate when you only need membership. Validate
known totals, then optimize the corrected query. Fast wrong results are not an
optimization.

[PostgreSQL SQL](https://www.postgresql.org/docs/current/sql.html),
[indexes](https://www.postgresql.org/docs/current/indexes.html),
[EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html) and
[Alembic](https://alembic.sqlalchemy.org/en/latest/) are the targeted references.

[Practice](practice.md) · [Next: transactions](../module-10/index.md)

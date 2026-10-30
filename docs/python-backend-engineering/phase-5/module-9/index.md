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

## Migrations and compatibility

Alembic records schema evolution, but generated migrations need review. Consider
locks, table rewrites, backfill duration, defaults, indexes and rollback data loss.
Autogeneration cannot infer every rename, business transformation or deployment rule.

Expand/contract separates compatibility stages: add a new optional representation,
deploy code that tolerates both, backfill in bounded batches, validate/enforce the
new invariant, move readers/writers, and remove the old representation only after
old binaries are gone. Some PostgreSQL operations require special transaction
handling, such as concurrent index creation; follow the target version's rules.

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

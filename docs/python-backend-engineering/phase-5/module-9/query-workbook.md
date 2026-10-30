# SQL query workbook — derive the result before optimizing

These read-only, self-contained fixtures teach result semantics without creating
the deferred database project. Each WITH ... VALUES block supplies its own data.
Amounts are integer minor units. Predict the rows before opening the answer.
The queries use PostgreSQL-compatible relational/window syntax; no PostgreSQL
locking behavior or measured execution plan is claimed by these examples.

## 1. Keep customers with zero completed orders

We need one row per tenant/customer, including customers without a completed order.

```sql
WITH customers(tenant_id, customer_id) AS (
    VALUES ('A', 'c1'), ('A', 'c2'), ('B', 'c1')
), orders(tenant_id, order_id, customer_id, status, total_minor) AS (
    VALUES ('A', 'o1', 'c1', 'completed', 1000),
           ('A', 'o2', 'c1', 'pending', 500),
           ('B', 'o3', 'c1', 'completed', 9000)
)
SELECT c.tenant_id, c.customer_id,
       COUNT(o.order_id) AS completed_orders,
       COALESCE(SUM(o.total_minor), 0) AS spend_minor
FROM customers AS c
LEFT JOIN orders AS o
  ON o.tenant_id = c.tenant_id
 AND o.customer_id = c.customer_id
 AND o.status = 'completed'
GROUP BY c.tenant_id, c.customer_id
ORDER BY c.tenant_id, c.customer_id;
```

??? note "Expected rows and reasoning"
    | tenant | customer | completed_orders | spend_minor |
    | --- | --- | ---: | ---: |
    | A | c1 | 1 | 1000 |
    | A | c2 | 0 | 0 |
    | B | c1 | 1 | 9000 |

    1. Match both tenant and customer, so A/c1 cannot inherit B/c1's orders.
    2. Put the completed-status condition in ON. A WHERE condition on o.status
       would discard the null-extended unmatched row for A/c2.
    3. COUNT(o.order_id) counts matched orders; COUNT(*) would count the unmatched
       outer-join row as one.
    4. SUM over no matching values is NULL; COALESCE expresses this report's zero rule.

**Change the requirement:** if only customers with completed orders should appear,
an inner join is appropriate. SQL style must follow the desired result, not a rule
that left joins are always safer.

## 2. Top two spend levels, including ties

“Top two customers” is ambiguous. Here we require the top two **distinct spend
levels** per tenant and include every tie at those levels.

```sql
WITH orders(tenant_id, customer_id, status, total_minor) AS (
    VALUES ('A', 'c1', 'completed', 1000),
           ('A', 'c1', 'completed', 1000),
           ('A', 'c2', 'completed', 2000),
           ('A', 'c3', 'completed', 1500),
           ('A', 'c4', 'pending', 5000),
           ('B', 'c1', 'completed', 1000),
           ('B', 'c2', 'completed', 500)
), totals AS (
    SELECT tenant_id, customer_id, SUM(total_minor) AS spend_minor
    FROM orders
    WHERE status = 'completed'
    GROUP BY tenant_id, customer_id
), ranked AS (
    SELECT tenant_id, customer_id, spend_minor,
           DENSE_RANK() OVER (
               PARTITION BY tenant_id ORDER BY spend_minor DESC
           ) AS spend_rank
    FROM totals
)
SELECT tenant_id, customer_id, spend_minor, spend_rank
FROM ranked
WHERE spend_rank <= 2
ORDER BY tenant_id, spend_rank, customer_id;
```

??? note "Expected rows and reasoning"
    | tenant | customer | spend_minor | spend_rank |
    | --- | --- | ---: | ---: |
    | A | c1 | 2000 | 1 |
    | A | c2 | 2000 | 1 |
    | A | c3 | 1500 | 2 |
    | B | c1 | 1000 | 1 |
    | B | c2 | 500 | 2 |

    Aggregate to customer grain first. DENSE_RANK counts distinct spend levels
    without gaps; c4 is excluded before aggregation because its order is pending.
    Adding customer_id to the window's ORDER BY would break the intended ties.

    If the contract requires at most two rows, use ROW_NUMBER with a deterministic
    tie-breaker instead. RANK would give A's customers ranks 1, 1, 3 and exclude c3
    under rank <= 2. The final output ORDER BY is separate from ranking semantics.

## 3. Detect and repair join multiplication

One order total is 100, with two items and three audit events:

```sql
WITH orders(order_id, total_minor) AS (VALUES ('o1', 100)),
items(order_id, item_id) AS (VALUES ('o1', 'i1'), ('o1', 'i2')),
audits(order_id, event_id) AS (
    VALUES ('o1', 'e1'), ('o1', 'e2'), ('o1', 'e3')
)
SELECT COUNT(*) AS joined_rows, SUM(o.total_minor) AS wrong_total
FROM orders AS o
JOIN items AS i ON i.order_id = o.order_id
JOIN audits AS a ON a.order_id = o.order_id;
```

The result is six joined rows and a wrong total of 600. Each item combines with
each audit event. Adding an index cannot correct that grain error.

If the actual requirement is “sum orders having at least one item and audit,”
use existence without multiplying the order rows:

```sql
WITH orders(order_id, total_minor) AS (VALUES ('o1', 100)),
items(order_id, item_id) AS (VALUES ('o1', 'i1'), ('o1', 'i2')),
audits(order_id, event_id) AS (
    VALUES ('o1', 'e1'), ('o1', 'e2'), ('o1', 'e3')
)
SELECT SUM(o.total_minor) AS total_minor
FROM orders AS o
WHERE EXISTS (SELECT 1 FROM items AS i WHERE i.order_id = o.order_id)
  AND EXISTS (SELECT 1 FROM audits AS a WHERE a.order_id = o.order_id);
```

This returns 100. If the requirement instead sums item-level amounts, aggregate
items at their intended grain. SUM(DISTINCT order_total) is not a general repair:
two different orders can legitimately have the same total.

## 4. Continue after a tied timestamp

The fixture uses one normalized UTC text format to make ordering easy to inspect.
A real PostgreSQL schema should use a suitable timestamptz column and typed cursor
parameters rather than relying on arbitrary timestamp strings.

```sql
WITH orders(tenant_id, order_id, created_at) AS (
    VALUES ('A', 'o9', '2026-01-01T12:00:00Z'),
           ('A', 'o8', '2026-01-01T12:00:00Z'),
           ('A', 'o7', '2026-01-01T11:59:00Z'),
           ('A', 'o6', '2026-01-01T11:58:00Z'),
           ('B', 'o99', '2026-01-01T13:00:00Z')
)
SELECT order_id, created_at
FROM orders
WHERE tenant_id = 'A'
  AND (created_at, order_id) < ('2026-01-01T12:00:00Z', 'o8')
ORDER BY created_at DESC, order_id DESC
LIMIT 2;
```

The prior page ended at A/o8; this page returns o7 then o6. Filtering only
created_at < the timestamp could skip tied rows when a prior page ends earlier
within a tie. Ordering by timestamp without the same tie-breaker can make the
continuation unstable. Bind cursor state to tenant/filter/order policy and state
whether a multi-page snapshot is required.

## 5. Running totals need ordering and a frame

```sql
WITH ledger(tenant_id, event_id, occurred_at, delta) AS (
    VALUES ('A', 'e1', '12:00', 3),
           ('A', 'e2', '12:00', -1),
           ('A', 'e3', '13:00', 2),
           ('B', 'e1', '12:00', 5)
)
SELECT tenant_id, event_id, delta,
       SUM(delta) OVER (
           PARTITION BY tenant_id
           ORDER BY occurred_at, event_id
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS balance
FROM ledger
ORDER BY tenant_id, occurred_at, event_id;
```

??? note "Expected rows and reasoning"
    | tenant | event | delta | balance |
    | --- | --- | ---: | ---: |
    | A | e1 | 3 | 3 |
    | A | e2 | -1 | 2 |
    | A | e3 | 2 | 4 |
    | B | e1 | 5 | 5 |

    PARTITION BY resets the calculation per tenant. The stable event tie-breaker
    orders same-time events, and ROWS defines a row-by-row frame. Ordering only
    by a nonunique timestamp with a default peer-based frame can give surprising
    same-time totals. This read query reports a balance; it does not enforce a
    concurrent stock-write invariant.

## Move from correct rows to performance evidence

Only after checking grain, tenant scope, ties and NULL behavior should you propose
indexes/loading changes. Review representative rows, plans, loops, buffers and
query counts against the actual PostgreSQL environment when practical work resumes.
Do not publish an invented plan or timing based on these tiny fixtures.

[Core SQL lesson](index.md) · [Practice](practice.md) ·
[Interview SQL](../../phase-10/module-19/practice.md) · [Assessment guide](../../assessment-guide.md)

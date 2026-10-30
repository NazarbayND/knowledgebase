# Module 19 — Coding and technical problem solving

**P0 · practice throughout; focused review in week 16**

A strong interview solution makes assumptions explicit, chooses a suitable data
structure, preserves an invariant and tests the important edges. Explain the
mechanism before optimizing; correct bounded work with clear limits is stronger
than a memorized pattern applied to the wrong requirement.

## Chapter navigation

1. [Data structures and complexity](#data-structures-and-complexity)
2. [Search, sorting and windows](#search-sorting-and-windows)
3. [Trees, graphs, heaps and dynamic programming](#trees-graphs-heaps-and-dynamic-programming)
4. [Python-specific reasoning](#python-specific-reasoning)
5. [SQL and backend challenges](#sql-and-backend-challenges)
6. [Timed API work and code review](#timed-api-work-and-code-review)

## Data structures and complexity

Lists support ordered storage/indexing; dictionaries/sets provide average constant
lookup under suitable hashing; deque supports efficient queue ends; list append/pop
at the end fits a stack. Repeated list pop(0) shifts elements and can turn a linear
queue traversal into quadratic work.

State n and other dimensions explicitly. O(n log k) top-k selection differs from
sorting all n values in O(n log n). Consider extra memory, recursion depth and
output size, not only time. Hash operations are average-case assumptions and very
large Python integers have magnitude-dependent arithmetic cost.

For arrays/strings, clarify mutation, ordering, duplicates, Unicode units and empty
input. Python strings expose Unicode code points, not arbitrary user-perceived
grapheme clusters. A “character” requirement may need clarification.

### Example — explain the data structure through the work it avoids

Removing the first element of a list shifts its remaining elements. Doing that
repeatedly for n queued nodes can make otherwise simple traversal quadratic.
deque.popleft avoids that shifting for a FIFO queue.

For top-k counts, define ties before selecting:

```python
from collections import Counter
from heapq import nsmallest

counts = Counter(["a", "b", "a", "c", "b", "a"])
top = nsmallest(2, counts.items(), key=lambda item: (-item[1], item[0]))
print(top)
```

Expected output is [('a', 3), ('b', 2)]. The key prefers larger counts, then
alphabetical order. Counting needs O(n) average work; bounded selection can avoid
sorting all distinct values when k is small. State both input length and distinct
key count, and include retained count/output memory in the explanation.

## Search, sorting and windows

Binary search requires a monotonic/sorted predicate and a shrinking interval.
This lower-bound example returns the first position whose value is not less than
the target, or len(values) if none exists:

```python
from collections.abc import Sequence

def lower_bound(values: Sequence[int], target: int) -> int:
    left, right = 0, len(values)
    while left < right:
        middle = (left + right) // 2
        if values[middle] < target:
            left = middle + 1
        else:
            right = middle
    return left
```

The invariant separates values known less than target from the remaining half-open
search interval. Test empty input, duplicates, before-first and after-last targets.
Do not search unsorted data without paying for sorting or choosing another method.

Two pointers fit monotonic movement through sorted or structured data. Sliding
windows maintain a condition while expanding/shrinking a contiguous region:

```python
def longest_distinct(text: str) -> int:
    last: dict[str, int] = {}
    start = best = 0
    for end, character in enumerate(text):
        start = max(start, last.get(character, -1) + 1)
        last[character] = end
        best = max(best, end - start + 1)
    return best
```

The start never moves backwards; last-seen positions let each code point be processed
once. Explain why `max` matters for an old repeated value outside the current
window. Sorting, windows and two pointers solve different constraints; do not force
a window onto a problem without the necessary condition.

### Example — trace the binary-search invariant before giving complexity

For values [1, 2, 2, 4] and target 2, the existing lower_bound uses a half-open
[left, right) interval:

| Step | left | right | middle/value | Decision |
| --- | ---: | ---: | --- | --- |
| 1 | 0 | 4 | 2 / 2 | right becomes 2 |
| 2 | 0 | 2 | 1 / 2 | right becomes 1 |
| 3 | 0 | 1 | 0 / 1 | left becomes 1 |

The interval is empty at 1, the first valid position. Using middle rather than
middle + 1 in the less-than branch can fail to make progress. Returning the
first equality encountered can return the second duplicate instead of the first.

For longest_distinct("abba"), the second b moves start to 2. The final a's earlier
position must not move start back to 1. The max in the window update protects
that invariant. Explaining these transitions demonstrates more than recalling
the labels binary search and sliding window.

### Two pointers — eliminate candidates using sorted order

```python
def pair_sum(values, target):
    left, right = 0, len(values) - 1
    while left < right:
        total = values[left] + values[right]
        if total == target:
            return left, right
        if total < target:
            left += 1
        else:
            right -= 1
    return None

print(pair_sum([1, 2, 4, 7], 9))
print(pair_sum([1, 2, 4], 8))
```

Expected output is (1, 3), then None. The return values are distinct indices in
the supplied sorted sequence. Start with 1+7=8: keeping 1 and choosing a smaller
right value cannot reach 9, so discard that left candidate. Now 2+7=9 succeeds.
When a sum is too large, discard the right candidate by the symmetric argument.

Each pointer moves inward at most n times: O(n) time and O(1) extra working space.
Sorting unsorted input first adds cost and changes original positions unless
indices are carried explicitly. State sorted-input and result-shape requirements
before applying the pattern. Negative numbers are fine under sorted order.

Python sorting is stable: equal keys retain their input order. That does not
create a deterministic database/API order when the input itself is unspecified;
use an explicit tie-breaker where the contract requires one.

## Trees, graphs, heaps and dynamic programming

### Binary trees — make traversal order and stack ownership visible

```python
from dataclasses import dataclass

@dataclass
class Node:
    value: int
    left: "Node | None" = None
    right: "Node | None" = None

def preorder(root):
    if root is None:
        return []
    pending = [root]
    result = []
    while pending:
        node = pending.pop()
        result.append(node.value)
        if node.right is not None:
            pending.append(node.right)
        if node.left is not None:
            pending.append(node.left)
    return result

tree = Node(2, Node(1), Node(3))
print(preorder(tree))
print(preorder(None))
```

Expected output is [2, 1, 3], then []. Push right before left because the stack
pops the most recently added node first. Preorder means root, left subtree, right
subtree; inorder and postorder use different visit positions.

For a proper acyclic tree, traversal is O(n), the working stack is bounded by
O(h) height, and this returned list also occupies O(n). A recursive variant uses
call-stack depth O(h); an unbalanced tree can exceed Python's recursion limit.
A general graph needs a visited/identity policy rather than assuming tree structure.

### Graphs, heaps and state transitions

BFS explores unweighted shortest-path layers; DFS fits reachability, cycle reasoning
and tree traversal. Track visited state at the right moment to avoid repeated
enqueues or infinite cycles. Recursive solutions need a depth/stack assumption.

```python
from collections import deque
from collections.abc import Mapping, Sequence

def distances(graph: Mapping[str, Sequence[str]], start: str) -> dict[str, int]:
    result = {start: 0}
    pending = deque([start])
    while pending:
        node = pending.popleft()
        for neighbor in graph.get(node, ()):
            if neighbor not in result:
                result[neighbor] = result[node] + 1
                pending.append(neighbor)
    return result
```

This treats a missing adjacency list as no outgoing edges; define whether an
unknown start should instead fail. Complexity is O(V+E) over reachable vertices
and edges with average mapping/set assumptions.

A heap supports repeated priority extraction and bounded top-k selection. Include
a stable tie-breaker when equal priorities would otherwise compare unorderable
objects. Updating arbitrary priorities may need lazy invalidation or another structure.

Dynamic programming identifies a state, transition, base case and evaluation
order. For minimum coin count, the state can be best achievable count for each
amount; unreachable states need an explicit sentinel. Check whether greedy is
actually valid before substituting it. Memoized recursion and bottom-up arrays
trade clarity, stack and state memory; basic mastery matters before exotic optimizations.

### Example — a greedy shortcut needs proof, while DP states the alternatives

```python
def minimum_coins(amount, coins):
    if amount < 0 or any(coin <= 0 for coin in coins):
        raise ValueError("invalid amount or coin")
    unreachable = amount + 1
    best = [0] + [unreachable] * amount
    for value in range(1, amount + 1):
        for coin in coins:
            if coin <= value:
                best[value] = min(best[value], best[value - coin] + 1)
    return None if best[amount] == unreachable else best[amount]

print(minimum_coins(6, [1, 3, 4]))
print(minimum_coins(3, [2]))
```

Expected output is 2, then None. Greedy chooses 4+1+1 for the first case, while
3+3 needs two coins. The state best[value] considers every permitted final coin;
zero is the base case and unreachable is distinct from a valid count.

Time depends on amount × number of denominations; the array uses O(amount) space.
For graphs, similarly state why BFS marks discovery before repeated enqueues and
why its shortest-path guarantee needs unweighted edges. A heap needs a tie-breaker
when equal priorities would otherwise compare unorderable payloads.

## Python-specific reasoning

Expect reference/mutable-default/closure questions, iterator exhaustion, equality
vs identity, exception cleanup, dataclass shallow freezing and typing vs runtime
validation. Use the [Phase 1 predictions](../../phase-1/module-1/practice.md) and
[Phase 2 runtime investigations](../../phase-2/module-3/runtime-investigations.md)
as cumulative checks.

When asked for a decorator/context manager/Protocol, preserve signatures, return
and exception behavior, and ownership. Do not implement a global mutable singleton
to save a minute if isolation is part of the task. Show a minimal negative case.

### Example — a validation pass can consume the business input

```python
records = iter([1, 2, 3])
print(all(value > 0 for value in records))
print(sum(records))
```

Expected output is True, then 0. all consumed the entire one-shot iterator while
checking positivity, so sum has no remaining values. If validation stopped early,
the remaining input would differ again.

Choose a materialized small collection, a fresh-iterator factory or a single-pass
validation/transformation contract. Do not fix the result by accidentally accepting
a partial dataset. Similar interview traps include mutable defaults, closure late
binding, shallow freezing, identity vs equality and exception cleanup that suppresses
errors. Explain the mechanism and a backend consequence, not just the output.

## SQL and backend challenges

SQL interviews combine joins, grouping, windows, ties, null handling and indexing.
Ask for the result grain and tie semantics before writing a query. A correct
ranking query can still be slow under its filter/order pattern; propose an index
and explain what a plan would need to show.

Concurrency exercises often hide read/await/write races or blocking calls in async
paths. Draw scheduling and transaction scope. Diagnose pool wait separately from
query time and distinguish a per-call timeout from the caller's total budget.

For a duplicate-order task, preserve the durable idempotency/business transaction
boundary, not a process-local set. For slow query review, do not invent EXPLAIN
results. State the expected evidence and how you would verify it.

### Example — start a SQL challenge with grain and ties

If the prompt asks for the top two customers per tenant, clarify whether ties
may produce more than two rows. ROW_NUMBER imposes a distinct position; RANK or
DENSE_RANK encode different tie behavior. Then state whether spend is per order,
per item or already aggregated before joining other one-to-many tables.

For a query-optimization task, propose the filter/order access pattern and ask
for actual plans/data distribution. Do not fabricate a measured speedup.
For backend debugging, distinguish pool wait, slow SQL, event-loop blocking and
transaction conflicts with observations that can separate them.

The interview is testing whether you preserve the result/consistency contract
while investigating performance, not simply whether you can name an index.

## Timed API work and code review

For fully worked SQL rows, use the
[query workbook](../../phase-5/module-9/query-workbook.md) before discussing indexes
or a hypothetical execution plan. It includes zero-match joins, tenant scope,
ties, multiplied totals, cursor boundaries and running frames.

Under a 45-minute API exercise, reserve time for requirements/contracts, a small
vertical behavior, negative tests and explanation. Clarify storage/identity
substitutes and which production properties are outside the bounded task. Avoid
spending the entire time scaffolding a framework with no demonstrated behavior.

Code review begins with correctness/security/ownership before naming/style. Identify
one reproducible defect, add a meaningful case, fix it locally and explain the
remaining risk. Keep refactors proportional and preserve public behavior unless
the task authorizes a contract change.

### Example — spend the timebox on evidence, not scaffolding

For a 45-minute create-order exercise, allocate time to clarify identity/storage
assumptions, implement or outline one small behavior, cover negative inputs and
explain transaction/idempotency limits. A large router tree with no tested invariant
is weak evidence.

A useful review sequence is: identify one concrete failure, write a reproducing
case, change the smallest relevant boundary, then explain what remains unverified.
If the task uses an in-memory store, say that it cannot prove multi-worker
PostgreSQL behavior.

Keep domain correctness, authorization and resource ownership ahead of naming
preferences. A clean formatter result does not establish a correct algorithm,
and a correctly typed quantity can still violate available stock.

## Worked problem-solving narrative

For longest-distinct substring: clarify code-point semantics, propose a quadratic
baseline, identify repeated rescanning, maintain a last-seen map and monotonic
start, then test empty/repeated/overlapping cases. State O(n) average time and O(u)
space for distinct code points. Explain limitations instead of claiming universal
constant memory or grapheme correctness.

[Python collections](https://docs.python.org/3.14/library/collections.html) and
[heapq](https://docs.python.org/3.14/library/heapq.html) are useful focused references.

[Practice](practice.md) · [Next: interview simulation](../module-20/index.md)

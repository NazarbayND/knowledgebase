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

## Trees, graphs, heaps and dynamic programming

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

## Python-specific reasoning

Expect reference/mutable-default/closure questions, iterator exhaustion, equality
vs identity, exception cleanup, dataclass shallow freezing and typing vs runtime
validation. Use the [Phase 1 predictions](../../phase-1/module-1/practice.md) and
[Phase 2 runtime investigations](../../phase-2/module-3/runtime-investigations.md)
as cumulative checks.

When asked for a decorator/context manager/Protocol, preserve signatures, return
and exception behavior, and ownership. Do not implement a global mutable singleton
to save a minute if isolation is part of the task. Show a minimal negative case.

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

## Timed API work and code review

Under a 45-minute API exercise, reserve time for requirements/contracts, a small
vertical behavior, negative tests and explanation. Clarify storage/identity
substitutes and which production properties are outside the bounded task. Avoid
spending the entire time scaffolding a framework with no demonstrated behavior.

Code review begins with correctness/security/ownership before naming/style. Identify
one reproducible defect, add a meaningful case, fix it locally and explain the
remaining risk. Keep refactors proportional and preserve public behavior unless
the task authorizes a contract change.

## Worked problem-solving narrative

For longest-distinct substring: clarify code-point semantics, propose a quadratic
baseline, identify repeated rescanning, maintain a last-seen map and monotonic
start, then test empty/repeated/overlapping cases. State O(n) average time and O(u)
space for distinct code points. Explain limitations instead of claiming universal
constant memory or grapheme correctness.

[Python collections](https://docs.python.org/3.14/library/collections.html) and
[heapq](https://docs.python.org/3.14/library/heapq.html) are useful focused references.

[Practice](practice.md) · [Next: interview simulation](../module-20/index.md)

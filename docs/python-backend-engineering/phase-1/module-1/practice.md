# Module 1 — Practice and assessment

Read the [semantics chapters](index.md), attempt the predictions without a REPL,
then run the executable answer key in
`examples/python-backend-engineering/tests/test_semantics.py`.

## Twelve prediction questions

For each snippet, state `result`, explain the mechanism, and name a backend bug
the behavior could cause. Each block runs in a fresh namespace.

### 1. Aliasing

```python
a = [1]
b = a
b.append(2)
result = a
```

### 2. Shallow copy

```python
a = [[1]]
b = a.copy()
b[0].append(2)
result = a
```

### 3. Deep copy

```python
import copy
a = [[1]]
b = copy.deepcopy(a)
b[0].append(2)
result = a
```

### 4. Identity and equality

```python
a = [1]
b = [1]
result = (a == b, a is b)
```

### 5. Boolean numbers

```python
result = (isinstance(True, int), True == 1)
```

### 6. Truthiness

```python
result = (bool([]), bool("0"), None is None)
```

### 7. Mutable default

```python
def add(x, items=[]):
    items.append(x)
    return items
a = add(1)
b = add(2)
result = (a, a is b)
```

### 8. Late closure binding

```python
functions = [lambda: i for i in range(3)]
result = [f() for f in functions]
```

### 9. Binding a default

```python
functions = [lambda i=i: i for i in range(3)]
result = [f() for f in functions]
```

### 10. Iterator exhaustion

```python
values = iter([1, 2])
first = list(values)
result = (first, list(values))
```

### 11. Cleanup order

```python
events = []
try:
    events.append("try")
finally:
    events.append("finally")
result = events
```

### 12. Dictionary order

```python
data = {"a": 1, "b": 2}
data["a"] = 3
result = list(data.items())
```

??? note "Prediction answer key — open after attempting"
    1. `[1, 2]`: both names reference one list.
    2. `[[1, 2]]`: the nested list is shared by the shallow copy.
    3. `[[1]]`: the deep copy has a separate nested list.
    4. `(True, False)`: equal values in distinct list objects.
    5. `(True, True)`: bool subclasses int; reject bool where quantities require integers.
    6. `(False, True, True)`: empty list is false, nonempty string is true, None is a singleton.
    7. `([1, 2], True)`: the definition-time default and returned list are reused.
    8. `[2, 2, 2]`: the closures read the final loop binding.
    9. `[0, 1, 2]`: each function captures a definition-time default value.
    10. `([1, 2], [])`: the iterator was exhausted.
    11. `["try", "finally"]`: cleanup follows the successful try suite.
    12. `[("a", 3), ("b", 2)]`: replacement preserves insertion order.

Run only this answer key from `examples/python-backend-engineering/`:

```bash
uv run --frozen pytest tests/test_semantics.py -v
```

## Implementation exercises

| Task | Acceptance criteria |
| --- | --- |
| **Values and collections:** choose containers for a SKU lookup, unique tags, FIFO jobs and ordered history | Explain average lookup/append costs, why `bytes[0]` is an int, and why float money is risky; test slicing without aliasing the outer list |
| **Function API:** implement `reserve(tenant, sku, *, quantity)` | Reject missing/invalid quantity, preserve meaningful zero in unrelated optional settings, and avoid mutable defaults; demonstrate argument unpacking |
| **Scopes and decorators:** build three callbacks and a logging decorator | Callbacks return independent values; decorator uses `wraps`, forwards args/kwargs and preserves the result and exception |
| **Iteration:** stream nonempty CSV rows with a generator | Read incrementally; repeated traversal needs a fresh iterator; a partial consumer does not leak an owned file |
| **Exceptions and resources:** translate malformed stock to a custom domain error | Preserve its cause; prove cleanup on success and failure; explain `else` vs `finally` |
| **Standard-library report:** produce an inventory summary | Use `pathlib`, `csv`, `json`, `Counter`, timezone-aware `datetime`, `islice`, `partial`, and a bounded SKU `fullmatch`; reject invalid rows explicitly |
| **Mutation diagnosis:** repair nested-copy and default-list bugs | Add regression tests that fail with the original behavior and explain ownership in the fixed API |

Keep your attempts in the subject's examples tree. Do not add a new third-party
library when a standard-library exercise is intended. The reference inventory
package demonstrates core invariants. The [worked examples](worked-examples.md)
now include a complete CSV/report solution with resource-lifetime tests. Attempt
the exercise first, then compare its explicit input and ownership contracts.

## Interview practice

Answer in 60–90 seconds, then give a small example:

1. Why does a mutable default persist between calls? When are defaults evaluated?
2. When do `is` and `==` differ, and why is comparing integer identity unreliable?
3. How can a tuple contain changing data? What makes an object hashable?
4. What does a closure retain? How would you repair loop-created callbacks?
5. Why might a generator reduce memory and still hold a resource open?
6. Where should malformed external input become a domain exception?

## Self-check before the assessment

A configuration value is 0. Compare value or 30 with 30 if value is None else value. Which preserves the caller's zero, and when should zero instead be rejected?

??? note "Model answer and a five-point check"
    The first expression returns 30; the second returns 0. Truthiness includes zero, while the explicit absence check identifies None. Whether zero is valid belongs to the setting's contract. Reject a forbidden zero explicitly rather than replacing it by accident. An empty collection or False can produce the same defaulting mistake.

    Award up to two points for the correct outcome, two for the mechanism, and
    one for a relevant limit or counterexample. Record hints honestly. This is
    a retrieval drill, not a replacement for the full module assessment.

Use the [assessment guide](../../assessment-guide.md) for the shared scoring
anchors and evidence rules.

## Mastery assessment

Timebox: **60 minutes implementation + 20 minutes explanation**.

| Dimension | Task and evidence | Points |
| --- | --- | ---: |
| Concepts | Explain four assessor-selected predictions and their mechanisms | 25 |
| Correctness | Implement typed reservation and input validation, with success/negative tests | 30 |
| Debugging | Reproduce and repair a shared-default or shallow-copy bug | 20 |
| Decisions | Justify collection choice, copy policy, lazy/eager behavior and cleanup ownership | 15 |
| Communication | Give a concise walkthrough with commands, results and remaining limits | 10 |

Target **80/100**. Attempt all twelve predictions; revisit every wrong explanation.
Do not mark mastery while rejected operations mutate stock or resources are leaked,
even if the numeric score passes. Record the result and next revision action in
[progress](../../progress.md).

[Module 1](index.md) · [Next: Module 2](../module-2/index.md)

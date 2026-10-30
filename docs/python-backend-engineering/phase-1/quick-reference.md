# Phase 1 — Quick reference and common traps

Use this during revision after the worked material. For mechanisms and examples,
return to [Module 1](module-1/index.md) and [Module 2](module-2/index.md).

## Semantics decision table

| Need | Prefer | Watch for |
| --- | --- | --- |
| Detect absence | `value is None` | `if not value` also matches zero/empty/false |
| Compare values | `left == right` | Custom equality; numeric bool/int relationships |
| Detect a deliberate sentinel | `value is sentinel` | Integer/string interning is not a portable identity contract |
| Copy a flat list | `list(values)` or `values.copy()` | Nested mutable values remain shared |
| Independent domain update | Construct/replace immutable values | Frozen dataclasses are only shallowly frozen |
| Optional collection argument | `None` default with an explicit ownership rule | Fixing the default does not decide whether caller input is copied |
| Bind per-loop callbacks | Factory, default argument, or `partial` | A closure normally reads the current enclosing binding |
| One-pass large input | Iterator/generator | Exhaustion, deferred errors and retained resources |
| Repeated traversal of small data | Tuple/list | Eager allocation is sometimes the clearer contract |
| Scoped resource | `with` / context manager | Iterator must not outlive its owner |

## Collection choices and costs

| Container | Typical use | Common costs and constraints |
| --- | --- | --- |
| list | Ordered mutable sequence | Index O(1), append amortized O(1), membership/middle edits O(n) |
| tuple | Stable ordered value | Hashable only if all elements are hashable |
| dict | Keyed lookup, insertion order | Average lookup O(1); keys need stable hash/equality |
| set | Unique members, fast membership | Average membership O(1); no application ordering guarantee |
| deque | FIFO queues, both-end operations | O(1) end operations; not a drop-in list for random access |
| Counter | Counts by hashable key | Memory grows with distinct keys |

Slicing usually builds a new sequence and stays shallow. Dict insertion order is
guaranteed in modern Python; set iteration order is not a business contract.
Arbitrary-precision integers avoid fixed-width overflow but their operations are
not constant-cost for arbitrarily large magnitudes.

## Function and resource checklist

```python
def operation(first, /, ordinary=None, *extras, required, **options):
    ...
```

- `first` is positional-only; `ordinary` may be positional or keyword.
- `extras` collects extra positional arguments; `required` is keyword-only.
- `options` collects extra keyword arguments; duplicate bindings still fail.
- Defaults evaluate when `def` executes. Closures and decorators have their own
  binding/execution moments; do not conflate them.
- `try/else` separates a successful protected operation from its handlers.
- `finally` owns cleanup. Returning from it can suppress an exception.
- `raise NewError(...) from exc` preserves the original cause.
- Catch expected errors narrowly; do not turn cancellation or every programmer
  defect into a plausible empty result.

## Typing and design checklist

| Tool | Use it for | Do not confuse it with |
| --- | --- | --- |
| Dataclass | Structured values and generated methods | Runtime validation of every annotated field |
| Enum | A closed vocabulary | An independent state field that can disagree with derived data |
| Property | Cheap derived/validated attribute behavior | A surprising network operation |
| Protocol | Structural operation compatibility | Semantic contract testing |
| ABC | Intentional runtime family and shared behavior | A mandatory base for every adapter |
| TypedDict | Static dictionary shape | Parsing untrusted JSON |
| TypeVar / type parameters | Relationships across arguments/results | “Any type” without constraints |
| Callable / ParamSpec | Callable contracts and forwarded signatures | Automatic runtime checking |
| `object` | Unknown values that must be narrowed | `Any`, which permits unchecked operations |

Prefer composition where storage/policy vary independently. Keep domain imports
independent of adapters, and compose objects at entry points. A circular import is
a clue to investigate dependency direction; `sys.path` edits are not packaging.

## Standard-library boundaries

- Text is `str`; encoded bytes are `bytes`. Choose encodings explicitly.
- Open CSV with `newline=""`; let a CSV parser handle quoting rather than `split(",")`.
- JSON decoding yields data that still needs shape/type/domain checks.
- Use timezone-aware datetimes for global instants; agree on a serialization format.
- `groupby` groups consecutive matching keys, not every equal key in arbitrary order.
- `lru_cache` retains arguments/results; bound size and choose invalidation policy.
- Regex `fullmatch` is for whole-field validation; regex is not a general nested parser.

## Fast review commands

From `examples/python-backend-engineering/`:

```bash
uv sync --frozen
uv run --frozen pytest tests/test_semantics.py tests/test_inventory.py tests/test_reporting.py
uv run --frozen mypy
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen python -m fulfillhub.reporting data/inventory.csv
uv build --wheel
```

An installed package should work without accidental imports from the checkout root.
Ruff/mypy/pytest answer different questions. Check actual test execution and negative
behavior; a zero-test run or a formatter-only pass does not validate the package.

## Interview answer shape

Use **mechanism → concrete example → production implication → tradeoff**. For
mutable defaults: definition-time evaluation → two calls share a list → request
state can leak → choose a fresh default and define ownership of explicit input.

For every topic you cannot explain without reading this page, choose a reproducing
example, run it, then explain it again from memory.

[Worked semantics](module-1/worked-examples.md) ·
[Design walkthrough](module-2/design-and-testing.md) · [Cumulative assessment](assessment.md)

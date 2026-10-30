# Module 3 — Practice and assessment

Use the [runtime chapters](index.md) to explain observations without confusing
CPython implementation details with language guarantees.

## Exercises

| Topic | Task | Acceptance criteria |
| --- | --- | --- |
| Identity and lifecycle | Draw a graph containing a list alias, closure and cycle; remove bindings one at a time | Identify remaining strong owners and why `del` is not a resource-close API |
| Interpreter and frames | Disassemble a small function and inspect its code/local names | Explain compilation, local lookup and a suspended generator frame; report runtime version, not fixed opcodes |
| Memory management | Build/release an object cycle and inspect `gc` and `tracemalloc` | Distinguish retained references, cycle collection, allocator reuse and RSS; avoid asserting exact counts |
| Descriptors and MRO | Implement a non-negative descriptor, compare with a property, trace a diamond | State data/non-data precedence, bound-method behavior and cooperative `super()` order |
| Decorators and class creation | Preserve a callable's signature with ParamSpec; demonstrate `__init_subclass__` registration | Preserve result/error/metadata; explain when a metaclass would add unnecessary complexity |
| Structural typing and variance | Substitute two repositories and a read-only `Sequence` of subtypes | Pass strict mypy; explain why a mutable list cannot use the same covariance rule |
| Functional techniques | Compare a pure comprehension pipeline with map/partial and a generator | Equivalent output; explain readability, consumption, caching and resource-lifetime limits |
| Serialization | Round-trip valid products and reject malformed JSON payloads | Reject bool/negative stock; preserve decoding cause; explain why untrusted pickle is unsafe |
| Profiling and complexity | Compare repeated list membership with a prebuilt set for growing input | Profile CPU and allocation separately; include construction cost and repeated equivalent runs |

## Runtime investigation

From `examples/python-backend-engineering/`:

```bash
uv run --frozen python -m fulfillhub.runtime_lab
uv run --frozen mypy
uv run --frozen pytest tests/test_inventory.py
```

Save a short report containing interpreter/build, workload, command, equivalent
output, profiler evidence, allocation interpretation, and next experiment. The
original runtime lab measures generator aggregation. `fulfillhub.performance_lab`
now supplies the membership comparison, including index construction and separate
allocation measurements. Attempt your experiment first, then compare the
[worked investigation](runtime-investigations.md#investigation-6-measure-an-algorithmic-change-fairly).
Do not invent before/after numbers or remove checks to improve timings.

## MRO reasoning challenge

```python
class Root:
    def trace(self):
        return ["Root"]

class Left(Root):
    def trace(self):
        return ["Left", *super().trace()]

class Right(Root):
    def trace(self):
        return ["Right", *super().trace()]

class Leaf(Left, Right):
    pass
```

Predict `Leaf.__mro__` and `Leaf().trace()`. Then explain why `Left.trace` may call
`Right.trace` even though `Right` is not a base named in `class Left(Root)`.

??? note "Answer and design implication"
    MRO: `Leaf, Left, Right, Root, object`. The trace is
    `["Left", "Right", "Root"]`. `super()` continues after Left in the actual
    instance's MRO. Hard-coding `Root.trace(self)` in Left would skip Right;
    mixing direct calls and cooperative calls can duplicate or skip behavior.

## Interview practice

1. Can an unreachable object still have positive reference counts? Explain a cycle.
2. Why might Python allocation counters drop while RSS stays high?
3. What makes a property take precedence over an instance dictionary entry?
4. How does `instance.method()` receive `self`?
5. Why are mutable generic containers usually invariant?
6. Why is JSON validation still necessary when a `TypedDict` exists?
7. What evidence would justify an optimization? When would a generator be worse?

## Self-check before the assessment

A property named stock returns the backing value 3. Someone inserts stock=999 in the instance dictionary. What does normal instance.stock lookup return, and does that make private storage tamper-proof?

??? note "Model answer and a five-point check"
    Normal lookup still uses the property/data descriptor and returns 3. A data descriptor precedes the instance dictionary. The validation/access policy is not a security barrier: code deliberately editing backing storage or overriding lookup can bypass assumptions. An ordinary function is a non-data descriptor with different precedence.

    Award up to two points for the correct outcome, two for the mechanism, and
    one for a relevant limit or counterexample. Record hints honestly. This is
    a retrieval drill, not a replacement for the full module assessment.

Use the [assessment guide](../../assessment-guide.md) for the shared scoring
anchors and evidence rules.

## Mastery assessment

Timebox: **60 minutes investigation/refactoring + 20 minutes explanation**.

| Dimension | Evidence | Points |
| --- | --- | ---: |
| Concepts | Correct object lifetime, descriptor/MRO and variance explanations | 25 |
| Correctness | Reusable service interface, two implementations, strict checking and tests | 30 |
| Debugging | Reproduce a retained-reference or repeated-scan issue and diagnose it | 20 |
| Decisions | Explain property/descriptor/metaclass choice and profiling limits | 15 |
| Communication | Report reproducible commands, observations and uncertainty | 10 |

Target **80/100**. Bytecode memorization and lower elapsed time alone do not
demonstrate mastery. Record the score and evidence in [progress](../../progress.md).

[Module 3](index.md) · [Phase project](../project.md) ·
[Next: Module 4](../module-4/index.md)

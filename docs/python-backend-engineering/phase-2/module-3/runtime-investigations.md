# Module 3 — Investigating the runtime with evidence

**P1 · advanced class creation is P2**

The [core chapters](index.md) describe the mechanisms. Here, use controlled
experiments to distinguish a language guarantee, a CPython observation, and an
application invariant. Each investigation asks for a prediction before the command.

## Investigation 1 — Follow the owners of an object

```python
def make_reader():
    records = [{"stock": 3}]
    def read():
        return records
    return read

reader = make_reader()
first = reader()
first[0]["stock"] = 1
assert reader()[0]["stock"] == 1
print(reader.__code__.co_freevars)
```

The enclosing function has returned, but the closure retains the `records`
binding through a cell. The list and its dictionary remain alive. Repeatedly
calling `gc.collect()` cannot release objects still reachable through the reader.
If this function lives in an unbounded cache, the retained state can look like a leak
even though the collector is doing exactly what it should.

### Diagnose retention before changing collection settings

1. Identify a repeated operation with growing retained memory.
2. Separate temporary allocation peaks from growth that remains after the operation.
3. Find long-lived owners: caches, registries, task results, tracebacks, closures,
   suspended generators, or global collections.
4. Bound or release the owner deliberately and repeat the same workload.
5. Only then investigate unreachable cycles or native allocation behavior.

`del first` removes one binding; `reader` still reaches the graph. Weak references
can observe supported objects without ownership, but they are not a substitute
for a service retaining resources it actually needs. A resource's `close()` belongs
in an explicit lifecycle boundary, not in a hoped-for finalizer.

### CPython observation vs portable contract

On ordinary CPython, reference counting often makes acyclic deallocation prompt.
The language does not promise every implementation has that timing. `id()` is
stable while an object is alive but can be reused later; it is not a persistent
business identifier. Immortal objects, free-threaded builds and changing GC
heuristics make exact refcount/generation folklore particularly fragile.

## Investigation 2 — Code objects are not the whole function

```python
import dis

def multiplier(factor):
    def apply(value):
        return value * factor
    return apply

double = multiplier(2)
triple = multiplier(3)
assert double.__code__ is triple.__code__
assert double(4) == 8
assert triple(4) == 12
print(double.__code__.co_freevars)
dis.dis(double)
```

Both functions can share compiled instructions while holding different closure
cells. A function also has defaults, globals, annotations and metadata. An active
call has execution state; a suspended generator/coroutine retains its state between
resumptions. This explains why caching “a function” or storing an unfinished task
can retain more than the visible code suggests.

When inspecting bytecode, identify the roles of loads, operations and return.
Do not assert exact opcode names/counts as application behavior: Python releases
can change representations and specialization while preserving results.

Python 3.14 also changes annotation evaluation behavior compared with older versions.
Use supported introspection such as `typing.get_type_hints()` when you need resolved
types rather than assuming `__annotations__` has one representation in all runtimes.
Do not use arbitrary annotation evaluation on untrusted code as a validation step.

## Investigation 3 — Prove descriptor precedence

The runnable `object_model.py` defines `NonNegativeInt` with `__get__`, `__set__`,
and `__set_name__`. Its `Quantity` owner delegates assignment to that descriptor.

```python
from fulfillhub.object_model import Quantity

quantity = Quantity(3)
quantity.__dict__["amount"] = 999
assert quantity.amount == 3
quantity.amount = 4
assert quantity.__dict__["_amount"] == 4
```

Why does the injected public dictionary entry not win? The class attribute is a
data descriptor because it implements assignment. Ordinary attribute lookup gives
it precedence over the instance dictionary. Its own storage is the separate
`_amount` key chosen in `__set_name__`.

The descriptor rejects negative, bool and non-integer assignments before changing
storage. Tests prove the old value survives a rejected assignment. It is an
attribute policy, not a security barrier: code deliberately editing private
storage can bypass the public setter. `frozen` values and descriptors solve
different design problems.

### Why the overloads matter

Class access `Quantity.amount` returns the descriptor object; instance access
`quantity.amount` returns an integer. Overloads express these two outcomes to the
type checker. Returning an unconstrained `Any` from `__get__` would erase useful
checking at every use site. Runtime checks and static signatures remain separate
parts of the contract.

Prefer a simple property if only one class needs the validation. Reach for a
descriptor when several owners genuinely share a policy and the extra indirection
earns its maintenance cost.

## Investigation 4 — A bound method follows the instance's MRO

```python
from fulfillhub.object_model import Leaf

leaf = Leaf()
method = leaf.trace
assert method.__self__ is leaf
assert method() == ["Left", "Right", "Root"]
assert [cls.__name__ for cls in Leaf.__mro__] == ["Leaf", "Left", "Right", "Root", "object"]
```

The function's descriptor creates a bound method carrying `leaf`. Inside Left,
`super()` continues in **Leaf's** resolution order, so Right is next. Replacing
`super().trace()` with `Root.trace(self)` would skip Right and break cooperative
composition.

For constructors, consistent keyword conventions are essential: each class consumes
the arguments it owns and forwards the remainder once. Mixing direct base calls
with cooperative calls can initialize shared ancestors twice. If the explanation
needs a complex diagram to justify a small business service, consider composition.

## Decorators preserve more than a name

The reference `traced(events)` is a decorator factory. It accepts an event sink,
returns a decorator, and wraps the target using `ParamSpec` and a return TypeVar.
The wrapper records entry and exit in `finally`, so both success and failure have
a trace without suppressing the original exception.

```python
from fulfillhub.object_model import traced

events: list[str] = []

@traced(events)
def add(value: int, *, extra: int) -> int:
    return value + extra

assert add(2, extra=3) == 5
assert add.__name__ == "add"
assert events == ["enter:add", "exit:add"]
```

`wraps` preserves useful metadata and an introspection link to the original;
`ParamSpec` preserves the relationship between arguments for static checking.
Neither automatically makes a synchronous decorator await a coroutine. For an
async operation, entry/exit should surround the awaited execution, and cancellation
must propagate. A production log sink also needs a policy for what happens if
logging itself fails; an unbounded list is only a small deterministic lab sink.

### Class creation without a custom metaclass

For a trusted plugin registry, an ordinary subclass hook can be enough:

```python
class Plugin:
    registry = {}

    def __init_subclass__(cls, *, key, **kwargs):
        super().__init_subclass__(**kwargs)
        if key in Plugin.registry:
            raise ValueError("duplicate plugin key")
        Plugin.registry[key] = cls

class CsvPlugin(Plugin, key="csv"):
    pass

assert Plugin.registry["csv"] is CsvPlugin
```

This is a concept demonstration, not a typed production plugin framework. The
hook registers a class after class creation begins; it should not acquire sockets
or start workers as an import side effect. A class decorator or explicit registration
function can make ordering more visible. Custom metaclasses are reserved for needs
that these smaller tools cannot express. Explain namespace preparation, class-body
execution, type construction, hooks, and later instance construction at P2 depth.

## Investigation 5 — Preserve type relationships

Compare `list[Cat]` and `Sequence[Animal]` from the core chapter. Reading animals
from cats is safe; appending an arbitrary Animal to the original cat list is not.
This is why a read-only producer interface can be covariant while a mutable
consumer/producer container generally cannot.

For a callable, reverse the input intuition: a function able to handle **any**
Animal can handle a Cat; a function accepting only Cats cannot handle arbitrary
Animals. Returns follow the producer direction. Work through one concrete unsafe
call rather than memorizing “co” and “contra.”

The repository Protocol supports structural substitution, but its static contract
does not describe every business guarantee. The adapter test suite supplies
evidence for rejection behavior and persistence. Types, invariants, and resource
ownership are three related but distinct concerns.

## Investigation 6 — Measure an algorithmic change fairly

`performance_lab.py` compares n queries against a list of n allowed integers with
the same queries against a newly constructed set. It includes set construction
inside each candidate timing. Both paths must count the same matching queries,
including repeated queries; deduplicating the **queries** would change behavior.

```bash
# Working directory: examples/python-backend-engineering/
uv run --frozen python -m fulfillhub.performance_lab
```

The report uses input sizes 100, 1,000 and 5,000; each has half matching queries
for these even sizes. It reports the median of three elapsed-time samples and
separately observed traced allocation peaks. There is no hardcoded performance
threshold or fabricated expected timing.

### Interpret the cost model

- Repeated list membership can require O(n²) comparisons for n queries over n
  values. Early matches can change constants, not the worst-case pattern.
- Set construction is average O(n), followed by average O(1) membership per query,
  at the cost of additional memory. Pathological hashes and huge integer values
  require more careful analysis than this integer experiment.
- A single query over a tiny list may not justify building a set. If an index is
  retained across calls, its lifetime, update policy and memory become part of the
  service design.
- The benchmark's input lists exist before `tracemalloc` starts. Reported peaks are
  **incremental traced allocations**, not total input memory or process RSS.
- Timings run without tracing; allocations are measured in separate invocations.
  Profiling overhead would otherwise distort the comparison being explained.

### A useful evidence worksheet

| Record | Example of the kind of information required |
| --- | --- |
| Question | Does building an index help this repeated-membership workload? |
| Environment | Actual Python implementation/version, GIL mode, OS and machine limits |
| Workload | n values, query count, hit ratio, repeated query semantics |
| Correctness | Both versions return the same count, including duplicate queries |
| Measurement | Command, repeats, median/range, whether setup is included |
| Memory | Incremental Python allocations vs total process memory |
| Decision | Which workload benefits enough to justify the index's cost? |
| Limit | What this synthetic run does not establish about production traffic |

Use `cProfile` to find time-consuming call paths, then use a suitable repeated
measurement to compare a candidate. Optimize a demonstrated bottleneck, not a
function chosen because it contains a loop. Serialization and retained state can
dominate an otherwise improved algorithm.

## Run the reference investigations

```bash
# Working directory: examples/python-backend-engineering/
uv run --frozen python -m fulfillhub.object_model
uv run --frozen python -m fulfillhub.runtime_lab
uv run --frozen python -m fulfillhub.performance_lab
uv run --frozen pytest tests/test_object_model.py tests/test_performance_lab.py
uv run --frozen mypy
```

The descriptor result is 3 despite the shadow dictionary entry. MRO tracing yields
Left → Right → Root. The decorator returns 6 and records entry/exit in the CLI.
Memory, bytecode and timing values are runtime observations, not fixed outputs.

[Core chapters](index.md) · [Practice](practice.md) ·
[Next: concurrency failure walkthrough](../module-4/concurrency-patterns.md)

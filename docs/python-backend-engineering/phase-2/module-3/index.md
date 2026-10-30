# Module 3 — Python data model and runtime

**P0/P1 · metaclass implementation is P2**

The data model is the set of protocols connecting syntax to object behavior.
CPython is an implementation of that language, with its own interpreter, memory
management and optimization choices. Separate portable guarantees from observations
of a specific build before using internals to explain production behavior.

## Chapter navigation

1. [Objects and ownership](#objects-and-ownership)
2. [Interpreter and frames](#interpreter-and-frames)
3. [Reference counting and collection](#reference-counting-and-collection)
4. [Descriptors and method resolution](#descriptors-and-method-resolution)
5. [Decorators and class creation](#decorators-and-class-creation)
6. [Structural typing and variance](#structural-typing-and-variance)
7. [Functional techniques](#functional-techniques)
8. [Serialization boundaries](#serialization-boundaries)
9. [Profiling and complexity](#profiling-and-complexity)

## Objects and ownership

Every object has identity, type and value. Names, containers, closures and suspended
frames can all retain references to it. `del name` removes a binding, not necessarily
the object. An object's identity is stable for its lifetime; a later unrelated
object may reuse the same `id()` after the first is gone.

```python
import weakref

class Item:
    pass

value = Item()
observe = weakref.ref(value)
aliases = [value]
del value
assert observe() is aliases[0]  # the list still owns a strong reference
```

A weak reference observes without keeping an object alive, when the type supports
weak references. It is useful for caches/registries, not for ensuring a business
resource stays available. A frozen dataclass is only shallowly frozen. Explicitly
define who may mutate a value and who closes a resource; memory management does not
replace transaction, lock, socket, or file ownership.

Java and Kotlin also use references, but Python's ordinary assignment does not
declare a static variable type. Rebinding changes which object a name denotes.
Avoid reasoning from a variable's address or assuming a C-like value copy.

## Interpreter and frames

CPython parses source, builds an AST, compiles code objects and executes bytecode.
A function combines a code object with globals, defaults, closure cells and other
metadata. Calling it creates an execution context/frame with local state and an
instruction position. `.pyc` files cache compiled code; they are not machine-code
executables or a source-protection mechanism.

```python
import dis

def add_tax(price: int, tax: int) -> int:
    total = price + tax
    return total

dis.dis(add_tax)
print(add_tax.__code__.co_varnames)
```

Observe local loads, addition and return in your own runtime. Opcodes, adaptive
specialization and frame representation change across releases; never assert an
exact instruction sequence in an application test. CPython can optimize repeated
operations without changing the language result.

Local/enclosing/global/builtin resolution has runtime consequences. A closure
captures cells rather than a snapshot of every value. Suspended generators and
coroutines keep their local state alive. Tracebacks can also retain frames and
large objects, so retaining every exception forever can retain more memory than
the visible error message suggests.

## Reference counting and collection

Standard CPython uses reference counting plus a collector for reference cycles.
An unreachable acyclic object is often reclaimed promptly when its final strong
reference disappears, but this is not a cross-implementation lifetime guarantee.
Immortal objects and free-threaded builds complicate simplistic refcount models;
`sys.getrefcount()` also adds a temporary reference and is not an ownership API.

A cycle can keep positive reference counts even though no live application root
reaches it. The cyclic collector can discover such unreachable graphs. Generation
details and heuristics vary with the Python patch/build: inspect `gc` documentation
for the runtime you actually run instead of memorizing a fixed generation count.

```python
import gc

before = gc.get_count()
cycle = []
cycle.append(cycle)
del cycle
collected = gc.collect()
print(before, collected)  # counts are observations, not fixed expected values
```

Freed objects do not imply RSS immediately falls. Allocators may reuse arenas/pools
and native extensions can allocate outside Python's tracing. A cache retaining live
objects is not a cyclic-GC defect. Prefer bounded caches, explicit close methods,
context managers and cancellation-aware cleanup over calling `gc.collect()` on
every request. Finalizers are unsuitable for deterministic release.

## Descriptors and method resolution

A descriptor implements `__get__`, `__set__`, or `__delete__`. Properties are data
descriptors; functions are non-data descriptors that create bound methods. For
ordinary instance lookup through `object.__getattribute__`, precedence is roughly:
data descriptor → instance dictionary → non-data descriptor/class attribute →
`__getattr__` fallback if normal lookup raises `AttributeError`.

```python
class NonNegative:
    def __set_name__(self, owner: type, name: str) -> None:
        self.storage = "_" + name

    def __get__(self, instance: object | None, owner: type | None = None) -> object:
        if instance is None:
            return self
        return getattr(instance, self.storage)

    def __set__(self, instance: object, value: int) -> None:
        if value < 0:
            raise ValueError("must be non-negative")
        setattr(instance, self.storage, value)

class Counter:
    value = NonNegative()

counter = Counter()
counter.value = 3
assert counter.value == 3
```

This teaching descriptor assumes a validated integer; a production version must
enforce its runtime type contract too. Prefer a property when only one class needs
the behavior. Descriptors become useful when a reusable attribute policy warrants
the extra indirection.

`instance.method` binds `instance` as the first argument through the function's
descriptor protocol. Inheritance follows the C3 method resolution order shown by
`Class.__mro__`. `super()` means “continue after this class in this instance's MRO,”
not “call my named parent.” In a diamond, cooperative methods should use compatible
signatures, consume their own arguments and call `super()` once. Mixing direct
base calls with cooperative calls can duplicate work. Multiple inheritance needs
consistent protocols; composition is often easier to maintain.

## Decorators and class creation

Decorators run when the decorated definition executes. A wrapper can preserve a
call signature for static tools using `ParamSpec` and preserve runtime metadata
with `wraps`:

```python
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

def traced(function: Callable[P, R]) -> Callable[P, R]:
    @wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print("calling", function.__name__)
        return function(*args, **kwargs)
    return wrapper
```

This synchronous wrapper does not measure awaited coroutine execution. An async
variant must accept/await an awaitable and handle cancellation correctly. A method
decorator can also interact with descriptors; test both bound and unbound access.

Class creation chooses a metaclass, prepares a namespace (`__prepare__`), executes
the class body, and constructs/initializes the class through metaclass `__new__`
and `__init__`. Descriptor `__set_name__` and subclass initialization hooks
participate in the process. Calling the completed class later normally invokes
metaclass `__call__`, which orchestrates instance construction.

Most registration/validation needs fit a class decorator or `__init_subclass__`.
A custom metaclass can enforce class-wide invariants but creates inheritance and
metaclass-conflict costs. At P2 depth, explain this lifecycle and why an ordinary
function or explicit registry is often preferable; writing a framework is optional.

## Structural typing and variance

Structural typing asks whether the operations match; nominal typing asks whether
a declared family matches. `InventoryRepository` lets the memory and JSON adapters
substitute without inheriting a framework. Static compatibility still needs
behavioral contract tests: “has `save`” does not prove failed saves are atomic.

Covariance permits a producer of a subtype where a producer of its base is wanted.
Contravariance permits a consumer of a base where a consumer of its subtype is
wanted. Mutable containers are generally invariant because they both consume and
produce values:

```python
from collections.abc import Sequence

class Animal:
    pass

class Cat(Animal):
    pass

def count_animals(animals: Sequence[Animal]) -> int:
    return len(animals)

cats: list[Cat] = [Cat()]
assert count_animals(cats) == 1  # read-only interface accepts the subtype sequence
```

Treating `list[Cat]` as `list[Animal]` would allow appending a dog to the cat list,
so that assignment is unsafe. `Callable` is contravariant in argument types and
covariant in its return. With legacy `TypeVar`, declare variance on generic classes
where appropriate; modern type-parameter syntax can infer it. Keep interfaces
small and let the checker verify substitutions instead of bypassing them with `Any`.

## Functional techniques

Comprehensions, generators, `map`, `filter`, `partial`, pure functions and immutable
values help isolate transformations. A pure function is easier to test because its
result depends only on its inputs and it does not mutate external state.

```python
from collections.abc import Iterable
from functools import partial

def normalize(prefix: str, value: str) -> str:
    return prefix + value.strip().lower()

def labels(values: Iterable[str]) -> list[str]:
    return list(map(partial(normalize, "sku:"), values))

assert labels([" ABC "]) == ["sku:abc"]
```

Prefer a comprehension if it reads more clearly. `reduce` is useful for a genuine
fold, but an explicit loop is often easier to debug. Laziness can defer errors and
retain upstream resources. Memoization is safe only for suitable inputs and
bounded lifetimes; caching an authorization result indefinitely is not a free
optimization. Python does not eliminate recursive tail calls, so do not convert a
large loop to deep recursion for style alone.

## Serialization boundaries

Serialization converts in-memory state into a transport/storage representation.
It needs a version, schema expectations, encoding rules, and limits. JSON carries
data, not arbitrary Python identity, tuples, timezone types or object methods.
Convert explicitly and validate decoded values:

```python
import json
from fulfillhub.storage import decode_product

raw: object = json.loads('{"tenant":"acme","sku":"keyboard","stock":3}')
product = decode_product(raw)
assert product.stock == 3
```

Never unpickle untrusted bytes: pickle can execute code while loading. A file
extension or internal-looking source does not establish trust. Prefer JSON or an
appropriate constrained binary schema for untrusted exchange; validation remains
necessary. `struct` packs explicit byte layouts and endianness, while protocols
such as MessagePack/Protobuf trade readability for compactness and require schema
and evolution decisions. A smaller payload is not automatically the dominant
latency improvement.

The JSON adapter writes a replacement snapshot before switching in-memory state.
It deliberately does not claim concurrent transactions, durable fsync semantics,
or multi-process coordination. Explain that boundary rather than calling it a database.

## Profiling and complexity

Measure the workload before optimizing. Complexity predicts scaling; profiling
identifies where this implementation spends resources. Use `time.perf_counter()`
for elapsed duration, `timeit` for repeated small operations, `cProfile` for call
costs, and `tracemalloc` for traced Python allocations.

```bash
# Working directory: examples/python-backend-engineering/
uv run --frozen python -m fulfillhub.runtime_lab
```

The lab prints implementation/version/GIL status, disassembles a function, traces
a bounded workload, and profiles it. Allocation peaks are not total process RSS;
native allocations can escape tracing. Profiling itself adds overhead, so compare
baseline and candidate under the same measurement conditions, with equivalent
outputs, repeated runs, warmup, and realistic input sizes.

An O(n²) repeated scan often dominates a micro-optimization to a method call. A
generator may reduce peak memory but add iterator overhead. Record sample size,
runtime, machine context, wall/CPU measurement, and variance. Do not assert fixed
speed ratios in unit tests or report a single noisy timing as a general result.

## Engineering decisions and common mistakes

Use internals to explain evidence, not to replace it. Prefer properties over custom
descriptors for one-off validation, composition over tangled MRO, simple functions
over metaclasses, and explicit serialization schemas over arbitrary object dumps.
Avoid exact bytecode assumptions, “`del` closes everything,” refcount-based logic,
unbounded caches, and unsafe deserialization.

[Exercises, interview and assessment](practice.md) · [Phase project](../project.md) ·
[Phase overview](../index.md) · [Next: Module 4](../module-4/index.md)

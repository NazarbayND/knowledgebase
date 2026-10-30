# Module 3 — Python data model and runtime

**P0/P1 · metaclass implementation is P2**

The data model is the set of protocols connecting syntax to object behavior.
CPython is an implementation of that language, with its own interpreter, memory
management and optimization choices. Separate portable guarantees from observations
of a specific build before using internals to explain production behavior.

## Chapter navigation

Use the [runtime investigations](runtime-investigations.md) for worked descriptor,
MRO, decorator, ownership and profiling experiments after this overview.

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

### Example — mutation changes an object; assignment changes a binding

```python
a = [1, 2]
b = a
c = [1, 2]
print(a == c, a is c)
b.append(3)
print(a, c)
a = [9]
print(a, b)
```

Expected output:

```text
True False
[1, 2, 3] [1, 2]
[9] [1, 2, 3]
```

Initially a and b reference one list; c references a different list with equal
contents. Appending through b changes the shared object. Assigning a new list to
a changes only that name: b still references the original list. Assignment,
argument passing and returning an object do not implicitly copy it.

In a backend, returning a cached dictionary directly can expose shared state.
A caller's modification can change what another request sees. Decide whether
the result is shared and immutable, independently copied, or deliberately mutable.
Returning a reference does not by itself transfer exclusive ownership.

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

### Example — the code can be shared while captured values differ

```python
def multiplier(factor):
    def apply(value):
        return value * factor
    return apply

double = multiplier(2)
triple = multiplier(3)
print(double(4), triple(4))
print(double.__code__ is triple.__code__)
print(double.__code__.co_freevars)
```

Expected output is 8 12, then True, then ('factor',). Both functions use the same
compiled instructions but retain different enclosing bindings. The code object
describes work; the function also supplies globals, defaults and closure cells.
An active call supplies a frame with its current arguments/local execution state.

This is why a closure can retain data after its enclosing call returns, and why
a saved traceback can retain a failed call's large local payload. Keeping every
exception in an unbounded diagnostics list may retain much more than its message.

When reading dis output, identify loading, operations and return. Opcodes and
specialization change across releases; do not turn one instruction listing into
an application compatibility requirement.

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

### Example — the collector cannot free data you still own

```python
import gc

cycle = []
cycle.append(cycle)
cache = {"latest": bytearray(1024)}
del cycle
gc.collect()
print(len(cache["latest"]))
cache.clear()
print(len(cache))
```

Expected output is 1024, then 0. The return value of gc.collect() is deliberately
not asserted. The list cycle has no application owner after del, so cyclic
collection can reclaim it. The bytearray is still reachable through cache and
must remain alive. Clearing cache removes that ownership.

Reclaiming an object is also different from returning memory to the OS. Allocators
can retain regions for reuse, and native libraries can allocate outside Python's
tracing. Rising RSS alone therefore cannot identify a Python reference leak.

Compare repeated equivalent batches: does retained traced memory grow, or does it
plateau while RSS remains high? Inspect caches, unfinished tasks and tracebacks
before changing GC thresholds. Files, sockets and transactions still need explicit
lifetime management; the collector does not know their business cleanup policy.

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

### Example — where self comes from

```python
class Greeter:
    def greet(self, name):
        return f"Hello, {name}"

user = Greeter()
bound = user.greet
print(bound.__self__ is user)
print(bound("Ada"))
print(Greeter.greet(user, "Ada"))
```

Expected output is True followed by Hello, Ada twice. Accessing user.greet invokes
the class function's descriptor and creates a bound method carrying user.
Accessing Greeter.greet does not bind an instance, so the last call supplies it
explicitly. self is a convention, not a keyword inserted into every function.

Properties use related attribute machinery for reads/writes. A data descriptor
takes precedence over an instance dictionary entry; a plain function is a
non-data descriptor. Private backing storage can still be edited deliberately,
so validation descriptors are not security barriers.

For inheritance, inspect the actual instance's MRO. In Leaf(Left, Right), super()
inside Left can reach Right before Root. It means continue after Left in this
resolution order. Cooperative calls need compatible signatures and a consistent
forwarding convention; mixing direct base calls can skip or duplicate behavior.

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

### Example — an async wrapper must await actual execution

```python
import asyncio
from functools import wraps

def trace_async(function):
    @wraps(function)
    async def wrapper(*args, **kwargs):
        print("enter")
        try:
            return await function(*args, **kwargs)
        finally:
            print("exit")
    return wrapper

@trace_async
async def calculate():
    await asyncio.sleep(0)
    return 6

async def main():
    print(await calculate())

asyncio.run(main())
```

Expected output is enter, exit, then 6. Cleanup runs before the value reaches
print. If calculate raises, finally still executes and the error propagates.
A synchronous wrapper returning function(...) would only obtain a coroutine
object; timing that call does not time its later execution.

Class creation is another distinct moment: Python executes a class body to build
a namespace, then the metaclass constructs the class object. Calling the finished
class later constructs an instance. A class decorator or __init_subclass__ often
satisfies registration needs with fewer inheritance constraints than a custom
metaclass. Choose the smallest hook that explains the required behavior.

### P2 example — a metaclass constructs the class, not its instances

```python
class Labelled(type):
    def __new__(metaclass, name, bases, namespace):
        result = super().__new__(metaclass, name, bases, namespace)
        result.label = name.lower()
        return result

class Exporter(metaclass=Labelled):
    pass

print(type(Exporter) is Labelled)
print(Exporter.label)
print(isinstance(Exporter(), Exporter))
```

Expected output is True, exporter, then True. Defining Exporter executes its class
body and lets Labelled create that class object. Exporter() later creates a normal
instance. A metaclass can influence class-wide construction rules; it is a
different hook from wrapping a function or creating one instance.

For a simple label/registry, a class decorator or __init_subclass__ is often
easier to compose. The point is understanding lifecycle and framework behavior,
not introducing metaclasses into ordinary services without a requirement.

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

### Example — compatible behavior without shared inheritance

```python
from typing import Protocol

class Notifier(Protocol):
    def send(self, message: str) -> str: ...

class Email:
    def send(self, message: str) -> str:
        return f"email:{message}"

class SMS:
    def send(self, message: str) -> str:
        return f"sms:{message}"

def notify(provider: Notifier) -> str:
    return provider.send("ready")

print(notify(Email()))
print(notify(SMS()))
```

Expected output is email:ready and sms:ready. Neither implementation inherits
Notifier. A checker verifies compatible operations, not whether a provider really
delivered a message; delivery needs a behavioral/integration contract.

Generics preserve type relationships: taking Sequence[T] and returning T retains
the element type. Any discards checking instead of expressing that relationship.

Imagine treating list[Dog] as list[Animal]. A caller could append a Cat through
the Animal alias, violating the Dog list's original promise. A read-only Sequence
does not expose that append, so reading Dogs as Animals is safe. A handler accepting
every Animal can also handle a Dog-specific task, while a Dog-only handler cannot
handle arbitrary Animals. Trace the unsafe operation to understand variance.

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

### Example — pure rules versus repeatable effects

```python
def remaining(stock: int, quantity: int) -> int:
    if quantity <= 0 or quantity > stock:
        raise ValueError("invalid reservation")
    return stock - quantity

print(remaining(5, 2))
print(remaining(5, 2))
```

Both calls print 3. Inputs determine the answer without modifying external state.
That makes the rule easy to test, but it does not reserve anything in a real
database. Persistence still needs a transaction.

Contrast a helper that increments a global counter: retries repeat its effect,
and tests can depend on execution order. A useful design keeps calculations
relatively pure and gives side effects an explicit application boundary.

Comprehensions, partial and generators help when they clarify the transformation.
Laziness avoids intermediates only if consumers stay incremental. lru_cache retains
arguments/results; a maximum entry count is not a byte limit, and mutable cached
results can be shared between callers. Choose ownership and freshness before
memoizing data derived from permissions or changing remote state.

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

### Example — serialization preserves a representation, not every Python type

```python
import json

original = {"coordinates": (10, 20)}
payload = json.dumps(original)
restored = json.loads(payload)
print(payload)
print(type(restored["coordinates"]).__name__)
print(restored == original)
```

Expected output:

```text
{"coordinates": [10, 20]}
list
False
```

JSON has arrays, not tuples. Datetimes, Decimal values and bytes also need explicit
encoding contracts. Decoding an apparently correct dictionary does not validate
field types, tenant ownership or domain rules.

Pickle can invoke behavior while reconstructing objects, so untrusted bytes must
not be loaded with it. A queue or Redis key does not automatically make data trusted.
Protocol Buffers, Avro and MessagePack make different schema/evolution/compactness
choices. Representation is distinct from HTTP, gRPC or broker transport behavior.
Choose compatibility and trust contracts first, then measure encoding cost.

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

### Example — optimize the dominant part of the request

Suppose an illustrative 900 ms request spends 800 ms on a database path, 80 ms
waiting for HTTP, 15 ms serializing and 5 ms calculating. Eliminating the Python
calculation cannot remove the other 895 ms. These are hypothetical nonoverlapping
intervals, not benchmark results.

First trace queue/pool wait separately from remote execution. Profile CPU when
computation is plausible, compare tracemalloc snapshots for retained allocations,
then benchmark an equivalent candidate repeatedly. Recheck correctness before
claiming an improvement.

Repeated list membership can require O(n²) work for n queries over n values.
Building a set costs average O(n) and extra memory but can make those queries
average O(n) overall. For one tiny query, construction can cost more than it saves.

The existing performance_lab includes construction and checks equivalent counts.
Its timings and allocation peaks vary: they are neither promised speed ratios
nor total process memory. Record input, repetitions, instrumentation and excluded
setup before using a measurement to justify architecture.

## Engineering decisions and common mistakes

Use internals to explain evidence, not to replace it. Prefer properties over custom
descriptors for one-off validation, composition over tangled MRO, simple functions
over metaclasses, and explicit serialization schemas over arbitrary object dumps.
Avoid exact bytecode assumptions, “`del` closes everything,” refcount-based logic,
unbounded caches, and unsafe deserialization.

[Exercises, interview and assessment](practice.md) · [Phase project](../project.md) ·
[Phase overview](../index.md) · [Next: Module 4](../module-4/index.md)

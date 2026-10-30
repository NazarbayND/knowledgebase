# Module 1 — Python language semantics

**P0 · language review for experienced engineers**

Python binds names to objects and lets protocols drive behavior. Understanding
those mechanisms prevents mutation bugs and makes later API and concurrency code
easier to reason about. Unlike a TypeScript type annotation, neither a Python
annotation nor an interface description validates runtime input by itself.

## Chapter navigation

For detailed applications and solutions, continue with the
[ownership and streaming walkthrough](worked-examples.md) after these chapters.

1. [Execution and truthiness](#execution-and-truthiness)
2. [Identity and copying](#identity-and-copying)
3. [Built-in values and collections](#built-in-values-and-collections)
4. [Function parameters](#function-parameters)
5. [Scope and closures](#scope-and-closures)
6. [Iteration and laziness](#iteration-and-laziness)
7. [Exceptions](#exceptions)
8. [Context managers](#context-managers)
9. [Practical standard library](#practical-standard-library)

## Execution and truthiness

Python executes a module's top-level statements when first importing it in an
interpreter session; importing is not just a type declaration. A function body runs
when called. Indentation defines suites, so mixing tabs/spaces can change or reject
structure. An expression produces a value; a statement such as `if`, `for`, or
`return` controls execution. Use the `if __name__ == "__main__":` guard to keep CLI
startup out of imports.

False values include `None`, `False`, numeric zero, and empty collections. Custom
objects may define `__bool__` or `__len__`. `and` and `or` short-circuit and return
an operand rather than forcing a boolean:

```python
name = "" or "anonymous"  # "anonymous"
items = []
if not items:
    print("empty")
timeout = 0
configured = timeout if timeout is not None else 30  # preserves a meaningful zero
```

Do not mechanically translate JavaScript truthiness: empty arrays/objects are
truthy in JavaScript but false in Python; the string `"0"` is true in both. Use
`is None` for missing values instead of conflating absence with zero or emptiness.

### Example — an explicit zero is different from no setting

```python
def wrong_timeout(value):
    return value or 30

def configured_timeout(value):
    return 30 if value is None else value

print(wrong_timeout(0))
print(configured_timeout(0))
print(configured_timeout(None))
```

Expected output is 30, 0, then 30. The first function asks whether the value is
truthy, so zero selects the fallback. The second asks whether the caller supplied
the absence marker. The right behavior depends on the setting's contract.

and/or return selected operands, not necessarily booleans. This is useful for
defaults but dangerous when zero, False or an empty collection is meaningful.
A backend page limit, feature switch or retry count needs a deliberate rule;
validation should reject forbidden zeroes explicitly rather than replace them by
accident. Unlike JavaScript, an empty Python list or dict is false.

### Control flow — distinguish a completed search from an early exit

```python
def first_even(values):
    for value in values:
        if value < 0:
            continue
        if value % 2 == 0:
            break
    else:
        return None
    return value

print(first_even([-2, 3, 4, 6]))
print(first_even([1, 3]))
```

The results are 4 and None. continue skips the negative candidate. break ends
the search at the first accepted even value; the loop's else executes only when
no break occurred. An empty input also reaches else. This is loop completion
behavior, not the else attached to an if.

For a simple search, returning directly inside the loop is often clearer.
Understand for/while, continue, break, early return and conditional expressions
before choosing the shortest spelling. A condition checking truthiness may still
conflate a valid zero with absence, so keep the result contract explicit.

## Identity and copying

Assignment copies a reference, not an object. `==` invokes value comparison;
`is` checks whether both operands refer to the same object. Use `is` for `None`
and deliberate sentinels, not strings or integers: interning is an implementation
detail, not an equality contract.

```python
from copy import deepcopy

original = {"tags": ["backend"]}
alias = original
shallow = original.copy()
deep = deepcopy(original)
shallow["tags"].append("python")
assert alias is original
assert original["tags"] == ["backend", "python"]
assert deep["tags"] == ["backend"]
```

A shallow copy creates a new outer container but shares its referenced values.
A deep copy recursively copies supported objects and preserves relationships via
a memo; it is not a way to duplicate sockets, transactions, or arbitrary ownership.
Prefer explicit domain copies or immutable values to defensive deep-copying entire
graphs. A tuple is immutable, but a list inside that tuple can still mutate.
The inventory project uses frozen products with primitive fields so returning a
product cannot mutate repository stock through an alias.

### Example — copying only the outside leaves the inside shared

```python
original = {"tags": ["backend"]}
copied = original.copy()
copied["tags"].append("python")
print(original is copied)
print(original["tags"] is copied["tags"])
print(original["tags"])
```

Expected output is False, True, then ['backend', 'python']. There are two outer
dictionaries and one inner list. copy() duplicates the mapping's references,
not every referenced object.

For nested state, rebuild the changed branch, choose immutable child values, or
use deep copying where its object semantics are appropriate. Do not assume a
frozen outer dataclass makes a nested list immutable. In a response cache this
mistake can let one request modify the value later served to another.

## Built-in values and collections

| Value | Model and engineering consequence |
| --- | --- |
| `int` | Arbitrary precision; arithmetic cost grows with magnitude |
| `float` | Binary floating point; `0.1 + 0.2` need not equal `0.3`; use `Decimal` or minor units for money |
| `bool` | A subclass of `int`; validate quantities so `True` is not accepted as one item |
| `str` | Immutable Unicode text; encode/decode explicitly at I/O boundaries |
| `bytes` | Immutable bytes; indexing yields an integer, not a one-character string |
| `None` | A singleton representing absence, distinct from an empty value |
| `list` | Mutable sequence; indexing O(1), append amortized O(1), middle insert O(n) |
| `tuple` | Fixed sequence; useful for records, hashable only when its elements are hashable |
| `set` | Unique hashable values; membership average O(1), iteration order not a business contract |
| `dict` | Insertion-ordered mapping with hashable keys; lookup average O(1) |

Slices use `start:stop:step`, exclude `stop`, and generally create a new sequence
for lists/tuples/strings. A list slice remains shallow. Comprehensions express
mapping/filtering; avoid side effects and nested comprehensions that hide the
logic. Their loop variables do not leak into the containing scope in Python 3.

```python
prices = {"a": 10, "b": 0, "c": 20}
available = [sku for sku, price in prices.items() if price > 0]
assert available == ["a", "c"]
assert available[::-1] == ["c", "a"]
```

Choose based on operations: `deque` for FIFO work, set for membership, dict for
keyed lookup. Hash/equality must remain consistent; mutable objects are usually
poor keys. Do not mutate a dict's size while iterating over it.

### Example — choose the container from the operation

```python
from collections import deque

pending = deque(["a", "b"])
pending.append("c")
print(pending.popleft())
print(list(pending))

keys = {True: "flag", 1: "quantity"}
print(len(keys), keys[True])
```

Expected output is a, then ['b', 'c'], then 1 quantity. deque removes from the
front without shifting every remaining list element. The dictionary example has
one key because True and 1 compare equal with compatible hashes.

Lists suit indexed sequences; sets suit membership; dicts suit keyed lookup.
Tuple fields can themselves reference mutable values, and only hashable elements
make a tuple usable as a key. str is Unicode text; bytes is encoded data and
indexing bytes produces an integer. For money, choose Decimal or minor units with
rounding/currency rules instead of assuming binary floats exactly represent cents.

## Function parameters

Functions create local bindings to passed objects. Rebinding a parameter does not
rebind the caller's variable, but mutating a passed list changes that shared list.
Defaults are evaluated once when the definition executes, not on every call.

```python
def collect(value: str, items: list[str] | None = None) -> list[str]:
    result = [] if items is None else list(items)
    result.append(value)
    return result

def reserve(tenant: str, sku: str, /, *, quantity: int = 1) -> tuple[str, str, int]:
    return tenant, sku, quantity

assert reserve("acme", "keyboard", quantity=2) == ("acme", "keyboard", 2)
```

`/` makes earlier parameters positional-only; `*` makes following parameters
keyword-only. `*args` collects extra positional arguments in a tuple; `**kwargs`
collects keyword arguments in a dict. Call-site unpacking expands a sequence or
mapping. Duplicate arguments raise `TypeError`. Prefer explicit named parameters
at service boundaries to unlimited `**kwargs`, which conceals the supported API.

The example copies a caller-owned list deliberately. A function that promises
in-place mutation should document that different ownership contract. Avoid using
`items or []` when callers may intentionally pass an empty container to mutate.

### Example — defaults are created when def executes

```python
def add_bad(value, history=[]):
    history.append(value)
    return history

first = add_bad("created")
second = add_bad("reserved")
print(first)
print(first is second)

def add_good(value, history=None):
    result = [] if history is None else list(history)
    result.append(value)
    return result

print(add_good("created"))
print(add_good("reserved"))
```

Expected output is ['created', 'reserved'], True, ['created'], then ['reserved'].
Both bad calls use the same definition-time list, and first still references it
when the second call mutates it. The good version creates independent output and
also copies explicitly supplied history.

That copy is an ownership choice: a deliberately in-place API would instead
document mutation. Keyword-only parameters such as quantity make call meaning
clear; *args/**kwargs are useful for forwarding, but can hide unsupported business
arguments if used without a clear contract.

## Scope and closures

LEGB means local, enclosing function, global module, builtins. Assignment normally
makes a name local throughout that function; reading it before assignment raises
`UnboundLocalError`. `global` and `nonlocal` change rebinding scope. Prefer passing
dependencies over mutating module globals.

Closures retain bindings in enclosing scopes; loop-created closures resolve those
bindings when called. This is similar to a JavaScript `var` closure problem,
although Python does not give a `for` loop a fresh block scope:

```python
late = [lambda: i for i in range(3)]
bound = [lambda i=i: i for i in range(3)]
assert [f() for f in late] == [2, 2, 2]
assert [f() for f in bound] == [0, 1, 2]
```

A lambda is a function restricted to one expression, not a separate execution
model. A decorator replaces a function at definition time: `@trace` means
`function = trace(function)`. Use `functools.wraps` for metadata and keep the
wrapper's return/exception behavior. Async wrappers must `await` the wrapped call;
returning a coroutine accidentally is a different contract.

### Example — a closure reads a binding when called

```python
late = [lambda: i for i in range(3)]
bound = [lambda i=i: i for i in range(3)]
print([function() for function in late])
print([function() for function in bound])
```

Expected output is [2, 2, 2], then [0, 1, 2]. The first functions share the loop
binding and read its final value. The second evaluate each default during that
function's creation.

LEGB explains where names are found, but assignment also affects scope. A function
assigning a name normally treats it as local throughout its body, so reading it
first can raise UnboundLocalError. nonlocal changes rebinding of an enclosing
name; it does not copy closure state. This matters for callbacks, decorators and
request factories that accidentally capture shared mutable configuration.

## Iteration and laziness

An iterable produces an iterator via `iter(obj)`; an iterator provides `next()`
until `StopIteration`. A generator function containing `yield` returns a generator
when called and suspends execution between yielded values. Unlike a list, a
generator is normally one-shot, defers work/errors, and cannot be indexed.

```python
from collections.abc import Iterator

def valid_lines(lines: list[str]) -> Iterator[str]:
    for line in lines:
        text = line.strip()
        if text:
            yield text

stream = valid_lines([" first ", "", " second "])
assert next(stream) == "first"
assert list(stream) == ["second"]
assert list(stream) == []
```

Lazy pipelines reduce retained intermediates, not necessarily CPU cost. They can
retain resources in suspended frames; consume them inside the resource owner's
scope. If callers need repeated traversal, return a collection or a factory for
fresh iterators. `yield from` delegates iteration; do not raise `StopIteration`
manually inside a generator to signal normal completion—use `return`.

### Example — laziness delays both work and errors

```python
def quantities():
    print("read first")
    yield 3
    print("read second")
    yield 2

values = quantities()
print("created")
print(next(values))
print(list(values))
print(list(values))
```

Expected output is created, read first, 3, read second, [2], then [].
Calling the generator function creates an iterator without running the body.
Each advance resumes it until yield/return/error. Exhaustion is persistent;
calling list again does not rewind it.

A generator can save retained intermediates, but errors now occur during
consumption and suspended locals can keep resources alive. Consume inside the
owner's context or materialize a small result deliberately. An iterable can
produce an iterator; an iterator generally represents one traversal.

## Exceptions

Exceptions propagate until a matching handler is found. Define a small domain
hierarchy so callers can catch business failures without treating programming
defects as expected outcomes. `else` runs when the `try` suite succeeds; `finally`
runs on normal and exceptional exits. A `return` in `finally` can suppress an error.

```python
class InvalidInventory(ValueError):
    pass

def parse_stock(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise InvalidInventory("stock is not an integer") from exc
    else:
        if value < 0:
            raise InvalidInventory("stock must not be negative")
        return value
```

Catch the narrow operation that can fail and preserve causes with `raise ... from
exc`. `raise` alone re-raises the current exception. Avoid broad catches that turn
every defect into an empty result. `Exception` excludes `BaseException` subclasses
such as `KeyboardInterrupt`, `SystemExit`, and `asyncio.CancelledError`; cleanup
should run while those signals still propagate.

### Example — preserve the cause and understand else/finally

```python
def parse_quantity(raw):
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError("invalid quantity") from exc
    else:
        return value
    finally:
        print("finished parsing")

try:
    parse_quantity("bad")
except ValueError as error:
    print(str(error))
    print(type(error.__cause__).__name__)
```

Expected output is finished parsing, invalid quantity, then ValueError.
The parsing operation failed, else did not run, and finally ran before the new
error reached the caller. Chaining retains the underlying cause for diagnosis.

Catch the smallest expected failure. Catching everything and returning zero
would make invalid input look like a legitimate business value. Returning from
finally can suppress an error; cleanup should normally preserve the outcome.

## Context managers

`with` expresses scoped acquisition/release through `__enter__` and `__exit__`.
The exit method receives exception information and can suppress an exception by
returning true. Most resource managers should clean up and allow propagation.
`contextlib.contextmanager` implements the same protocol with a generator:

```python
from contextlib import contextmanager
from pathlib import Path
from collections.abc import Iterator
from typing import TextIO

@contextmanager
def text_input(path: Path) -> Iterator[TextIO]:
    stream = path.open(encoding="utf-8")
    try:
        yield stream
    finally:
        stream.close()
```

The function acquiring a file owns closing it unless ownership is explicitly
transferred. Do not return a lazy reader from inside an already-exited `with`.
`ExitStack` helps with a dynamic number of resources. Async resources use `async
with` and awaitable enter/exit methods. Garbage collection timing is not a reliable
resource-lifecycle strategy across Python implementations.

### Example — cleanup still runs when the consumer fails

```python
from contextlib import contextmanager

@contextmanager
def owned(events):
    events.append("acquire")
    try:
        yield "resource"
    finally:
        events.append("release")

events = []
try:
    with owned(events) as resource:
        events.append(resource)
        raise RuntimeError("consumer failed")
except RuntimeError:
    events.append("caught")
print(events)
```

Expected output is ['acquire', 'resource', 'release', 'caught']. The generator
pauses at yield while the body runs; an exceptional exit resumes cleanup before
the outer handler receives the error. A class-based manager expresses this with
__enter__/__exit__, where returning a truthy value can suppress the exception.

Apply the same ownership rule to files, locks and clients. Returning an iterator
over a file that has already left its with scope violates it. Garbage collection
is not a substitute for deterministic release.

## Practical standard library

Use explicit text encodings and `newline=""` for CSV files. JSON is an exchange
format, not a type validator; check the decoded object shape before constructing
domain values. Dates need an agreed timezone and serialization contract.

```python
import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

def summarize(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as stream:
        counts = Counter(row["sku"] for row in csv.DictReader(stream))
    return json.dumps({"at": datetime.now(UTC).isoformat(), "counts": dict(counts)})
```

- `pathlib`: compose paths with `/`, not platform-specific string concatenation.
- `collections`: `Counter` counts, `defaultdict` groups, `deque` provides efficient ends.
- `itertools`: `islice` bounds a stream; `groupby` groups consecutive keys and often requires sorting first.
- `functools`: `partial` binds arguments; `wraps` preserves metadata; `lru_cache` retains keys/results and needs bounded growth and suitable inputs.
- `re`: use raw strings for patterns and `fullmatch` for whole-value validation;
  a pattern such as `r"[A-Z][A-Z0-9-]{0,31}"` describes a constrained SKU.

Regex is not a parser for arbitrary nested structures. JSON/CSV files may be large
or malformed; decide size limits and error boundaries before processing untrusted
inputs. A naive local `datetime` is not an unambiguous global timestamp.

### Example — a timestamp is a contract, not just a string

```python
import json
from datetime import UTC, datetime
from pathlib import PurePosixPath

at = datetime(2026, 1, 2, 12, tzinfo=UTC)
path = PurePosixPath("reports") / "inventory.json"
print(str(path))
print(json.dumps({"generated_at": at.isoformat(), "units": 5}))
```

Expected output is reports/inventory.json and a JSON object whose timestamp is
2026-01-02T12:00:00+00:00. Datetime was converted explicitly because default JSON
encoding does not serialize arbitrary Python objects.

pathlib expresses path operations; csv handles quoting that split(",") misses.
Counter aggregates keys, islice limits consumption, groupby groups consecutive
keys, partial binds arguments, and fullmatch validates a whole string. Each tool
has a semantic boundary. In a report pipeline, define encoding, timezone, invalid
row handling and whether partial consumption is allowed before choosing utilities.

## Engineering decisions and common mistakes

Prefer explicit ownership to hidden mutation, domain errors to magic sentinel
values, and readable loops to clever nested expressions. Eager collections make
repeatable small data easy; lazy iterators make large streams possible at the cost
of lifetime and consumption constraints. Benchmark only after choosing the correct
data structure and behavior.

**Self-check:** explain why a shallow copy is insufficient for nested mutable
data; why `None` differs from zero; when a generator holds a file open; and where
an exception should become a domain error.

[Exercises, 12 predictions, interview and assessment](practice.md) ·
[Phase overview](../index.md) · [Next: Module 2](../module-2/index.md)

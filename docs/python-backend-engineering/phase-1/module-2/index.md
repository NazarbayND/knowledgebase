# Module 2 — Professional Python development

**P0 · typed boundaries, packages, and reliable feedback**

Professional Python combines runtime invariants with static analysis and behavioral
tests. The goal is a package whose API is clear, whose dependencies are repeatable,
and whose implementation can change without invalidating callers.

## Chapter navigation

1. [Objects and composition](#objects-and-composition)
2. [Data classes and domain values](#data-classes-and-domain-values)
3. [Typing interfaces](#typing-interfaces)
4. [Static checking](#static-checking)
5. [Modules and imports](#modules-and-imports)
6. [Packaging and environments](#packaging-and-environments)
7. [Quality tools and testing](#quality-tools-and-testing)

## Objects and composition

An object combines state with behavior. Inheritance is appropriate for a stable
substitution relationship; composition delegates work to another object. Python's
polymorphism often comes from compatible operations rather than a shared base.
For FulfillHub, the service accepts a repository and owns business decisions;
the repository owns storage:

```python
from fulfillhub.inventory import InventoryService, MemoryRepository, Product

repository = MemoryRepository([Product("acme", "keyboard", 3)])
service = InventoryService(repository)
assert service.reserve("acme", "keyboard", quantity=2).stock == 1
```

Swapping the repository should not change reservation behavior. Avoid a service
subclass for every storage backend; that couples two independent reasons to change.
The JSON repository composes the in-memory repository, reusing value lookup while
adding file persistence.

Special methods participate in protocols: `__len__` supports length/truthiness,
`__iter__` iteration, `__eq__` equality, `__repr__` debugging. Python looks many of
these up on the type rather than the instance. Implement only operations that make
semantic sense: treating an inventory service as a list can conceal side effects.
Do not use inheritance merely to share two utility methods.

## Data classes and domain values

Dataclasses generate initialization, representation and equality from declared
fields. `frozen=True` prevents normal field assignment but does not recursively
freeze a nested list. `slots=True` removes the ordinary per-instance dictionary
for that class and can reduce overhead; it is not a security mechanism.

```python
from dataclasses import dataclass
from enum import StrEnum

class State(StrEnum):
    OPEN = "open"
    CLOSED = "closed"

@dataclass(frozen=True, slots=True)
class Ticket:
    state: State
    attempts: int = 0

    def __post_init__(self) -> None:
        if self.attempts < 0:
            raise ValueError("attempts must be non-negative")

    @property
    def can_retry(self) -> bool:
        return self.state is State.OPEN and self.attempts < 3
```

Use an enum for a closed set of states and a property for cheap derived behavior.
A property should not unexpectedly make a network call. Mutable fields need
`field(default_factory=list)` to create one collection per instance.

An abstract base class (`abc.ABC`, `@abstractmethod`) declares a nominal runtime
family and can share implementation. Choose it when subclass participation and a
common lifecycle are intentional. A structural `Protocol` is often a smaller
coupling for adapters you do not own.

## Typing interfaces

Annotations communicate constraints to tools. They do not run validators when a
function is called. `TypedDict` describes the expected keys of a plain dict;
`Protocol` describes supported operations; generics preserve relationships between
types. Validate JSON first, then build a typed domain object.

```python
from collections.abc import Callable, Sequence
from typing import Protocol, TypedDict, TypeVar

class ProductPayload(TypedDict):
    tenant: str
    sku: str
    stock: int

class Lookup(Protocol):
    def get(self, tenant: str, sku: str) -> object: ...

T = TypeVar("T")
U = TypeVar("U")

def transform(values: Sequence[T], function: Callable[[T], U]) -> list[U]:
    return [function(value) for value in values]

assert transform([1, 2], str) == ["1", "2"]
```

Modern Python also supports `def first[T](items: Sequence[T]) -> T:`. Learn the
`TypeVar` form to read older libraries and understand binding. Prefer `object` for
an unknown value that must be narrowed; `Any` disables useful checking and can
spread unchecked assumptions. Use `X | None` for optional values and narrow with
`is None`. Never use `cast()` as input validation: it changes a checker's view,
not the object.

An implementation satisfies a Protocol when its method signatures are compatible;
no inheritance is required. `@runtime_checkable` permits limited member-presence
checks, not full signature or business-contract verification.

## Static checking

Strict mypy checks annotated calls, return paths, generic use and unexpected `Any`
in application source. It catches a bad service call before execution; pytest
catches a correctly typed method returning the wrong stock. Both are needed.

From `examples/python-backend-engineering/`:

```bash
uv run --frozen mypy
```

The configuration lives in `pyproject.toml` with `strict = true` and `files =
["src"]`. Tests exercise dynamic failure inputs and are checked by pytest/Ruff;
the strict type-check target is the package source. For a deliberate type failure,
make a temporary copy of a client and pass `quantity="2"`; mypy should reject it.
Do not leave the failure in the package or add blanket ignore comments to pass.

Pyright can serve the same role, but running two checkers is not required for this
course. Pin the chosen checker and enable strictness gradually in legacy code.
Type correctness does not establish tenant authorization, race freedom, or
validated external data.

## Modules and imports

A module is a namespace loaded through the import system. A package groups modules;
an `__init__.py` makes an ordinary package, while namespace packages are a deliberate
advanced option. Python caches loaded modules in `sys.modules`.

The example's `src/fulfillhub/` layout separates importable code from the checkout
root. Editable installation makes it available to tests and `python -m` commands
without manually changing `sys.path` or requiring a lucky current directory.

```text
src/fulfillhub/
  inventory.py      # domain, repository protocol, service
  storage.py        # JSON adapter depending on the domain
  aggregation.py    # independent concurrency client
  __main__.py       # composition and CLI entry
tests/               # contract and boundary tests
```

Keep dependency direction toward stable domain interfaces. A circular import can
observe a partially initialized module: moving imports inside functions can hide
the symptom but leave the design tangled. Extract the shared interface, move
composition to an entry point, and keep package initialization lightweight. Do not
name local modules `json.py`, `typing.py`, or `httpx.py` and accidentally shadow
dependencies.

## Packaging and environments

`pyproject.toml` describes build backend, project metadata, runtime dependencies,
development tools, and configuration. Build isolation creates the build backend's
own environment; the installed wheel contains the declared package, not arbitrary
working-directory files.

A virtual environment isolates installed packages, not the OS, network, database,
or interpreter semantics. The course uses Python 3.14 in its example environment
and Python 3.12 for the independent MkDocs site. `.python-version` selects the course
runtime for uv, and `requires-python` declares supported versions.

```bash
cd examples/python-backend-engineering
uv python install 3.14
uv sync --frozen
uv run --frozen python -m fulfillhub
```

`uv.lock` records the resolved graph. `uv sync --frozen` consumes it without
rewriting it. Change dependencies deliberately, regenerate the lockfile, inspect
the diff, and rerun checks. pip can install packages and resolved requirements in a
virtual environment; it does not consume `uv.lock`. The site therefore has its own
pinned `requirements.txt`. Do not share one global environment across subjects.

## Quality tools and testing

Ruff checks static mistakes and import ordering; its formatter standardizes layout.
Neither proves behavior. pytest discovers test functions, reports counts, and
supports isolated fixtures and parametrized cases. Fixture scope determines
lifetime; mutable session-scoped fixtures can leak state between tests.

```python
import pytest
from fulfillhub.inventory import InventoryService, MemoryRepository, Product

@pytest.mark.parametrize("quantity,remaining", [(1, 2), (3, 0)])
def test_reserve(quantity: int, remaining: int) -> None:
    repository = MemoryRepository([Product("acme", "keyboard", 3)])
    result = InventoryService(repository).reserve("acme", "keyboard", quantity=quantity)
    assert result.stock == remaining
```

Run from the examples directory:

```bash
uv run --frozen pytest
uv run --frozen ruff check .
uv run --frozen ruff format --check .
```

Test observable guarantees: rejected reservations leave state unchanged, original
values do not mutate, different tenants' keys do not collide, and storage survives
reopening. Parametrize the repository contract over memory/JSON implementations.
Use `tmp_path` for filesystem isolation.

Mock slow or nondeterministic boundaries when it clarifies a failure: replace the
file-replacement operation to prove a failed save cannot mutate memory. Patch the
name looked up by the code under test. Do not mock every internal method and merely
verify call order; a refactor should be allowed to change implementation. Keep a
real boundary test too—HTTP transport mocks alone do not prove sockets work.

## Engineering decisions and common mistakes

Choose composition for replaceable storage, frozen values for clear ownership,
runtime validation at external boundaries, and a small Protocol for static
substitution. Avoid service/repository inheritance trees, `Any` everywhere, global
test fixtures, hidden import side effects, and lockfile changes caused by ordinary
installation. Passing quality tools is necessary evidence, not the whole senior
engineering assessment.

[Exercises, interview and mastery assessment](practice.md) ·
[Inventory project](../project.md) · [Phase overview](../index.md) ·
[Next: Module 3](../../phase-2/module-3/index.md)

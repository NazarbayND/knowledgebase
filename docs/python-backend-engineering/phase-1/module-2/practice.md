# Module 2 — Practice and assessment

Use the [professional development chapters](index.md) and the
[inventory project](../project.md). Work from
`examples/python-backend-engineering/` for all commands below.

## Exercises

1. **Composition and polymorphism:** inject a repository into a reservation service.
   Implement memory and JSON adapters with the same observable contract. The service
   must not branch on the adapter's concrete type. Add `__repr__` or iteration only
   if a meaningful public use case requires it.
2. **Domain values:** model products with a dataclass, a stock-status enum and a
   derived property. Reject invalid construction. Demonstrate why a frozen dataclass
   with a list field is not deeply immutable, then choose a safer field representation.
3. **ABC vs Protocol:** sketch an ABC-based plugin with one abstract method, then
   model the inventory adapter boundary as a Protocol. Explain why structural typing
   reduces coupling here without removing runtime contract tests.
4. **Typing:** describe an incoming payload with `TypedDict`, validate it as an
   unknown `object`, and convert it into a Product. Write a generic mapping function
   using `TypeVar`/`Callable` or equivalent modern syntax. Deliberately pass a wrong
   argument in a temporary client and verify mypy rejects it.
5. **Imports and packages:** draw the import dependency direction. Move CLI startup
   out of module imports. Explain how a circular import can expose incomplete state
   and refactor shared interfaces rather than adding `sys.path` modifications.
6. **Reproducibility:** create the project environment with `uv sync --frozen`,
   inspect the dependency declarations and lockfile, and explain why pip cannot
   directly consume that lockfile. Run the installed package from outside its source
   directory to check it does not rely on accidental import paths.
7. **Feedback and boundaries:** use parametrized fixtures for both adapters. Inject
   a filesystem replacement failure and prove neither memory nor the saved snapshot
   changes. Distinguish this boundary test from a pure unit test and a socket-level
   integration test. Run Ruff formatting/linting as separate checks.

## Refactoring challenge

Begin with this intentionally poor design in a scratch file:

```python
stock = {"keyboard": 3}

def reserve(sku, amount):
    stock[sku] -= amount
    return stock
```

First list failures: negative amount increases stock, insufficient stock can go
negative, callers can mutate the returned dictionary, tenant keys collide, and
global state leaks across tests. Add reproducing tests before designing a typed
service and repository. Explain what the refactor still does not solve: storage
durability, authentication, transactions and multi-process concurrency.

## Validation

```bash
uv run --frozen pytest
uv run --frozen mypy
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen python -m fulfillhub
```

Passing type checks prove static compatibility, not correct business behavior.
Negative tests must assert unchanged state, not just that an exception was raised.

## Interview practice

- What should a repository own, and what belongs in a service?
- When would an ABC be preferable to a Protocol? Can runtime Protocol checks verify signatures?
- What does `TypedDict` validate at runtime? How do `Any`, `object` and `cast` differ?
- Why use a `src` layout, editable installation and a lockfile?
- When is mocking helpful, and how can mocking every call make refactors harder?
- Which defects can mypy, Ruff and pytest each detect? Which can none prove absent?

??? note "Expected reasoning"
    A repository adapts storage; a service makes domain decisions. A Protocol
    supports structural substitution, while an ABC can define an intentional
    runtime family with shared behavior. TypedDict/cast do not validate decoded
    JSON. `object` requires narrowing; `Any` permits unchecked operations. A
    contract test should survive an internal refactor. Installation and a `src`
    layout expose packaging assumptions; locking controls resolution drift.

## Mastery assessment

Timebox: **75 minutes refactoring + 15 minutes explanation**.

| Dimension | Evidence | Points |
| --- | --- | ---: |
| Concepts | Explain dataclass immutability, structural typing, imports and locking | 25 |
| Correctness | Package with two adapters, passing strict typing and contract tests | 30 |
| Debugging | Regression tests for mutation, invalid quantity and failed persistence | 20 |
| Decisions | Justify composition, dependency direction and unit/integration boundaries | 15 |
| Communication | Reproducible README and concise review of limitations | 10 |

Target **80/100**. All project invariants and required tool checks must pass before
claiming Phase 1 mastery. Record commands, results, score, and weak areas in
[progress](../../progress.md).

[Module 2](index.md) · [Phase 1 project](../project.md) ·
[Next: Module 3](../../phase-2/module-3/index.md)

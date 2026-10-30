# Phase 1 — Cumulative assessment and model review

**Goal:** demonstrate independent command of semantics, typed design, package
boundaries and behavioral tests. Work after Modules 1–2 and the
[inventory project](project.md). Review the [worked semantics](module-1/worked-examples.md)
and [design walkthrough](module-2/design-and-testing.md) only after your first attempt.

Allocate about **90 minutes**: 15 concepts, 40 implementation, 15 debugging,
10 design review and 10 explanation. Fit the assessment into the existing weekly
implementation/interview budget; it does not add a new week to the course.

## A. Explain the behavior — 25 points

Each question is worth five points: one for the result, three for the mechanism,
and one for a practical consequence.

1. A frozen dataclass contains a `list[str]`. Can callers append to it? What would
   you change if the value must be safe to share between service boundaries?
2. `callbacks = [lambda: index for index in range(3)]`. What do three calls return?
   Show two fixes and explain when their binding happens.
3. Why can `True` pass an integer type check? What can go wrong if it is accepted
   as inventory stock or as a dictionary key mixed with integer identities?
4. A generator is created inside a `with` block but consumed after it. When will
   the bug occur, and what two API designs can repair the ownership contract?
5. A dictionary fits a `TypedDict` annotation but came from untrusted JSON. Which
   guarantees still need runtime checks, and why does `cast` not supply them?

??? note "Concept model answers"
    1. Freezing prevents normal field assignment, not list mutation. Use an
       immutable representation such as a tuple, or explicitly transfer/copy
       mutable ownership. Choose based on the API contract.
    2. Calls return `[2, 2, 2]` because the functions read the final enclosing loop
       binding. Default arguments, `partial`, or a factory can bind each value.
    3. bool subclasses int; `True == 1` and equal hashes make those dictionary keys
       collide. Reject bool for quantities and avoid a mixed identity key domain.
    4. Lazy iteration encounters the closed resource when it advances. Materialize
       within the scope if small, or expose a context manager owning the iterator.
    5. Check shape, field types, required keys and domain constraints. Static type
       descriptions/casts do not execute validators or convert the object.

## B. Implement a low-stock view — 30 points

Add a pure query function to your own attempt at the inventory package:

```python
def low_stock(repository, tenant, *, threshold):
    ...
```

Requirements:

- Give it a fully annotated interface using the repository Protocol.
- Require a non-negative integer threshold; reject bool.
- Return an immutable tuple of the selected tenant's Products with stock **less
  than or equal to** threshold, sorted by SKU.
- Preserve the repository and original Product values.
- Use the same behavior with memory and JSON repositories.

Use this fixture:

| Tenant | SKU | Stock |
| --- | --- | ---: |
| acme | monitor | 2 |
| acme | keyboard | 0 |
| acme | mouse | 5 |
| other | keyboard | 0 |

For tenant `acme` and threshold two, the result is keyboard then monitor. For an
unknown tenant it is an empty tuple; this query does not use the single-product
lookup contract that raises UnknownSku. State that choice in the docstring.

Scoring: **10** for type/API correctness, **10** for filtering/order/immutability,
**10** for tests proving both adapters and negative inputs. Check state before and
after every rejected threshold case.

??? note "Reference solution — compare after testing your attempt"
    ```python
    from fulfillhub.inventory import InventoryRepository, Product

    def low_stock(
        repository: InventoryRepository, tenant: str, *, threshold: int
    ) -> tuple[Product, ...]:
        """Return a stable ordered view; an unknown tenant has no products."""
        if isinstance(threshold, bool) or not isinstance(threshold, int) or threshold < 0:
            raise ValueError("threshold must be a non-negative integer")
        selected = (
            product for product in repository.all()
            if product.tenant == tenant and product.stock <= threshold
        )
        return tuple(sorted(selected, key=lambda product: product.sku))
    ```

    The generator filters once and sorting materializes the selected products.
    Sharing these Product values is safe under the reference's immutable field
    contract. This query is not a transactional snapshot across concurrent writers;
    the current adapters assume a single-process/single-writer learning context.

## C. Diagnose two failures — 20 points

**Ten points:** a CSV report sometimes raises “I/O operation on closed file.” The
function returns a lazy reader from inside an already-exited `with`. Reproduce the
bug, show the ownership boundary, repair it, and prove early consumer exit closes
the file. A fix that materializes everything must acknowledge its memory tradeoff.

**Ten points:** after a rejected reservation, a later valid request sees too little
stock. The service decremented before checking availability. Write a regression
test that asserts full state equality after rejection, move validation before the
save, and explain why an exception-only test missed it.

Full credit needs a failing reproduction and an explanation, not only a replacement
function. Use `tests/test_reporting.py` and `tests/test_inventory.py` as references
after attempting your own cases.

## D. Review the design — 15 points

Give a short decision note covering:

- **Five points:** why service composition and a small Protocol fit two storage adapters.
- **Five points:** why JSON replacement does not establish multi-writer transactions
  or crash durability, and what later requirement would motivate a database.
- **Five points:** the tests you keep at unit, adapter-contract and real boundary
  levels; what you mock and what must run for real.

Reject both extremes: no interfaces despite demonstrated substitution needs, and a
generic framework around every three-line helper. Explain the need driving each
boundary.

## E. Communicate the result — 10 points

Give a two-minute walkthrough: problem and invariant, reproduction, final design,
commands/results, and remaining limits. Include one JS/TypeScript/JVM assumption
you had to change. A list of tool names without interpreting their evidence earns
at most half credit.

## Completion and revision

The target is **80/100**, with all required invariants preserved. Rejected inputs
mutating state, leaked owned resources, or silently coerced invalid stock require
revision even if other sections raise the numeric total.

Record your score, evidence paths/commands and the weakest two concepts in
[progress](../progress.md). Start the next session by reproducing those explanations
without the answer key. Do not mark learner progress merely because the supplied
reference suite is green.

[Phase overview](index.md) · [Quick reference](quick-reference.md) ·
[Next: Phase 2](../phase-2/index.md)

# Phase 1 — Python fundamentals: fast review

**Weeks 1–2 · mostly P0** · Prerequisite: experience programming in another language.

Move quickly through syntax and spend time on Python's reference semantics,
resource ownership, interfaces, and test boundaries. The output is a small typed,
tested package that starts FulfillHub's domain without a web framework.

| Module | Chapters | Deliverable |
| --- | --- | --- |
| [1 — Python language semantics](module-1/index.md) | Execution, references, collections, functions, scope, iteration, exceptions, resources, standard library | [Twelve predictions and implementation exercises](module-1/practice.md) |
| [2 — Professional Python development](module-2/index.md) | OOP, data models, typing, checking, packages, tooling, testing | [Typed package and refactoring assessment](module-2/practice.md) |

## Practical project

Build the [inventory manager](project.md) with dataclasses, typed service methods,
two repository implementations, and contract tests. Runnable reference code lives
under `examples/python-backend-engineering/`; use it to compare your solution after
attempting the requirements independently.

## Time and checkpoints

Week 1 uses **3h theory / 5h implementation / 2h interview practice**. Week 2 uses
**4h / 4h / 2h** across Module 2 review and the beginning of Module 3. The overlapping
phase labels do not create an additional week of work.

- [ ] Explain all twelve Module 1 predictions before running the answer key.
- [ ] Implement inventory invariants and prove failure leaves state unchanged.
- [ ] Run pytest, strict mypy, Ruff, and the package demo.
- [ ] Explain composition, structural typing, and the chosen persistence boundary.
- [ ] Score at least 80/100 and record evidence in [progress](../progress.md).

[Subject overview](../index.md) · [Next: Phase 2](../phase-2/index.md)

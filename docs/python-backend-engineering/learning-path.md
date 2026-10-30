# Learning path

Use this page to plan study within [Python Backend Engineering](index.md).
The subject owns its sequence and checkpoints; the library's other subjects can
follow different structures.

## Implemented sequence

| Order | Study | Apply | Checkpoint |
| --- | --- | --- | --- |
| 1 | [Module 1: semantics](phase-1/module-1/index.md) | Reference/mutation, function and resource exercises | [Twelve predictions](phase-1/module-1/practice.md) |
| 2 | [Module 2: professional development](phase-1/module-2/index.md) | [Inventory package](phase-1/project.md) | [Typed package and refactoring](phase-1/module-2/practice.md#mastery-assessment) |
| 3 | [Module 3: data model and runtime](phase-2/module-3/index.md) | Interface substitution and profiler investigation | [Runtime assessment](phase-2/module-3/practice.md#mastery-assessment) |
| 4 | [Module 4: concurrency](phase-2/module-4/index.md) | [Concurrent aggregation project](phase-2/project.md) | [Blocking/cancellation diagnosis](phase-2/module-4/practice.md#mastery-assessment) |

Week 1 is approximately **3h theory / 5h implementation / 2h interview practice**.
Weeks 2 and 3 use **4h / 4h / 2h**. Phase 1 spans weeks 1–2; Phase 2 spans weeks
2–3, sharing week 2 rather than adding a second allocation. Adjust pacing around
assessment evidence rather than advancing with unresolved prerequisites.

**P0** means independently implement and explain. **P1** means apply and justify
tradeoffs. **P2** means conceptual familiarity for now. Metaclasses and free-threaded
internals are selected P2 topics; core semantics and asyncio are P0.

The [whole-course plan](course-plan.md) keeps later HTTP, FastAPI, persistence,
distributed-system and production phases visible without creating those lessons yet.

## Study cycle

1. **Set a goal.** Pick one observable behavior you want to understand or implement.
2. **Read and explain.** Read the relevant chapter and explain the model without
   copying its wording. Record unanswered questions.
3. **Practise.** Complete the exercise and compare its result with the expected
   behavior. Try an edge case or a deliberately invalid input.
4. **Apply.** Use the idea in a practical project. Write down the execution command,
   expected result, and the design decision the exercise helped you make.
5. **Review.** Demonstrate the checkpoint and add evidence to your
   [progress log](progress.md). Revisit anything you cannot explain independently.

## Before starting practical work

- Read the exercise's runtime and dependency requirements.
- Run commands from the working directory specified by the example.
- Keep project environments separate from the site's `.venv`.
- Store credentials outside Git and provide only non-secret example configuration.
- Prefer a small verified change before expanding the project.

## Review a completed unit

Check whether you can explain the main idea, reproduce the result, and diagnose a
failure. Reading completion and implementation completion are separate milestones.
Use the [checkpoint criteria](progress.md#checkpoint-criteria) to make that distinction
explicit.

[Subject overview](index.md) · [Progress & checkpoints](progress.md)

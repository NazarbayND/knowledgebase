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

## Continue through the complete course

| Weeks | Phase and lessons | Review |
| --- | --- | --- |
| 4 | [3 — Networking and HTTP](phase-3/index.md) | [Cumulative HTTP/request review](phase-3/assessment.md) |
| 5–6 | [4 — FastAPI and application architecture](phase-4/index.md) | [API/transaction boundaries](phase-4/assessment.md) |
| 7–8 | [5 — PostgreSQL and persistence](phase-5/index.md) | [Cumulative query/concurrency review](phase-5/assessment.md) |
| 9–10 | [6 — Redis and distributed workflows](phase-6/index.md) | [Cache/message failure review](phase-6/assessment.md) |
| 11–12 | [7 — Security and reliability](phase-7/index.md) | [Cumulative authorization/incident review](phase-7/assessment.md) |
| 13–14 | [8 — Cloud and delivery](phase-8/index.md) | [Rollout/recovery review](phase-8/assessment.md) |
| 15 | [9 — Architecture and system design](phase-9/index.md) | [Three design reviews](phase-9/assessment.md) |
| 16 | [10 — Senior interview preparation](phase-10/index.md) | [Final cumulative assessment](phase-10/assessment.md) |

Use the [curriculum map](curriculum-map.md) for all twenty module links and the
[whole-course plan](course-plan.md#4-week-by-week-learning-roadmap) for every week's
theory/implementation/interview allocation. In the current study-only scope,
use practical blocks for small written code/SQL answers, failure timelines and
design review. Phases 3–10 project implementations remain deferred; do not count
unrun integration, deployment or load-test requirements as demonstrated skills.

## Study cycle

For a deeper pass, follow each module's worked page after its core chapters:
[semantics and streaming](phase-1/module-1/worked-examples.md),
[typed design and testing](phase-1/module-2/design-and-testing.md),
[runtime investigations](phase-2/module-3/runtime-investigations.md), and
[concurrency failure patterns](phase-2/module-4/concurrency-patterns.md).
Then take the [Phase 1](phase-1/assessment.md) and [Phase 2](phase-2/assessment.md)
cumulative assessments. Use the [Phase 1 reference](phase-1/quick-reference.md) and
[Phase 2 playbook](phase-2/debugging-playbook.md) for focused revision.

1. **Set a goal.** Pick one observable behavior you want to understand or implement.
2. **Read and explain.** Read the relevant chapter and explain the model without
   copying its wording. Record unanswered questions.
3. **Practise.** Complete the exercise and compare its result with the expected
   behavior. Try an edge case or a deliberately invalid input.
4. **Apply.** Complete the written exercise or failure/design walkthrough. When
   practical work resumes, record actual commands, observed results and the design
   decision the exercise helped you make; keep deferred project evidence pending.
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

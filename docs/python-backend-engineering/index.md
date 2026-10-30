# Python Backend Engineering

Study how Python programs become reliable backend services. Use explanations to
build a mental model, exercises to practise individual skills, and practical
projects to connect those skills into observable behavior.

Designed for experienced frontend/full-stack engineers moving toward senior Python
backend work. The complete plan is **16 weeks / 160 hours**, with lessons and
assessments for **all 10 phases and 20 modules**. The lesson runtime is **Python 3.14**; newer features and
free-threaded behavior are studied with explicit version/build boundaries.

## Study navigation

| Page | Purpose |
| --- | --- |
| [Learning path](learning-path.md) | Plan a study session and use a repeatable practice cycle |
| [Progress & checkpoints](progress.md) | Record work, evidence, and questions for review |
| [Complete course plan](course-plan.md) | Preserve the ten-phase, twenty-module curriculum and later project roadmap |
| [Curriculum map](curriculum-map.md) | Find every module's lessons and practice in the original sequence |

## Chapters and projects

| Phase | Modules | Practical work |
| --- | --- | --- |
| [1 — Fundamentals](phase-1/index.md) | [1: language semantics](phase-1/module-1/index.md), [2: professional development](phase-1/module-2/index.md) | [Typed inventory package](phase-1/project.md) |
| [2 — Internals and concurrency](phase-2/index.md) | [3: data model and runtime](phase-2/module-3/index.md), [4: concurrent execution](phase-2/module-4/index.md) | [Profiling and bounded HTTP aggregation](phase-2/project.md) |
| [3 — Networking and HTTP](phase-3/index.md) | [5: networking and HTTP](phase-3/module-5/index.md), [6: web-server architecture](phase-3/module-6/index.md) | [Deferred project](phase-3/project.md) |
| [4 — FastAPI and API engineering](phase-4/index.md) | [7: FastAPI](phase-4/module-7/index.md), [8: architecture and testing](phase-4/module-8/index.md) | [Deferred project](phase-4/project.md) |
| [5 — PostgreSQL and persistence](phase-5/index.md) | [9: modeling and SQL](phase-5/module-9/index.md), [10: transactions and scalability](phase-5/module-10/index.md) | [Deferred project](phase-5/project.md) |
| [6 — Redis and distributed workflows](phase-6/index.md) | [11: caching](phase-6/module-11/index.md), [12: messaging](phase-6/module-12/index.md) | [Deferred project](phase-6/project.md) |
| [7 — Security and reliability](phase-7/index.md) | [13: security](phase-7/module-13/index.md), [14: operational reliability](phase-7/module-14/index.md) | [Deferred project](phase-7/project.md) |
| [8 — Cloud and infrastructure](phase-8/index.md) | [15: containers and AWS](phase-8/module-15/index.md), [16: Kubernetes](phase-8/module-16/index.md) | [Deferred project](phase-8/project.md) |
| [9 — Architecture and system design](phase-9/index.md) | [17: software architecture](phase-9/module-17/index.md), [18: distributed design](phase-9/module-18/index.md) | [Deferred project](phase-9/project.md) |
| [10 — Senior interviews](phase-10/index.md) | [19: problem solving](phase-10/module-19/index.md), [20: simulation](phase-10/module-20/index.md) | [Deferred project](phase-10/project.md) |

Every module links its chapters, implementation exercises, interview prompts,
assessment rubric and next unit. Phases 3–10 include written exercises, model
reasoning, failure analyses and phase assessments. Their practical projects are
intentionally placeholders; no new service, cloud deployment or capstone is claimed.
The existing Phase 1–2 runnable examples remain available.

## Approach

The lessons use worked examples throughout: start with a concept, predict a small
program/request/query outcome, follow the execution or failure sequence, then
connect the result to backend decisions and common mistakes. Exact outputs are
shown where the behavior is deterministic; timing/capacity scenarios are labelled
as illustrative rather than measured results.

For each concept, explain the behavior, write a small example, and test an edge
case. For practical work, document how to run it and how to tell whether it works.
When a design has alternatives, record the tradeoff that led to your choice.

Keep runnable material in `examples/python-backend-engineering/` as exercises and
projects are introduced. Record dependencies with each example so it can be run
independently of the documentation site.

Return to the [library dashboard](../index.md) to explore the full library, or use
the [library guide](../library-guide.md) for content conventions.

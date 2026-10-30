# Module 20 — Senior interview simulation

**P0 · cumulative review of all twenty modules**

An interview evaluates bounded problem solving, technical judgment and communication
under uncertainty. Demonstrate how you reach and verify a decision, not only that
you know tool names. Separate work you have done from designs you can reason about.
Deferred projects must not become invented portfolio claims.

## Chapter navigation

1. [Structure a full practice loop](#structure-a-full-practice-loop)
2. [Backend architecture discussion](#backend-architecture-discussion)
3. [System-design conversation](#system-design-conversation)
4. [Incident and debugging interview](#incident-and-debugging-interview)
5. [Code review and implementation assessment](#code-review-and-implementation-assessment)
6. [Behavioral evidence with STAR](#behavioral-evidence-with-star)
7. [Uncertainty and tradeoffs](#uncertainty-and-tradeoffs)
8. [Competency report and revision](#competency-report-and-revision)

## Structure a full practice loop

A useful three-hour simulation is 45 minutes coding, 45 backend deep dive, 60 system
design and 30 behavioral. Use a further review session to score evidence and select
revision priorities. These are study timeboxes, not a promise every employer uses
this format. The original week 16 reserves five interview hours and additional
implementation/theory time for this work.

Choose unfamiliar prompts and withhold model answers until after the attempt.
Record where hints were needed and distinguish independent completion, completion
with hints and incomplete work. A memorized design presented fluently is not the
same evidence as adapting to a changed requirement.

## Backend architecture discussion

Start with a request contract and trace identity, validation, domain behavior,
transaction, serialization and response. Be ready to explain sync/async choice,
session lifetime, pool budgets, errors and shutdown.

Use one concrete invariant such as stock never negative. Explain SQL concurrency
control, duplicate requests, outbox publication and consumer effects. Distinguish
what a local unit test proves from real database, identity and failure integration.
If an interviewer changes the workload, re-evaluate the bottleneck rather than
defending the first tool choice reflexively.

## System-design conversation

Clarify functional/nonfunctional requirements, then estimate load/data/skew. State
units and assumptions. Propose APIs/data and a minimal architecture, explain its
first limit and evolve it when justified. Include security, rollout/recovery and
operating cost from the beginning.

The [design studies](../../phase-9/module-18/design-studies.md) provide eight prompt
families. For a multi-tenant notification system, clarify channel, delivery meaning,
ordering, tenant fairness and provider limits before drawing a broker. Ask how
unknown send outcomes and preference changes should behave.

When given a new region or stronger consistency requirement, identify which
previous assumption breaks and the cost of the revised design. This is a stronger
signal than adding more boxes without changing contracts.

## Incident and debugging interview

State user impact and immediate safe mitigation, then propose competing hypotheses.
Choose evidence that can distinguish them. For high p99 with low CPU, consider
database/pool waits, locks, downstream latency and thread/queue saturation; do not
assume CPU scaling is the answer.

Trace symptoms through logs, metrics and spans with sampling/cardinality limits
understood. Protect evidence while recovering service. A postmortem should connect
contributing conditions to prevention, ownership and a check that can fail when
the problem recurs. Describe what remains uncertain instead of pretending a restart
proved the root cause.

## Code review and implementation assessment

Read for business correctness, authorization, data integrity and resource ownership
before stylistic preferences. Point to a failing input/interleaving and a minimal
regression case. Explain whether a proposed refactor preserves or changes the
public contract and which test boundary must be rerun.

For timed implementation, deliver a small coherent slice and reserve explanation
time. State omitted production concerns explicitly. Avoid a large untested scaffold
that claims transaction safety or authentication without exercising either.

## Behavioral evidence with STAR

STAR structures Situation, Task, Action and Result. Emphasize your decisions,
collaboration, uncertainty and measurable outcome, while identifying team work
honestly. Prepare stories about ownership, conflict, incidents, tradeoffs, failed
approaches and learning—not only flawless launches.

Use this worksheet with actual experience:

| Part | Questions |
| --- | --- |
| Situation | Who was affected and what constraints mattered? |
| Task | What responsibility was yours, and how was success defined? |
| Action | What options did you compare, choose, communicate and verify? |
| Result | What observed evidence changed, and which outcome remains uncertain? |
| Reflection | What would you repeat/change, and what prevented recurrence? |

Do not invent traffic, savings or team impact. If exact numbers are unavailable,
use truthful bounded observations and explain the missing measurement. A failed
attempt with sound correction can demonstrate stronger ownership than an inflated
success story.

## Uncertainty and tradeoffs

Use precise phrases: “I am assuming this endpoint needs read-after-write; if stale
reads are acceptable, a replica changes the latency/cost tradeoff.” “I have not
measured that; I would compare pool wait and query time before scaling.” Pair
uncertainty with a useful next check.

Avoid unexplained absolutes such as always async, always microservices or exactly
once everywhere. Identify the scope where a guarantee holds. Compare at least one
simpler alternative and state what evidence would trigger a more complex one.

Communication should expose a short chain: requirement → invariant/mechanism →
decision → evidence → limitation. Pause to confirm a materially ambiguous requirement
instead of silently solving a different problem; do independent reasoning with
the facts already established.

## Competency report and revision

Use the [final competency review](../competency-review.md) for all eighteen original
readiness items. Attach an explanation, independent exercise/design or observed
implementation result appropriate to the item. Mark practical evidence pending
where projects are deferred; do not downgrade the requirement just to raise a score.

Rank weak areas by hiring relevance and prerequisite impact. Choose a reproducing
problem, study the mechanism, retry without the solution, then reassess. A course
being fully written is a resource milestone; readiness is an evidence milestone.

[Practice](practice.md) · [Final assessment](../assessment.md) ·
[Course overview](../../index.md)

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

### Example — separate independent completion from fluent repetition

In the coding round, a candidate reaches the correct approach only after the
interviewer suggests a sliding window. Record "completed with hint," not
"independently solved." In a second attempt, change the constraint and see whether
the candidate can explain the invariant rather than repeat the memorized code.

Use the same distinction for system design: recognizing a notification diagram
does not prove adapting it to strict ordering, a new provider quota or tenant
isolation. Withhold model answers until the first attempt is recorded.

The feedback session should select the weakest prerequisite and a new bounded
attempt. Repeating only familiar successes can improve presentation while leaving
the actual uncertainty unchanged.

## Backend architecture discussion

Start with a request contract and trace identity, validation, domain behavior,
transaction, serialization and response. Be ready to explain sync/async choice,
session lifetime, pool budgets, errors and shutdown.

Use one concrete invariant such as stock never negative. Explain SQL concurrency
control, duplicate requests, outbox publication and consumer effects. Distinguish
what a local unit test proves from real database, identity and failure integration.
If an interviewer changes the workload, re-evaluate the bottleneck rather than
defending the first tool choice reflexively.

### Example — explain one request through success and uncertain failure

A strong checkout discussion traces trusted identity/tenant, input validation,
stock concurrency control, order/outbox commit, response projection and owned
resource cleanup. Then the interviewer asks: "What if the client disconnects
immediately after commit?"

The answer changes from "return an error" to "the outcome can be unknown to the
caller; use the durable request identity to recover/reconcile it." A process-local
set or a later rollback cannot undo an already committed operation.

Next ask how payment and notification effects relate to that boundary. This tests
whether the candidate understands idempotency and remote uncertainty rather than
merely listing FastAPI, PostgreSQL and a broker.

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

### Example — change the design when an assumption changes

Start a notification design by asking what delivered means: persisted intent,
provider acceptance, device delivery or user read. Those states need different
evidence and recovery behavior.

If the interviewer changes the requirement to strict per-customer ordering,
partition/workflow ownership now matters. If a second region must accept writes,
identity, ordering, duplicate effects and failover need revision. Adding a region
box without revisiting those contracts is not an adaptation.

Use estimates with units and distinguish facts from assumed peak factors.
Propose a simple baseline and the metric that would justify the next scaling
step. Technical judgment is visible in the tradeoff chain, not maximum diagram size.

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

### Example — a hypothesis should predict a useful observation

Observation: p99 rose after exports, but CPU is low. One hypothesis is that slow
downloads retain sessions and exhaust the database pool. It predicts high checkout
wait/transaction age even when admitted queries remain fast.

Another hypothesis is a slow vendor; that predicts longer vendor spans instead.
A thread-pool bottleneck predicts offload waiting. Choose evidence that can
distinguish them before changing every timeout/pool setting.

Mitigate user impact safely, preserve evidence where possible and verify the
correction under the relevant slow-consumer/cancellation case. "We restarted and
latency fell" is a result to explain, not sufficient proof of root cause.

## Code review and implementation assessment

Read for business correctness, authorization, data integrity and resource ownership
before stylistic preferences. Point to a failing input/interleaving and a minimal
regression case. Explain whether a proposed refactor preserves or changes the
public contract and which test boundary must be rerun.

For timed implementation, deliver a small coherent slice and reserve explanation
time. State omitted production concerns explicitly. Avoid a large untested scaffold
that claims transaction safety or authentication without exercising either.

### Example — review a defect through an invariant

A reservation function subtracts first, raises for negative stock afterward,
and a test checks only the exception. Point to the concrete failure: the rejected
call changed state. A regression must compare the repository before/after failure,
not merely assert a method call occurred.

Explain whether the fix preserves the API or changes a documented contract.
For persistence, mocked repositories may not expose independent commits, wrong
tenant predicates or real rollback behavior. Choose the lowest test boundary
capable of falsifying the claim.

Under a timebox, one correct bounded change with meaningful evidence is stronger
than a broad refactor whose security/transaction consequences are unexplained.

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

### Example — make a behavioral story specific without inventing evidence

A vague answer says, "We improved performance." A stronger truthful story identifies
who was affected, your responsibility, the alternatives, your chosen investigation
and the observed result.

Use this hypothetical structure as a guide, not as a claim about your experience:

```text
Situation: exports delayed ordinary requests.
Task: investigate without losing business correctness.
Action: compare pool wait and query time; reproduce slow consumption;
        shorten session ownership and add the regression case.
Result: report the actual observed measurements and remaining limits.
Reflection: state what earlier signal/test would have exposed the risk.
```

If no exact metric was collected, say so and describe the bounded observation.
Separate your individual actions from team work. A failed first hypothesis followed
by evidence-based correction can demonstrate ownership better than inflated success.

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

### Example — a score should reveal a revision action

Consider hypothetical scores of 20/25 concepts, 23/30 correctness, 12/20 debugging,
10/15 tradeoffs and 8/10 communication: total 73/100. The useful outcome is not
only "below 80"; debugging and independent correctness need targeted work.

Choose one reproducing problem, revisit its mechanism, retry without the answer
and record whether hints were needed. Even a numeric pass does not excuse a
critical cross-tenant or stock-invariant failure.

Say "I can explain the transaction model; I still need a real concurrent database
test" when that is the evidence. Written lessons and deferred projects must not
become invented portfolio/deployment claims. Uncertainty paired with a concrete
next check is stronger than an unsupported assertion of mastery.

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

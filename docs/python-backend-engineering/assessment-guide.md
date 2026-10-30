# Study and assessment guide

Use this guide with the [curriculum map](curriculum-map.md), module practice pages
and [progress log](progress.md). The course supplies material; your evidence shows
what you can explain, solve and operate independently.

## Choose the right study mode

| Mode | Work to do | Evidence it can establish |
| --- | --- | --- |
| Reading | Explain a mechanism, predict an example, compare a failure case | Conceptual understanding when recalled without the text |
| Written practice | Solve a code/SQL/design prompt and inspect negative cases | The correctness/reasoning of that bounded answer |
| Existing example review | Run Phase 1–2 references and change one relevant input | Observed behavior of that example, not independent authorship |
| Independent practical work | Implement, exercise real boundaries, collect results | Implementation/integration/operational competence in the tested scope |

Phases 3–10 practical projects remain deferred. Complete their written exercises
now, but leave database concurrency, broker recovery, identity integration, cloud
deployment and load-test evidence pending. This does not reduce those competencies
to reading tasks or declare them demonstrated.

## A repeatable study session

1. Pick one outcome and recall the prerequisite without opening its answer.
2. Read the explanation and predict the worked example's result.
3. Trace the relevant bindings, requests, transaction or task timeline.
4. Solve a practice case before opening its model answer.
5. Change one assumption: invalid input, a competing writer, a lost response,
   a slow consumer, a failed dependency or a different consistency requirement.
6. Explain the result in your own words and record a concrete revision action.

Use these steps inside the original weekly budget. Extra references are for
targeted gaps, not a requirement to read every linked manual cover to cover.
For JS/JVM comparisons, check the specific behavior rather than translating syntax
mechanically: truthiness, closure binding, coroutine startup and type validation
are common sources of mistaken assumptions.

## What a good answer contains

Use **requirement → mechanism/invariant → worked result → failure/edge → tradeoff
→ evidence/limit**. For example, explain why a rejected reservation must preserve
state, trace the unsafe mutation, show the corrected transaction/ownership boundary,
and state whether the evidence is a local calculation or a real concurrent test.

Separate a fact from an assumption and an observation from a prediction. Timing
examples are labelled illustrative; a speedup requires equivalent work, repeated
measurements and a stated environment. SQL plans and deployment results cannot be
invented from a diagram.

## Apply the 100-point rubric consistently

| Dimension | Maximum | Full-credit evidence | Common partial-credit gap |
| --- | ---: | --- | --- |
| Concepts | 25 | Correct mechanism, scope and prerequisite explanation | Knows terms but cannot trace behavior |
| Correctness | 30 | Answer satisfies the prompt and important negative cases | Happy path works but an invariant/edge is missing |
| Debugging | 20 | Reproduction, competing hypotheses and discriminating evidence | Guesses a fix without showing the cause |
| Tradeoffs | 15 | Relevant alternatives with workload/failure/cost assumptions | Lists products without a reasoned choice |
| Communication | 10 | Clear sequence, honest uncertainty and actionable limits | Long description hides the decision or overclaims evidence |

For each dimension, use these anchors:

- **0%:** no useful answer or a fundamentally incorrect mechanism.
- **25%:** recognizes vocabulary but needs substantial guidance to proceed.
- **50%:** partly correct answer with an important unresolved gap.
- **75%:** mostly independent and correct, with a limited missing case or explanation.
- **100%:** independent, correct in scope and supported by relevant evidence.

Multiply the anchor by the dimension maximum and use justified intermediate scores
when appropriate. Record hints and the specific missing case rather than using
precision such as 83.4/100 to imply more certainty than the assessment supports.

### Worked scoring example

A hypothetical answer earns 20 concepts, 24 correctness, 12 debugging, 10 tradeoffs
and 8 communication: **74/100**. The next action is not merely to reread everything.
Reproduce the failed edge, compare two diagnostic hypotheses and reattempt the
specific invariant without hints.

The target is **80/100**, but a critical failure still needs correction: cross-tenant
access, overselling, lost/duplicated business effects outside the stated contract,
swallowed cancellation or leaked owned resources cannot be averaged away by good
presentation. Keep a written assessment result separate from any deferred practical gate.

## Record outcomes honestly

Use independent / completed with hints / incomplete for an attempt. Attach the
prompt, date, commands or written result, score, missing cases and next action.
Do not mark the original [18 competencies](phase-10/competency-review.md) complete
because a reference implementation passed its own tests.

Weeks 4, 8, 12 and 16 are the larger cumulative checks. Revisit earlier ownership,
HTTP, transaction, identity and resource-limit ideas rather than replacing them
with the newest module. The [SQL workbook](phase-5/module-9/query-workbook.md)
and each module's self-check can supply a bounded revision prompt.

[Learning path](learning-path.md) · [Progress](progress.md) · [Final review](phase-10/assessment.md)

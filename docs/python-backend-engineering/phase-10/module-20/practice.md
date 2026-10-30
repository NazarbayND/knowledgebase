# Module 20 — Full-loop practice and assessment

## Simulation rounds

| Round | Prompt | Look for |
| --- | --- | --- |
| Coding, 45 min | Unknown algorithm or bounded API problem | Clarified preconditions, correct invariant, edges, complexity and honest scope |
| Backend, 45 min | Last-item checkout with retries and notifications | Transaction/identity/resource ownership and duplicate-safe effects |
| System design, 60 min | Multi-tenant notification system at stated scale | Requirements, estimates, APIs/data, bottlenecks, failure/recovery and cost |
| Behavioral, 30 min | Incident ownership, disagreement and a failed decision | True individual actions, collaboration, evidence and reflection |

After each round, note hints, incorrect assumptions and unverified claims before
reading the chapter/model answer. Reserve follow-up time to reassess the weakest
prerequisite rather than only repeating strengths.

## Follow-up questions

1. A payment succeeded but your request timed out. What do you know, and what
   durable identity/protocol supports recovery?
2. Two tenants have identical roles. Why is role verification not enough to read
   an order? How does the answer carry into caches, events and search?
3. A release improves p50 and worsens p99. What could explain that, and which
   observation would disprove your current hypothesis?
4. Your service split still requires simultaneous releases and shared schema edits.
   Which benefit did it deliver, and would you change the boundary?
5. Which of your design claims are measured, assumed, or pending practical evidence?

??? note "Model review"
    Unknown outcomes need reconciliation rather than automatic new effects. Role
    grants do not imply access to every tenant/object. Tail changes require
    distribution and wait-path evidence. Independent deployment needs owned data
    and compatible contracts. Senior communication separates established facts,
    assumptions and proposed validation while still making a useful decision.

## Behavioral revision exercise

Rewrite a vague story such as “we improved performance” using a real constraint,
your own decision, alternatives, verified result and remaining limit. Do not invent
numbers to satisfy the format. Include what you learned and what changed afterward.

## Self-check before the assessment

An interview story claims a 40% p99 improvement, but no latency measurements were recorded. How should you improve the answer without inventing evidence?

??? note "Model answer and a five-point check"
    State the real situation, your responsibility, chosen investigation/actions, actual observed outcome and missing measurement. Explain how you would collect comparable latency/error evidence. Separate individual work from the team's contribution and identify a concrete lesson. A truthful bounded result is stronger than a precise unsupported metric.

    Award up to two points for the correct outcome, two for the mechanism, and
    one for a relevant limit or counterexample. Record hints honestly. This is
    a retrieval drill, not a replacement for the full module assessment.

Use the [assessment guide](../../assessment-guide.md) for the shared scoring
anchors and evidence rules.

## Mastery assessment

Score 25 for mechanisms/requirements, 30 for solution correctness, 20 for debugging,
15 for tradeoffs and 10 for communication. Target 80/100. Track independent/hinted/
incomplete outcomes and practical gaps in the [competency review](../competency-review.md).

[Module 20](index.md) · [Final assessment](../assessment.md)

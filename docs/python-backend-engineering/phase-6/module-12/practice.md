# Module 12 — Practice and assessment

## Exercises

1. Choose queue vs retained log for notification jobs, order facts and replayable
   ingestion. State required ordering scope, retention and consumer recovery.
2. Draw crash points before/after business commit and acknowledgement. Explain
   at-most-once/at-least-once outcomes and SQS visibility expiry.
3. Design a processed-event table and atomic local consumer transaction. Explain
   why a uniqueness constraint is needed under concurrent duplicate deliveries.
4. Draw API/outbox/relay/broker failures, including publish accepted but relay
   outcome not saved. Identify why consumers still need idempotency.
5. Define retries, budgets, jitter, DLQ ownership and safe redrive for transient
   dependency failures vs incompatible event schemas.
6. Sketch a payment/reservation saga with compensation failure and manual repair.
   Explain when keeping the operation in one local transaction is simpler.
7. State a precise partition scenario and choose which operation may reject or
   serve stale data. Avoid labelling the whole product with one CAP letter pair.

??? note "Model reasoning"
    Acknowledgement ordering trades potential loss against duplicates. Atomic
    outbox intent survives an API crash but relay publication can repeat. Local
    dedup/business effects share a transaction; external effects need their own
    idempotency/reconciliation. Budgets prevent retry storms. Compensations are
    explicit domain actions and can fail. CAP reasoning needs a concrete partition
    and read/write consistency contract.

## Interview questions

- Can exactly-once broker processing guarantee exactly-once payment?
- Why is the outbox not a substitute for idempotent consumers?
- When do you acknowledge a message, and what remains uncertain after a crash?
- What happens when a visibility timeout is shorter than processing time?
- How can retries at several layers turn a small outage into overload?

??? note "Answer guide"
    Broker guarantees stop at defined boundaries. Outbox relays can repeat, so
    effects must be duplicate-safe. Ack-after-commit allows safe redelivery under
    the local dedup contract but does not cover arbitrary remote effects. Expired
    visibility permits another delivery. Retry multiplication and synchronized
    bursts consume the very capacity needed to recover.

## Self-check before the assessment

An outbox relay publishes e-42, receives acceptance, then crashes before recording delivery. What should happen after restart, and which guarantee remains outside a local dedup transaction?

??? note "Model answer and a five-point check"
    It may publish e-42 again with the same stable business identity. Consumers must tolerate redelivery; a unique processed-event claim and database-local effect share one transaction. An arbitrary external email/payment cannot be atomically covered by that local claim, so use provider idempotency/status/reconciliation or an explicit uncertainty policy.

    Award up to two points for the correct outcome, two for the mechanism, and
    one for a relevant limit or counterexample. Record hints honestly. This is
    a retrieval drill, not a replacement for the full module assessment.

Use the [assessment guide](../../assessment-guide.md) for the shared scoring
anchors and evidence rules.

## Mastery assessment

Use 25 for delivery/consistency mechanisms, 30 for a complete workflow contract,
20 for crash/duplicate diagnosis, 15 for broker/retry/saga tradeoffs and 10 for
communication. Target 80/100. Runtime broker/worker recovery evidence is deferred.

[Module 12](index.md) · [Phase assessment](../assessment.md)

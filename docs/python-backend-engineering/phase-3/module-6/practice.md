# Module 6 — Practice and assessment

## Exercises

1. Draw browser → proxy → Uvicorn → middleware → router → service → database,
   then mark TLS termination, path prefixes, trust boundaries and error owners.
2. Explain the ASGI scope/receive/send contract and compare a streamed response
   with returning a normal JSON object. Where can failure still change the status?
3. Design lifetimes for a shared HTTP client, a database pool, a request session
   and a transaction. Explain why a global request session is unsafe.
4. Plan budgets for a two-second client deadline with one database and one vendor
   call. Include time for queuing, cleanup and returning a response.
5. Model eight processes with ten allowed database connections each and a database
   service budget of sixty. Propose limits accounting for workers and other clients.
6. Write a shutdown sequence for a request streaming a large response when a deploy
   begins. Include readiness withdrawal, drain, cancellation and pool closure.

??? note "Model reasoning"
    ASGI separates server transport from application behavior. Client/pool objects
    are commonly lifespan-owned; sessions/transactions are request/use-case-owned.
    Eight times ten permits eighty connections before other users and overflow,
    already beyond sixty. Lower per-process caps or worker/admission count while
    reserving capacity. Application budgets must finish inside upstream budgets
    when feasible. Streaming errors after headers need a different contract from
    a pre-response JSON error. Shutdown closes resources only after users drain
    or are cancelled and awaited.

## Interview questions

- Why can a sync endpoint remain responsive while an async endpoint blocks peers?
- What does adding a proxy change about trusted headers and timeouts?
- Why can adding workers make a database-backed application slower?
- Does client disconnection prove the database write was cancelled?
- Why is a server keep-alive timeout not a handler deadline?

??? note "Answer guide"
    Framework thread offload may keep blocking I/O off the loop, while async code
    directly calling a blocking library monopolizes it. Proxy headers require
    trusted-hop configuration. More workers create more pools and contention.
    Disconnects and transaction commits can race; a durable idempotency policy
    handles uncertain outcomes. Idle connection management and execution deadlines
    protect different resources.

## Mastery assessment

Award 25 for interface/lifetime explanations, 30 for a correct request/shutdown
sequence, 20 for a pool-exhaustion investigation, 15 for worker/timeout tradeoffs
and 10 for communication. Target 80/100. A diagram must trace both success and
failure cleanup, rather than listing product logos.

[Module 6](index.md) · [Cumulative review](../assessment.md)

# Phase 4 — API architecture assessment

Review weeks 5–6: contract design, dependencies, resource lifetimes, persistence
boundaries and tests. The service project is deliberately deferred.

## Scenario

An order route accepts a tenant header, coerces quantity, writes inventory and
orders through two self-committing repositories, and returns an ORM entity. Tests
mock the repositories and replace authentication. A rollout adds streaming export.

## Tasks and scoring

| Dimension | Evidence | Points |
| --- | --- | ---: |
| Concepts | Explain representation/domain rules, DI caching, lifespan and sessions | 25 |
| Correctness | Specify schemas, authorization, errors and one atomic Unit of Work | 30 |
| Debugging | Diagnose partial commits, exposed fields and closed-session streaming | 20 |
| Tradeoffs | Choose model separation, sync/async I/O and test boundaries | 15 |
| Communication | Show a dependency diagram and safe refactor sequence | 10 |

## Model review

An authenticated identity must authorize tenant context; the header is not proof.
Strict parsing and state validation are distinct. Compose repositories under the
use-case commit boundary, translate expected failures deliberately and project
safe responses before their storage lifetime ends. Export resource scope must
match streaming without retaining a transaction unnecessarily.

Mocked route tests cannot prove the JWT verifier, real SQL constraints, transaction
rollback or deployed proxy behavior. Add distinct test layers when implementation
resumes, with controlled startup/readiness and isolated data.

## Pass and revision

Target 80/100. Fix any design that treats authentication as tenant authorization
or a later rollback as undoing an earlier independent commit. Record the contract,
failure matrix and score in [progress](../progress.md). Keep implementation evidence
pending instead of counting paper designs as deployed capability.

[Overview](index.md) · [Project placeholder](project.md)

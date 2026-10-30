# Module 15 — Practice and assessment

## Exercises

1. Describe a multi-stage Python image build: dependency resolution, wheel build,
   runtime installation, user, signal handling and reproducible artifact identity.
2. Draw Compose networks/volumes for the planned service and dependencies.
   Distinguish process startup, functional readiness and schema readiness.
3. Design CI gates and one-artifact promotion. Separate PR validation permissions
   from release identity and coordinated migration execution.
4. Specify Terraform module/state/backend responsibilities, locking, access,
   drift handling and review of destructive replacements.
5. Compare EC2, ECS/Fargate, EKS and Lambda for a small API with background jobs.
   Include database connection behavior and team operating burden.
6. Draw an AWS network with private persistence, application identity/permissions,
   required egress and recovery boundaries. Estimate major cost categories.

??? note "Model reasoning"
    Images package artifacts, not live database state. Readiness needs a useful
    operation after startup and migrations. CI validates different boundaries and
    privileged deployment must not trust arbitrary PR code. Terraform state is
    sensitive mapping data requiring locking/protection. Managed compute still
    consumes finite database/network capacity. Service choice follows workload,
    team, recovery and total cost rather than feature count.

## Interview questions

- Why can localhost work on a laptop and fail inside a container?
- Why not run migrations from every new replica?
- What is in Terraform state that a provider lockfile does not contain?
- When would ECS be a better choice than EKS?
- Which costs are missed by comparing only instance hourly prices?

??? note "Answer guide"
    Containers have separate network contexts. Concurrent migrations can race and
    lock production schema. State maps actual resource identity/attributes; the
    lockfile selects providers/checksums. ECS can meet container scheduling needs
    without Kubernetes operations. Storage/I/O, idle capacity, backups, telemetry,
    NAT and data movement materially affect total cost.

## Self-check before the assessment

CI tested image digest A. Production rebuilds the same source tag later and obtains digest B. Which artifact has test evidence, and what would make the release reproducible?

??? note "Model answer and a five-point check"
    The tests establish behavior for A's tested scope, not automatically B. Promote a reviewed immutable artifact identity through environments, or independently verify the new artifact under the relevant checks. A source tag or mutable image tag alone does not identify identical contents. Migration/configuration compatibility still matters beside image identity.

    Award up to two points for the correct outcome, two for the mechanism, and
    one for a relevant limit or counterexample. Record hints honestly. This is
    a retrieval drill, not a replacement for the full module assessment.

Use the [assessment guide](../../assessment-guide.md) for the shared scoring
anchors and evidence rules.

## Mastery assessment

Use 25 for delivery/cloud mechanisms, 30 for coherent pipeline/network/state
contracts, 20 for container connectivity diagnosis, 15 for platform/cost choices
and 10 for communication. Target 80/100. No image, Terraform apply or AWS deployment
is created by these written exercises.

[Module 15](index.md) · [Next: Module 16](../module-16/index.md)

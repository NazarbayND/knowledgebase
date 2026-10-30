# Module 15 — Containers, automation and AWS

**P0/P1 · prerequisite: application lifetimes, persistence and reliability**

Delivery packages code, configuration and operational contracts into repeatable
artifacts. Containers do not fix missing startup dependencies, unsafe migrations
or an application that cannot shut down. Cloud selection should follow workload,
recovery, team and cost constraints rather than a preference for the most complex
platform.

## Chapter navigation

1. [Images and runtime boundaries](#images-and-runtime-boundaries)
2. [Compose and local services](#compose-and-local-services)
3. [Continuous integration and deployment](#continuous-integration-and-deployment)
4. [Terraform and state](#terraform-and-state)
5. [AWS compute choices](#aws-compute-choices)
6. [Data, identities and network](#data-identities-and-network)
7. [Managed services and cost](#managed-services-and-cost)

## Images and runtime boundaries

An image is an immutable layered filesystem/configuration artifact; a container is
a running process set with isolation/resource controls. Containers share a host
kernel and do not provide the same boundary as a dedicated virtual machine.
Runtime writes disappear with container replacement unless data is explicitly
stored on a retained volume or external service.

Use multi-stage builds to separate compilers/build tools from runtime artifacts.
Build a wheel, install only needed runtime packages, and run as a non-root user
where the application permits. Pin/review base and dependency versions and record
artifact identities/digests. Copy lock/dependency files before frequently changing
source to reuse valid build layers; do not optimize caches by omitting integrity
checks or silently reusing stale dependencies.

Keep secrets outside image layers and build arguments that can leak into history.
Use a deliberate build context/.dockerignore and runtime secret injection. Exec-form
startup helps signal delivery; understand PID 1 and graceful termination rather
than wrapping the server in a shell that never forwards signals.

The localhost inside a container is that container's network namespace, not the
developer host or another service. Bind the server to the intended interface,
publish ports explicitly and use service DNS names on shared networks.

### Example — image layers and runtime files have different lifetimes

Imagine a build stage compiling/installing tools and producing a wheel, followed
by a runtime stage containing only the interpreter and required installed artifact.
The runtime does not need every compiler/cache that helped create it.

When the container runs, a report written to its ordinary writable filesystem
may disappear when it is replaced. A database volume or external object store
has a different retained-data policy. Image immutability does not make runtime
writes durable.

Secrets copied into a layer can remain recoverable from image history even after
a later layer deletes the visible file. Inject credentials through supported
runtime/build mechanisms instead. Choose an exec-form entry command and understand
signal forwarding so shutdown reaches the server, not only an intermediate shell.

## Compose and local services

Compose declares a local multi-service topology, networks, volumes and configuration.
Distinguish startup order from functional readiness: a created PostgreSQL process
may not accept migrated application queries yet. Use health/readiness checks and
application connection handling under bounded retry rules.

Persist database state only where intended and document reset/cleanup semantics.
An old volume can conceal a missing migration or wrong seed assumption. Avoid
binding production secrets into a local topology. A fresh-checkout procedure should
identify runtime versions, install/build, readiness, migrations and representative
checks; the actual project remains a placeholder for later work.

### Example — localhost changes meaning across network namespaces

```text
Host localhost:8000       → published application port, if configured
API-container localhost  → API container's own network context
API → postgres service   → database reached through shared network DNS/routing
```

A connection string copied from a laptop can therefore target the wrong place
inside a container. Check listener bind address, published ports, service DNS and
credentials/TLS independently.

Starting a database process before an API does not prove the database accepts
queries or has the expected schema. Functional readiness, migrations and application
startup have separate outcomes. An old retained volume can conceal a missing
migration; a clean-environment procedure must state what is created and preserved.

These are explanatory network/lifecycle examples. The new Compose project remains
deferred rather than represented by an untested manifest.

## Continuous integration and deployment

CI should provide distinct evidence: lint/format, strict typing, unit behavior,
real dependency integration, contract/schema review and artifact build. A formatter
pass is not a functional test. Use immutable build artifacts promoted between
environments rather than rebuilding a subtly different image for production.

Separate untrusted pull-request execution from privileged release credentials.
Use minimal job permissions, controlled action/dependency versions and supported
OIDC federation where appropriate. A short-lived cloud role still needs restricted
repository/branch/environment trust and least-privilege actions.

Migrations need an owned, coordinated deployment step. Letting every replica run
an uncoordinated schema migration on startup can race or hold locks. Expand/contract
compatibility lets old and new applications share a schema during rollout. Define
failed-release and failed-migration recovery separately.

### Example — build once, then promote the identity you tested

Suppose CI tests image digest A, while production rebuilds from the same branch
later and obtains digest B after a dependency/base image changes. Passing A's tests
is not evidence for B's exact contents.

Build a reviewed immutable artifact, record its identity and promote that artifact
through environments. Keep lint/type/unit/integration/schema checks distinct:
each can fail for a different meaningful reason. A package/image build alone
does not prove the application starts against a migrated database.

Privileged release identity must not be available to arbitrary untrusted PR code.
Use restricted job permissions and federation trust where suitable. Run migrations
as an owned coordinated step compatible with old/new binaries, not an uncontrolled
startup side effect of every replica.

## Terraform and state

Providers expose resource APIs; resources describe managed objects; modules group
reusable configuration. State maps configuration to remote objects and can contain
sensitive data. Protect its access, storage encryption, versioning and concurrency
locking using the selected backend's supported configuration.

A provider lockfile controls selected provider versions/checksums; it is not the
state and does not encode every remote object's current values. Pin meaningful
constraints, review plan changes and handle drift/import deliberately. Two writers
without proper state locking can corrupt assumptions even if each plan looks valid.

Do not treat a plan as an eternal approval: remote state can change before apply.
Review replacements/destruction and resource names in the intended account/region.
Keep environment boundaries explicit rather than repurposing an unrelated workspace
or copying credentials into configuration. No cloud apply is part of this course-content change.

### Example — configuration, provider selection and state are three layers

A Terraform resource block expresses desired configuration. A provider lockfile
selects provider versions/checksums. State maps that configuration to actual remote
objects and attributes, potentially including sensitive data.

Two operators applying from stale independent state assumptions can conflict.
Use supported state protection/locking and review a plan against the intended
account/region and current state. A previously reviewed plan is not timeless
proof that no remote conditions changed.

A resource rename in configuration can look like destroy/create unless migration
of identity is handled appropriately. Read replacements and dependencies, not just
the final count of additions. No apply or real cloud change is part of these
lesson examples; the practical infrastructure project is deferred.

## AWS compute choices

| Service | Starting fit | Main tradeoff |
| --- | --- | --- |
| EC2 | Workloads needing host/runtime control | OS patching, capacity and orchestration ownership |
| ECS/Fargate | Managed container scheduling without a Kubernetes requirement | Platform conventions, task/network/cost constraints |
| EKS | Kubernetes APIs/ecosystem or established cluster operations | Cluster/platform complexity and shared ownership |
| Lambda | Event-driven bounded functions and spiky demand | Duration/concurrency/startup/runtime and connection behavior |

Do not choose EKS just to run one HTTP container. Existing team capability,
operational consistency and integration needs can justify it. Lambda concurrency
can multiply database connections; “serverless” does not remove downstream capacity.
Compute scale must remain compatible with startup, sessions and graceful shutdown.

### Example — choose compute from the operational requirement

A small team needs one containerized HTTP API and a worker with managed scheduling.
ECS/Fargate may satisfy that without operating Kubernetes. EKS can be justified
by established platform capability or required Kubernetes integrations, not simply
because the workload is a container.

Lambda can suit event-driven/spiky bounded work, but high function concurrency
can multiply database connections and contend on the same stock rows. EC2 gives
host control with more operating responsibility.

For each choice ask who patches/scales/diagnoses it, how it drains work, what
quotas apply and how persistence remains safe. Managed compute changes ownership
and price; it does not remove downstream limits or business failure modes.

## Data, identities and network

RDS provides managed relational infrastructure; query design, transaction correctness,
backups/recovery policies and connection budgets still require decisions. ElastiCache
supplies managed cache infrastructure with explicit topology/availability choices.
S3 fits object storage with lifecycle/access policies; SQS provides managed queued
work with visibility/redelivery semantics.

IAM policies grant actions over resources under conditions. Use workload roles
rather than static shared administrator keys. Separate application, migration,
deployment and human privileges where their responsibilities differ.

A VPC contains routed networks; subnets span a single availability zone. Public
or private behavior depends on routing and addressing, not the subnet name. Security
groups are stateful access controls; network ACLs are stateless subnet controls.
Keep databases/cache behind intended network paths and permit only required callers.
Private workloads may need NAT or service endpoints for egress; account for both
connectivity and cost. Network reachability alone does not authenticate a workload.

### Example — network reachability and IAM grant different authority

A workload may be able to open a TCP connection to a database while lacking valid
database credentials. Conversely, an IAM role can permit an AWS action while
routing/security-group rules prevent reaching its endpoint.

Trace both: application subnet/route → destination/network policy → TLS/credential
authentication → authorized operation. A private subnet is defined by routing and
addressing, not its name. Workloads needing public egress may use NAT; service
endpoints can change connectivity and cost.

RDS, ElastiCache, S3 and SQS supply different managed capabilities, not interchangeable
storage. Give runtime, migration and deployment identities the privileges matching
their jobs rather than sharing an administrative key everywhere.

## Managed services and cost

Managed services trade some infrastructure work for service constraints and price.
Compare compute, storage, backups, I/O, idle capacity, logs, NAT and cross-zone/region
egress. A cheaper instance can increase operating time or failure risk; an oversized
platform can dominate the cost of a small application.

Use an explicit availability/recovery objective, expected/peak load, data size and
team support model. Choose a simple baseline and identify measurements that would
justify more capacity or another architecture. Include quotas and recovery from
account/region or dependency limitations in the plan.

### Example — hourly compute price is only one line in the estimate

Two designs have the same application CPU footprint. One sends all traffic through
NAT, stores verbose logs indefinitely and copies large payloads across regions.
The other uses a suitable network/data-retention path. Their total bills can differ
even if instance hourly prices match.

Estimate storage/I/O, backups, idle headroom, surge, telemetry, NAT and data movement.
Include operating time and recovery capability too: a cheaper self-managed database
is not cheaper if the team cannot maintain or restore it.

State the expected/peak workload and revisit assumptions with actual measurements.
Do not choose the largest managed platform for a small problem, or eliminate
needed redundancy merely to minimize a single monthly number.

## Worked failure analysis

The container works locally but cannot reach PostgreSQL in deployment. Check the
actual hostname, bind address, DNS, route, security-group edges, credentials/TLS
and database readiness independently. `localhost` often points to the wrong
namespace. Fix the identified boundary; disabling TLS or opening every network
path hides the diagnosis and weakens the intended contract.

[Docker build guidance](https://docs.docker.com/build/building/best-practices/),
[Terraform](https://developer.hashicorp.com/terraform/docs) and
[AWS Well-Architected](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)
provide the deeper references.

[Practice](practice.md) · [Next: Kubernetes](../module-16/index.md)

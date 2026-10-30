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

## Managed services and cost

Managed services trade some infrastructure work for service constraints and price.
Compare compute, storage, backups, I/O, idle capacity, logs, NAT and cross-zone/region
egress. A cheaper instance can increase operating time or failure risk; an oversized
platform can dominate the cost of a small application.

Use an explicit availability/recovery objective, expected/peak load, data size and
team support model. Choose a simple baseline and identify measurements that would
justify more capacity or another architecture. Include quotas and recovery from
account/region or dependency limitations in the plan.

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

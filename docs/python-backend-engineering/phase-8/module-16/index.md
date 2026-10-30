# Module 16 — Kubernetes and delivery

**P1 · prerequisite: containers, health semantics and cloud networking**

Kubernetes reconciles desired workload state through controllers. It can restart
containers and route to ready pods, but cannot infer a correct business transaction,
schema migration or capacity target. Delivery correctness depends on the contract
between application lifecycle, cluster controls and external dependencies.

## Chapter navigation

1. [Workloads and traffic](#workloads-and-traffic)
2. [Configuration and workload identity](#configuration-and-workload-identity)
3. [Resources and scaling](#resources-and-scaling)
4. [Health and graceful termination](#health-and-graceful-termination)
5. [Helm and GitOps](#helm-and-gitops)
6. [Release strategies and rollback](#release-strategies-and-rollback)
7. [Diagnostics and recovery](#diagnostics-and-recovery)

## Workloads and traffic

A Pod groups containers sharing networking and selected volumes. Pods are replaceable;
their IPs and local files are not durable identities. A Deployment manages ReplicaSets
for replica count and rollouts. A Service provides a stable access abstraction over
selected endpoints; selector/port mistakes can route nowhere or to the wrong process.

Ingress describes HTTP routing implemented by an installed controller; it does
not itself conjure a load balancer or certificate. Controller/cloud integrations
determine details. Trace external load balancer → ingress/controller → Service →
ready Pod → process listener and compare targetPort with the actual bind address.

Do not store authoritative orders on a pod filesystem. Durable state has separate
storage/recovery ownership. Scheduling a database in a Pod does not automatically
provide its replication, backup or failover plan.

## Configuration and workload identity

ConfigMaps hold non-secret configuration. Secrets provide a separate API/resource
type and access controls, but base64 encoding is not encryption. Configure storage
protection, RBAC and secret delivery according to the cluster/platform. Do not
commit real credentials in manifests or Helm values.

Service accounts identify workloads to Kubernetes; cloud IAM integration can give
them scoped cloud access. Avoid default broad privileges. Applications must adopt
rotated configuration/secrets through a deliberate reload or restart policy;
changing an object does not guarantee every process rereads an environment variable.

## Resources and scaling

Requests influence scheduling and CPU shares; limits constrain usage. CPU limits
can throttle; exceeding memory limits can lead to OOM termination. Actual behavior
also depends on runtime/cluster configuration. Choose values from measured workload
and startup peaks, not the lowest number that once passed a local smoke check.

HPA scales replicas from configured signals. CPU utilization targeting depends on
requests and may miss a workload bottlenecked on a queue, database or vendor. More
replicas multiply connection pools and can amplify downstream overload. Account
for scale-up delay, metrics lag, stabilization and maximum replica capacity.

Autoscaling does not instantly fix a sudden burst. Admission controls, queue bounds,
headroom and dependency quotas remain necessary. Cluster capacity and pod topology
also determine whether desired replicas can actually schedule.

## Health and graceful termination

Startup probes protect long initialization from premature normal probes. Readiness
controls traffic eligibility; liveness can trigger restart when the process is
unhealthy. Avoid making every remote dependency failure a liveness failure.

```text
termination plan:
    stop accepting new application work / withdraw readiness
    allow routing changes and in-flight requests to drain
    handle termination signal under a finite grace period
    cancel and await remaining owned tasks
    close pools/clients and exit before forced termination
```

Routing changes and shutdown signals can overlap and propagation takes time.
Coordinate preStop/application drain and termination grace with request duration.
A fixed arbitrary sleep is not a complete correctness argument. Workers also need
to stop claiming jobs and acknowledge only according to their durable effect contract.

## Helm and GitOps

Helm packages parameterized Kubernetes resources. Separate defaults, environment
configuration and secrets; render/review output and validate assumptions. Templates
can hide a bad selector or overly broad permission as effectively as duplicated YAML.

Argo CD/GitOps reconciles desired configuration from a controlled source. It improves
auditability and drift management but requires repository/cluster permissions,
secret policy and deployment ordering. A reconciler may undo manual emergency
changes unless the runbook addresses the source of truth.

Database migrations should be coordinated with application compatibility. A Job
or pipeline stage is a mechanism, not proof the migration is safe or only runs once.
Define ownership, retry behavior and release ordering.

## Release strategies and rollback

Rolling updates replace replicas gradually using availability/surge settings.
Ensure enough capacity for surge and readiness of new versions. Canary delivery
exposes limited traffic and compares useful error/latency/business signals. Blue-green
keeps separate environments and switches traffic, with additional capacity/state costs.

Rollback restores an application artifact/configuration, not magically reverses
every database or message effect. Expand/contract keeps old/new binaries compatible
while rollback is possible. Removing a column before old pods drain can break both
rollout and rollback. Message schema evolution also needs consumer compatibility.

Define automatic abort thresholds and who decides when signals disagree. A canary
that receives only easy traffic can miss tenant/size-dependent failures.

## Diagnostics and recovery

For rollout 503s inspect events, desired/ready replica counts, Service endpoints,
probe failures, listener/port configuration, ingress routing and downstream capacity.
Pending pods suggest scheduling/quota/resource problems; CrashLoopBackOff needs
process logs, exit reasons/configuration; OOMKilled suggests memory peak/limits.
Different states require different investigations.

High availability includes zones, disruption handling, replicas and external data
availability under explicit failure assumptions. Avoid placing all replicas on one
failure domain when the objective requires surviving it. Backups/restore and disaster
recovery remain necessary even with healthy controllers.

Cost-aware infrastructure includes requests reserving capacity, idle replicas,
surge, telemetry, storage and egress. Choose managed vs self-operated persistence
based on actual support capability. A cluster dashboard showing green pods does
not prove orders are correct or restores will work.

## Worked failure analysis

503s occur only during rollout. Compare readiness becoming true with actual resource
initialization, termination/drain timing, endpoints and available replicas. Check
whether migrations break old pods or surge exhausts database pools. Fix the
specific lifecycle/capacity contract rather than permanently disabling health checks.

[Kubernetes concepts](https://kubernetes.io/docs/concepts/),
[Helm](https://helm.sh/docs/) and [Argo CD](https://argo-cd.readthedocs.io/en/stable/)
are the references. Cluster implementation is deferred.

[Practice](practice.md) · [Phase review](../assessment.md) ·
[Next: software architecture](../../phase-9/module-17/index.md)

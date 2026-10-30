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

### Example — follow a request through selectors and ports

An illustrative Service.spec fragment is:

```yaml
selector:
  app: fulfillhub
ports:
  - port: 80
    targetPort: 8000
```

This is not a complete deployment manifest. It shows that clients use Service
port 80 while traffic targets port 8000 on selected ready endpoints. If pods have
app: inventory instead, the selector does not identify them. If the server listens
only on the wrong interface/port, a correct selector still cannot reach it.

Trace ingress/controller → Service → ready endpoints → Pod listener. A Deployment
reporting desired replicas does not prove that path is usable. Pods are replaceable;
do not store durable orders on their ordinary local filesystem or depend on a
specific pod IP surviving.

## Configuration and workload identity

ConfigMaps hold non-secret configuration. Secrets provide a separate API/resource
type and access controls, but base64 encoding is not encryption. Configure storage
protection, RBAC and secret delivery according to the cluster/platform. Do not
commit real credentials in manifests or Helm values.

Service accounts identify workloads to Kubernetes; cloud IAM integration can give
them scoped cloud access. Avoid default broad privileges. Applications must adopt
rotated configuration/secrets through a deliberate reload or restart policy;
changing an object does not guarantee every process rereads an environment variable.

### Example — updating a Secret does not necessarily update the process

A process reads DATABASE_PASSWORD from its environment at startup. Changing the
Kubernetes Secret later does not mutate that already-running process's environment.
The rotation plan must include supported reload/restart and credential overlap.

Base64-encoded Secret data is not encrypted merely by being base64. Storage
encryption, API/RBAC access, delivery and logs each need appropriate protection.
A service account identifies a workload but does not automatically imply the right
cloud permissions.

Keep non-secret configuration, credentials and workload identity separate in the
design. A manifest that can be applied is not evidence that application adoption
and revocation behavior are correct.

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

### Example — autoscaling can exceed a database budget

Assume a database budget of 80 connections, with 20 reserved for other work.
If the API may scale to five pods with one process each, the remaining 60 imply
at most 12 pooled connections per pod under this simplified allocation. Three
processes per pod would require another multiplication.

CPU requests also affect utilization-based HPA interpretation. A 100m observed
load against a 250m request is 40% utilization; changing the request changes that
ratio without changing the work. Memory limits and actual startup peaks can
produce OOM kills even if ordinary traffic looked small.

Choose metrics from the bottleneck. A service waiting on a database pool can have
low CPU, so CPU-only scaling may miss overload or add even more competing pools.

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

### Example — readiness and draining must line up with real timing

A terminating pod stops admitting work, but load-balancer/endpoint propagation
takes time and existing connections may still carry requests. If the application
immediately closes its database pool, requests it still owns can fail.

Design a finite sequence: withdraw readiness/admission, allow intended routing
drain, finish accepted work within a budget, cancel/await remaining tasks, close
resources and exit before forced termination. A fixed sleep can be one platform
detail, but is not the complete correctness argument.

Startup probes protect initialization; readiness governs traffic eligibility;
liveness asks whether restart may help. A shared database outage should not
automatically restart every healthy application process and amplify the incident.

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

### Example — a live emergency patch can fight the source of truth

An operator changes a running deployment to mitigate an incident. A GitOps
controller sees a difference from its configured desired source and may restore
the old value. Both components can be working as designed while the mitigation
keeps disappearing.

The runbook needs source/reconciliation ownership and a controlled way to preserve
or deliberately override emergency changes. Helm adds parameterization, but a
template can still render a wrong selector or overly broad role. Review rendered
resources and environment values, not only whether template syntax passed.

Migration ordering, retry behavior and secrets need the same explicit treatment.
A Kubernetes Job is a mechanism for work; its existence does not prove a migration
is safe, compatible or exactly once.

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

### Example — an application rollback cannot restore a removed column

New pods use display_name; old pods use full_name. If a migration drops full_name
before old pods drain, a rolling deployment can break existing traffic. Rolling
back the image then restores code that still expects a missing column.

Use expand/contract compatibility to keep old/new versions working during the
rollback window. Messages and external effects have version/state consequences too.

Rolling updates need availability/surge capacity. Canary needs representative
traffic and meaningful abort signals; one easy tenant can hide a size-dependent
failure. Blue-green provides a traffic switch at additional capacity/state cost,
not an automatic reversal of every database or business effect.

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

### Example — similar symptoms require different investigations

| Observation | First boundary to investigate |
| --- | --- |
| Pod Pending | Scheduling, requests, quotas, node/topology capacity |
| CrashLoopBackOff | Process exit, configuration and startup logs |
| OOMKilled | Memory peak, retention and limits |
| Running but not Ready | Probe contract and actual initialization/dependency policy |
| Ready but requests fail | Listener, selector/endpoints, ingress and application behavior |

These are starting hypotheses, not automatic root causes. A rollout 503 can
come from an empty endpoint set, premature readiness, drain timing or downstream
exhaustion. Disabling probes permanently only removes one signal.

Recovery also includes zone placement, durable data, backup/restore and promotion
ownership. Healthy pod counts do not demonstrate correct orders or successful
restoration.

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

# Module 13 — Backend application security

**P0/P1 · prerequisite: identity boundaries, API contracts and transactions**

Security is an explicit set of trust and authorization decisions. A valid token
does not prove a caller can access every object, tenant or field. Start with assets,
actors, entry points and abuse cases, then enforce checks at the boundary that
actually owns the resource.

## Chapter navigation

1. [OAuth, OIDC and PKCE](#oauth-oidc-and-pkce)
2. [JWT validation and Keycloak](#jwt-validation-and-keycloak)
3. [Scopes, roles and object authorization](#scopes-roles-and-object-authorization)
4. [Sessions and browser risks](#sessions-and-browser-risks)
5. [OWASP API failure modes](#owasp-api-failure-modes)
6. [Injection, SSRF and unsafe data](#injection-ssrf-and-unsafe-data)
7. [Service identities, rotation and audit](#service-identities-rotation-and-audit)

## OAuth, OIDC and PKCE

OAuth 2.0 delegates access; OpenID Connect adds an identity layer and ID-token
semantics. An API normally receives an access token intended for that API, not an
ID token intended for a client. Authentication and authorization remain separate.

In Authorization Code + PKCE, the client creates a verifier and sends a derived
challenge during authorization. Redeeming the returned code requires the verifier,
reducing stolen-code usefulness. Redirect URI validation, state/nonce handling as
appropriate, HTTPS and client configuration still matter. PKCE is not a replacement
for backend token checks or browser security.

A public client such as a browser application cannot keep a meaningful embedded
client secret. A confidential backend can authenticate using an appropriate secret
or stronger supported mechanism. Do not move a backend secret into frontend
environment variables and call it hidden because the build system supplied it.

### Example — follow what PKCE proves and what it does not

```text
Browser: create verifier; derive challenge
Browser → identity provider: authorize with challenge and registered redirect
Provider → browser redirect: authorization code
Client → token endpoint: code + verifier
Provider: validate the relationship; issue tokens under client policy
```

An intercepted code is less useful without its verifier. That does not authorize
the browser to read every tenant, validate an API audience, or prevent all XSS.
State/nonce and redirect/HTTPS rules serve additional flow requirements.

A browser is a public client because bundled code cannot keep an embedded secret.
A backend can be a confidential client under a supported credential mechanism.
An ID token identifies a user to a client; an access token grants resource access
under its intended audience/use. Treating them interchangeably loses those boundaries.

## JWT validation and Keycloak

Keycloak provides realms, clients, roles, identity flows and discovery/JWKS endpoints.
Map issuer, audience and roles/scopes deliberately; defaults do not automatically
match your API's trust contract. The backend must verify at least:

- Cryptographic signature with a trusted key and explicitly accepted algorithms.
- Expected issuer and intended audience, not a vaguely matching hostname.
- Expiry/not-before and relevant time claims using a bounded clock-skew policy.
- Required token type/use, claims and application permission semantics.

Decoding base64/JSON is not verification. A kid selects from configured trusted
issuer keys; an attacker-controlled jku/URL must not direct arbitrary key fetching.
Use a mature verifier and its supported algorithm/key restrictions rather than
implementing signature checks yourself.

JWKS caching needs rotation and failure behavior: bounded cache lifetime, controlled
refresh for unknown keys, and protection against one network refresh per malicious
token. Rotation should overlap valid keys as required by token lifetime. Removing
a key or logging out at the provider does not necessarily revoke every already
issued self-contained access token immediately.

Refresh tokens renew access under provider policy and require careful storage,
rotation/reuse detection and client treatment. They should not be casually sent
to ordinary resource endpoints. Short access-token lifetime trades exposure window
against availability/refresh complexity.

### Example — a correct signature can accompany the wrong token

An illustrative decoded token claims:

```json
{"iss":"https://identity.example/realm",
 "aud":"another-api",
 "sub":"user-7",
 "exp":2000000000}
```

Even if a trusted issuer signed it and it has not expired, FulfillHub must reject
it when another-api is not its accepted audience. Decoding JSON/base64 proves
neither authenticity nor intended use.

A real verifier uses trusted issuer configuration, accepted algorithms/keys,
audience, time and required claims/use policy. kid selects among trusted keys;
it must not turn an attacker-provided URL into arbitrary key fetching. Unknown
keys need bounded refresh and failure behavior so invalid tokens cannot force a
network request on every API call.

Rotation also needs overlap/adoption rules. A cached self-contained access token
may remain valid after provider logout unless the chosen revocation contract
provides something stronger.

## Scopes, roles and object authorization

Scopes describe granted capabilities; RBAC maps roles to permissions; ABAC evaluates
attributes such as ownership, tenant, status and policy context. Choose the smallest
policy model satisfying the domain instead of combining acronyms without ownership.

For every object operation, derive a trusted principal, authorize the selected
tenant, then fetch/change the object under that tenant/policy. A request containing
another tenant id is not authority to use it. Composite database relationships
help prevent inconsistent links but cannot authenticate callers.

Check function-level permission, object-level access and property-level changes.
An editor allowed to change a product description may not change tenant_id or an
administrative approval flag. Use explicit writable schemas plus domain permission
checks. Random/UUID identifiers make guessing harder, not unauthorized access valid.

### Example — require both the action and the object's tenant

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Principal:
    tenants: frozenset[str]
    permissions: frozenset[str]

def can_read_order(principal, order_tenant):
    return (
        "orders:read" in principal.permissions
        and order_tenant in principal.tenants
    )

user = Principal(frozenset({"A"}), frozenset({"orders:read"}))
print(can_read_order(user, "A"))
print(can_read_order(user, "B"))
```

Expected output is True, then False. This is one simplified authorization check
for a principal already established by trusted identity/membership resolution,
not a complete credential verifier.

A caller may request tenant B, but that request cannot add B to trusted membership.
Apply object and field checks too: an editor allowed to change a description may
not change tenant_id or grant itself an admin role. UUIDs and authentication do
not remove these checks.

### Negative-case matrix — identify the failed boundary

| Case | Expected policy direction |
| --- | --- |
| Invalid signature or disallowed algorithm | Reject authentication |
| Correct signature, wrong issuer/audience/token use | Reject authentication |
| Expired/not-yet-valid token beyond allowed skew | Reject authentication |
| ID token presented where an API access token is required | Reject the wrong credential contract |
| Valid identity without required action permission | Deny authorization |
| Same role, another tenant's object | Deny object access |
| Allowed object action, forbidden administrative field | Deny property change |
| Caller-supplied key URL or tenant membership claim not trusted by policy | Do not expand trust from unverified input |

Authentication failures commonly map to 401 and permission failures to 403, with
a deliberate 404 concealment policy where appropriate. Document the chosen public
behavior without leaking protected object existence. A JWKS fetch outage is an
operational condition, not proof of a valid token: never accept unverifiable data,
and distinguish outage handling from bad credentials under the API contract.

Route tests with a verifier override can test authorization, but the original
verifier needs its own negative cases for signature, issuer/audience and time.

## Sessions and browser risks

Cookie sessions need Secure/HttpOnly/SameSite policies appropriate to the flow,
session fixation defenses, expiry and server-side revocation expectations. Cookie
authentication can create CSRF risk because credentials attach automatically;
use a fitting anti-CSRF design and origin validation strategy.

Bearer tokens reduce some automatic-cookie CSRF patterns but introduce token
exposure/storage risks. XSS can act in the application origin even when an HttpOnly
cookie is unreadable. CORS restricts browser response access and is not a tenant
permission mechanism or a guarantee requests cannot be sent.

### Example — choose controls from how credentials travel

With cookie authentication, a browser may attach credentials automatically to
a cross-site request, so a state-changing endpoint needs the appropriate CSRF
contract. HttpOnly restricts scripts reading the cookie, but an XSS script can
still issue actions in the application's origin.

With bearer tokens, explicit attachment changes some CSRF patterns but creates
storage/exposure questions. CORS controls a browser's response-access behavior,
not whether a non-browser caller may send traffic or whether a tenant check passed.

Follow credential issuance, storage, attachment, validation and revocation
separately. No single cookie flag or CORS allowlist covers that entire lifecycle.

## OWASP API failure modes

| API Security 2023 area | FulfillHub example and control |
| --- | --- |
| Broken object-level authorization | Fetch another tenant's order; enforce tenant/object checks |
| Broken authentication | Accept invalid/expired tokens; validate the complete credential contract |
| Broken object-property authorization | Mass-assign approval/tenant fields; allowlist exposed/writable properties |
| Unrestricted resource consumption | Unlimited exports/uploads; bound size, rate, concurrency and cost |
| Broken function-level authorization | Ordinary user calls an admin refund; check action-level permission |
| Unrestricted access to sensitive business flows | Automated inventory hoarding; model abuse and business limits |
| SSRF | User URL reaches internal metadata; enforce destination/network policy |
| Security misconfiguration | Debug mode or permissive proxy trust; review deployment configuration |
| Improper inventory management | Forgotten older API exposes data; track/version/retire endpoints |
| Unsafe consumption of APIs | Trust partner payload blindly; validate and constrain external data |

Use this as a threat-review map, not a claim that a framework checkbox eliminates
the category. Combine preventive controls, negative tests and observable audit.

### Example — a legitimate endpoint can still enable business abuse

An attacker uses valid credentials and well-formed requests to reserve popular
stock repeatedly, preventing others from buying. No SQL injection or invalid JWT
is necessary: the abuse uses an intended function at harmful scale.

Define limits at the business scope—tenant/user/reservation duration/quantity,
duplicate identity and cost—not only requests per IP. Observe suspicious flows
without putting every order id into metric labels.

Likewise, mass assignment of an internal approval field is property authorization;
calling an admin endpoint is function authorization; fetching another tenant's
order is object authorization. Naming the category helps identify the missing
boundary rather than treating every security bug as authentication.

## Injection, SSRF and unsafe data

Parameterized SQL binds values; user-selected identifiers/order expressions still
need allowlisted construction. Concatenating a tenant predicate into SQL can
undermine both injection safety and isolation. Test cross-tenant and field escalation
as well as malformed syntax.

SSRF defenses consider schemes, hosts, ports, DNS resolution, redirects and network
egress. A superficial URL-prefix check can be bypassed, and DNS rebinding/redirects
can change the eventual destination. Prefer constrained server-owned integrations
and network enforcement where possible. Do not allow a token/JWKS hint to become
an unrestricted HTTP fetch.

Never unpickle untrusted data. Validate partner payload sizes/types/semantics and
use bounded parsers. Dependency scanning, trusted sources, pinned resolution and
timely updates reduce supply-chain exposure but do not replace runtime controls.

### Example — values and destinations are separate trust boundaries

Binding a SQL value prevents it becoming arbitrary SQL syntax. A caller-selected
ORDER BY column cannot generally be handled as an ordinary value parameter;
construct it from a controlled allowlist. Authorization predicates must remain
present even when the query is injection-safe.

For a URL fetch, validating a prefix does not establish the eventual destination:
redirects, DNS resolution and rebinding can change it. Prefer server-owned
integrations and enforce scheme/host/port/address/egress rules at supported
boundaries. Do not trust a token's key-URL hint to make unrestricted HTTP calls.

Untrusted pickle can execute behavior during loading. Internal-looking queues,
caches and partner payloads need source, size, schema and permission checks too.

## Service identities, rotation and audit

Give each workload a least-privilege identity with only needed destinations/actions.
Separate human admin permissions from runtime access. Use supported workload
identity/secret bindings and rotate credentials without baking them into images,
source, logs or test fixtures. Rotation includes client reload/restart and overlap
behavior, not just changing a value in a vault.

Audit important authorization and business decisions with actor, tenant, action,
resource, outcome and correlation id. Protect integrity/retention and access to the
audit trail. Redact tokens/secrets and minimize sensitive payloads. A normal debug
log is not automatically a trustworthy business audit record.

### Example — rotate a secret without confusing storage with adoption

Changing a credential in a secret store does not prove an already-running process
has loaded it. Environment variables commonly require a restart; mounted or
client-managed sources have their own refresh behavior. Plan overlap, client
adoption, least privilege and safe fallback during the transition.

Audit actor, tenant, action, resource, outcome and correlation rather than raw
tokens. Protect the audit trail's access/integrity/retention. A debug message with
a full bearer token can create a new credential exposure while diagnosing another
problem.

Separate deployment, migration, runtime and human identities when their privileges
differ. A short-lived credential with administrator permissions is still too
powerful for a read-only application task.

## Worked failure analysis

A valid user reads another tenant's order by changing its id. Signature checks
can all be correct while object authorization is absent. Reproduce using two
tenants with the same role, enforce tenant/object constraints at the query/use-case
boundary, add negative access/write cases and review list/export paths for the
same defect. “IDs are unguessable” is not a fix.

[OIDC](https://openid.net/specs/openid-connect-core-1_0.html),
[Keycloak](https://www.keycloak.org/documentation) and
[OWASP API Security](https://owasp.org/API-Security/editions/2023/en/0x00-header/)
are the references.

[Practice](practice.md) · [Next: reliability](../module-14/index.md)

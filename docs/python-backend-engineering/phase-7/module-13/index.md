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

## Sessions and browser risks

Cookie sessions need Secure/HttpOnly/SameSite policies appropriate to the flow,
session fixation defenses, expiry and server-side revocation expectations. Cookie
authentication can create CSRF risk because credentials attach automatically;
use a fitting anti-CSRF design and origin validation strategy.

Bearer tokens reduce some automatic-cookie CSRF patterns but introduce token
exposure/storage risks. XSS can act in the application origin even when an HttpOnly
cookie is unreadable. CORS restricts browser response access and is not a tenant
permission mechanism or a guarantee requests cannot be sent.

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

# Module 13 — Practice and assessment

## Exercises

1. Draw Authorization Code + PKCE for a browser and identify public/confidential
   client boundaries. Distinguish API access tokens, ID tokens and refresh tokens.
2. Write a verifier checklist including algorithm, key source, issuer, audience,
   time and rotation. Plan bounded JWKS refresh and unknown-key failure handling.
3. Design RBAC/object/field checks for a tenant editor and administrator. Produce
   negative cases for cross-tenant reads/writes, admin actions and mass assignment.
4. Threat-model cookie and bearer clients for CSRF, XSS, token exposure and CORS.
5. Map each OWASP category from the chapter to an entry point and control.
   Include resource-cost abuse and forgotten API versions.
6. Review a URL-fetching partner integration for SSRF and unsafe partner payloads.
7. Specify service identity permissions, secret rotation and safe audit fields.

??? note "Model reasoning"
    PKCE binds code redemption, not object authorization. Access-token verification
    needs trusted key/issuer/audience/time and token-use policy. Valid credentials
    still require action/object/property checks. URL destinations and payloads are
    separate trust boundaries. Audit records identify actor/outcome without copying
    tokens or sensitive bodies. Rotation needs runtime adoption, not only vault edits.

## Interview questions

- Why must the API not accept any signed JWT from a familiar issuer?
- What happens to cached signing keys during rotation?
- Why can a correct JWT verifier still allow horizontal privilege escalation?
- Does HttpOnly eliminate the consequences of XSS?
- How can parameterized SQL coexist with an unsafe dynamic ORDER BY?

??? note "Answer guide"
    Signature alone omits audience/use/claims. Rotation needs overlapping trust
    and bounded refresh; provider logout is not universal immediate revocation.
    Object permission is independent of identity. HttpOnly limits token reading,
    not arbitrary actions from compromised script. Identifiers/expressions cannot
    be treated like ordinary bound values and need controlled construction.

## Mastery assessment

Use 25 for identity/security mechanisms, 30 for a complete authorization/verifier
contract, 20 for escalation/SSRF diagnosis, 15 for storage/rotation tradeoffs and
10 for explanation. Target 80/100. Security integration and negative requests
remain unrun until the [deferred project](../project.md) is implemented.

[Module 13](index.md) · [Next: Module 14](../module-14/index.md)

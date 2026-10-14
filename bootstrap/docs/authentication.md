# Authentication setup and verification

## Organization setup — Owner

An Anthropic organization administrator verifies/registers GitHub's issuer
https://token.actions.githubusercontent.com through discovery and public JWKS.
Issuer reuse does not confer repository authority. Administrative sessions remain
outside all agent jobs. Record administrator/recovery ownership and incident actions.
Use provider-supported administration and separately approved OAuth scope; do not
put admin credentials into the project or model environment.

## Per project — Owner

Create dedicated workspace and service account, audit memberships and all alternate
rules targeting the account, and bind each rule to that workspace only. Default
workspace membership alone does not establish isolation. Choose the least scope
actually compatible with the pinned Claude Action; no org:admin grant is permitted.
Select approved models, data retention, short token lifetime and saved workspace
spend/rate limits. Record sanitized setting match/status only, no billing export.

The generator derives immutable repository/owner identity from the new manifest.
The exact GitHub subject must be verified using genuine signed claims; subjects may
change with environment, repository transfer or customization. Never add a wildcard
or broaden a failed rule. Audience is https://api.anthropic.com. Production rule
must restrict repository and immutable IDs, ref refs/heads/main, workflow_dispatch,
caller agent-orchestrator.yml (and the separately authorized integration-smoke.yml
when testing) and reusable agent-build.yml identity. Use separate exact rules where
OR conditions would widen authority. This candidate supplies claim expectations,
not a provisioning API; provider-supported claims must be verified by the Owner.

Authentication-only testing uses a separate rule restricted to the generated
.github/workflows/authentication-test.yml identity,
main/manual/project scope and no model call. Preserve production rule restrictions;
a positive test under the test rule cannot prove production caller/callee enforcement.
Only the authentication job receives id-token:write after credential-free config
success; production grants it only to Claude jobs. Intake/CI/publisher/Codex do not.
Set GitHub nonsecret variables ENGINEERING_ANTHROPIC_ORGANIZATION_ID,
ENGINEERING_ANTHROPIC_WORKSPACE_ID, ENGINEERING_ANTHROPIC_SERVICE_ACCOUNT_ID,
ENGINEERING_ANTHROPIC_FEDERATION_RULE_ID (production),
ENGINEERING_ANTHROPIC_AUTH_TEST_RULE_ID (test), ENGINEERING_WIF_REPOSITORY,
ENGINEERING_ORCHESTRATION_ENABLED=false, ENGINEERING_SMOKE_ENABLED=false.
Issuer ID is recorded in the manifest; the Action consumes rule/org/account/workspace.

## Authorized testing — Codex

After reviewed merge and separate Owner test authorization, dispatch authentication-
only from main. First run the credential-free configuration check. Verify RS256
signature against discovery/JWKS before trusting issuer, audience, subject, repository/
owner IDs, ref, event, workflow identity, control SHA, run and time claims.
Token exchange uses the explicit workspace/account/rule. Require documented response
scope/type and bounded granted TTL; rule lifetime is a ceiling, not guaranteed expiry.
Then test provider replay rejection and a fresh correctly signed wrong-audience token.
Never print JWT/JTI/access token, authorization header, environment dump or provider body.
Never use static credential fallback; unset shadowing profile/key variables.

Additional required genuine signed-context negatives: other repository, branch,
caller/callee workflow, PR/fork, expired assertion, wrong account/workspace. These
remain NOT RUN until separately authorized safe contexts exist. A tampered payload
is a signature test, not provider restriction evidence. No privileged workflow on
an untrusted PR. Production identity requires separate validation without broadening
trust. Unexpected behavior stops without retries; record local checks separately
from Anthropic-enforced denial. No inference occurs in authentication tests.

Sources: [Anthropic WIF reference](https://platform.claude.com/docs/en/manage-claude/wif-reference),
[rule schema](https://platform.claude.com/docs/en/api/organization/federation/rules/create),
[GitHub reusable identity](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-with-reusable-workflows).

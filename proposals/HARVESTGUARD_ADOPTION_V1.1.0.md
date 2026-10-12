# HarvestGuard Governance v1.1.0 Adoption Proposal

**Status:** Proposed, adoption inactive; Tim approval required.

**Review date:** 2026-10-12

**Project baseline:** `serewicz/HarvestGuard` remote main at `77b52ac56833d9821008d1466683bb9969ed7641`.

**Upstream baseline:** released v1.0.0 at `bb08e871568f953f36e061d7fd89e467598bdcac`.

**Candidate:** this governance PR's reviewed exact head SHA, recorded in the PR evidence. Proposed v1.1.0 is not yet published. Resolve the final released SHA separately before adoption; do not substitute a moving branch or assume the eventual release commit equals the current PR head.

## Minimal proposed project configuration
| Field | Proposed value |
|---|---|
| Project / repository | HarvestGuard / serewicz/HarvestGuard |
| Owner, merge and release authority | Tim Serewicz; human-only merge and separately authorized publication |
| Governance pin | 1.1.0 after separate publication and adoption approval; exact verified release SHA required |
| Project revision | New explicit revision assigned in the adoption change; existing contract/YAML v1 identities reconciled |
| Product boundary | Cryptographic asset inventory and evidence collection; ADR-006 remains authoritative for product scope |
| Architecture/privacy | Local-first, no telemetry by default, evidence/inference separation, no raw customer scans to external models; private repository content needs explicit processing authorization |
| Architect / builder / principal / security | ChatGPT / Claude / Codex / Grok or Tim-designated independent security reviewer |
| Classification | Tim or explicitly delegated classifier independent of builder; every task starts Tier 2 |
| Tier 0 | Nontechnical prose only outside governed/security/config/executable files; retain independent Codex review required by existing policy |
| Tier 1 | Clear bounded nonsecurity task only, approved issue where existing policy requires it; abbreviated independent Codex review |
| Tier 2 | Default; all security/privacy/governance/deployment/supply-chain/publication/trust triggers; preserve full project process |
| Checks | Ruff and pytest; required Python 3.10/3.11/3.12 CI; issue-specific probes, applicable container/package/security checks |
| Correction budget | Retain 3 automated correction/re-review cycles as a recorded deviation; initial review is cycle 0 |
| Evidence | Issue approval/spec revision, PR, exact reviewed SHA, commands/environments/results/limitations, workflow artifacts, security disposition, Tim authorization and recovery notes |
| Approval / effective date | Pending; no existing policy has changed |

Existing principal review remains required even for Tier 0. Estimated HarvestGuard executions are therefore at least builder + principal reviewer (normally 2) for Tier 0 and Tier 1; the generic one-execution Tier 0 estimate is not an adoption promise. No cheap tier changes issue approval, customer-data permissions, or merge/release authority.

## Safeguards to preserve
Keep human-only merge and sensitive decisions; builder/reviewer independence; exact-SHA freshness; all mandatory CI; resolved conversations; isolated disposable workspaces and human-controlled canonical checkout; no force push; protected paths; independently revocable role-scoped credentials; no agent credential management; customer-data restrictions; fixture-first development and provenance; two 40-turn builder segments, complete recovery checkpoints, correction failure recovery, and budget escalation. Preserve product boundary, evidence semantics, closure review and documentation reconciliation.

Map upstream PASS / CHANGES REQUIRED / BLOCKED to project APPROVED / BLOCKERS / NEEDS_HUMAN without changing schemas or severity meaning. IMPORTANT prevents automated approval. Existing process language allowing deliberately accepted IMPORTANT findings must identify Tim's recorded acceptance and must not imply the automated checker will accept a nonempty important list.

Precedence is the pinned upstream baseline plus approved project configuration and retained stronger local controls. Contradictions block work; no generic template may silently override local safeguards. Do not rewrite the upstream version label when recording a project deviation.

## Enforcement gaps and proposed reconciliation
These were verified against the project snapshot and live settings on the review date; they are not claims that adoption is already enforced.

| Gap | Evidence | Proposed change requiring Tim approval |
|---|---|---|
| Spec authorization | Engineering process requires READY TO IMPLEMENT; dispatch retrieves issue but does not validate approval | Bind approved issue/spec revision to authorization; either explicitly authorize human dispatch as attestation or add an independently verified approval gate; refuse ambiguous/stale approval |
| Security review | Contract requires CISO paths and behavioral triggers; orchestrator has no designated security-review stage | Record trigger assessment and designated independent review for exact final SHA before merge/release; missing review blocks; no-trigger case records NOT REQUIRED and rationale |
| CI permissions | Repository workflow default is write and Actions may approve PRs; ci.yml has no permissions restriction | Set explicit contents: read for CI and read defaults; narrow write scopes to authorized publishing jobs; review default Actions PR-approval capability and automation token separately |
| Container checks | Main protection and check_required_ci.py require only Python matrix checks | Require applicable container validation for affected changes; use a non-skipped aggregate readiness gate if needed so path-filtered checks do not deadlock unaffected PRs |
| Publication authority | Container publish runs on main push or workflow_dispatch, depends on container validation only, and manual path has no main-ref/environment guard | Decide whether main merges explicitly authorize commit-SHA GHCR publication; enforce reviewed main SHA, mandatory CI, security disposition and authorization for each permitted publication path; manual non-main publication must fail closed |
| Protected governance | check_builder_result.py protects workflows, policy and current contract only | Protect adopted contract/configuration/routing plus governance enforcement scripts and composite actions; mirror enforcement in prompts, path gates and publish backstops, not just advisory prose |
| Release recovery | Package checklist is explicit, but release recovery/rollback is not a general gate | Record previous verified version/digest, compatibility and recovery steps/limitations appropriate to risk before publication |
| Independent merge gates | Main requires 0 approving reviews; no rulesets; principal/security verdicts are not required protection checks | Choose an enforceable readiness mechanism suited to available human reviewers, not a blanket approving-review count that could prevent sole-maintainer work; retain human merge and exact-SHA principal/security evidence |
| Security trigger drift | YAML path list omits behavioral triggers and pyproject.toml supply-chain changes | Unify behavioral and path assessment; include packaging, parser, personal-data, credential, network and trust-boundary changes even outside listed directories |

Main currently requires strict Python 3.10/3.11/3.12 checks, resolved conversations, stale approval dismissal and administrator enforcement; force pushes/deletion are disabled. Preserve these. Token scopes, bypass actors and historical compliance were not audited; protection alone does not prove Tim is the only credential holder capable of merging.

## Migration and validation plan
1. Tim approves candidate semantics, project precedence/revision, classifier delegation, three-cycle deviation, and publication boundaries. The user task authorizes preparation, not activation or publication.
2. Complete independent Tier 2 governance review and re-review each changed head. Tim decides governance merge and separately authorizes release; verify and record the final v1.1.0 tag and release SHA.
3. Prepare a separate isolated HarvestGuard adoption branch only after authorization. Preserve all local uncommitted work; recheck remote main and live settings. Copy the core documents from the exact released commit, customize configuration, add provenance and retained controls, and reconcile instructions/contracts/YAML. Do not use unapproved candidate text as an active policy.
4. Address approved enforcement changes in bounded reviewed PRs. Governance/workflow changes require independent principal and designated security evaluation and human approval. No live settings change is bundled silently.
5. Test positive/negative tier eligibility, no self-downgrade, scope growth, stale approvals/SHA, cycle 3 permitted and cycle 4 rejected, missing security evidence, protected-file edits, least-privilege scopes, applicable container checks, failed/missing CI, non-main/manual publication, and recovery readiness. Run existing affected governance/workflow tests; no publication needed to validate a denied path.
6. Tim approves activation after required changes pass or explicitly records permitted temporary exceptions with owner, rationale, expiry/review date, and manual mitigation. Mandatory upstream controls cannot simply be waived by a tier. Record adoption date and final project revision.

## Unresolved risks and approval actions
- Approve or reject retaining 3 correction cycles; prior project code records authorization but the new adoption deviation still needs an adoption record.
- Confirm role assignments and any classifier delegation; do not infer new permissions from role names.
- Decide enforceable principal/security readiness and spec authorization mechanism.
- Decide main-push GHCR authorization and manual-dispatch controls; automatic publishing today is not proof of release authorization.
- Approve any workflow/default permission, token or branch-protection changes separately; verify actual token scope without exposing credentials.
- Approve project governance revision/precedence, deviations and migration order; keep adoption inactive until resolved.
- Separately approve governance merge, v1.1.0 publication, HarvestGuard adoption work/activation, live settings, and any artifact publication. None is performed by this proposal.

## Inspected sources
- [Agent contract](https://github.com/serewicz/HarvestGuard/blob/77b52ac56833d9821008d1466683bb9969ed7641/docs/AGENT_CONTRACT.md)
- [Machine policy](https://github.com/serewicz/HarvestGuard/blob/77b52ac56833d9821008d1466683bb9969ed7641/.agent-policy.yml)
- [Engineering process](https://github.com/serewicz/HarvestGuard/blob/77b52ac56833d9821008d1466683bb9969ed7641/docs/ENGINEERING_PROCESS.md)
- [Orchestrator](https://github.com/serewicz/HarvestGuard/blob/77b52ac56833d9821008d1466683bb9969ed7641/.github/workflows/agent-orchestrator.yml)
- [CI](https://github.com/serewicz/HarvestGuard/blob/77b52ac56833d9821008d1466683bb9969ed7641/.github/workflows/ci.yml)
- [Container workflow](https://github.com/serewicz/HarvestGuard/blob/77b52ac56833d9821008d1466683bb9969ed7641/.github/workflows/container-build.yml)
- [Protected paths](https://github.com/serewicz/HarvestGuard/blob/77b52ac56833d9821008d1466683bb9969ed7641/scripts/check_builder_result.py)
- [Release policy](https://github.com/serewicz/HarvestGuard/blob/77b52ac56833d9821008d1466683bb9969ed7641/docs/RELEASE.md)
- Live read-only API inspection: main branch protection, repository rulesets, and Actions workflow permissions. Recheck these at migration; they are mutable external state.

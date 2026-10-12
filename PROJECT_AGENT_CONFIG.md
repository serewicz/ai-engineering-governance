# Project Agent Configuration

> **Reusable template — project-specific customization required.** Replace every placeholder, assign accountable roles, define project gates and checks, and obtain recorded owner approval before adoption. This draft grants no implementation, merge, deployment, or release authority.

**Project:** [PROJECT_NAME]

**Repository:** [OWNER/REPO]

**Governance contract version:** 1.1.0 candidate

**Upstream tag:** v1.1.0 (not yet published; do not treat as a released pin)

**Upstream exact commit:** [REVIEWED CANDIDATE SHA; REPLACE WITH VERIFIED RELEASE SHA AFTER PUBLICATION]

**Configuration owner:** [NAME]

**Project governance revision:** [VERSION]

**Status:** Draft, adoption inactive

## Outcomes and boundaries
- Product objective: [OUTCOME]
- In/out of scope: [BOUNDARIES]
- Architecture/compatibility constraints: [CONTRACTS]
- Risk class and sensitive assets: [DETAILS; CLASSIFY EACH TASK]

## Assignments
- Owner / CTO, final policy and release authority: [HUMAN]
- Merge executor/authority: [HUMAN-ONLY OR BOUNDED AUTOMATION UNDER EXPLICIT OWNER-APPROVED POLICY; HARVESTGUARD IS HUMAN-ONLY]
- Architect / advisor: [AGENT OR AUTHORIZED SUBSTITUTE]
- Builder: [AGENT]
- Independent principal reviewer: [AGENT]
- Independent security reviewer: [DESIGNATED REVIEWER WHEN TRIGGERED]
- Classification authority: [OWNER OR DELEGATE INDEPENDENT OF BUILDER; EVIDENCE OF DELEGATION]

## Tools and mandatory gates
- Issue tracker and approval evidence: [LOCATION; ISSUE REQUIREMENTS STILL APPLY]
- Spec gate: [WHO RECORDS READY TO IMPLEMENT; BIND APPROVAL TO SPEC REVISION]
- CI/test matrix: [COMMANDS, ENVIRONMENTS, REQUIRED CHECKS]
- Applicable container/package/security checks: [TRIGGERS AND CHECKS]
- Branch/PR and isolation policy: [RULES]
- Merge delegation: [NONE OR OWNER-APPROVED POLICY REVISION, APPROVAL EVIDENCE, EXECUTOR, BRANCH/SCOPE LIMITS, DURATION/REVOCATION, CREDENTIAL LIMITS, AND ESCALATION OWNER]
- Merge execution gate: independently verify reviewed/current exact SHA, successful required checks, independent approval, security disposition, atomic stale-head guard, and retained project safeguards; record final SHA. Uncertain, stale, failed, missing or out-of-scope evidence blocks execution. Delegation never authorizes self-approval, policy changes, risk acceptance or publication.
- Protected governance paths: [CONTRACT, CONFIGURATION, POLICY, WORKFLOWS, ENFORCEMENT CODE]
- Credential/deployment permissions: [LIMITS; HUMAN-CONTROLLED]
- Security review recording: [EXACT-SHA DISPOSITION AND LOCATION]
- Release/publication authorization and recovery evidence: [WHO, SCOPE, SHA, SURFACES, CHECKS, RECOVERY NOTES]
- Retained stronger safeguards: [EXISTING CONTRACTS, PRIVACY RULES, REVIEW AND HUMAN GATES]

## Tier eligibility and overrides
All tasks start Tier 2. Upstream exclusions and triggers are mandatory; project overrides may only narrow eligibility or add safeguards.

- Tier 0 positive evidence: [NEGLIGIBLE RISK; NONTECHNICAL PROSE/FORMATTING ONLY; NO EXCLUDED CONTENT]
- Tier 0 independent disposition: [AUTHORIZED HUMAN OR PROJECT-MANDATED REVIEWER; NO SELF-APPROVAL]
- Tier 1 positive evidence: [LOW-RISK BOUNDED NONSECURITY SCOPE; CLEAR ACCEPTANCE AND FOCUSED TESTS]
- Tier 1 independent reviewer: [CODEX OR AUTHORIZED SUBSTITUTE; EXACT SHA]
- Additional Tier 2 triggers: [PROJECT PATHS AND BEHAVIORS]
- Scope expansion/uncertainty: stop for approval and reclassification; Tier 2 if ambiguous.
- Severity mapping: [PRESERVE PROJECT RULES; IMPORTANT PREVENTS AUTOMATED APPROVAL]
- Review freshness: every changed SHA requires fresh independent disposition.

## Deviations and version control
- Default maximum correction/re-review cycles: 2; initial review is cycle 0.
- Project maximum: [2 OR EXPLICIT APPROVED DEVIATION]
- Deviation register: [CONTROL, RATIONALE, APPROVER, APPROVAL EVIDENCE, REVIEW DATE]
- Precedence: upstream baseline plus approved configuration and retained stricter local controls; contradictions block work until owner resolution.
- Policy changes: owner approval and recorded project contract revision; never relabel a modified upstream contract as unchanged.
- Evidence storage: [ISSUE/PR/ARTIFACTS/RELEASE RECORDS]

## Adoption record
- Approved by / evidence: [HUMAN AND LINK]
- Date / next review: [DATES]
- Contract version pinned: [1.1.0 AFTER SEPARATE PUBLICATION APPROVAL]
- Verified release commit: [SHA]
- Existing project baseline reviewed: [SHA]
- Unresolved decisions: [NONE BEFORE ACTIVATION]

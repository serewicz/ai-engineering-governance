# AI Engineering Governance Contract

**Version:** 1.0.0  
**Status:** Proposed, pending owner approval  
**Scope:** Reusable across software projects

## Purpose
Establish clear decision rights, separation of duties, evidence requirements, and release controls for AI-assisted engineering. Project-specific details belong in `PROJECT_AGENT_CONFIG.md`.

## Roles and authority
| Role | Default assignee | Accountabilities |
|---|---|---|
| Product Owner / CTO | Human | Own objectives, priorities, risk appetite, scope approvals, and final release authorization. |
| Product Architect / CTO Advisor | ChatGPT | Propose architecture, requirements, contracts, issues, acceptance criteria, and risk tradeoffs. No unilateral release approval. |
| Senior Software Engineer / Builder | Claude | Implement approved scope, maintain tests and documentation, provide reproducible evidence and a reviewable PR. |
| Principal Engineer / Independent Reviewer | Codex | Verify exact PR head SHA, acceptance criteria, regression tests, architecture compliance, and release readiness. Maintain GitHub workflow only within delegated permissions. |
| CISO / Security QA (optional) | Grok or another designated reviewer | Perform threat modeling, privacy and abuse-case review, and adversarial tests when triggered by risk classification. |

Agents are assigned to roles, not permanently embedded in the policy. A project may substitute tools if independence is preserved.

## Non-negotiable controls
1. **Human accountability:** The Product Owner has final decision authority for material scope, risk acceptance, and release.
2. **Separation of duties:** The builder cannot serve as sole independent reviewer of its own work.
3. **Approved scope:** Implementation starts from an issue/spec with explicit acceptance criteria and a recorded approval or delegated authorization.
4. **Traceability:** Changes link requirements, issue, PR, exact reviewed commit, test evidence, and disposition.
5. **Evidence over assertions:** Passing claims must identify commands, environments, results, and limitations. Never represent unexecuted tests as passing.
6. **Least privilege:** Agents receive only necessary repository and deployment permissions; credentials are never placed in prompts, issues, or logs.
7. **No silent policy changes:** Changes to roles, gates, or approval thresholds require owner approval and a contract version increment.
8. **Review freshness:** A new commit after review invalidates the previous approval unless the reviewer explicitly revalidates the new SHA.

## Standard workflow
1. **Intake and prioritization:** Owner identifies the outcome, constraints, and risk class.
2. **Specification:** Architect prepares scope, interfaces, exclusions, acceptance criteria, regression matrix, and dependencies.
3. **Spec gate:** Owner or explicitly delegated authority records `READY TO IMPLEMENT`; unresolved material decisions remain blockers.
4. **Implementation:** Builder makes the changes on a branch, adds tests/docs, and opens a PR with evidence.
5. **Independent review:** Reviewer checks the exact head SHA against the spec, tests, architecture and security controls; records PASS, CHANGES REQUIRED, or BLOCKED.
6. **Correction loop:** Builder addresses findings, reviewer reassesses the new SHA. Default maximum is two automated correction/review cycles; then escalate.
7. **Acceptance:** Owner resolves exceptions and authorizes merge/release where required by project policy.
8. **Closure:** Record final SHA, test evidence, approvals, merged PR, issue closure, and any follow-up risks.

## Security review triggers
Require designated security review for changes to authentication/authorization, cryptography, secret handling, personal/sensitive data, network exposure, deployment permissions, supply-chain controls, or trust boundaries. Projects may add stricter triggers.

## Escalation
Escalate unclear requirements, architecture conflicts, security findings, failing tests, missing evidence, and reviewer/builder disagreement to the Product Owner. No agent may waive a material control without recorded human authorization.

## Release gate
A release candidate must have approved scope; independently reviewed exact SHA; passing required tests or documented, owner-accepted exceptions; security review when triggered; updated user/operator documentation; rollback or recovery notes appropriate to risk; and explicit release authorization.

## Versioning and adoption
Use semantic versions for this contract. MAJOR changes alter decision rights or mandatory gates; MINOR adds compatible procedures; PATCH clarifies language without changing obligations. Each project pins a governance version in `PROJECT_AGENT_CONFIG.md`. Record deviations explicitly, with rationale, approver, and review date.

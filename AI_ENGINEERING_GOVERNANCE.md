# AI Engineering Governance Contract

**Version:** 1.1.0

**Status:** Proposed candidate, pending owner approval and publication

**Scope:** Reusable across software projects

## Purpose
Establish clear decision rights, separation of duties, evidence requirements, and release controls for AI-assisted engineering. Project-specific details belong in [PROJECT_AGENT_CONFIG.md](PROJECT_AGENT_CONFIG.md). Execution tiers scale preparation and review depth to risk; they do not waive mandatory controls.

## Roles and authority
| Role | Default assignee | Accountabilities |
|---|---|---|
| Product Owner / CTO | Human; Tim for the initial adopting project | Own objectives, priorities, risk appetite, scope approvals, final merge and release authorization. |
| Product Architect / CTO Advisor | ChatGPT | Propose architecture, requirements, contracts, issues, acceptance criteria, and risk tradeoffs. No unilateral release approval. |
| Senior Software Engineer / Builder | Claude | Implement approved scope, maintain tests and documentation, provide reproducible evidence and a reviewable PR. |
| Principal Engineer / Independent Reviewer | Codex | Verify exact PR head SHA, acceptance criteria, regression tests, architecture compliance, and release readiness. Maintain GitHub workflow only within delegated permissions and human approval for governance changes. |
| CISO / Security QA | Grok or another designated independent security reviewer | Perform threat modeling, privacy and abuse-case review, and adversarial tests when triggered by risk classification. |

These are five responsibilities, not five mandatory agent executions per change. A project may substitute tools if independence is preserved. Security review is mandatory when triggered; otherwise record `NOT REQUIRED` with rationale without an additional model execution.

## Non-negotiable controls
1. **Human accountability:** The Product Owner has final decision authority for material scope, risk acceptance, and release. Merge remains human-only; tiers do not delegate merge authority to agents.
2. **Separation of duties:** The builder cannot serve as sole independent reviewer of its own work. Tier 0 may use an authorized independent human for a minimal exact-SHA review; retain an independent agent review if project policy requires it. Preparation, classification, review, and merge authorization are distinct evidence records even when an authorized human handles several of them.
3. **Approved scope:** Implementation starts from an issue/spec with explicit acceptance criteria and a recorded approval or delegated authorization. A concise approved task can serve as the spec for a limited or trivial change; an existing mandatory issue requirement still applies. No task tier removes the approval gate.
4. **Traceability:** Changes link requirements, issue/task, PR, exact reviewed commit, test evidence, and disposition.
5. **Evidence over assertions:** Passing claims must identify commands, environments, results, and limitations. Never represent unexecuted tests as passing.
6. **Least privilege:** Agents receive only necessary repository and deployment permissions; credentials are never placed in prompts, issues, or logs.
7. **No silent policy changes:** Changes to roles, gates, or approval thresholds require owner approval and a contract version increment. Project policy changes have a separately recorded project revision and approval; editing a local copy does not change the upstream version.
8. **Review freshness:** A new commit after review invalidates the previous approval unless the reviewer explicitly revalidates the new SHA. Prior specifications and evidence may be reused only when their scope, inputs, environment, and applicability remain valid; stale approval never carries over automatically.

## Classification and escalation
Every task starts at **Tier 2**. The Owner or an explicitly delegated classifier independent of the builder may downgrade only with documented positive eligibility evidence. The builder may propose a tier but may not authorize its own downgrade to bypass required independent review. Classify risk and impact, not lines or file counts. Project rules may narrow eligibility or demand deeper review; they may not make an excluded change eligible.

Security, privacy, governance, deployment, dependencies/supply chain, CI permissions, publication, and trust-boundary triggers force Tier 2. Authentication, secrets, cryptography, network exposure, and sensitive data are included in these triggers. Unknown risk, mixed changes with an excluded component, unclear requirements, or missing eligibility evidence remain Tier 2. Assess actual behavior as well as changed paths; a test or prose edit can affect security or governance.

Scope expansion requires approval and reclassification before further implementation. Any participant may escalate; the independent reviewer may require Tier 2. Preserve project severity rules: `IMPORTANT` findings prevent automated approval. Missing evidence, failing required checks, material disagreement, or unresolved security findings escalate to the Owner; agents may not waive material controls.

## Execution tiers
### Tier 0: Trivial
Negligible risk and value: typos, punctuation, whitespace, formatting, and simple nontechnical prose corrections only. One authorized agent may prepare a change; no full planning or multi-agent evaluation cycle is needed. Batch compatible trivial changes where practical.

Exclude executable content (including code whitespace), governance-controlled files, security documentation, configuration, dependencies, and behavioral changes. Technical claims, instructions, commands, links affecting trust, or changed obligations are not simple nontechnical prose. Run relevant deterministic validation plus mandatory project checks; record a minimal disposition and exact SHA. Obtain a minimal independent exact-SHA review from an authorized human, or the independent reviewer required by project policy. No self-approval. Human-only merge and every mandatory control remain intact.

### Tier 1: Limited
Low-risk bounded changes: isolated nonsecurity bug fixes, small presentation changes, simple tests, and narrowly scoped documentation updates with demonstrably clear impact. Use an existing issue or concise approved task/spec with acceptance criteria. Claude or another authorized builder implements it. ChatGPT planning is optional when the approved requirements are already clear; preserve any mandatory project planning gate.

Run focused tests and all mandatory project checks before Codex (or an authorized independent substitute) performs an abbreviated review of the exact SHA. The reviewer may escalate to Tier 2 if scope, risk, or uncertainty increases. Exclude cryptography, authentication, secrets, privacy, governance, deployment, dependencies/supply chain, CI permissions, publication, trust boundaries, and security documentation. Retain human-only merge authority.

### Tier 2: Standard, default
All normal engineering work and anything not demonstrably eligible for Tier 0 or Tier 1 follows the full role model. The Owner sets priorities and approves material decisions. The Architect prepares or validates architecture, requirements, interfaces, acceptance criteria, risk, and test plans. The Builder implements the approved specification, tests, documentation, and PR. The Principal Reviewer independently evaluates the exact SHA, acceptance criteria, tests, and release readiness. A designated independent security reviewer evaluates triggered work; otherwise record `NOT REQUIRED` with rationale. The Owner authorizes merge and release.

A valid approved specification can be reused; performing a role does not necessarily require a new model invocation. Governance changes, including this candidate, are Tier 2 and require substantive independent review and recorded owner approval.

## Standard workflow and cost control
1. **Intake:** Owner identifies outcome, constraints, and risk; record Tier 2 initially.
2. **Classify and specify:** Establish eligible tier, rationale, triggers, classifier authority, exclusions, acceptance criteria, and required checks. Prepare or reuse a valid approved specification at the appropriate depth.
3. **Spec gate:** Owner or delegated authority records `READY TO IMPLEMENT`; unresolved material decisions remain blockers. A concise task approval may record the same gate for Tier 0/1.
4. **Implement:** Builder changes only approved scope on a branch and provides a PR with evidence.
5. **Validate then review:** Run deterministic checks before model review. Independent review checks the exact SHA at the required depth; record PASS, CHANGES REQUIRED, or BLOCKED. Security review is separate when triggered.
6. **Correct:** Builder addresses findings; reviewer reassesses the new SHA. Initial review is cycle 0. Default maximum is two automated correction/re-review cycles (cycles 1 and 2), then escalate. Project deviations must be approved and recorded; HarvestGuard's proposed adoption retains three (cycles 1 through 3).
7. **Accept:** Owner resolves exceptions and authorizes human merge and release. `IMPORTANT` findings cannot be automatically accepted.
8. **Close:** Record final SHA, executed checks, approvals, review disposition, merged PR, closure, and follow-up risks.

Avoid repeated context analysis, redundant agent calls, and repeated checks whose evidence remains applicable. Bound correction loops. Never use cost or time savings to bypass safety, security, independent review, or human authorization. See [TIER_ROUTING.md](TIER_ROUTING.md) for routing, invocation estimates, and classification examples.

## Security review triggers
Require designated independent security review for changes to authentication/authorization, cryptography, secret handling, personal/sensitive data, network exposure, deployment permissions, supply-chain controls, or trust boundaries. These changes force Tier 2. Projects may add stricter triggers. Tier 2 alone does not imply a security trigger: record the decision and rationale.

## Evidence record
Store tier and positive rationale; classifier and approval/delegation; actual changed scope and triggers; approved spec; commands, environments, results and limitations; exact reviewed SHA; reviewer identity, findings, disposition; security verdict or justified `NOT REQUIRED`; and owner merge/release authorization. Preserve links between task, PR, checks, artifacts, and final commit. Use [AGENT_HANDOFF_TEMPLATE.md](AGENT_HANDOFF_TEMPLATE.md).

## Release gate
A release candidate must have approved scope; independently reviewed exact SHA; passing required tests or documented, owner-accepted exceptions; security review when triggered; updated user/operator documentation; rollback or recovery notes appropriate to risk; and explicit human release authorization. Publication itself is Tier 2. An automated publication path requires explicit owner authorization covering the reviewed SHA, required checks, security disposition, and publication surface; a task tier or merge alone never silently grants that authorization.

## Versioning and adoption
Use semantic versions. MAJOR changes alter decision rights or mandatory gates; MINOR adds compatible procedures; PATCH clarifies language without changing obligations. This candidate proposes risk-based execution depth while retaining approval, independence, evidence, and release safeguards; it does not permit bypassing an existing project gate. **Unresolved version decision:** v1.0.0 authorized merge/release where required by project policy; this task requests universal human-only merge. That stronger mandatory gate may require a MAJOR version under the published rule. The requested 1.1.0 label is provisional, not a compatibility finding. Tim must resolve the baseline interpretation or approve a version consistent with the semantic-version rule before merge/publication. Do not weaken human authority to avoid this conflict. Any proposed gate weakening likewise requires escalation and a separately reviewed version decision, not a silent tier override.

Each project pins the upstream version and exact commit in its configuration, preserves stronger local safeguards, and records deviations with rationale, approver, and review date. Conflicts block adoption until owner resolution. Upstream publication does not activate project adoption. The published v1.0.0 remains available at `bb08e871568f953f36e061d7fd89e467598bdcac`; v1.1.0 is only a candidate until separately authorized and published.

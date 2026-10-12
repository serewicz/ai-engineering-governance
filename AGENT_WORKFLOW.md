# Agent Workflow

**Governance version:** 1.1.0 candidate

1. **Intake (Owner):** Record the task, outcome, and constraints; start at Tier 2.
2. **Classify (Owner or independent delegated classifier):** Downgrade only with positive eligibility evidence and recorded authority. Assess behavioral and path triggers, mixed scope, uncertainty, and stronger project rules. The builder cannot self-authorize a downgrade. Triggers or ambiguity keep Tier 2.
3. **Plan and approve:** Use a concise approved spec for Tier 0/1, or a complete approved specification for Tier 2. Valid prior specifications may be reused. Record acceptance criteria and `READY TO IMPLEMENT`; retain mandatory issue and planning requirements.
4. **Build (Builder):** Implement approved scope in the authorized branch/workspace; provide PR, exact SHA, changed files, checks, outputs, and gaps. Scope growth stops work for approval and reclassification.
5. **Validate:** Run relevant deterministic checks and all mandatory project checks before model review. Missing/failing required evidence blocks progression unless an exception is explicitly permitted and owner-approved.
6. **Review independently:** Tier 0 uses a minimal exact-SHA disposition by an authorized independent human or the project's required reviewer. Tier 1 uses abbreviated Codex/substitute review. Tier 2 uses full principal review and designated independent security review when triggered; otherwise record justified `NOT REQUIRED`. Return PASS / CHANGES REQUIRED / BLOCKED with evidence. `IMPORTANT` prevents automated approval.
7. **Correct and re-review:** Every new SHA needs fresh review. Initial review is cycle 0; default at most two corrections and re-reviews, then escalate. An approved project deviation can retain HarvestGuard's three corrections. No unbounded loop.
8. **Merge/release (Authorized executor):** Follow explicitly Owner-approved project policy. HarvestGuard retains human-only merge. Other projects may permit bounded automated execution only with documented delegation, approved independent review, matching current/reviewed exact SHA, successful required checks, applicable security disposition, atomic stale-head protection and escalation on any uncertainty. Missing authorization blocks merge. Publication requires separate explicit authorization and the contract release gate; it always routes to Tier 2. Record final evidence and closure.

**Stop conditions:** unclear approval/classification, missing required checks, secrets exposure, unreviewed commit, material scope expansion, unresolved security issue or material disagreement, exhausted budget/cycle limit, or contradictory governance.

Roles need not produce separate model calls. Reuse valid approved context and evidence, avoid redundant reviews, and batch eligible Tier 0 changes. Efficiencies do not waive mandatory gates. See [contract](AI_ENGINEERING_GOVERNANCE.md), [routing matrix](TIER_ROUTING.md), and [handoff](AGENT_HANDOFF_TEMPLATE.md).

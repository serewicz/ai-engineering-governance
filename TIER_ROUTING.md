# Tier Classification and Agent Routing

**Governance version:** 1.1.0 candidate

The [contract](AI_ENGINEERING_GOVERNANCE.md) governs. Every task starts Tier 2; a lower tier needs documented positive evidence and independent owner/delegate authorization. File count is not eligibility evidence.

| Tier | Positive eligibility | Planning | Preparation | Independent review | Security | Human gates |
|---|---|---|---|---|---|---|
| 0 Trivial | Negligible-risk typo, punctuation, prose whitespace/formatting or simple nontechnical correction; no exclusions/triggers | Concise approved task/spec; no full planning cycle | One authorized agent; batch where practical | Minimal exact-SHA human disposition; retain required agent review | No trigger allowed | Classification/spec approval, merge; release routes to Tier 2 |
| 1 Limited | Demonstrably bounded low-risk nonsecurity bug, presentation, simple test or documentation update; clear requirements | Existing/concise approved spec; separate ChatGPT execution optional | Claude or authorized substitute | Abbreviated Codex/substitute exact-SHA review | No trigger allowed | Classification/spec approval and merge |
| 2 Standard | Default, uncertain, mixed, substantial, or triggered work | Full approved specification; reuse valid prior work | Claude or authorized substitute | Full Codex/substitute exact-SHA review | Independent reviewer when triggered; otherwise justified NOT REQUIRED | Material decisions, merge and release |

## Estimated model invocations
An invocation here means one role's model execution, not one API request, tool call, turn, or guaranteed billable unit. Humans and deterministic checks are excluded. Estimates are planning assumptions, not measurements.

| Tier | Typical initial executions | Conditions |
|---|---|---|
| 0 | 1 | Preparation only if an independent human provides required review; 2 or more if project policy requires model review/planning |
| 1 | 2 | Builder plus abbreviated independent review; 3 if new architect execution is needed |
| 2 | 2–4 | Builder and principal review, plus 0–1 architect execution (approved spec reuse), plus 0–1 independent security execution when triggered |

Each permitted correction/re-review normally adds 2 executions. Security-relevant corrections may also need fresh security review. Default maximum is 2 corrections; an approved HarvestGuard deviation permits 3. Batching and valid evidence reuse can reduce calls; mandatory project controls can increase them. No promised percentage cost/time saving is claimed.

## Classification boundaries
- Tier 0 excludes executable content, configuration, dependencies, behavioral changes, governance-controlled files and security documentation. Code indentation or an executable example is not prose whitespace.
- Tier 1 excludes security/cryptography/authentication/secrets/privacy/governance/deployment/dependencies/supply chain/CI permissions/publication/trust boundaries and security documentation.
- All such triggers force Tier 2. A security-test deletion or a 'typo' in a permission setting still has a trigger. Assess mixed scope at the highest risk.
- Unknown risk or absent approval/eligibility evidence remains Tier 2. Builder self-downgrade is invalid. Scope expansion stops work for reapproval and reclassification.
- Principal/security findings retain project severity; IMPORTANT cannot be automatically approved.

## Validation
Run `python3 -m unittest discover -s tests -v` and `python3 scripts/validate_documents.py`.

[Classification scenarios](tests/classification_cases.json) contain positive and negative examples, including executable whitespace, technical prose, security documentation, sensitive tests, dependency/configuration changes, all mandatory trigger classes, mixed scope, self-downgrade, missing evidence, uncertainty and scope expansion. [Reference classifier](scripts/classify_task.py) makes these examples executable. It is a decision aid over supplied facts, not a production authorization gate or a replacement for inspecting the diff. Its inputs do not prove identity, approval, eligibility, or absence of a trigger. Record independently verified evidence in the real task; false input can misclassify a change. Every result still requires the contract's review and human gates.

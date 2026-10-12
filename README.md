# AI Engineering Governance

Reusable governance for AI-assisted software engineering: human accountability, independent review, evidence, and release controls. Proposed **v1.1.0** adds three execution tiers to reduce redundant model executions without waiving mandatory safeguards.

## Documents
- [Governance contract](AI_ENGINEERING_GOVERNANCE.md): five responsibilities, mandatory controls, classification, tiers, security triggers, and release gates.
- [Project configuration](PROJECT_AGENT_CONFIG.md): reusable template requiring project customization and recorded owner approval.
- [Agent workflow](AGENT_WORKFLOW.md): routing, checks, review, correction, and human authorization.
- [Handoff template](AGENT_HANDOFF_TEMPLATE.md): classification, exact SHA, evidence, review, and closure.
- [Tier routing matrix](TIER_ROUTING.md): eligibility, positive/negative cases, and estimated model executions.
- [HarvestGuard adoption proposal](proposals/HARVESTGUARD_ADOPTION_V1.1.0.md): inactive proposal preserving stronger controls and tracking enforcement gaps.

## Roles and execution
Owner/CTO (human; Tim in HarvestGuard), Architect (ChatGPT), Builder (Claude), Principal Reviewer (Codex), and Security QA (Grok or independent substitute) are responsibilities, not five obligatory calls. Default Tier 2 uses the full role model; Tier 1 permits clear bounded work with abbreviated independent review; Tier 0 permits negligible-risk nontechnical corrections with minimal independent disposition. Security/governance and other mandatory triggers force Tier 2. The builder cannot self-authorize a downgrade or self-approve. Humans retain merge and release authority.

## Reuse, version pinning, and adoption
The published baseline remains [v1.0.0](https://github.com/serewicz/ai-engineering-governance/releases/tag/v1.0.0) at `bb08e871568f953f36e061d7fd89e467598bdcac`. **v1.1.0 is a proposed candidate, not a published release or active project adoption.** Its reviewed PR head identifies the candidate. After separate publication approval, verify and pin the release tag and exact commit; never adopt a moving `main`.

1. Select a separately approved released version and retrieve all four core documents from the same exact commit. Retain provenance and supporting routing guidance where used.
2. Customize every configuration placeholder, including project boundaries, roles, classifier authority, checks, security triggers, protected paths, permissions, and release authorization.
3. Preserve stronger existing controls. Record deviations with rationale, approver, evidence and review date. Resolve contradictions before adoption.
4. Obtain recorded owner approval, pin version and release SHA, complete the adoption record, and activate only then. Publication alone grants no project authority.
5. Link project contributor/agent instructions to the adopted controls. Use exact-SHA review, valid evidence, human gates and bounded correction loops.

MAJOR versions change decision rights or mandatory gates; MINOR adds compatible procedures; PATCH clarifies existing obligations. The proposed 1.1.0 changes execution depth, preserves mandatory gates and requires stricter project rules to remain in force. Governance changes require owner approval and a recorded revision.

## Validation
Use Python 3.10+ with its standard library; no package installation is required:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_documents.py
```

Checks cover executable classification examples, required files, local Markdown link/anchor targets, candidate versions and key cross-document invariants. Manual review covers semantic consistency, retained baseline controls, trigger boundaries, and adoption risks. External links are verified where needed through GitHub API inspection; the local validator does not claim to check remote availability. Independent review evidence and exact candidate SHA belong in the PR record. No v1.1.0 tag, release, adoption activation, live protection change, or artifact publication is authorized by this candidate.

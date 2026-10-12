# AI Engineering Governance

Reusable governance documents for AI-assisted software engineering: human accountability, clear decision rights, independent review, evidence, and release controls.

## Documents

- [AI Engineering Governance Contract](AI_ENGINEERING_GOVERNANCE.md): shared roles, mandatory controls, security triggers, escalation, release gates, and versioning.
- [Project Agent Configuration](PROJECT_AGENT_CONFIG.md): **reusable template requiring project-specific customization and owner approval**.
- [Agent Workflow](AGENT_WORKFLOW.md): planning, approval, implementation, independent review, correction, escalation, and release sequence.
- [Agent Handoff Template](AGENT_HANDOFF_TEMPLATE.md): scope, exact commit, evidence, findings, and review disposition for role transitions.

## Roles

The human Product Owner / CTO owns priorities, material risk acceptance, and final release authorization. The Architect proposes specifications and architecture. The Builder implements approved scope and supplies evidence. The Independent Reviewer verifies the exact commit against acceptance criteria and required checks. A designated Security QA reviewer participates when security triggers apply.

The contract includes illustrative tool assignments. Projects may substitute tools while preserving role independence; a builder cannot be the sole independent reviewer of its own work.

## Reuse and version pinning

Use the published `v1.0.0` tag or its exact commit rather than copying from a moving `main` branch. Retrieve all four documents from the same release, retain their provenance, and record both the governance contract version (`1.0.0`) and the upstream tag or commit in your project's adoption record. The contract version identifies policy obligations; the Git tag and commit identify the complete document bundle.

Future updates require an explicit adoption review. MAJOR contract versions change decision rights or mandatory gates; MINOR versions add compatible procedures; PATCH versions clarify existing obligations. Changes to roles, gates, or approval thresholds require owner approval and a contract version increment.

## Adoption process

1. Select a released version and copy the four documents into the adopting repository's documentation directory.
2. Customize every placeholder in `PROJECT_AGENT_CONFIG.md`: outcomes, boundaries, architecture constraints, risk, role assignments, tooling, checks, permissions, and approval gates.
3. Record the upstream tag or commit, deviations with rationale, approver and review date, and the required security reviewer when triggered. Resolve material conflicts with the Product Owner before adoption.
4. Obtain recorded owner approval, complete the adoption record, and update the project's configuration status. The upstream contract remains a proposed reusable policy until approved for that project.
5. Link the adopted documents from the project's contributor guidance and use the workflow and handoff template for engineering changes.
6. Retain traceability from issue and approved scope through PR, reviewed exact SHA, executed checks, acceptance, and release. New commits require fresh review.

Publishing this starter does not grant agents repository, merge, deployment, or release authority in an adopting project. Configure those permissions explicitly and follow the contract's release gate.

## Validation of this release

The starter documents were checked for required files, local Markdown link targets, consistent versions and role controls, secrets, personal data, local filesystem paths, and project-specific assumptions. Project placeholders are intentional and must be replaced during adoption. No software runtime or test suite is included.

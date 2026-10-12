# Agent Workflow

1. **Plan (Architect):** Draft a complete issue with context, contracts, exclusions, acceptance criteria, dependencies, test matrix, and risks.
2. **Approve (Owner):** Confirm material choices and record the spec gate. Do not implement unresolved blockers.
3. **Build (Builder):** Implement only approved scope. Provide PR, head SHA, changed files, tests executed, outputs, and known gaps.
4. **Review (Independent Reviewer):** Verify the exact PR SHA and assess each acceptance criterion, tests, regression risk, security triggers, and documentation. Return PASS / CHANGES REQUIRED / BLOCKED with evidence.
5. **Correct (Builder):** Fix review findings. Do not expand scope without approval. Request fresh review of new SHA.
6. **Escalate (Owner):** After two automated correction cycles, or immediately for material disagreement or security risk.
7. **Merge and release (Authorized roles):** Follow the project's approval gates; capture final evidence and issue closure.

**Stop conditions:** unclear approval, missing required tests, secrets exposure, unreviewed commit, material scope expansion, unresolved critical security issue.

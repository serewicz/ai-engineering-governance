# Independent Review Evidence

**Candidate:** proposed v1.1.0; no merge, release, or adoption authorization.

**Baseline:** `bb08e871568f953f36e061d7fd89e467598bdcac` (published v1.0.0).

**Initial reviewed SHA:** `982acafb3ee2ff97aaa051bdad81f752bf33695e`.

## Historical principal evaluation (superseded; not a current approval)
Reviewer: independent governance-review agent, separate from the drafting agent.

Disposition: **CHANGES REQUIRED**.

IMPORTANT: Universal human-only merge strengthens the baseline's project-policy-dependent acceptance gate. The contract reserves mandatory-gate/decision-right changes for MAJOR versions, so the compatibility claim for 1.1.0 needs Tim's resolution. Do not weaken human authority to remove the discrepancy. No other BLOCKER/IMPORTANT findings were identified.

Historical response at `d0acceb`: preserve requested human-only merge; explicitly mark the requested version provisional and the version decision unresolved in the contract, README and adoption proposal. The PR remains draft and blocked for merge/publication pending Tim's version decision. Disclosure is not resolution or approval. Final-head re-review evidence is recorded in the PR; this snapshot review does not approve later commits.

## Historical Security QA evaluation (superseded; not a current approval)
Reviewer: separately assigned independent Security QA agent, independent of both drafting and principal evaluation.

Disposition: **PASS** for the initial reviewed SHA; no BLOCKER/IMPORTANT findings.

Reviewed downgrade abuse, mixed scope, sensitive triggers, independent classification and exact-SHA review, least privilege, human authority, publication controls, classifier limitations and retained HarvestGuard safeguards.

FOLLOW_UP: Validate denial paths and live settings during separately authorized HarvestGuard implementation. Existing enforcement gaps remain unresolved; this is not certification of enforcement.

## Checks and limits
Both reviewers independently ran `python3 -m unittest discover -s tests -v` (2 methods, 77 scenarios plus malformed inputs) and `python3 scripts/validate_documents.py`; all passed at the reviewed SHA. Principal review also ran the baseline diff whitespace check. Both verified exact HEAD and clean working tree.

Tests exercise supplied facts; they do not authenticate identities, delegation, actual scope or absence of triggers. Document checks are local/structural, not proof of semantic equivalence. Reviewers did not independently audit live HarvestGuard settings, tokens, historical compliance or all remote links. Neither review grants Tim's approval or release/adoption authority. A fresh independent evaluation is required for the final changed SHA; retain its exact SHA and disposition in the PR evidence.

## Tim’s resolution and fresh review requirement
Tim directed retention of v1.1.0 by restoring v1.0.0 owner-controlled project merge authority. Universal human-only merge was removed from the reusable contract; HarvestGuard’s mandatory human-only rule remains. Other projects may explicitly approve bounded automated execution with independent review, exact-SHA validation, required checks, security evidence and escalation. This does not authorize governance merge, publication or adoption.

Neither `982acafb3ee2ff97aaa051bdad81f752bf33695e` nor `d0accebcbdd06680e37fdbb44b272e08c5b6fd42` approval/disposition is reused for the changed candidate. Fresh Principal and Security QA reviews of the complete new exact PR head, including comparison to v1.0.0 for any new universal decision-right/mandatory-gate change, must be recorded in the PR before the blocker is considered resolved.

# Credentials, CI and repository controls

Owner creates a new fine-grained publishing PAT restricted to this repository,
contents read/write and pull requests read/write, named owner and short expiration.
No administration/workflows rights are needed for allowed text-only implementation.
Store directly as ENGINEERING_AUTOMATION_TOKEN. Only deterministic publish write
steps receive it; Claude, CI and Codex never do. A PAT may possess merge capability;
fixed publisher logic and human-only policy, not the token alone, forbid merge.

Create a dedicated OpenAI review project and restricted credential compatible with
the pinned Codex Action. Store directly as ENGINEERING_OPENAI_API_KEY. Only Codex
receives it (Action input and necessary process environment). Read-only GitHub token
cannot GitHub-approve, publish or push. Provider usage/admin credentials belong only
in a future trusted meter service; never in either agent or publisher job.

Presence checks list secret names only; they cannot verify secret scope, expiry,
correctness or provider account. Owner verifies those directly and records sanitized
match/status. No tokens, credentials, balances, invoices or raw billing reports in
source, evidence, logs or artifacts. Rotate each credential independently, verify a
separately authorized synthetic run, then revoke predecessors. On compromise disable
execution, cancel runs, revoke PAT/OpenAI key and disable WIF rules; issued tokens
may remain valid until expiry. Recovery needs named human ownership and fresh evidence.

PAT-triggered pushes/PRs must actually start CI; GITHUB_TOKEN generally suppresses
recursive events. Required check must match exact candidate head, trusted CI path,
event and GitHub Actions provenance; missing/pending/skipped/failed/stale checks block
Codex review. PR CI merge-tree SHA and reviewed candidate SHA are distinct evidence.
Unittest discovery must have nonzero tests. Future project-specific contracts must
be retained and reviewed; the generic profile does not replace stronger A1 contracts.

Owner checks private repository plan support, effective main rules and bypass actors.
If API returns403, inspect Settings/Rules/Rulesets and Branches in browser. Record
unavailable/unknown protections and precise account action, never assumed enforcement.
Require PRs, successful named CI, fresh reviews/base, conversation resolution and
no force pushes/deletion/automation bypass where required by project policy.
Privileged owners may edit/remove rules. Exceptions need Owner evidence and cannot
waive mandatory pinned governance or stronger existing controls.
Auto-merge remains disabled. No generated workflow merges or closes issues.

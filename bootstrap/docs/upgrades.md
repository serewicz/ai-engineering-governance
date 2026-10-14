# Pins and safe upgrades

Bootstrap and governance versions are independent. v0.1.0 is an unreleased candidate;
no tag/release/publication is authorized. Pin an independently approved release and
exact commit when one exists, then verify release file/digest inventory and immutable
Action pins. Existing v1.1.0 candidate governance remains a candidate unless separately
published; project-specific candidate adoption needs explicit recorded Owner authority.

Generate new project values from scratch. Share issuer registration only where allowed;
never inherit source workspace/account/rule, PAT/OpenAI key, task issue approvals,
reviewer designations or specification digests. No silent policy downgrade to fit a
profile. Changes to mandatory authority follow upstream semantic-version rules.

For existing projects: snapshot clean reviewed control baseline without touching dirty
work; audit retained contracts and permissions; run comparison-only upgrade; review
all changed files in a governed PR; actual CI and fresh Principal/triggered task-specific
Security QA must bind final head and material base; Owner authorizes exact merge.
Changing control SHA invalidates prior execution authorization. Keep execution false
through migration; verify trust/credentials/tests for new identity before new activation.
A conflicting approval/protected path/budget/identity refuses automatic migration.

This version's upgrade CLI compares manifests and never installs. Future released
versions need explicit schema migration adapters; unknown versions fail. Rollback is
an Owner-authorized reviewed PR restoring a known baseline with execution disabled;
never force-push/reset production history or reuse stale activation approval. Reverify
provider rule/workflow compatibility and revoke changed credentials where appropriate.

The30minute hands-on claim requires two fresh-project trials with published artifacts,
separately timed manual steps, no YAML edits, full readiness evidence and clear excluded
wait/prerequisite time. Until then it is a target, not an achieved acceptance result.

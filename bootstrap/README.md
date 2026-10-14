# Reusable engineering bootstrap — 0.1.0 candidate

This is a disabled, versioned onboarding foundation, not a released or operational
framework. Tim approved implementation of the design. It grants no publication,
adoption, merge, provider provisioning, inference or activation authority.
The governance contract remains unchanged; candidate v1.1.0 must not be described
as a published release. Three corrections require a newly verified Owner-approved
project deviation. Human-only merge is this profile's stronger project rule.

Supported first profile: Python 3.14, stdlib unittest, macOS CI; agent jobs on Linux
are orchestration environments, not a claim that project software is qualified there.
Other runtimes need separately reviewed profiles, not custom workflow programming.

## Offline use

From the governance repository root:

```sh
python3 bootstrap/scripts/bootstrap.py validate --manifest project.json --offline
python3 bootstrap/scripts/bootstrap.py render --manifest project.json --dry-run --offline
python3 bootstrap/scripts/bootstrap.py report --manifest project.json --offline
python3 bootstrap/scripts/bootstrap.py render --manifest project.json --output new-staging
python3 bootstrap/scripts/bootstrap.py inspect --manifest project.json --read-only-remote
python3 bootstrap/scripts/bootstrap.py upgrade --manifest proposed.json --previous current.json --dry-run
```

`render` writes only a previously nonexistent staging directory. It never edits an
existing checkout, pushes, creates a PR or configures settings. The caller must
review the staged adoption in a clean project worktree. Existing projects require
manual comparison of all existing governance before adoption; generated files may
not overwrite stronger existing instructions. `upgrade` is comparison-only and
rejects identity, scope, trust, governance and budget drift. This initial version
supports no later release; cross-version migration requires a reviewed migration
adapter and tests. A successful offline exit is not READY TO EXECUTE.

The manifest schema is strict and contains desired values and approval references,
not provider observations. Load the schema to create a fresh project manifest;
no SAR or HarvestGuard sample credentials or approvals are supplied.
Template code has labeled source provenance; rendered controllers bind new project
values. No template source is an active workflow in this repository.
Acquire the approved exact commit independently. The release-manifest hashes detect
corruption, not malicious replacement of both code and metadata. Verify version,
commit, bundle and dependency hashes against independently reviewed provenance.

## Execution profile

Two initial conditional 40-turn segments; validated resume/fallback; full bounded
index/worktree/untracked regular-file recovery, including binary bytes; 100 files,
25 MiB data, 64 KiB metadata and 14-day retention. Ignored files and model session
history are outside Git recovery. Overflow, unsafe modes, credential patterns or
failed verification block continuation/publication; missing upload is missing evidence.
Three correction calls of at most 80 turns each, each followed by deterministic
publication, exact-head successful CI and independent Codex review. Early approval
stops; unresolved final blockers escalate. Binary publication remains prohibited.
Claude GitHub permissions read-only; publisher has its separate credential only in
fixed write steps; reviewer receives only its OpenAI credential and read-only GitHub
permissions. No auto-merge/closure exists.

Standard and smoke tasks are independently approved, digest-bound issues with disjoint
roots. The no-input integration-smoke workflow selects only the smoke issue. Product
activation must remain false for smoke; a separate smoke flag and Owner authorization
are required. Both still hit the unconditional live budget denial. The synthetic
smoke workflow is prepared but NOT RUN and cannot currently invoke agents or publish.

## Remaining operational prerequisites

Authenticated provider metering adapters, atomic durable reservations, verified next-
invocation bounds and OS/process/artifact isolation are NOT IMPLEMENTED. The inherited
pure cumulative ledger is tested but is not a distributed transaction service.
Live admission always blocks; no environment/manifest/evidence switch enables it.
Do not weaken it to meet the time target. Provider monthly settings cannot establish
an exact per-task dollar ceiling. Further separately governed implementation and
real positive/negative tests are required before enabling credentialed execution.

Read [authentication](docs/authentication.md), [credentials](docs/credentials.md),
[budgets and isolation](docs/budgets-and-isolation.md), [troubleshooting](docs/troubleshooting.md)
and [upgrades](docs/upgrades.md). Use the [Owner/Codex checklist](../BOOTSTRAP_CHECKLIST.md).

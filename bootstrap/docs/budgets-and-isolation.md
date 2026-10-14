# Budget enforcement and isolation

All budgets are new Owner inputs in integer cents; no SAR allocation is inherited.
Standard role limits and smoke/monthly allocations must agree. Account subscriptions,
taxes, storage/runner cost and data handling require explicit treatment.

Owner configures a dedicated Anthropic workspace spend limit (not Default), saves,
reopens and verifies effective amount/currency/reset/enforcement and alternate bindings.
For OpenAI project Limits/Spend, set the approved monthly amount and enable Enforce a
hard limit; save/reopen and independently verify. Alerts alone are insufficient;
provider propagation may permit slight overshoot. Monthly caps are not task bounds.
GitHub Actions budgets must be checked for actual stop-usage behavior and exclusions.
Record settings matched/not matched/date only, never actual billing data or credentials.

The tested pure ledger carries all initial segments, cycles0–3, both agents, failures,
retries and pending reservations under one stable task identity. Unknown/stale/nonfinal
usage, replay, overrun or month rollover blocks admission. New dispatch/approval must
not erase prior task consumption. Agent-reported cost is not authoritative.

Operational backend is NOT IMPLEMENTED: authenticated provider adapters, concurrent
atomic durable reservations, task/account/period/call binding, rounding, late-charge
reconciliation and verified next-call bounds need a separately reviewed implementation.
Turns are not money bounds; max output alone does not bound agent input/tool calls.
The live gate always fails closed in0.1.0. Synthetic accounting PASS is not cost
integration evidence. Reports never claim an exact monetary cap with unknown usage.

Runner trust: read-only tokens alone do not isolate arbitrary generated/test code.
Before live execution, use enforceable OS/process/filesystem boundaries between
candidate code, trusted controls, credentials, session state and verified artifacts.
Privileged publisher must execute no candidate code and receive only validated
immutable artifacts. Review runs candidate code never; CI remains uncredentialed.
Secure handoff must prevent verification/upload races, symlink substitution and
preseeded artifact paths. Hashes are integrity, not authorization or sandboxing.
Recovery needs fresh trusted checkout and no restored-code execution. Timeout,
runner loss or upload failure can prevent capture; missing evidence stays BLOCKED.
No activation permitted until independently validated real isolation and budgeting.

[OpenAI limits](https://developers.openai.com/api/docs/guides/spend-limits)
[Anthropic workspace limits](https://platform.claude.com/docs/en/manage-claude/workspaces)

# Troubleshooting from reference failures

| Observed failure | Diagnosis and safe correction |
|---|---|
| SAR name-only OIDC subject expectation | Compare genuine signed immutable owner/repository IDs; correct reviewed exact rule, never wildcard trust. |
| SAR positive exchange expected exactly3600seconds | Validate granted TTL against documented assertion-dependent ceiling; config is not grant duration. |
| Missing Claude Action session output | Accept validated terminal-result fallback; missing both stops before resume. |
| Staged-only changes omitted | Union staged, unstaged and untracked paths; verify restored index/worktree separately. |
| Encoded staged secret or compressed checkpoint bypass | Scan raw decoded blobs and bound sizes before reading/archiving; uncompressed verified regular-file images. |
| Unsafe recovery symlink/file modes | Reject unsupported index/archive modes before any restore mutation. |
| PR/push did not start CI | Verify dedicated scoped non-GITHUB_TOKEN publishing credential and actual run provenance. |
| Private-main protection API403 | Owner verifies plan capability and effective rules; unavailable protection is not enabled. |
| Unknown budget usage/backend | Remain blocked; do not treat synthetic ledger or an alert as live enforcement. |
| SAR auth PR conflicted after parity merge | Preserve stronger controls, revise policy coherently and obtain fresh exact-head CI/reviews. |
| Rule lacks workflow/event claims | Local assertions are not provider restriction; narrow reviewed provider trust and test real negative contexts. |
| Signed-out administration Console | Owner signs in directly; never ask for passwords or tokens in chat. |

Stop on mismatched identity, scope, signature, token response or security assumptions.
Use fixed nonsecret failure categories and provider/GitHub audit references. No shell
tracing, raw exceptions, environment dumps, transcript or token uploads. Reference
fixes are genuine code-review discoveries; live provider integration is NOT RUN.

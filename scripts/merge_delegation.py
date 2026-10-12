"""Example prerequisite evaluator, not a merge executor or authorization gate.

Inputs must be independently verified. This cannot authenticate an Owner,
reviewer, policy, check, security verdict, or atomic operation. It grants no
permission and makes no external changes. Tier does not grant merge authority.
"""
import re


def automated_merge_prerequisites(facts):
    if not isinstance(facts, dict):
        return False
    for key in (
        "owner_approved_policy", "documented_policy", "delegation_current",
        "executor_authorized", "within_scope", "independent_review_approved",
        "required_checks_successful", "conversations_resolved",
        "atomic_head_guard", "base_validated", "evidence_recorded",
    ):
        if facts.get(key) is not True:
            return False
    if facts.get("human_only_project") is not False:
        return False
    if facts.get("unresolved_findings") != [] or not isinstance(facts.get("unresolved_findings"), list):
        return False
    reviewed, current = facts.get("reviewed_sha"), facts.get("current_sha")
    if not isinstance(reviewed, str) or not re.fullmatch(r"[0-9a-f]{40}", reviewed) or reviewed != current:
        return False
    required = facts.get("security_required")
    if required is True:
        if facts.get("security_independent_approved") is not True or facts.get("security_sha") != current:
            return False
    elif required is False:
        if facts.get("security_disposition") != "NOT REQUIRED" or not isinstance(facts.get("security_rationale"), str) or not facts["security_rationale"].strip():
            return False
    else:
        return False
    return True

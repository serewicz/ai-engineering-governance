"""Reference classification decision aid, not an authorization/security gate.

Facts must be independently verified against the actual diff. This helper
cannot establish identity, scope, delegation, or the absence of a trigger.
"""

TIER_0_KINDS = frozenset({"typo", "punctuation", "prose_whitespace", "prose_formatting", "nontechnical_prose"})
TIER_1_KINDS = TIER_0_KINDS | frozenset({"nonsecurity_bug", "presentation", "simple_test", "bounded_docs"})


def classify(facts):
    """Return an eligible tier; missing/unknown/ill-typed facts retain Tier 2.

    This result never authorizes implementation, self-approval, or merge.
    scope_expanded means unapproved expansion; reapproval requires new facts.
    """
    if not isinstance(facts, dict):
        return 2
    requested = facts.get("requested_tier")
    if type(requested) is not int or requested not in (0, 1):
        return 2
    for key in ("positive_evidence", "independent_authorized_classifier", "scope_clear", "mandatory_controls_preserved", "approved_spec"):
        if facts.get(key) is not True:
            return 2
    if facts.get("scope_expanded") is not False:
        return 2
    # Any trigger (including unknown trigger labels) prevents a downgrade.
    triggers = facts.get("triggers")
    kinds = facts.get("change_kinds")
    if not isinstance(triggers, list) or triggers:
        return 2
    if not isinstance(kinds, list) or not kinds or not all(isinstance(k, str) for k in kinds):
        return 2
    allowed = TIER_0_KINDS if requested == 0 else TIER_1_KINDS
    return requested if set(kinds) <= allowed else 2

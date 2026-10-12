"""Policy examples over supplied facts; no GitHub merge or permission change."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from merge_delegation import automated_merge_prerequisites


class MergeDelegationScenarios(unittest.TestCase):
    def setUp(self):
        self.facts = dict(
            owner_approved_policy=True, documented_policy=True,
            delegation_current=True, executor_authorized=True, within_scope=True,
            independent_review_approved=True, required_checks_successful=True,
            conversations_resolved=True, atomic_head_guard=True, base_validated=True,
            evidence_recorded=True, human_only_project=False, unresolved_findings=[],
            reviewed_sha="a" * 40, current_sha="a" * 40,
            security_required=False, security_disposition="NOT REQUIRED",
            security_rationale="Independent trigger assessment found no applicable trigger.",
        )

    def test_positive_delegated_nonsecurity_merge(self):
        self.assertTrue(automated_merge_prerequisites(self.facts))

    def test_positive_delegated_security_merge_requires_same_sha(self):
        self.facts.update(security_required=True, security_independent_approved=True, security_sha="a" * 40)
        self.assertTrue(automated_merge_prerequisites(self.facts))
        self.facts["security_sha"] = "b" * 40
        self.assertFalse(automated_merge_prerequisites(self.facts))

    def test_missing_or_false_mandatory_prerequisites(self):
        for key in self.facts:
            missing = self.facts.copy()
            del missing[key]
            with self.subTest(missing=key):
                self.assertFalse(automated_merge_prerequisites(missing))
        for key, value in self.facts.items():
            if value is True:
                for invalid in (False, "true", 1):
                    with self.subTest(key=key, invalid=invalid):
                        self.assertFalse(automated_merge_prerequisites(self.facts | {key: invalid}))

    def test_denial_paths(self):
        cases = (
            {"human_only_project": True},  # HarvestGuard, every tier
            {"current_sha": "b" * 40}, {"reviewed_sha": ""},
            {"unresolved_findings": ["BLOCKER"]},
            {"unresolved_findings": ["IMPORTANT"]},
            {"unresolved_findings": None},
            {"security_required": True}, {"security_required": "false"},
            {"security_rationale": ""}, {"security_rationale": None},
            {"security_disposition": "PASS"},
        )
        for case in cases:
            with self.subTest(case=case):
                self.assertFalse(automated_merge_prerequisites(self.facts | case))

    def test_tier_never_grants_delegation_or_overrides_harvestguard(self):
        for tier in (0, 1, 2):
            with self.subTest(tier=tier):
                self.assertFalse(automated_merge_prerequisites(self.facts | {"tier": tier, "owner_approved_policy": False}))
                self.assertFalse(automated_merge_prerequisites(self.facts | {"tier": tier, "human_only_project": True}))

    def test_malformed_facts(self):
        for facts in (None, [], {}, "approved"):
            self.assertFalse(automated_merge_prerequisites(facts))


if __name__ == "__main__":
    unittest.main()

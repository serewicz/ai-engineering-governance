import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from classify_task import classify


class ClassificationScenarios(unittest.TestCase):
    def test_scenarios(self):
        cases = json.loads((ROOT / "tests/classification_cases.json").read_text())
        for case in cases:
            with self.subTest(name=case["name"]):
                self.assertEqual(classify(case["facts"]), case["expected_tier"])

    def test_malformed_inputs_remain_standard(self):
        for facts in (None, [], "Tier 0", {}, {"requested_tier": True}):
            with self.subTest(facts=facts):
                self.assertEqual(classify(facts), 2)


if __name__ == "__main__":
    unittest.main()

"""Check released evidence, ranking metrics, and failure handling."""
import csv
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from metrics import bootstrap_cases, jaccard, kendall
from analyze import parse_discard, validate


class Metrics(unittest.TestCase):
    def test_empty_results_are_not_agreement(self):
        with self.assertRaises(ValueError):
            jaccard([], [])

    def test_set_overlap(self):
        self.assertEqual(jaccard([1, 2], [2, 3]), 1/3)
        self.assertEqual(jaccard([1], []), 0)

    def test_tau_direction_and_candidate_validation(self):
        self.assertEqual(kendall([1, 2, 3], [1, 2, 3]), 1)
        self.assertEqual(kendall([1, 2, 3], [3, 2, 1]), -1)
        with self.assertRaises(ValueError):
            kendall([1, 2], [1, 3])
        with self.assertRaises(ValueError):
            kendall([1, 1], [1, 1])

    def test_bootstrap_unit_is_case(self):
        result = bootstrap_cases([0, 1], repeats=1000)
        self.assertEqual((result["cases"], result["ci_low"], result["ci_high"]), (2, 0, 1))

    def test_discard_requires_valid_status_and_candidate(self):
        row = {"presented_order": "a;b;c", "discard_candidate_id": "b",
               "discard_position": "2", "parse_status": "discard_only", "n": "3"}
        self.assertTrue(parse_discard(row, "discard_candidate_id"))
        self.assertFalse(parse_discard({**row, "parse_status": "error"}, "discard_candidate_id"))
        self.assertFalse(parse_discard({**row, "discard_candidate_id": "x"}, "discard_candidate_id"))
        with self.assertRaises(AssertionError):
            parse_discard({**row, "discard_position": "1"}, "discard_candidate_id")


class ReleasedEvidence(unittest.TestCase):
    def test_manifest_matches_release_and_row_counts(self):
        manifest = validate()
        expected = {"jury.csv", "selection.csv", "same_order.csv", "permutations.csv", "sessions.csv", "resolution.csv"}
        self.assertEqual({Path(f["export"]).name for f in manifest["files"]}, expected)
        self.assertEqual({p.name for p in (ROOT / "data").glob("*.csv")}, expected)
        self.assertEqual(set(manifest), {"snapshot_date", "files", "sources"})
        for entry in manifest["files"]:
            with (ROOT / entry["export"]).open(newline="") as f:
                self.assertEqual(sum(1 for _ in csv.DictReader(f)), entry["rows"])
        self.assertEqual(sum(f["rows"] for f in manifest["files"]), 16565)

    def test_analysis_scope_and_independent_cases(self):
        summary = json.loads((ROOT / "results/summary.json").read_text())
        self.assertEqual(set(summary), {"jury", "creative"})
        self.assertEqual(summary["jury"]["family_interaction"]["cases"], 45)
        counts = {r["judge"]: r["valid_calls"] for r in summary["creative"]["resolution"]}
        self.assertEqual(sorted(counts.values()), [46, 50, 50])


if __name__ == "__main__":
    unittest.main()

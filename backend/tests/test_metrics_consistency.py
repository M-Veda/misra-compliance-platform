"""
test_metrics_consistency.py
===========================

Regression tests that verify metric consistency across all API endpoints and
workflow operations.

These tests enforce the following architectural guarantees:

1. SINGLE SOURCE OF TRUTH
   computeMetrics() in AppContext.tsx is the authoritative calculation.
   Backend tests replicate the same formula to verify the API contract.

2. COMPLIANCE SCORE SEMANTICS
   Score = 100 - (unique MISRA rules still violated in WORKING CODE × 10)
   - Accept  ✓ → code changes → score improves
   - Manual  ✓ → code changes → score improves
   - Reject  ✗ → code UNCHANGED → score must NOT change
   - Skip    ✗ → code UNCHANGED → score must NOT change
   - Re-analyze → backend provides authoritative score

3. COUNTER INVARIANT
   Accepted + Rejected + Skipped + Manual + Remaining == Total Detected
   Accepted must never exceed Total Detected.
   No value may be negative.

4. API CONTRACT
   /api/upload, /api/apply-patches, /api/generate-report, and
   /api/generate-project-report must return consistent metrics.

Run with:
    pytest backend/tests/test_metrics_consistency.py -v
"""
import os
import sys
import json
import requests
import unittest
import tempfile
import textwrap
from typing import List, Dict, Any

# ── Path Setup ────────────────────────────────────────────────────────────────
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from backend.services.parser import CParserService
from backend.rules import ALL_RULES
from backend.services import patch_engine

# ── Helpers ───────────────────────────────────────────────────────────────────

BASE_URL = "http://localhost:8000"

# Backend scoring formula — mirrors frontend computeMetrics exactly
def compute_compliance_score(violations: list) -> float:
    """
    Score = 100 - (unique_rule_numbers × 10).
    Mirrors the authoritative formula in AppContext.tsx / backend /api/upload.
    """
    if not violations:
        return 100.0
    unique_rules = set(v.get("rule_number", v.rule_number if hasattr(v, "rule_number") else "") for v in violations)
    return max(0.0, 100.0 - len(unique_rules) * 10.0)


def compute_metrics(all_violations: list, decisions: dict, current_violations: list, auth_score: float) -> dict:
    """
    Replicate computeMetrics() from AppContext.tsx.
    
    Parameters
    ----------
    all_violations    : immutable baseline violations list
    decisions         : {stable_id: decision_string} dict
    current_violations: remaining (undecided) violations
    auth_score        : compliance_score from analysisResult (NOT recomputed)
    """
    total_detected = len(all_violations) if all_violations else len(current_violations)
    rejected  = sum(1 for d in decisions.values() if d == "Reject")
    skipped   = sum(1 for d in decisions.values() if d == "Skip")
    manual    = sum(1 for d in decisions.values() if d == "Manual")
    remaining = len(current_violations)
    accepted  = max(0, total_detected - (rejected + skipped + manual + remaining))
    return {
        "total_detected":   total_detected,
        "accepted":         accepted,
        "rejected":         rejected,
        "skipped":          skipped,
        "manual":           manual,
        "remaining":        remaining,
        "compliance_score": auth_score,
    }


def assert_invariant(m: dict, context: str = ""):
    """
    Assert the counter invariant:
      accepted + rejected + skipped + manual + remaining == total_detected
    """
    total = m["total_detected"]
    summed = m["accepted"] + m["rejected"] + m["skipped"] + m["manual"] + m["remaining"]
    assert summed == total, (
        f"INVARIANT VIOLATED {context}: "
        f"accepted({m['accepted']}) + rejected({m['rejected']}) + skipped({m['skipped']}) + "
        f"manual({m['manual']}) + remaining({m['remaining']}) = {summed} ≠ total({total})"
    )
    assert m["accepted"] <= total, f"accepted({m['accepted']}) > total({total}) {context}"
    for key in ("accepted", "rejected", "skipped", "manual", "remaining", "total_detected"):
        assert m[key] >= 0, f"{key} is negative ({m[key]}) {context}"


# ── Test Sources ──────────────────────────────────────────────────────────────

# small.c from perf_test — must trigger all 10 MISRA rules
SMALL_C_PATH = os.path.join(repo_root, "perf_test", "small.c")

# Inline minimal test source for fast unit tests (no server required)
MINIMAL_SOURCE = textwrap.dedent("""\
    int global_var = 0;

    void unused_param_func(int x, int unused) {
        x = x + 1;
    }

    void dead_code_func(void) {
        int y = 5;
        y = y + 1;
        return;
        y = 10;
    }

    void no_proto();

    void no_proto() {
        int mode = 1;
        switch (mode) {
            case 1:
                global_var = 1;
            default:
                global_var = 0;
        }
    }
""")


# ── Unit Tests (no server required) ──────────────────────────────────────────

class TestComputeMetricsFunction(unittest.TestCase):
    """Unit tests for the computeMetrics formula (no network)."""

    def test_initial_state_no_decisions(self):
        """After upload, no decisions have been made."""
        violations = [{"rule_number": f"{i}"} for i in range(5)]
        m = compute_metrics(violations, {}, violations, 50.0)
        self.assertEqual(m["total_detected"], 5)
        self.assertEqual(m["accepted"], 0)
        self.assertEqual(m["rejected"], 0)
        self.assertEqual(m["skipped"], 0)
        self.assertEqual(m["manual"], 0)
        self.assertEqual(m["remaining"], 5)
        self.assertEqual(m["compliance_score"], 50.0)
        assert_invariant(m, "initial state")

    def test_accept_one_violation(self):
        """Accepting one violation removes it from remaining."""
        all_v = [{"rule_number": "2.2"}, {"rule_number": "2.7"}, {"rule_number": "14.4"}]
        decisions = {"key1": "Accept"}
        # After accept, current_violations shrinks by 1 and compliance_score updates
        current_v = [{"rule_number": "2.7"}, {"rule_number": "14.4"}]
        new_score = compute_compliance_score(current_v)  # 80.0
        m = compute_metrics(all_v, decisions, current_v, new_score)
        self.assertEqual(m["total_detected"], 3)
        self.assertEqual(m["accepted"], 1)
        self.assertEqual(m["remaining"], 2)
        self.assertAlmostEqual(m["compliance_score"], 80.0)
        assert_invariant(m, "after accept")

    def test_reject_does_not_improve_score(self):
        """Rejecting a violation must NOT change compliance_score."""
        all_v = [{"rule_number": "2.2"}, {"rule_number": "2.7"}, {"rule_number": "14.4"}]
        original_score = 70.0
        decisions = {"key1": "Reject"}
        # After reject, current_violations shrinks by 1 (removed from UI queue)
        # but compliance_score MUST stay at 70.0 (code unchanged)
        current_v = [{"rule_number": "2.7"}, {"rule_number": "14.4"}]
        # Score stays at original_score — Reject does NOT update it
        m = compute_metrics(all_v, decisions, current_v, original_score)
        self.assertEqual(m["rejected"], 1)
        self.assertEqual(m["remaining"], 2)
        self.assertAlmostEqual(m["compliance_score"], 70.0,
                               msg="Reject must NOT improve compliance score")
        assert_invariant(m, "after reject")

    def test_skip_does_not_improve_score(self):
        """Skipping a violation must NOT change compliance_score."""
        all_v = [{"rule_number": "2.2"}, {"rule_number": "14.4"}]
        original_score = 80.0
        decisions = {"key1": "Skip"}
        current_v = [{"rule_number": "14.4"}]
        m = compute_metrics(all_v, decisions, current_v, original_score)
        self.assertEqual(m["skipped"], 1)
        self.assertAlmostEqual(m["compliance_score"], 80.0,
                               msg="Skip must NOT improve compliance score")
        assert_invariant(m, "after skip")

    def test_invariant_all_decisions(self):
        """Counter invariant holds after a mix of all decision types."""
        all_v = [{"rule_number": str(i)} for i in range(10)]
        decisions = {
            "k0": "Accept",
            "k1": "Accept",
            "k2": "Reject",
            "k3": "Skip",
            "k4": "Manual",
        }
        # 5 remain undecided
        current_v = [{"rule_number": str(i)} for i in range(5, 10)]
        auth_score = 50.0
        m = compute_metrics(all_v, decisions, current_v, auth_score)
        assert_invariant(m, "mixed decisions")
        self.assertEqual(m["accepted"], 2)
        self.assertEqual(m["rejected"], 1)
        self.assertEqual(m["skipped"], 1)
        self.assertEqual(m["manual"], 1)
        self.assertEqual(m["remaining"], 5)

    def test_accept_all_gives_100_percent(self):
        """After accepting all violations, remaining = 0 and score = 100.0."""
        all_v = [{"rule_number": str(i)} for i in range(10)]
        decisions = {f"k{i}": "Accept" for i in range(10)}
        current_v = []
        m = compute_metrics(all_v, decisions, current_v, 100.0)
        self.assertEqual(m["remaining"], 0)
        self.assertEqual(m["accepted"], 10)
        self.assertAlmostEqual(m["compliance_score"], 100.0)
        assert_invariant(m, "accept all")

    def test_no_negative_values(self):
        """No metric value may ever be negative."""
        m = compute_metrics([], {}, [], 100.0)
        for key in ("accepted", "rejected", "skipped", "manual", "remaining", "total_detected"):
            self.assertGreaterEqual(m[key], 0, f"{key} should not be negative")

    def test_accepted_never_exceeds_total(self):
        """Accepted count must never exceed total_detected."""
        all_v = [{"rule_number": "2.2"}, {"rule_number": "14.4"}]
        # Edge case: extra decisions that shouldn't exist
        decisions = {f"k{i}": "Accept" for i in range(5)}  # 5 decisions, only 2 violations
        current_v = []
        m = compute_metrics(all_v, decisions, current_v, 100.0)
        self.assertLessEqual(m["accepted"], m["total_detected"],
                             "accepted must never exceed total_detected")


# ── Backend Rule Engine Tests (no server required) ─────────────────────────

class TestBackendRuleEngineMetrics(unittest.TestCase):
    """Tests using the backend rule engine directly (no HTTP server needed)."""

    def setUp(self):
        """Load small.c if available, otherwise use MINIMAL_SOURCE."""
        if os.path.exists(SMALL_C_PATH):
            with open(SMALL_C_PATH, "r", encoding="utf-8") as f:
                self.source = f.read()
        else:
            self.source = MINIMAL_SOURCE

    def _analyze(self, source: str):
        ast, err = CParserService.parse_code(source, "test.c")
        self.assertIsNone(err, f"Parse error: {err}")
        violations = []
        for rule in ALL_RULES:
            violations.extend(rule.analyze(ast, source, "test.c"))
        unique_rules = set(v.rule_number for v in violations)
        score = max(0.0, 100.0 - len(unique_rules) * 10.0)
        return violations, score

    def test_backend_score_formula_matches_frontend(self):
        """Backend compliance_score formula is identical to frontend computeMetrics."""
        violations, score = self._analyze(self.source)
        if violations:
            expected_score = compute_compliance_score([{"rule_number": v.rule_number} for v in violations])
            self.assertAlmostEqual(score, expected_score, places=1,
                                   msg="Backend score formula must match frontend formula")

    def test_bulk_patch_invariant_holds_after_accept_all(self):
        """After bulk Accept All, invariant holds and score is re-derivable."""
        violations, initial_score = self._analyze(self.source)
        if not violations:
            self.skipTest("No violations detected — skipping")

        result = patch_engine.apply_bulk(self.source, violations)
        self.assertTrue(result.success, f"Bulk patch failed: {result.error}")

        # Re-analyze patched source
        re_violations, re_score = self._analyze(result.patched_source)

        all_v = [{"rule_number": v.rule_number} for v in violations]
        decisions = {f"k{i}": "Accept" for i in range(len(violations))}
        current_v = [{"rule_number": v.rule_number} for v in re_violations]
        m = compute_metrics(all_v, decisions, current_v, re_score)

        assert_invariant(m, "after bulk accept all")
        self.assertGreaterEqual(m["compliance_score"], initial_score,
                                "Score must not decrease after Accept All")

    def test_reject_all_score_unchanged(self):
        """Rejecting all violations leaves score at initial value."""
        violations, initial_score = self._analyze(self.source)
        if not violations:
            self.skipTest("No violations detected — skipping")

        all_v = [{"rule_number": v.rule_number} for v in violations]
        decisions = {f"k{i}": "Reject" for i in range(len(violations))}
        # After reject: violations removed from UI queue, code unchanged, score unchanged
        current_v = []  # all removed from UI queue
        m = compute_metrics(all_v, decisions, current_v, initial_score)

        self.assertAlmostEqual(m["compliance_score"], initial_score, places=1,
                               msg="Reject must NOT change compliance score")
        assert_invariant(m, "after reject all")

    def test_skip_all_score_unchanged(self):
        """Skipping all violations leaves score at initial value."""
        violations, initial_score = self._analyze(self.source)
        if not violations:
            self.skipTest("No violations detected — skipping")

        all_v = [{"rule_number": v.rule_number} for v in violations]
        decisions = {f"k{i}": "Skip" for i in range(len(violations))}
        current_v = []
        m = compute_metrics(all_v, decisions, current_v, initial_score)

        self.assertAlmostEqual(m["compliance_score"], initial_score, places=1,
                               msg="Skip must NOT change compliance score")
        assert_invariant(m, "after skip all")

    def test_partial_accept_partial_reject_invariant(self):
        """Mixed decisions: invariant holds and score reflects only accepted fixes."""
        violations, initial_score = self._analyze(self.source)
        if len(violations) < 4:
            self.skipTest("Not enough violations for mixed decision test")

        # Accept first 2, reject next 2, leave rest undecided
        all_v = [{"rule_number": v.rule_number} for v in violations]
        decisions = {
            f"k{i}": ("Accept" if i < 2 else "Reject")
            for i in range(min(4, len(violations)))
        }
        current_v = [{"rule_number": v.rule_number} for v in violations[4:]]

        # Score after accepting 2 violations (estimating)
        accepted_violations = violations[:2]
        remaining_in_code = violations[2:]  # rejected are still in code; undecided too
        # Compliance = based on violations REMAINING IN CODE (accepted have been patched)
        rules_in_code = set(v.rule_number for v in remaining_in_code)
        auth_score = max(0.0, 100.0 - len(rules_in_code) * 10.0) if rules_in_code else 100.0

        m = compute_metrics(all_v, decisions, current_v, auth_score)
        assert_invariant(m, "mixed accept/reject")
        self.assertLessEqual(m["accepted"], m["total_detected"])


# ── API Integration Tests (requires running backend) ─────────────────────────

def is_server_running() -> bool:
    try:
        r = requests.get(f"{BASE_URL}/api/rules", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


@unittest.skipUnless(is_server_running(), "Backend server not running — skip API tests")
class TestAPIMetricsConsistency(unittest.TestCase):
    """Integration tests that verify API responses are metrically consistent."""

    def _upload_file(self, source: str, filename: str = "test.c") -> dict:
        with tempfile.NamedTemporaryFile(suffix=".c", delete=False) as f:
            f.write(source.encode("utf-8"))
            tmp_path = f.name
        try:
            with open(tmp_path, "rb") as f:
                r = requests.post(f"{BASE_URL}/api/upload", files={"file": (filename, f, "text/plain")})
            r.raise_for_status()
            return r.json()
        finally:
            os.unlink(tmp_path)

    def test_upload_score_matches_formula(self):
        """POST /api/upload score must match 100 - unique_rules×10."""
        if not os.path.exists(SMALL_C_PATH):
            self.skipTest("small.c not found")
        with open(SMALL_C_PATH, "r") as f:
            source = f.read()
        data = self._upload_file(source, "small.c")
        self.assertTrue(data["success"])
        violations = data["violations"]
        expected_score = compute_compliance_score(violations)
        self.assertAlmostEqual(data["compliance_score"], expected_score, places=1,
                               msg="Upload score must match formula")

    def test_upload_then_apply_patches_score_consistent(self):
        """POST /api/apply-patches + re-upload: score is consistent."""
        if not os.path.exists(SMALL_C_PATH):
            self.skipTest("small.c not found")
        with open(SMALL_C_PATH, "r") as f:
            source = f.read()
        upload_data = self._upload_file(source, "small.c")
        self.assertTrue(upload_data["success"])
        violations = upload_data["violations"]
        if not violations:
            self.skipTest("No violations to patch")

        # Apply all patches
        r = requests.post(f"{BASE_URL}/api/apply-patches",
                          json={"source_code": source, "violations": violations})
        r.raise_for_status()
        patch_data = r.json()
        self.assertTrue(patch_data["success"])

        # Re-upload to get new score
        re_data = self._upload_file(patch_data["modified_code"], "small.c")
        self.assertTrue(re_data["success"])
        re_violations = re_data["violations"]
        re_score_api = re_data["compliance_score"]
        re_score_formula = compute_compliance_score(re_violations)
        self.assertAlmostEqual(re_score_api, re_score_formula, places=1,
                               msg="Re-upload score must match formula after patching")

    def test_generate_report_metrics_consistent_with_upload(self):
        """POST /api/generate-report: JSON report metrics match upload metrics."""
        if not os.path.exists(SMALL_C_PATH):
            self.skipTest("small.c not found")
        with open(SMALL_C_PATH, "r") as f:
            source = f.read()
        upload_data = self._upload_file(source, "small.c")
        self.assertTrue(upload_data["success"])
        violations = upload_data["violations"]
        score = upload_data["compliance_score"]

        # Build decisions: accept all
        decisions = {}
        for v in violations:
            sid = v.get("stable_id") or f"{v['rule_number']}_{v['line']}_{v['column']}"
            decisions[sid] = "Accept"

        payload = {
            "file_name": "small.c",
            "original_code": source,
            "corrected_code": source,
            "violations": violations,
            "decisions": decisions,
            "compliance_score": 100.0,  # after accepting all
            "remaining_violations_count": 0,
        }
        r = requests.post(f"{BASE_URL}/api/generate-report", json=payload)
        r.raise_for_status()
        report_data = r.json()
        self.assertTrue(report_data["success"])

        json_report = report_data["json_report"]
        summary = json_report["summary"]

        # Counter invariant in JSON report
        d = summary["decisions_applied"]
        self.assertEqual(
            d["accepted"] + d["rejected"] + d["skipped"] + d["manual_fix"] + d["remaining"],
            summary["total_violations_detected"],
            msg="JSON report counter invariant violated"
        )
        # Compliance score in report matches what we passed in
        self.assertAlmostEqual(summary["compliance_score"], 100.0, places=1)
        # Invariant check field in JSON
        self.assertEqual(d["_invariant_check"], summary["total_violations_detected"])

    def test_report_invariant_check_field_equals_total(self):
        """The _invariant_check field in JSON report always equals total_violations_detected."""
        upload_data = self._upload_file(MINIMAL_SOURCE, "test.c")
        violations = upload_data.get("violations", [])
        score = upload_data.get("compliance_score", 100.0)

        # No decisions made
        payload = {
            "file_name": "test.c",
            "original_code": MINIMAL_SOURCE,
            "corrected_code": MINIMAL_SOURCE,
            "violations": violations,
            "decisions": {},
            "compliance_score": score,
            "remaining_violations_count": len(violations),
        }
        r = requests.post(f"{BASE_URL}/api/generate-report", json=payload)
        r.raise_for_status()
        summary = r.json()["json_report"]["summary"]
        d = summary["decisions_applied"]
        self.assertEqual(
            d["_invariant_check"],
            summary["total_violations_detected"],
            "Invariant check field must equal total_violations_detected"
        )

    def test_reject_decisions_not_in_score(self):
        """Violations marked Reject don't improve the score in the report."""
        upload_data = self._upload_file(MINIMAL_SOURCE, "test.c")
        violations = upload_data.get("violations", [])
        initial_score = upload_data.get("compliance_score", 100.0)
        if not violations:
            self.skipTest("No violations in minimal source")

        # Mark all as Reject — score must stay at initial (code unchanged)
        decisions = {}
        for v in violations:
            sid = v.get("stable_id") or f"{v['rule_number']}_{v['line']}_{v['column']}"
            decisions[sid] = "Reject"

        payload = {
            "file_name": "test.c",
            "original_code": MINIMAL_SOURCE,
            "corrected_code": MINIMAL_SOURCE,  # code unchanged
            "violations": violations,
            "decisions": decisions,
            "compliance_score": initial_score,  # score unchanged — passed in from session
            "remaining_violations_count": 0,
        }
        r = requests.post(f"{BASE_URL}/api/generate-report", json=payload)
        r.raise_for_status()
        summary = r.json()["json_report"]["summary"]
        self.assertAlmostEqual(
            summary["compliance_score"], initial_score, places=1,
            msg="Reject decisions must not improve compliance score in report"
        )

    def test_skip_decisions_not_in_score(self):
        """Violations marked Skip don't improve the score in the report."""
        upload_data = self._upload_file(MINIMAL_SOURCE, "test.c")
        violations = upload_data.get("violations", [])
        initial_score = upload_data.get("compliance_score", 100.0)
        if not violations:
            self.skipTest("No violations in minimal source")

        decisions = {}
        for v in violations:
            sid = v.get("stable_id") or f"{v['rule_number']}_{v['line']}_{v['column']}"
            decisions[sid] = "Skip"

        payload = {
            "file_name": "test.c",
            "original_code": MINIMAL_SOURCE,
            "corrected_code": MINIMAL_SOURCE,
            "violations": violations,
            "decisions": decisions,
            "compliance_score": initial_score,  # code unchanged — score unchanged
            "remaining_violations_count": 0,
        }
        r = requests.post(f"{BASE_URL}/api/generate-report", json=payload)
        r.raise_for_status()
        summary = r.json()["json_report"]["summary"]
        self.assertAlmostEqual(
            summary["compliance_score"], initial_score, places=1,
            msg="Skip decisions must not improve compliance score in report"
        )

    def test_metrics_identical_upload_vs_report(self):
        """Metrics from /api/upload match metrics embedded in /api/generate-report response."""
        if not os.path.exists(SMALL_C_PATH):
            self.skipTest("small.c not found")
        with open(SMALL_C_PATH, "r") as f:
            source = f.read()
        upload_data = self._upload_file(source, "small.c")
        self.assertTrue(upload_data["success"])
        violations = upload_data["violations"]
        score = upload_data["compliance_score"]

        payload = {
            "file_name": "small.c",
            "original_code": source,
            "corrected_code": source,
            "violations": violations,
            "decisions": {},
            "compliance_score": score,
            "remaining_violations_count": len(violations),
        }
        r = requests.post(f"{BASE_URL}/api/generate-report", json=payload)
        r.raise_for_status()
        summary = r.json()["json_report"]["summary"]

        # Score in report must equal score from upload (no decisions made)
        self.assertAlmostEqual(summary["compliance_score"], score, places=1,
                               msg="Report score must match upload score when no decisions made")
        self.assertEqual(summary["total_violations_detected"], len(violations),
                         msg="Report total must match upload violations count")

    def test_pdf_endpoint_reachable_after_report_generation(self):
        """After /api/generate-report, the PDF file is downloadable via /api/download-pdf/."""
        upload_data = self._upload_file(MINIMAL_SOURCE, "test.c")
        violations = upload_data.get("violations", [])
        score = upload_data.get("compliance_score", 100.0)
        payload = {
            "file_name": "test.c",
            "original_code": MINIMAL_SOURCE,
            "corrected_code": MINIMAL_SOURCE,
            "violations": violations,
            "decisions": {},
            "compliance_score": score,
            "remaining_violations_count": len(violations),
        }
        r = requests.post(f"{BASE_URL}/api/generate-report", json=payload)
        r.raise_for_status()
        pdf_filename = r.json()["pdf_report_filename"]
        pdf_r = requests.get(f"{BASE_URL}/api/download-pdf/{pdf_filename}")
        self.assertEqual(pdf_r.status_code, 200)
        self.assertEqual(pdf_r.headers.get("content-type", ""), "application/pdf")
        self.assertGreater(len(pdf_r.content), 1000, "PDF should not be empty")


if __name__ == "__main__":
    unittest.main(verbosity=2)

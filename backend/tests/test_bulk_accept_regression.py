"""
Regression test to ensure BulkPatch-All fully resolves supported violations.
"""
import unittest
import os
import sys

# Ensure repository root is on sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.append(repo_root)

from backend.services.parser import CParserService
from backend.rules import ALL_RULES
from backend.services import patch_engine

class TestBulkAcceptAllResolution(unittest.TestCase):
    def test_bulk_accept_eliminates_all_supported(self):
        source = """
int global_counter = 0;

void process_data(int param_a, int unused_param) {
    param_a = param_a + 1;
    if (global_counter) {
        global_counter = global_counter + 1;
    }
}
"""
        # Parse and detect violations
        ast, err = CParserService.parse_code(source, "sample.c")
        self.assertIsNone(err)
        violations = []
        for r in ALL_RULES:
            violations.extend(r.analyze(ast, source, "sample.c"))
        # Apply bulk patch
        result = patch_engine.apply_bulk(source, violations)
        self.assertTrue(result.success, f"Bulk patch failed: {result.error}")
        self.assertTrue(result.parse_valid, "Patched source failed parse validation")
        patched = result.patched_source
        # Re-analyze patched source
        ast_re, err_re = CParserService.parse_code(patched, "sample.c")
        self.assertIsNone(err_re)
        re_violations = []
        for r in ALL_RULES:
            re_violations.extend(r.analyze(ast_re, patched, "sample.c"))
        # All auto‑patchable violations should be eliminated
        self.assertEqual(len(re_violations), 0, f"Remaining violations after bulk accept: {re_violations}")

if __name__ == "__main__":
    unittest.main()

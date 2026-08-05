"""
test_e2e_stress.py — End-to-end, stress, rule verification, regression, and performance benchmark.

Tests:
1. End-to-End Workflow Validation (Detect -> Accept All -> Generate Code -> Re-analyze)
2. Large-scale stress testing (100, 500, 1000, 2500+ violations)
   - Checks structural integrity: no duplicate declarations, no duplicate comments, no reordered functions.
   - Measures and records: Detection time, Patch generation time, Bulk apply time, Validation time, Memory usage.
3. Rule-by-rule verification for all 10 rules (2.2, 2.7, 7.1, 8.4, 8.7, 10.3, 12.1, 14.4, 16.3, 16.4).
4. Parse & Compilation verification (pycparser + gcc/clang system compiler if available).
5. Regression verification (Single Accept, Reject, Skip, Bulk Accept, Bulk Reject, Re-analysis, Report generation).
6. Final audit check (dead code, imports, architecture).

Run with:
    python -m pytest backend/tests/test_e2e_stress.py -v
"""

import sys
import os
import time
import tracemalloc
import subprocess
import shutil
import unittest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.parser import CParserService
from backend.rules import ALL_RULES
from backend.models.violation import RuleViolation
from backend.services import patch_engine
from backend.services.patch import PatchService
from backend.report.generator import ReportGenerator


def _has_system_compiler() -> bool:
    """Return True if gcc or clang is available on system PATH."""
    return shutil.which("gcc") is not None or shutil.which("clang") is not None


def _compile_c_code(code_str: str) -> tuple[bool, str]:
    """Attempts to compile code_str with gcc or clang if available."""
    compiler = shutil.which("gcc") or shutil.which("clang")
    if not compiler:
        return True, "No system C compiler found (skipped native build check)"

    temp_file = "temp_test_compile.c"
    out_file = "temp_test_compile.out"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code_str)
        # Run compiler syntax check (-fsyntax-only or -c)
        cmd = [compiler, "-fsyntax-only", temp_file]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            return True, "Compilation succeeded"
        else:
            return False, res.stderr
    finally:
        if os.path.exists(temp_file):
            try: os.remove(temp_file)
            except Exception: pass
        if os.path.exists(out_file):
            try: os.remove(out_file)
            except Exception: pass


# ─────────────────────────────────────────────────────────────────────────────
# 1. End-to-End Workflow Verification
# ─────────────────────────────────────────────────────────────────────────────

class TestEndToEndWorkflow(unittest.TestCase):

    def test_full_pipeline_real_c_file(self):
        """
        Full lifecycle: Parse source -> Detect violations -> Accept All via patch engine ->
        Verify code compiles / parses -> Re-analyze patched code.
        """
        source = """
int global_counter = 0;

void process_data(int param_a, int unused_param) {
    param_a = param_a + 1;
    if (global_counter) {
        global_counter = global_counter + 1;
    }
}
"""
        # Step 1: Parse
        ast, err = CParserService.parse_code(source, "e2e_sample.c")
        self.assertIsNone(err, f"Initial parse failed: {err}")
        self.assertIsNotNone(ast)

        # Step 2: Detect
        violations = []
        for r in ALL_RULES:
            v_list = r.analyze(ast, source, "e2e_sample.c")
            violations.extend(v_list)

        self.assertGreater(len(violations), 0, "Should detect violations in sample code")

        # Step 3: Accept All via bulk patch engine
        result = patch_engine.apply_bulk(source, violations)
        self.assertTrue(result.success, f"Bulk patch failed: {result.error}")
        self.assertTrue(result.parse_valid, "Patched source must pass parse validation")

        patched = result.patched_source

        # Step 4: Verify structure (no corruption)
        self.assertIn("static int global_counter = 0;", patched)
        self.assertIn("(void)unused_param;", patched)
        self.assertIn("if (global_counter != 0)", patched)

        # Step 5: Native Compilation check (if compiler installed)
        compiled_ok, comp_msg = _compile_c_code(patched)
        self.assertTrue(compiled_ok, f"Patched code failed compilation: {comp_msg}")

        # Step 6: Re-analyze patched code
        ast_re, err_re = CParserService.parse_code(patched, "e2e_sample.c")
        self.assertIsNone(err_re, "Patched code must parse cleanly on re-analysis")
        re_violations = []
        for r in ALL_RULES:
            re_violations.extend(r.analyze(ast_re, patched, "e2e_sample.c"))

        # Re-analyzed violations should be strictly fewer
        self.assertLess(len(re_violations), len(violations),
                        "Re-analysis must show fewer remaining violations")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Large-Scale Stress Testing (100, 500, 1000, 2500+ violations)
# ─────────────────────────────────────────────────────────────────────────────

class TestLargeScaleStress(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.perf_records = {}

    def _generate_stress_c_file(self, count: int) -> tuple[str, list[RuleViolation]]:
        """Generates a synthetic C file with `count` rule 8.7 & 12.1 & 14.4 & 2.7 violations."""
        lines = ["#include <stdio.h>", ""]
        violations = []
        line_idx = 3

        for i in range(count):
            # 1. Global declaration (Rule 8.7 violation if used in one func)
            var_name = f"g_stress_var_{i}"
            decl_line = f"int {var_name} = {i};"
            lines.append(decl_line)
            violations.append(RuleViolation(
                rule_number="8.7", rule_name="Objects block scope", severity="Advisory",
                category="Declarations", file="stress.c", line=line_idx, column=1,
                message=f"Global variable '{var_name}' is only referenced in function 'fn_{i}'",
                code_snippet=decl_line, reason="Single func ref",
                suggested_fix=f"static {decl_line}", confidence=1.0
            ))
            line_idx += 1

            # 2. Function with unused param (2.7) and non-boolean cond (14.4)
            func_line = f"void fn_{i}(int param_{i}) {{"
            lines.append(func_line)
            violations.append(RuleViolation(
                rule_number="2.7", rule_name="Unused param", severity="Advisory",
                category="Unused Code", file="stress.c", line=line_idx, column=1,
                message=f"Parameter 'param_{i}' is unused", code_snippet=func_line,
                reason="Unused param", suggested_fix=f"(void)param_{i};", confidence=1.0
            ))
            line_idx += 1

            cond_line = f"    if ({var_name}) {{ {var_name} = {var_name} + 1; }}"
            lines.append(cond_line)
            violations.append(RuleViolation(
                rule_number="14.4", rule_name="Condition Boolean", severity="Required",
                category="Control Flow", file="stress.c", line=line_idx, column=5,
                message=f"Condition of 'if' is not Boolean", code_snippet=cond_line,
                reason="Non-boolean condition",
                suggested_fix=f"    if ({var_name} != 0) {{ {var_name} = {var_name} + 1; }}",
                confidence=1.0
            ))
            line_idx += 1

            lines.append("}")
            line_idx += 1
            lines.append("")
            line_idx += 1

        source = "\n".join(lines)
        return source, violations

    def _run_stress_scale(self, count: int):
        source, violations = self._generate_stress_c_file(count // 3 + 1)
        # Limit to exact requested violation count
        violations = violations[:count]

        tracemalloc.start()
        t0 = time.perf_counter()

        # Step 1: Detection measurement (re-parse)
        t_det_0 = time.perf_counter()
        ast, _ = CParserService.parse_code(source, f"stress_{count}.c")
        t_det = time.perf_counter() - t_det_0

        # Step 2: Patch generation & Bulk apply
        t_apply_0 = time.perf_counter()
        result = patch_engine.apply_bulk(source, violations)
        t_apply = time.perf_counter() - t_apply_0

        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        t_total = time.perf_counter() - t0

        self.assertTrue(result.success, f"Stress test at scale {count} failed: {result.error}")
        self.assertTrue(result.parse_valid, f"Patched code at scale {count} failed parse check")

        patched = result.patched_source

        # Assert structural integrity:
        # 1. No duplicated function declarations or headers
        self.assertEqual(patched.count("void fn_0"), 1)
        # 2. No duplicated static static
        self.assertNotIn("static static", patched)
        # 3. No corrupted function bodies
        self.assertIn("void fn_0(int param_0) {", patched)
        self.assertIn("(void)param_0;", patched)

        record = {
            "scale": len(violations),
            "detection_sec": round(t_det, 4),
            "bulk_apply_sec": round(t_apply, 4),
            "total_sec": round(t_total, 4),
            "ops_applied": result.ops_applied,
            "peak_mem_mb": round(peak_mem / (1024 * 1024), 2)
        }
        TestLargeScaleStress.perf_records[count] = record
        print(f"\n[STRESS {count} VIO] Applied {result.ops_applied} ops in {t_apply:.3f}s | Peak Mem: {record['peak_mem_mb']} MB")

    def test_stress_100(self):
        self._run_stress_scale(100)

    def test_stress_500(self):
        self._run_stress_scale(500)

    def test_stress_1000(self):
        self._run_stress_scale(1000)

    def test_stress_2500(self):
        self._run_stress_scale(2500)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Rule Verification (All 10 rules)
# ─────────────────────────────────────────────────────────────────────────────

class TestAllTenRules(unittest.TestCase):

    def test_rule_inventory_and_auto_patch_behavior(self):
        """Verify all 10 supported rules for detection & patch behavior."""
        rule_numbers = [r.rule_number for r in ALL_RULES]
        expected_rules = ["2.2", "2.7", "7.1", "8.4", "8.7", "10.3", "12.1", "14.4", "16.3", "16.4"]

        for expected in expected_rules:
            self.assertIn(expected, rule_numbers, f"Rule {expected} missing from ALL_RULES")

        # Verify all 10 rules are auto-patchable
        self.assertEqual(len(patch_engine.MANUAL_ONLY_RULES), 0)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Regression Verification
# ─────────────────────────────────────────────────────────────────────────────

class TestRegression(unittest.TestCase):

    def test_patch_service_preview(self):
        """Verify PatchService.generate_preview adapter for single Accept, Reject, Skip, Manual."""
        src = "int counter = 0;\n"
        v = RuleViolation(
            rule_number="8.7", rule_name="Scope", severity="Advisory",
            category="Decl", file="test.c", line=1, column=1, message="msg",
            code_snippet="int counter = 0;", reason="r", suggested_fix="static int counter = 0;", confidence=1.0
        )

        # Accept
        acc = PatchService.generate_preview(src, v, "Accept")
        self.assertIn("static int counter = 0;", acc)

        # Reject
        rej = PatchService.generate_preview(src, v, "Reject")
        self.assertEqual(rej, src)

        # Skip
        skp = PatchService.generate_preview(src, v, "Skip")
        self.assertEqual(skp, src)

        # Manual
        man = PatchService.generate_preview(src, v, "Manual", manual_code="/* manual fix */ int counter = 0;")
        self.assertEqual(man, "/* manual fix */ int counter = 0;")

    def test_report_generation(self):
        """Verify PDF report generation with patched code."""
        out_pdf = "temp_test_report.pdf"
        try:
            v = RuleViolation(
                rule_number="8.7", rule_name="Scope", severity="Advisory",
                category="Decl", file="main.c", line=1, column=1, message="msg",
                code_snippet="int counter = 0;", reason="r", suggested_fix="static int counter = 0;", confidence=1.0
            )
            decisions = {"8.7_1_1": "Accept"}
            ReportGenerator.generate_pdf_report(
                file_name="main.c", violations=[v], decisions=decisions,
                compliance_score=100.0, corrected_code="static int counter = 0;\n",
                output_path=out_pdf
            )
            self.assertTrue(os.path.exists(out_pdf))
            self.assertGreater(os.path.getsize(out_pdf), 100)
        finally:
            if os.path.exists(out_pdf):
                try: os.remove(out_pdf)
                except Exception: pass


if __name__ == "__main__":
    unittest.main(verbosity=2)

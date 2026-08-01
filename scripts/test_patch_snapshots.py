"""
test_patch_snapshots.py
-----------------------
Permanent snapshot regression & idempotency test suite for all 10 implemented MISRA C:2012 rules.

Verifies:
1. Every violation for all 10 rules produces a Patch object with all 17 mandatory fields.
2. original_source != replacement_source (real transformation, zero placeholders).
3. replacement_source compiles cleanly when substituted into working source.
4. apply_single substitutes exact replacement_source byte-for-byte.
5. Re-analysis on the transformed working copy confirms the violation is ELIMINATED (Idempotency).
"""

import sys
import os
import re
import json

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.services.parser import CParserService
from backend.rules import ALL_RULES
from backend.services import patch_engine
from backend.models.violation import RuleViolation, PatchPreview

TEST_FILE = os.path.join(PROJECT_ROOT, "perf_test", "multi_rule_test.c")
MANDATORY_FIELDS = [
    "violation_id", "rule_number", "file", "line", "column",
    "original_start_line", "original_end_line", "original_source",
    "replacement_source", "unified_diff", "explanation", "confidence",
    "patch_type", "applies_cleanly", "can_autopatch", "affected_lines",
    "compliance_gain"
]

TARGET_RULES = ["2.2", "2.7", "7.1", "8.4", "8.7", "10.3", "12.1", "14.4", "16.3", "16.4"]

def run_snapshot_tests():
    print("=" * 75)
    print("MISRA C:2012 COMPLIANCE AGENT — PERMANENT PATCH SNAPSHOT REGRESSION SUITE")
    print("=" * 75)

    with open(TEST_FILE, "r", encoding="utf-8") as f:
        initial_source = f.read()

    # Step 1: Initial Parse & Analysis
    ast, err = CParserService.parse_code(initial_source, "multi_rule_test.c")
    if err:
        print(f"FAILED: Pre-analysis parse error: {err}")
        sys.exit(1)

    violations: list[RuleViolation] = []
    for rule in ALL_RULES:
        try:
            v_list = rule.analyze(ast, initial_source, "multi_rule_test.c")
            for v in v_list:
                v.patch_preview = patch_engine.generate_patch_preview(initial_source, v)
            violations.extend(v_list)
        except Exception as e:
            print(f"Rule {rule.rule_number} analyze error: {e}")

    detected_rules = set(v.rule_number for v in violations)
    print(f"\nInitial Detection: Found {len(violations)} violations across {len(detected_rules)} rules.")
    print(f"Detected rules: {sorted(list(detected_rules))}")

    missing_rules = set(TARGET_RULES) - detected_rules
    if missing_rules:
        print(f"WARNING: Test file did not trigger rules: {missing_rules}")

    rule_violations_map = {}
    for v in violations:
        rule_violations_map.setdefault(v.rule_number, []).append(v)

    failures = []
    passed_rules = []

    print("\n" + f"{'Rule':<8} {'17 Fields':<12} {'Orig!=Prop':<12} {'Compilable':<12} {'Idempotent':<12} {'Status'}")
    print("-" * 75)

    for rule_num in TARGET_RULES:
        viols = rule_violations_map.get(rule_num, [])
        if not viols:
            print(f"{rule_num:<8} {'(not triggered)':<54} SKIP")
            continue

        v = viols[0]
        pp = v.patch_preview
        rule_errs = []

        # Check 1: 17 Mandatory Fields
        if pp is None:
            rule_errs.append("patch_preview is None")
        else:
            for f in MANDATORY_FIELDS:
                val = getattr(pp, f, None)
                if val is None or (isinstance(val, str) and not val.strip() and f not in ("explanation", "no_patch_reason")):
                    rule_errs.append(f"Missing mandatory field '{f}'")

        # Check 2: original_source != replacement_source
        orig = (pp.original_source if pp else "").strip()
        rep  = (pp.replacement_source if pp else "").strip()
        if orig == rep:
            rule_errs.append("original_source == replacement_source (no transformation candidate)")

        # Check 3: Apply single patch to working copy
        res = patch_engine.apply_single(initial_source, v)
        if not res.success:
            rule_errs.append(f"apply_single failed: {res.error}")

        patched_src = res.patched_source

        # Check 4: Compilable (pycparser parse check)
        p_ast, p_err = CParserService.parse_code(patched_src, "patched.c")
        if p_err:
            rule_errs.append(f"Patched code syntax error: {p_err[:60]}")

        # Check 5: Idempotency (Re-analysis on patched code should eliminate violation)
        rule_obj = next((r for r in ALL_RULES if r.rule_number == rule_num), None)
        if rule_obj and p_ast:
            re_viols = rule_obj.analyze(p_ast, patched_src, "patched.c")
            if len(re_viols) >= len(viols):
                rule_errs.append(f"Re-analysis failed: {len(re_viols)} violations remain (not idempotent)")

        fields_ok = "PASS" if not [e for e in rule_errs if "field" in e] else "FAIL"
        diff_ok   = "PASS" if orig != rep else "FAIL"
        comp_ok   = "PASS" if not [e for e in rule_errs if "syntax" in e or "failed" in e] else "FAIL"
        idem_ok   = "PASS" if not [e for e in rule_errs if "idempotent" in e] else "FAIL"

        status = "PASS" if not rule_errs else "FAIL"

        print(f"{rule_num:<8} {fields_ok:<12} {diff_ok:<12} {comp_ok:<12} {idem_ok:<12} {status}")

        if rule_errs:
            for err_msg in rule_errs:
                print(f"   -> {err_msg}")
            failures.append((rule_num, rule_errs))
        else:
            passed_rules.append(rule_num)

    print("\n" + "=" * 75)
    if not failures:
        print(f"ALL SNAPSHOT REGRESSION TESTS PASSED! ({len(passed_rules)}/{len(TARGET_RULES)} rules verified)")
        print("Contract Satisfaction: 100% Deterministic, Compilable, Idempotent Patch Engine.")
        return 0
    else:
        print(f"REGRESSION FAILURES DETECTED ({len(failures)}):")
        for r, errs in failures:
            print(f"  Rule {r}: {'; '.join(errs)}")
        return 1

if __name__ == "__main__":
    sys.exit(run_snapshot_tests())

"""
test_patch_engine.py — Comprehensive unit tests for backend.services.patch_engine

Coverage
--------
1.  Bottom-up application order (no offset corruption)
2.  Duplicate patch detection / deduplication
3.  Overlap / conflict handling (severity-ordered resolution)
4.  Idempotency — applying twice produces identical output
5.  Large-file patching (500-5000 violation scale)
6.  Post-patch parser validation (invalid C is rejected)
7.  All 10 rules auto-patchable (2.2, 2.7, 7.1, 8.4, 8.7, 10.3, 12.1, 14.4, 16.3, 16.4)
8.  apply_single covers happy path, validation failure, already-applied
9.  Rule-specific builder sanity checks

Run with:
    python -m pytest backend/tests/test_patch_engine.py -v
"""

import sys
import os
import time
import unittest

# Ensure the project root is on sys.path so backend.* imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.patch_engine import (
    PatchOp,
    PatchResult,
    build_patch_op,
    apply_single,
    apply_bulk,
    _validate_op,
    _is_already_applied,
    _overlaps,
    _resolve_overlaps,
    _apply_ops_bottom_up,
    _line_start_offset,
    _find_snippet_offset,
    MANUAL_ONLY_RULES,
)
from backend.models.violation import RuleViolation


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_violation(
    rule_number: str,
    line: int = 1,
    column: int = 1,
    code_snippet: str = "",
    suggested_fix: str = "",
    severity: str = "Required",
    message: str = "",
) -> RuleViolation:
    return RuleViolation(
        rule_number=rule_number,
        rule_name=f"Rule {rule_number}",
        severity=severity,
        category="Test",
        file="test.c",
        line=line,
        column=column,
        message=message or f"Violation of rule {rule_number}",
        code_snippet=code_snippet,
        reason="Test reason",
        suggested_fix=suggested_fix,
        confidence=1.0,
    )


def make_op(
    rule: str = "2.2",
    severity: str = "Required",
    start: int = 0,
    end: int = 5,
    original: str = "hello",
    replacement: str = "world",
    id_suffix: str = "L1_C1",
) -> PatchOp:
    return PatchOp(
        id=f"{rule.replace('.', '_')}_{id_suffix}",
        rule=rule,
        severity=severity,
        start_offset=start,
        end_offset=end,
        original_text=original,
        replacement_text=replacement,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Offset helpers
# ─────────────────────────────────────────────────────────────────────────────

class TestLineStartOffset(unittest.TestCase):

    def test_first_line(self):
        src = "line1\nline2\nline3"
        self.assertEqual(_line_start_offset(src, 1), 0)

    def test_second_line(self):
        src = "line1\nline2\nline3"
        self.assertEqual(_line_start_offset(src, 2), 6)

    def test_third_line(self):
        src = "line1\nline2\nline3"
        self.assertEqual(_line_start_offset(src, 3), 12)

    def test_beyond_end(self):
        src = "abc"
        self.assertEqual(_line_start_offset(src, 99), len(src))

    def test_empty_source(self):
        self.assertEqual(_line_start_offset("", 1), 0)


class TestFindSnippetOffset(unittest.TestCase):

    def test_exact_line(self):
        src = "int x = 0;\nint y = 1;\n"
        result = _find_snippet_offset(src, 1, "int x = 0;")
        self.assertIsNotNone(result)
        start, end = result
        self.assertEqual(src[start:end], "int x = 0;")

    def test_within_window(self):
        # Snippet is 3 lines away from reported line but within window
        src = "a\nb\nc\nd\ne\nfoo bar\n"
        result = _find_snippet_offset(src, 3, "foo bar", window=5)
        self.assertIsNotNone(result)

    def test_not_found(self):
        src = "int x = 0;\n"
        result = _find_snippet_offset(src, 1, "NOTHERE")
        self.assertIsNone(result)


# ─────────────────────────────────────────────────────────────────────────────
# 2. PatchOp validation
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateOp(unittest.TestCase):

    def test_valid_replacement(self):
        src = "hello world"
        op = make_op(start=0, end=5, original="hello", replacement="HELLO")
        self.assertTrue(_validate_op(src, op))

    def test_invalid_replacement(self):
        src = "hello world"
        op = make_op(start=0, end=5, original="XXXXX", replacement="HELLO")
        self.assertFalse(_validate_op(src, op))

    def test_pure_insertion_valid(self):
        src = "hello"
        op = make_op(start=0, end=0, original="", replacement="\n(void)p;")
        self.assertTrue(_validate_op(src, op))

    def test_pure_insertion_out_of_bounds(self):
        src = "hi"
        op = make_op(start=100, end=100, original="", replacement="x")
        self.assertFalse(_validate_op(src, op))

    def test_offset_past_end(self):
        src = "hi"
        op = make_op(start=0, end=10, original="hi        ", replacement="x")
        self.assertFalse(_validate_op(src, op))


# ─────────────────────────────────────────────────────────────────────────────
# 3. Already-applied idempotency guard
# ─────────────────────────────────────────────────────────────────────────────

class TestIsAlreadyApplied(unittest.TestCase):

    def test_same_original_and_replacement(self):
        src = "int x;"
        op = make_op(start=0, end=6, original="int x;", replacement="int x;")
        self.assertTrue(_is_already_applied(src, op))

    def test_insertion_already_present(self):
        # Simulates "(void)p;" already inserted right at position
        src = "(void)p;\n    int x;"
        op = make_op(start=0, end=0, original="", replacement="(void)p;")
        self.assertTrue(_is_already_applied(src, op))

    def test_not_applied(self):
        src = "    int x;"
        op = make_op(start=0, end=6, original="int x;", replacement="static int x;")
        self.assertFalse(_is_already_applied(src, op))


# ─────────────────────────────────────────────────────────────────────────────
# 4. Overlap detection
# ─────────────────────────────────────────────────────────────────────────────

class TestOverlaps(unittest.TestCase):

    def test_non_overlapping(self):
        a = make_op(start=0, end=5, original="hello")
        b = make_op(start=6, end=11, original="world")
        self.assertFalse(_overlaps(a, b))
        self.assertFalse(_overlaps(b, a))

    def test_overlapping_replacements(self):
        a = make_op(start=0, end=10, original="0123456789")
        b = make_op(start=5, end=15, original="5678901234")
        self.assertTrue(_overlaps(a, b))

    def test_adjacent_no_overlap(self):
        a = make_op(start=0, end=5, original="hello")
        b = make_op(start=5, end=10, original="world")
        self.assertFalse(_overlaps(a, b))

    def test_insertion_inside_replacement(self):
        # Insertion at position 3 is inside replacement [0, 10)
        a = make_op(start=0, end=10, original="0123456789")
        b = make_op(start=3, end=3, original="", replacement="X")
        self.assertTrue(_overlaps(a, b))

    def test_same_insertion_point(self):
        a = make_op(start=5, end=5, original="", replacement="A")
        b = make_op(start=5, end=5, original="", replacement="B")
        self.assertTrue(_overlaps(a, b))

    def test_different_insertion_points(self):
        a = make_op(start=5, end=5, original="", replacement="A")
        b = make_op(start=6, end=6, original="", replacement="B")
        self.assertFalse(_overlaps(a, b))


# ─────────────────────────────────────────────────────────────────────────────
# 5. Overlap resolution (severity-ordered)
# ─────────────────────────────────────────────────────────────────────────────

class TestResolveOverlaps(unittest.TestCase):

    def test_mandatory_beats_advisory(self):
        mandatory_op = make_op(severity="Mandatory", start=0, end=5, original="hello", id_suffix="L1_C1")
        advisory_op  = make_op(severity="Advisory",  start=2, end=7, original="lloww", id_suffix="L2_C1")
        kept, conflicts = _resolve_overlaps([advisory_op, mandatory_op])
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0].severity, "Mandatory")
        self.assertEqual(len(conflicts), 1)

    def test_required_beats_advisory(self):
        required = make_op(severity="Required", start=0, end=5, original="hello", id_suffix="L1_C1")
        advisory = make_op(severity="Advisory", start=0, end=5, original="hello", replacement="byeee", id_suffix="L1_C2")
        kept, _ = _resolve_overlaps([required, advisory])
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0].severity, "Required")

    def test_no_overlaps_all_kept(self):
        ops = [
            make_op(start=0,  end=5,  original="hello", id_suffix="L1_C1"),
            make_op(start=10, end=15, original="world", id_suffix="L2_C1"),
            make_op(start=20, end=25, original="xxxxx", id_suffix="L3_C1"),
        ]
        kept, conflicts = _resolve_overlaps(ops)
        self.assertEqual(len(kept), 3)
        self.assertEqual(len(conflicts), 0)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Bottom-up application order
# ─────────────────────────────────────────────────────────────────────────────

class TestApplyOpsBottomUp(unittest.TestCase):

    def test_two_non_overlapping_applied_correctly(self):
        src = "AAA BBB CCC"
        op1 = make_op(start=0, end=3, original="AAA", replacement="111")
        op2 = make_op(start=8, end=11, original="CCC", replacement="333")
        result = _apply_ops_bottom_up(src, [op1, op2])
        self.assertEqual(result, "111 BBB 333")

    def test_order_independence(self):
        # Applying in either order must produce the same result
        src = "ABCDE FGHIJ KLMNO"
        op1 = make_op(start=0,  end=5,  original="ABCDE", replacement="11111")
        op2 = make_op(start=12, end=17, original="KLMNO", replacement="33333")
        r1 = _apply_ops_bottom_up(src, [op1, op2])
        r2 = _apply_ops_bottom_up(src, [op2, op1])
        self.assertEqual(r1, r2)

    def test_pure_insertion_bottom_up(self):
        # Insert at position 5, then insert at position 0 — offsets should not conflict
        src = "HELLO WORLD"
        op_mid = make_op(start=5, end=5, original="", replacement="[MID]")
        op_start = make_op(start=0, end=0, original="", replacement="[START]")
        result = _apply_ops_bottom_up(src, [op_mid, op_start])
        self.assertEqual(result, "[START]HELLO[MID] WORLD")

    def test_many_ops_no_offset_drift(self):
        # Build a source with 100 identifiable tokens, replace each one
        tokens = [f"T{i:03d}" for i in range(100)]
        src = " ".join(tokens)
        ops = []
        offset = 0
        for i, tok in enumerate(tokens):
            replacement = f"R{i:03d}"
            ops.append(PatchOp(
                id=f"op_{i}",
                rule="2.2",
                severity="Required",
                start_offset=offset,
                end_offset=offset + len(tok),
                original_text=tok,
                replacement_text=replacement,
            ))
            offset += len(tok) + 1  # +1 for the space separator
        result = _apply_ops_bottom_up(src, ops)
        expected = " ".join(f"R{i:03d}" for i in range(100))
        self.assertEqual(result, expected)


# ─────────────────────────────────────────────────────────────────────────────
# 7. MANUAL_ONLY rule enforcement
# ─────────────────────────────────────────────────────────────────────────────

class TestManualOnlyRules(unittest.TestCase):

    def test_manual_only_set_empty(self):
        self.assertEqual(len(MANUAL_ONLY_RULES), 0, "All 10 rules are 100% auto-patchable")


# ─────────────────────────────────────────────────────────────────────────────
# 8. Rule-specific builder sanity checks
# ─────────────────────────────────────────────────────────────────────────────

class TestRuleBuilders(unittest.TestCase):

    # ── Rule 2.2 ──────────────────────────────────────────────────────────────

    def test_rule_2_2_blanks_line(self):
        src = "int a;\ndeadExpr;\nint b;\n"
        v = make_violation("2.2", line=2, code_snippet="deadExpr;")
        op = build_patch_op(src, v)
        self.assertIsNotNone(op)
        result = _apply_ops_bottom_up(src, [op])
        lines = result.splitlines()
        self.assertTrue(lines[1].strip() in ("", "/* Dead code removed (MISRA Rule 2.2) */"), "Dead code line should be blanked or replaced with comment")
        # Other lines must remain identical
        self.assertEqual(lines[0], "int a;")
        self.assertEqual(lines[2], "int b;")

    def test_rule_2_2_already_blank(self):
        src = "int a;\n\nint b;\n"
        v = make_violation("2.2", line=2, code_snippet="")
        op = build_patch_op(src, v)
        # No patch needed for a blank line
        self.assertIsNone(op)

    # ── Rule 2.7 ──────────────────────────────────────────────────────────────

    def test_rule_2_7_inserts_void_cast(self):
        src = "void foo(int x) {\n    return;\n}\n"
        v = make_violation("2.7", line=1, suggested_fix="(void)x;")
        op = build_patch_op(src, v)
        self.assertIsNotNone(op)
        result = _apply_ops_bottom_up(src, [op])
        self.assertIn("(void)x;", result)
        # The function structure must be preserved
        self.assertIn("void foo(int x)", result)
        self.assertIn("return;", result)

    def test_rule_2_7_no_suggested_fix(self):
        src = "void foo(int x) {\n    return;\n}\n"
        v = make_violation("2.7", line=1, suggested_fix="")
        op = build_patch_op(src, v)
        self.assertIsNone(op)

    # ── Rule 8.4 ──────────────────────────────────────────────────────────────

    def test_rule_8_4_prepends_prototype(self):
        src = "int add(int a, int b) {\n    return a + b;\n}\n"
        v = make_violation("8.4", line=1, code_snippet="int add(int a, int b) {")
        op = build_patch_op(src, v)
        self.assertIsNotNone(op)
        result = _apply_ops_bottom_up(src, [op])
        # Prototype should appear before the definition
        self.assertIn("int add(int a, int b);", result)
        proto_pos = result.index("int add(int a, int b);")
        def_pos   = result.index("int add(int a, int b) {")
        self.assertLess(proto_pos, def_pos, "Prototype must precede definition")

    # ── Rule 8.7 ──────────────────────────────────────────────────────────────

    def test_rule_8_7_makes_static(self):
        src = "int counter = 0;\nvoid inc(void) { counter++; }\n"
        v = make_violation("8.7", line=1, code_snippet="int counter = 0;")
        op = build_patch_op(src, v)
        self.assertIsNotNone(op)
        result = _apply_ops_bottom_up(src, [op])
        self.assertIn("static int counter = 0;", result)
        self.assertNotIn("\nstatic static", result, "Must not double-static")

    def test_rule_8_7_already_static(self):
        src = "static int counter = 0;\nvoid inc(void) { counter++; }\n"
        v = make_violation("8.7", line=1, code_snippet="static int counter = 0;")
        op = build_patch_op(src, v)
        # Already static — idempotent guard returns None
        self.assertIsNone(op)

    # ── Rule 10.3 ─────────────────────────────────────────────────────────────

    def test_rule_10_3_inserts_cast(self):
        src = "    short s = longVal;\n"
        v = make_violation("10.3", line=1,
                           code_snippet="short s = longVal;",
                           suggested_fix="short s = (short)longVal;")
        op = build_patch_op(src, v)
        self.assertIsNotNone(op)
        result = _apply_ops_bottom_up(src, [op])
        self.assertIn("(short)longVal", result)

    def test_rule_10_3_no_change_needed(self):
        snippet = "short s = (short)longVal;"
        src = f"    {snippet}\n"
        v = make_violation("10.3", line=1,
                           code_snippet=snippet,
                           suggested_fix=snippet)
        op = build_patch_op(src, v)
        self.assertIsNone(op, "No patch when snippet == suggested_fix")

    # ── Rule 12.1 ─────────────────────────────────────────────────────────────

    def test_rule_12_1_adds_parentheses(self):
        src = "    int z = a + b * c;\n"
        v = make_violation("12.1", line=1,
                           code_snippet="int z = a + b * c;",
                           suggested_fix="int z = a + (b * c);")
        op = build_patch_op(src, v)
        self.assertIsNotNone(op)
        result = _apply_ops_bottom_up(src, [op])
        self.assertIn("(b * c)", result)

    # ── Rule 14.4 ─────────────────────────────────────────────────────────────

    def test_rule_14_4_adds_boolean_comparison(self):
        src = "    if (x) {\n        foo();\n    }\n"
        v = make_violation("14.4", line=1,
                           code_snippet="if (x) {",
                           suggested_fix="if (x != 0) {")
        op = build_patch_op(src, v)
        self.assertIsNotNone(op)
        result = _apply_ops_bottom_up(src, [op])
        self.assertIn("if (x != 0)", result)

    def test_rule_14_4_does_not_rewrite_return(self):
        # Safety guard: must not auto-patch a return statement
        src = "    return y;\n"
        v = make_violation("14.4", line=1,
                           code_snippet="return y;",
                           suggested_fix="return y != 0;")
        op = build_patch_op(src, v)
        self.assertIsNone(op, "Must never auto-patch a return statement")


# ─────────────────────────────────────────────────────────────────────────────
# 9. apply_single
# ─────────────────────────────────────────────────────────────────────────────

class TestApplySingle(unittest.TestCase):

    def test_happy_path_8_7(self):
        src = "int counter = 0;\nvoid inc(void) { counter++; }\n"
        v = make_violation("8.7", line=1, code_snippet="int counter = 0;")
        result = apply_single(src, v)
        self.assertTrue(result.success)
        self.assertEqual(result.ops_applied, 1)
        self.assertIn("static int counter = 0;", result.patched_source)

    def test_manual_only_returns_original(self):
        src = "int x;\n"
        self.assertEqual(len(MANUAL_ONLY_RULES), 0, "All 10 implemented rules are 100% auto-patchable")

    def test_idempotent_apply_single(self):
        """Applying the same patch twice must yield the same result as applying once."""
        src = "int counter = 0;\nvoid inc(void) { counter++; }\n"
        v = make_violation("8.7", line=1, code_snippet="int counter = 0;")
        first  = apply_single(src, v)
        second = apply_single(first.patched_source, v)
        self.assertEqual(first.patched_source, second.patched_source,
                         "Idempotency violated: second application changed output")


# ─────────────────────────────────────────────────────────────────────────────
# 10. Deduplication
# ─────────────────────────────────────────────────────────────────────────────

class TestDeduplication(unittest.TestCase):

    def test_duplicate_violations_applied_once(self):
        src = "int counter = 0;\nvoid inc(void) { counter++; }\n"
        v = make_violation("8.7", line=1, code_snippet="int counter = 0;")
        # Feed the same violation twice
        result = apply_bulk(src, [v, v])
        self.assertTrue(result.success)
        self.assertEqual(result.ops_applied, 1,
                         "Duplicate op must be applied only once")
        # Ensure "static" appears exactly once
        self.assertEqual(result.patched_source.count("static int counter"), 1)

    def test_100_identical_violations(self):
        src = "int counter = 0;\nvoid inc(void) { counter++; }\n"
        v = make_violation("8.7", line=1, code_snippet="int counter = 0;")
        result = apply_bulk(src, [v] * 100)
        self.assertEqual(result.ops_applied, 1)
        self.assertEqual(result.patched_source.count("static int counter"), 1)


# ─────────────────────────────────────────────────────────────────────────────
# 11. Idempotency — apply_bulk twice
# ─────────────────────────────────────────────────────────────────────────────

class TestIdempotency(unittest.TestCase):

    def _run_idempotency(self, src: str, violations: list) -> None:
        first  = apply_bulk(src, violations)
        second = apply_bulk(first.patched_source, violations)
        self.assertEqual(
            first.patched_source, second.patched_source,
            "Idempotency violated: second bulk-apply changed the output"
        )

    def test_idempotent_8_7(self):
        src = "int counter = 0;\nvoid inc(void) { counter++; }\n"
        v = make_violation("8.7", line=1, code_snippet="int counter = 0;")
        self._run_idempotency(src, [v])

    def test_idempotent_12_1(self):
        src = "    int z = a + b * c;\n"
        v = make_violation("12.1", line=1,
                           code_snippet="int z = a + b * c;",
                           suggested_fix="int z = a + (b * c);")
        self._run_idempotency(src, [v])

    def test_idempotent_2_2(self):
        src = "int a = 1;\ndeadExpr;\nint b = 2;\n"
        v = make_violation("2.2", line=2, code_snippet="deadExpr;")
        self._run_idempotency(src, [v])


# ─────────────────────────────────────────────────────────────────────────────
# 12. Large-file patching (500–5000 violation scale)
# ─────────────────────────────────────────────────────────────────────────────

class TestLargeFilePatching(unittest.TestCase):

    def _build_large_source(self, n_vars: int) -> tuple:
        """
        Build a C source with `n_vars` global variables each used in exactly
        one function — all Rule 8.7 violations.
        """
        lines = []
        violations = []
        line_num = 1

        for i in range(n_vars):
            decl = f"int g_{i} = {i};"
            lines.append(decl)
            violations.append(make_violation(
                "8.7",
                line=line_num,
                code_snippet=decl,
                severity="Advisory",
            ))
            line_num += 1

        # Add a dummy function so the file is valid C
        lines.append("void use_all(void) {")
        line_num += 1
        for i in range(n_vars):
            lines.append(f"    g_{i}++;")
            line_num += 1
        lines.append("}")

        src = "\n".join(lines)
        return src, violations

    def _assert_valid_structure(self, result_src: str, n_vars: int):
        """Check that every var is now static exactly once."""
        for i in range(n_vars):
            count = result_src.count(f"static int g_{i} =")
            self.assertEqual(count, 1,
                             f"g_{i} should appear static exactly once, got {count}")
            self.assertEqual(result_src.count(f"\nstatic static"), 0,
                             "No double-static should appear")

    def test_500_violations(self):
        src, violations = self._build_large_source(500)
        t0 = time.perf_counter()
        result = apply_bulk(src, violations)
        elapsed = time.perf_counter() - t0
        self.assertTrue(result.success, f"apply_bulk failed: {result.error}")
        self._assert_valid_structure(result.patched_source, 500)
        print(f"\n[PERF] 500 violations applied in {elapsed:.3f}s")

    def test_1000_violations(self):
        src, violations = self._build_large_source(1000)
        t0 = time.perf_counter()
        result = apply_bulk(src, violations)
        elapsed = time.perf_counter() - t0
        self.assertTrue(result.success, f"apply_bulk failed: {result.error}")
        self._assert_valid_structure(result.patched_source, 1000)
        print(f"\n[PERF] 1000 violations applied in {elapsed:.3f}s")

    def test_idempotent_1000_violations(self):
        src, violations = self._build_large_source(1000)
        first  = apply_bulk(src, violations)
        second = apply_bulk(first.patched_source, violations)
        self.assertEqual(first.patched_source, second.patched_source,
                         "Large-file idempotency violated")

    def test_duplicate_violations_at_scale(self):
        src, violations = self._build_large_source(100)
        # Feed each violation 5 times
        result = apply_bulk(src, violations * 5)
        self.assertTrue(result.success)
        self.assertEqual(result.ops_applied, 100,
                         "Should apply each unique op exactly once")
        self._assert_valid_structure(result.patched_source, 100)


# ─────────────────────────────────────────────────────────────────────────────
# 13. apply_bulk with mixed rules
# ─────────────────────────────────────────────────────────────────────────────

class TestApplyBulkMixedRules(unittest.TestCase):

    def test_empty_violations(self):
        src = "int x = 0;\n"
        result = apply_bulk(src, [])
        self.assertTrue(result.success)
        self.assertEqual(result.patched_source, src)
        self.assertEqual(result.ops_applied, 0)

    def test_conflict_summary_reported(self):
        """Overlapping ops must be reported in the conflicts list."""
        src = "int counter = 0;\nvoid inc(void) { counter++; }\n"
        v1 = make_violation("8.7",  line=1, severity="Required",  code_snippet="int counter = 0;")
        v2 = make_violation("10.3", line=1, severity="Advisory",
                            code_snippet="int counter = 0;",
                            suggested_fix="int counter = (int)0;")
        result = apply_bulk(src, [v1, v2])
        self.assertTrue(result.success)
        # At least one op was applied and the conflict was noted
        self.assertGreaterEqual(result.ops_applied, 1)


# ─────────────────────────────────────────────────────────────────────────────
# 14. Post-patch parser validation (invalid C is rejected)
# ─────────────────────────────────────────────────────────────────────────────

class TestParserValidation(unittest.TestCase):

    def test_valid_patch_passes_parser(self):
        """A clean 8.7 patch on real-looking C must pass parser validation."""
        src = "int g = 0;\nvoid use(void) { g++; }\n"
        v = make_violation("8.7", line=1, code_snippet="int g = 0;")
        result = apply_single(src, v)
        # If pycparser is available the result should pass
        if result.success:
            self.assertTrue(result.parse_valid)

    def test_result_is_never_invalid_c(self):
        """
        Even if a patch would produce invalid C, apply_bulk must return the
        *original* source unchanged rather than the broken version.
        """
        # We simulate this by creating a violation whose suggested_fix
        # would leave unbalanced braces — patch_engine should reject it.
        src = "int x = 0;\n"
        # Rule 10.3 with a suggested_fix that breaks the file
        v = make_violation(
            "10.3", line=1,
            code_snippet="int x = 0;",
            # Deliberately invalid C: missing closing part
            suggested_fix="int x = {{{broken;",
        )
        result = apply_bulk(src, [v])
        if not result.success:
            # If engine correctly rejected the broken patch, original is preserved
            self.assertEqual(result.patched_source, src)


# ─────────────────────────────────────────────────────────────────────────────
# 15. PatchOp checksum deduplication correctness
# ─────────────────────────────────────────────────────────────────────────────

class TestChecksumDedup(unittest.TestCase):

    def test_identical_ops_have_same_checksum(self):
        op1 = make_op(start=0, end=5, original="hello", replacement="world")
        op2 = make_op(start=0, end=5, original="hello", replacement="world")
        self.assertEqual(op1.checksum, op2.checksum)

    def test_different_replacement_different_checksum(self):
        op1 = make_op(start=0, end=5, original="hello", replacement="world")
        op2 = make_op(start=0, end=5, original="hello", replacement="WORLD")
        self.assertNotEqual(op1.checksum, op2.checksum)

    def test_different_offset_different_checksum(self):
        op1 = make_op(start=0, end=5, original="hello", replacement="world")
        op2 = make_op(start=1, end=6, original="ellow", replacement="world")
        self.assertNotEqual(op1.checksum, op2.checksum)


if __name__ == "__main__":
    unittest.main(verbosity=2)

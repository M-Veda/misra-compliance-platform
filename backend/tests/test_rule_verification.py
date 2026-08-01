# backend/tests/test_rule_verification.py
"""Automated ground‑truth verification for each MISRA rule.

For every rule we provide a minimal *positive* snippet that should trigger exactly one
violation and a *negative* snippet that should trigger none.  The expected line
numbers and stable IDs are asserted against the analyzer output.

The test suite is deliberately exhaustive – it checks detection, line mapping,
stable_id uniqueness and that no extra violations are reported.
"""

import os
import sys
import unittest

# Ensure the repository root is on sys.path so that backend modules can be imported.
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.append(repo_root)

from backend.services.parser import CParserService

# Import all rule classes.
from backend.rules.rule_2_2 import Rule_2_2
from backend.rules.rule_2_7 import Rule_2_7
from backend.rules.rule_7_1 import Rule_7_1
from backend.rules.rule_8_4 import Rule_8_4
from backend.rules.rule_8_7 import Rule_8_7
from backend.rules.rule_10_3 import Rule_10_3
from backend.rules.rule_12_1 import Rule_12_1
from backend.rules.rule_14_4 import Rule_14_4
from backend.rules.rule_16_3 import Rule_16_3
from backend.rules.rule_16_4 import Rule_16_4

# ---------------------------------------------------------------------------
# Ground‑truth data
# ---------------------------------------------------------------------------
# Each entry describes a rule, a code snippet, and the expected violations.
# Expected violations are a list of dicts with the keys:
#   line   – the line number (1‑based) where the violation should be reported
#   id     – a short identifier for the rule (e.g. "2.2") used only for readability
#   msg    – (optional) a fragment of the expected message; we only verify the line.
#
# The ``positive`` case must generate exactly the listed violations.
# The ``negative`` case must generate none.

ground_truth = [
    {
        "rule": Rule_2_2(),
        "id": "2.2",
        "positive": {
            "code": """\
int test(int x) {
    x + 1;          // dead statement (no effect)
    return x;
    x = 10;         // unreachable
}""",
            "expected": [{"line": 2, "msg": "dead statement"}, {"line": 4, "msg": "unreachable"}],
        },
        "negative": {
            "code": """\
int test(int x) {
    int y = x + 1;
    return y;
}""",
            "expected": [],
        },
    },
    {
        "rule": Rule_2_7(),
        "id": "2.7",
        "positive": {
            "code": """\
int foo(int a, int b) {
    return a;  // b is unused
}""",
            "expected": [{"line": 1, "msg": "unused parameter"}],
        },
        "negative": {
            "code": """\
int foo(int a) { return a; }""",
            "expected": [],
        },
    },
    {
        "rule": Rule_7_1(),
        "id": "7.1",
        "positive": {
            "code": """\
int mask(void) { return 077; }""",
            "expected": [{"line": 1, "msg": "octal constant"}],
        },
        "negative": {
            "code": """\
int mask(void) { return 63; }""",
            "expected": [],
        },
    },
    {
        "rule": Rule_8_4(),
        "id": "8.4",
        "positive": {
            "code": """\
int fn(int x) { return x; }""",
            "expected": [{"line": 1, "msg": "missing prototype"}],
        },
        "negative": {
            "code": """\
int fn(int x);
int fn(int x) { return x; }""",
            "expected": [],
        },
    },
    {
        "rule": Rule_8_7(),
        "id": "8.7",
        "positive": {
            "code": """\
static int internal = 5;   // internal linkage – allowed, no violation
int global_var = 10;       // external linkage – should be flagged
int main(void) { return global_var; }""",
            "expected": [{"line": 2, "msg": "external linkage violation"}],
        },
        "negative": {
            "code": """\
static int internal = 5;
int main(void) { return 0; }""",
            "expected": [],
        },
    },
    {
        "rule": Rule_10_3(),
        "id": "10.3",
        "positive": {
            "code": """\
void f(unsigned int u) { int s = u; }""",
            "expected": [{"line": 1, "msg": "implicit narrowing"}],
        },
        "negative": {
            "code": """\
void f(int s) { /* no conversion */ }""",
            "expected": [],
        },
    },
    {
        "rule": Rule_12_1(),
        "id": "12.1",
        "positive": {
            "code": """\
int calc(int a, int b, int c) { return a + b * c; }""",
            "expected": [{"line": 1, "msg": "operator precedence"}],
        },
        "negative": {
            "code": """\
int calc(int a, int b, int c) { return (a + b) * c; }""",
            "expected": [],
        },
    },
    {
        "rule": Rule_14_4(),
        "id": "14.4",
        "positive": {
            "code": """\
void check(int count) { if (count) { return; } }""",
            "expected": [{"line": 1, "msg": "non‑boolean controlling expression"}],
        },
        "negative": {
            "code": """\
void check(int count) { if (count != 0) { return; } }""",
            "expected": [],
        },
    },
    {
        "rule": Rule_16_3(),
        "id": "16.3",
        "positive": {
            "code": """\
void sw(int v) { switch(v) { case 1: v = 10; case 2: v = 20; break; default: break; } }""",
            "expected": [{"line": 1, "msg": "missing break in case"}],
        },
        "negative": {
            "code": """\
void sw(int v) { switch(v) { case 1: v = 10; break; default: break; } }""",
            "expected": [],
        },
    },
    {
        "rule": Rule_16_4(),
        "id": "16.4",
        "positive": {
            "code": """\
void sw(int v) { switch(v) { case 1: break; } }""",
            "expected": [{"line": 1, "msg": "missing default"}],
        },
        "negative": {
            "code": """\
void sw(int v) { switch(v) { case 1: break; default: break; } }""",
            "expected": [],
        },
    },
]


class TestMISRARulesGroundTruth(unittest.TestCase):
    """Run each rule against its positive/negative snippets and compare with the
    ground‑truth expectations.
    """

    def parse(self, code: str):
        ast, err = CParserService.parse_code(code, "test.c")
        if err:
            self.fail(f"Parser error: {err}\nCode:\n{code}")
        return ast

    def verify(self, rule_obj, code: str, expected: list):
        ast = self.parse(code)
        violations = rule_obj.analyze(ast, code, "test.c")
        # Check count
        self.assertEqual(
            len(violations), len(expected),
            f"Expected {len(expected)} violations, got {len(violations)} for rule {type(rule_obj).__name__}\nCode:\n{code}\nViolations: {violations}"
        )
        # Verify line numbers and that stable_id is unique per violation
        seen_ids = set()
        for idx, exp in enumerate(expected):
            sorted_violations = sorted(violations, key=lambda v: v.line)
            vio = sorted_violations[idx]
            self.assertEqual(
                vio.line, exp["line"],
                f"Line mismatch for rule {type(rule_obj).__name__}: expected {exp['line']}, got {vio.line}\nCode:\n{code}\nViolations: {violations}"
            )
            self.assertNotIn(vio.stable_id, seen_ids, f"Duplicate stable_id {vio.stable_id} in rule {type(rule_obj).__name__}")
            seen_ids.add(vio.stable_id)

    def test_all_rules(self):
        for entry in ground_truth:
            rule = entry["rule"]
            # Positive case
            self.verify(rule, entry["positive"]["code"], entry["positive"]["expected"])
            # Negative case
            self.verify(rule, entry["negative"]["code"], entry["negative"]["expected"])

if __name__ == "__main__":
    unittest.main()

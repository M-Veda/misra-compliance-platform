import sys
import os
import unittest

# Add parent directory of 'backend' to path to ensure backend modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.parser import CParserService
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

class TestMISRARules(unittest.TestCase):
    
    def parse_helper(self, code: str):
        ast, err = CParserService.parse_code(code, "test.c")
        if err:
            self.fail(f"Parsing failed during test: {err}")
        return ast

    # ----------------------------------------------------
    # RULE 2.2: Dead Code
    # ----------------------------------------------------
    def test_rule_2_2_positive(self):
        code = """
        int test(int x) {
            x + 1;
            return x;
            x = 10;
        }
        """
        ast = self.parse_helper(code)
        violations = Rule_2_2().analyze(ast, code, "test.c")
        self.assertEqual(len(violations), 2)

    def test_rule_2_2_negative(self):
        code = """
        int test(int x) {
            int y = x + 1;
            return y;
        }
        """
        ast = self.parse_helper(code)
        violations = Rule_2_2().analyze(ast, code, "test.c")
        self.assertEqual(len(violations), 0)

    # ----------------------------------------------------
    # RULE 2.7: Unused Parameter
    # ----------------------------------------------------
    def test_rule_2_7_positive(self):
        code = """
        int test(int a, int b) {
            return a;
        }
        """
        ast = self.parse_helper(code)
        violations = Rule_2_7().analyze(ast, code, "test.c")
        self.assertEqual(len(violations), 1)

    # ----------------------------------------------------
    # RULE 7.1: Octal Constants
    # ----------------------------------------------------
    def test_rule_7_1_positive(self):
        code = """
        int get_mask(void) {
            return 077;
        }
        """
        ast = self.parse_helper(code)
        violations = Rule_7_1().analyze(ast, code, "test.c")
        self.assertEqual(len(violations), 1)

    def test_rule_7_1_negative(self):
        code = """
        int get_mask(void) {
            return 63;
        }
        """
        ast = self.parse_helper(code)
        violations = Rule_7_1().analyze(ast, code, "test.c")
        self.assertEqual(len(violations), 0)

    # ----------------------------------------------------
    # RULE 8.4: Missing Prototype
    # ----------------------------------------------------
    def test_rule_8_4_positive(self):
        code = """
        int fn(int x) {
            return x;
        }
        """
        ast = self.parse_helper(code)
        violations = Rule_8_4().analyze(ast, code, "test.c")
        self.assertEqual(len(violations), 1)

    # ----------------------------------------------------
    # RULE 8.7: Internal Linkage
    # ----------------------------------------------------
    def test_rule_8_7_positive(self):
        code = """
        int global_var = 10;
        int main(void) {
            return global_var;
        }
        """
        ast = self.parse_helper(code)
        violations = Rule_8_7().analyze(ast, code, "test.c")
        self.assertEqual(len(violations), 1)

    # ----------------------------------------------------
    # RULE 10.3: Implicit Narrowing Conversion
    # ----------------------------------------------------
    def test_rule_10_3_positive(self):
        code = """
        void convert(unsigned int u) {
            int s = u;
        }
        """
        ast = self.parse_helper(code)
        violations = Rule_10_3().analyze(ast, code, "test.c")
        self.assertEqual(len(violations), 1)

    # ----------------------------------------------------
    # RULE 12.1: Operator Precedence
    # ----------------------------------------------------
    def test_rule_12_1_positive(self):
        code = """
        int calc(int a, int b, int c) {
            return a + b * c;
        }
        """
        ast = self.parse_helper(code)
        violations = Rule_12_1().analyze(ast, code, "test.c")
        self.assertEqual(len(violations), 1)

    # ----------------------------------------------------
    # RULE 14.4: Non-boolean Controlling Expression
    # ----------------------------------------------------
    def test_rule_14_4_positive(self):
        code = """
        void check(int count) {
            if (count) {
                return;
            }
        }
        """
        ast = self.parse_helper(code)
        violations = Rule_14_4().analyze(ast, code, "test.c")
        self.assertEqual(len(violations), 1)

    # ----------------------------------------------------
    # RULE 16.3: Switch Case Missing Break
    # ----------------------------------------------------
    def test_rule_16_3_positive(self):
        code = """
        void test_switch(int val) {
            switch (val) {
                case 1:
                    val = 10;
                case 2:
                    val = 20;
                    break;
                default:
                    break;
            }
        }
        """
        ast = self.parse_helper(code)
        violations = Rule_16_3().analyze(ast, code, "test.c")
        self.assertEqual(len(violations), 1)

    # ----------------------------------------------------
    # RULE 16.4: Switch Missing Default Clause
    # ----------------------------------------------------
    def test_rule_16_4_positive(self):
        code = """
        void test_switch(int val) {
            switch (val) {
                case 1:
                    break;
            }
        }
        """
        ast = self.parse_helper(code)
        violations = Rule_16_4().analyze(ast, code, "test.c")
        self.assertEqual(len(violations), 1)


if __name__ == "__main__":
    unittest.main()

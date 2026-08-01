from backend.rules.base import BaseRule
from backend.models.violation import RuleViolation
from backend.services.parser import CParserService
from pycparser.c_ast import NodeVisitor, Constant
import re

class OctalConstantVisitor(NodeVisitor):
    def __init__(self, rule, source_lines, file_name):
        self.rule = rule
        self.source_lines = source_lines
        self.file_name = file_name
        self.violations = []

    def visit_Constant(self, node):
        if node.type in ('int', 'char') and node.value:
            val = node.value.strip()
            # Match octal integer literal (starts with 0 followed by digits 0-7, not 0x/0X/0b/0B, and length > 1)
            if re.match(r'^0[0-7]+[uUlL]*$', val):
                line = CParserService.adjust_line(node.coord.line) if node.coord else 1
                col = node.coord.column if node.coord else 1
                snippet = self.source_lines[line - 1].strip() if line - 1 < len(self.source_lines) else ""
                
                # Convert octal literal to decimal string
                digits_part = re.sub(r'[uUlL]+$', '', val)
                suffix = val[len(digits_part):]
                try:
                    dec_val = int(digits_part, 8)
                    replacement_val = f"{dec_val}{suffix}"
                except ValueError:
                    replacement_val = val

                suggested_fix = snippet.replace(val, replacement_val) if snippet and val in snippet else replacement_val

                self.violations.append(RuleViolation(
                    rule_number=self.rule.rule_number,
                    rule_name=self.rule.rule_name,
                    severity=self.rule.severity,
                    category=self.rule.category,
                    file=self.file_name,
                    line=line,
                    column=col,
                    message=f"Octal constant '{val}' used. Octal constants and escape sequences shall not be used.",
                    code_snippet=snippet,
                    reason=f"The integer literal '{val}' is specified in octal notation. MISRA Rule 7.1 prohibits octal constants because the leading zero can easily be misread or cause unintended base-8 interpretations.",
                    suggested_fix=suggested_fix,
                    confidence=1.0
                ))
        self.generic_visit(node)


class Rule_7_1(BaseRule):
    @property
    def rule_number(self) -> str:
        return "7.1"

    @property
    def rule_name(self) -> str:
        return "Octal constants shall not be used"

    @property
    def severity(self) -> str:
        return "Required"

    @property
    def category(self) -> str:
        return "Literals"

    @property
    def description(self) -> str:
        return "Octal constants and octal escape sequences shall not be used."

    def analyze(self, ast, source_code: str, file_name: str = "source.c") -> list[RuleViolation]:
        source_lines = source_code.splitlines()
        visitor = OctalConstantVisitor(self, source_lines, file_name)
        visitor.visit(ast)
        return visitor.violations

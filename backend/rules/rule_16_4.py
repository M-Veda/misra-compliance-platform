from backend.rules.base import BaseRule
from backend.models.violation import RuleViolation
from backend.services.parser import CParserService
from pycparser.c_ast import NodeVisitor, Switch, Default, Compound
import re

class SwitchDefaultVisitor(NodeVisitor):
    def __init__(self, rule, source_lines, file_name):
        self.rule = rule
        self.source_lines = source_lines
        self.file_name = file_name
        self.violations = []

    def visit_Switch(self, node):
        has_default = False
        body = node.stmt
        items = body.block_items if (isinstance(body, Compound) and body.block_items) else [body]
        
        for item in items:
            if isinstance(item, Default):
                has_default = True
                break
        
        if not has_default:
            line = CParserService.adjust_line(node.coord.line) if node.coord else 1
            col = node.coord.column if node.coord else 1
            snippet = self.source_lines[line - 1].strip() if line - 1 < len(self.source_lines) else ""
            
            suggested_fix = f"{snippet}\n        default:\n            break;"

            self.violations.append(RuleViolation(
                rule_number=self.rule.rule_number,
                rule_name=self.rule.rule_name,
                severity=self.rule.severity,
                category=self.rule.category,
                file=self.file_name,
                line=line,
                column=col,
                message="Switch statement does not contain a default clause.",
                code_snippet=snippet,
                reason="MISRA Rule 16.4 requires every switch statement to have a final default clause to explicitly handle unhandled conditions and avoid undefined control flow.",
                suggested_fix=suggested_fix,
                confidence=1.0
            ))
            
        self.generic_visit(node)


class Rule_16_4(BaseRule):
    @property
    def rule_number(self) -> str:
        return "16.4"

    @property
    def rule_name(self) -> str:
        return "Every switch statement shall have a default clause"

    @property
    def severity(self) -> str:
        return "Required"

    @property
    def category(self) -> str:
        return "Control Flow"

    @property
    def description(self) -> str:
        return "Every switch statement shall have a default clause."

    def analyze(self, ast, source_code: str, file_name: str = "source.c") -> list[RuleViolation]:
        source_lines = source_code.splitlines()
        visitor = SwitchDefaultVisitor(self, source_lines, file_name)
        visitor.visit(ast)
        return visitor.violations

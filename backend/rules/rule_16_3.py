from backend.rules.base import BaseRule
from backend.models.violation import RuleViolation
from backend.services.parser import CParserService
from pycparser.c_ast import NodeVisitor, Switch, Case, Default, Break, Return, Goto, Continue, Compound
import re

class SwitchBreakVisitor(NodeVisitor):
    def __init__(self, rule, source_lines, file_name):
        self.rule = rule
        self.source_lines = source_lines
        self.file_name = file_name
        self.violations = []

    def visit_Switch(self, node):
        # Traverse switch statement body
        body = node.stmt
        items = body.block_items if (isinstance(body, Compound) and body.block_items) else [body]
        
        for i, item in enumerate(items):
            if isinstance(item, (Case, Default)):
                stmts = item.stmts or []
                # Check if non-empty case clause lacks unconditional break/return/goto/continue
                if stmts:
                    last_stmt = stmts[-1]
                    if not isinstance(last_stmt, (Break, Return, Goto, Continue)):
                        line = CParserService.adjust_line(last_stmt.coord.line) if last_stmt.coord else (CParserService.adjust_line(item.coord.line) if item.coord else 1)
                        col = last_stmt.coord.column if last_stmt.coord else 1
                        snippet = self.source_lines[line - 1].strip() if line - 1 < len(self.source_lines) else ""
                        
                        clause_type = "default" if isinstance(item, Default) else "case"
                        suggested_fix = f"{snippet}\n    break;" if snippet else "break;"

                        self.violations.append(RuleViolation(
                            rule_number=self.rule.rule_number,
                            rule_name=self.rule.rule_name,
                            severity=self.rule.severity,
                            category=self.rule.category,
                            file=self.file_name,
                            line=line,
                            column=col,
                            message=f"Switch clause ({clause_type}) is non-empty and does not end with an unconditional break statement.",
                            code_snippet=snippet,
                            reason=f"MISRA Rule 16.3 requires that an unconditional break statement shall terminate every non-empty switch clause to prevent unintentional fall-through behavior.",
                            suggested_fix=suggested_fix,
                            confidence=1.0
                        ))
        self.generic_visit(node)


class Rule_16_3(BaseRule):
    @property
    def rule_number(self) -> str:
        return "16.3"

    @property
    def rule_name(self) -> str:
        return "Switch clause missing break statement"

    @property
    def severity(self) -> str:
        return "Required"

    @property
    def category(self) -> str:
        return "Control Flow"

    @property
    def description(self) -> str:
        return "An unconditional break statement shall terminate every non-empty switch clause."

    def analyze(self, ast, source_code: str, file_name: str = "source.c") -> list[RuleViolation]:
        source_lines = source_code.splitlines()
        visitor = SwitchBreakVisitor(self, source_lines, file_name)
        visitor.visit(ast)
        return visitor.violations

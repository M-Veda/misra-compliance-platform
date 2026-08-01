from backend.rules.base import BaseRule
from backend.models.violation import RuleViolation
from backend.services.parser import CParserService
from pycparser.c_ast import NodeVisitor, Compound, Return, Break, Continue, Goto, Assignment, FuncCall, UnaryOp, ExprList, For, While, DoWhile, If, EmptyStatement, Cast, Case, Default
import re

class DeadCodeVisitor(NodeVisitor):
    def __init__(self, rule, source_lines, file_name):
        self.rule = rule
        self.source_lines = source_lines
        self.file_name = file_name
        self.violations = []

    def has_side_effects(self, node) -> bool:
        """
        Recursively check if an expression node has side effects.
        Side effects include assignments, function calls, and increment/decrement.
        """
        if node is None:
            return False
        
        if isinstance(node, Assignment):
            return True
        if isinstance(node, FuncCall):
            return True
        if isinstance(node, UnaryOp) and node.op in ['++', '--', 'p++', 'p--']:
            return True
        
        # Recursively check children
        for _, child in node.children():
            if self.has_side_effects(child):
                return True
        return False

    def visit_Compound(self, node):
        # 1. Check for unreachable statements
        unreachable_start = -1
        for i, item in enumerate(node.block_items or []):
            # Check if previous statement was an unconditional exit
            if unreachable_start != -1:
                line = CParserService.adjust_line(item.coord.line) if item.coord else 1
                col = item.coord.column if item.coord else 1
                snippet = self.source_lines[line - 1].strip() if line - 1 < len(self.source_lines) else ""
                
                self.violations.append(RuleViolation(
                    rule_number=self.rule.rule_number,
                    rule_name=self.rule.rule_name,
                    severity=self.rule.severity,
                    category=self.rule.category,
                    file=self.file_name,
                    line=line,
                    column=col,
                    message="Unreachable code: statement follows an unconditional control transfer (return/break/continue/goto).",
                    code_snippet=snippet,
                    reason="This code statement is situated after a return, break, continue, or goto statement in the same execution block, meaning it can never be executed.",
                    suggested_fix="",  # empty string means remove it
                    confidence=1.0
                ))
            
            # Check if this item is an exit statement
            if isinstance(item, (Return, Break, Continue, Goto)):
                unreachable_start = i

        # 2. Check for expressions with no effect (dead expressions)
        for item in node.block_items or []:
            # Expression statement (not control flow, decl, return, empty statement, cast, case, default, etc.)
            if not isinstance(item, (Compound, Return, Break, Continue, Goto, Assignment, FuncCall, If, For, While, DoWhile, EmptyStatement, Cast, Case, Default, type(None))):
                # Check if it's a declaration or cast/case/default
                if hasattr(item, '__class__') and item.__class__.__name__ in ('Decl', 'EmptyStatement', 'Cast', 'Case', 'Default'):
                    continue
                # If it doesn't have side effects, it is dead expression code
                if not self.has_side_effects(item):
                    line = CParserService.adjust_line(item.coord.line) if item.coord else 1
                    col = item.coord.column if item.coord else 1
                    snippet = self.source_lines[line - 1].strip() if line - 1 < len(self.source_lines) else ""
                    
                    self.violations.append(RuleViolation(
                        rule_number=self.rule.rule_number,
                        rule_name=self.rule.rule_name,
                        severity=self.rule.severity,
                        category=self.rule.category,
                        file=self.file_name,
                        line=line,
                        column=col,
                        message="Statement has no side effects and its result is discarded.",
                        code_snippet=snippet,
                        reason="This statement evaluates an expression (e.g., a variable reference or arithmetic operation) but does not assign the result or trigger a function call, making it dead code.",
                        suggested_fix="",  # empty string means remove it
                        confidence=1.0
                    ))

        # Continue traversing children
        self.generic_visit(node)

class Rule_2_2(BaseRule):
    @property
    def rule_number(self) -> str:
        return "2.2"

    @property
    def rule_name(self) -> str:
        return "No dead code"

    @property
    def severity(self) -> str:
        return "Required"

    @property
    def category(self) -> str:
        return "Unused Code"

    @property
    def description(self) -> str:
        return "There shall be no dead code. This includes unreachable code and statements with no side effects."

    def analyze(self, ast, source_code: str, file_name: str) -> list[RuleViolation]:
        source_lines = source_code.splitlines()
        visitor = DeadCodeVisitor(self, source_lines, file_name)
        visitor.visit(ast)
        return visitor.violations

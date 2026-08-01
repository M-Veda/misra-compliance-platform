from backend.rules.base import BaseRule
from backend.models.violation import RuleViolation
from backend.services.parser import CParserService
from pycparser.c_ast import NodeVisitor, BinaryOp, ID, Constant, UnaryOp
import re

# Grouping operators of similar class to allow no parentheses (e.g., a + b + c)
SIMILAR_OPERATORS = [
    {'+', '-'},
    {'*', '/', '%'},
    {'&&'},
    {'||'},
    {'&'},
    {'^'},
    {'|'},
    {'==', '!='},
    {'<', '>', '<=', '>='},
    {'<<', '>>'}
]

def are_similar_ops(op1: str, op2: str) -> bool:
    for group in SIMILAR_OPERATORS:
        if op1 in group and op2 in group:
            return True
    return False

def get_operator_depths(line_text: str, op: str) -> list[int]:
    depths = []
    current_depth = 0
    i = 0
    n = len(line_text)
    while i < n:
        char = line_text[i]
        if char == '(':
            current_depth += 1
        elif char == ')':
            current_depth -= 1
        elif line_text[i : i + len(op)] == op:
            is_match = True
            if op in ('&', '|') and i + 1 < n and line_text[i + 1] == op:
                is_match = False
            if op in ('&', '|') and i - 1 >= 0 and line_text[i - 1] == op:
                is_match = False
            if op in ('<', '>') and i + 1 < n and line_text[i + 1] == op:
                is_match = False
            if op in ('<', '>') and i - 1 >= 0 and line_text[i - 1] == op:
                is_match = False
            
            if is_match:
                depths.append(current_depth)
                i += len(op) - 1
        i += 1
    return depths

def reconstruct_expr(node) -> str:
    """
    Reconstructs an expression string from pycparser AST nodes for regex matching.
    """
    if node is None:
        return ""
    if isinstance(node, ID):
        return node.name
    if isinstance(node, Constant):
        return str(node.value)
    if isinstance(node, BinaryOp):
        return f"{reconstruct_expr(node.left)} {node.op} {reconstruct_expr(node.right)}"
    if isinstance(node, UnaryOp):
        return f"{node.op}{reconstruct_expr(node.expr)}"
    return ""

def make_regex_for_expr(expr_str: str) -> str:
    """
    Creates a flexible regex that matches the expression string regardless of spacing.
    """
    # Escape special characters, then replace spaces with \s*
    escaped = re.escape(expr_str)
    # Replace escaped spaces with \s*
    flexible = re.sub(r'\\\s+', r'\\s*', escaped)
    # Also allow \s* around operators
    for op in ('+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||', '&', '|', '^', '<<', '>>'):
        esc_op = re.escape(op)
        flexible = flexible.replace(esc_op, r'\s*' + esc_op + r'\s*')
    return flexible

class OperatorPrecedenceVisitor(NodeVisitor):
    def __init__(self, rule, source_lines, file_name):
        self.rule = rule
        self.source_lines = source_lines
        self.file_name = file_name
        self.violations = []

    def visit_BinaryOp(self, node):
        self.generic_visit(node)
        
        # Check if parent is BinaryOp and child is BinaryOp
        for child_name, child in node.children():
            if isinstance(child, BinaryOp):
                parent_op = node.op
                child_op = child.op
                
                if not are_similar_ops(parent_op, child_op):
                    line_num = CParserService.adjust_line(node.coord.line) if node.coord else 1
                    col = node.coord.column if node.coord else 1
                    
                    if line_num - 1 < len(self.source_lines):
                        line_text = self.source_lines[line_num - 1]
                        
                        parent_depths = get_operator_depths(line_text, parent_op)
                        child_depths = get_operator_depths(line_text, child_op)
                        
                        is_parenthesized = False
                        if parent_depths and child_depths:
                            max_parent_depth = max(parent_depths)
                            max_child_depth = max(child_depths)
                            if max_child_depth > max_parent_depth:
                                is_parenthesized = True
                        
                        if not is_parenthesized:
                            snippet = line_text.strip()
                            
                            # Generate a precise suggested fix by wrapping the child expression in parentheses
                            child_expr_str = reconstruct_expr(child)
                            suggested_fix = snippet
                            if child_expr_str:
                                # Build flexible regex to match child expression in the snippet
                                regex_pattern = make_regex_for_expr(child_expr_str)
                                match = re.search(regex_pattern, snippet)
                                if match:
                                    matched_text = match.group(0)
                                    # Wrap in parentheses
                                    # Ensure we don't double parenthesize
                                    if not (matched_text.startswith('(') and matched_text.endswith(')')):
                                        suggested_fix = snippet.replace(matched_text, f"({matched_text})")
                            
                            reason = f"The expression mixes operators '{parent_op}' and '{child_op}' without explicit parentheses, which violates MISRA Rule 12.1. This may affect readability and cause logic errors depending on precedence."
                            
                            self.violations.append(RuleViolation(
                                rule_number=self.rule.rule_number,
                                rule_name=self.rule.rule_name,
                                severity=self.rule.severity,
                                category=self.rule.category,
                                file=self.file_name,
                                line=line_num,
                                column=col,
                                message=f"Operator precedence is not explicit for '{parent_op}' and '{child_op}'.",
                                code_snippet=snippet,
                                reason=reason,
                                suggested_fix=suggested_fix,
                                confidence=1.0
                            ))
                            break

class Rule_12_1(BaseRule):
    @property
    def rule_number(self) -> str:
        return "12.1"

    @property
    def rule_name(self) -> str:
        return "Operator precedence should be explicit"

    @property
    def severity(self) -> str:
        return "Advisory"

    @property
    def category(self) -> str:
        return "Expressions"

    @property
    def description(self) -> str:
        return "The precedence of operators within expressions should be made explicit by using parentheses."

    def analyze(self, ast, source_code: str, file_name: str) -> list[RuleViolation]:
        source_lines = source_code.splitlines()
        visitor = OperatorPrecedenceVisitor(self, source_lines, file_name)
        visitor.visit(ast)
        return visitor.violations

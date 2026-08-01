from backend.rules.base import BaseRule
from backend.models.violation import RuleViolation
from backend.services.parser import CParserService
from pycparser.c_ast import NodeVisitor, If, While, DoWhile, For, BinaryOp, UnaryOp, ID, Constant, Cast
from backend.rules.rule_10_3 import clean_type_name

class BooleanConditionVisitor(NodeVisitor):
    def __init__(self, rule, source_lines, file_name):
        self.rule = rule
        self.source_lines = source_lines
        self.file_name = file_name
        self.violations = []
        self.var_types = {}

    def visit_Decl(self, node):
        # Track variable types to determine if a variable is boolean
        if node.name and not isinstance(node.type, type(None)):
            if node.type.__class__.__name__ != 'FuncDecl':
                self.var_types[node.name] = clean_type_name(node.type)
        self.generic_visit(node)

    def visit_FuncDef(self, node):
        # Track parameters
        if node.decl.type and hasattr(node.decl.type, 'args') and node.decl.type.args:
            for p in node.decl.type.args.params or []:
                if p.name:
                    self.var_types[p.name] = clean_type_name(p.type)
        self.generic_visit(node)

    def is_essentially_boolean(self, node) -> bool:
        """
        Check if an expression node is essentially Boolean.
        Essentially Boolean includes:
        - Relational and logical binary operations (==, !=, <, >, <=, >=, &&, ||)
        - Logical negation (!)
        - Variables of type 'bool' or '_Bool'
        - Casts to 'bool' or '_Bool'
        - Boolean constants (true, false)
        """
        if node is None:
            return False

        if isinstance(node, BinaryOp):
            return node.op in ('==', '!=', '<', '>', '<=', '>=', '&&', '||')
            
        if isinstance(node, UnaryOp):
            return node.op == '!'

        if isinstance(node, Cast):
            t_name = clean_type_name(node.to_type)
            return t_name in ('bool', '_Bool')

        if isinstance(node, ID):
            t_name = self.var_types.get(node.name)
            return t_name in ('bool', '_Bool')

        if isinstance(node, Constant):
            # Check if it is a boolean constant name (like true/false) or is parsed as bool
            return node.type == 'bool' or node.value in ('true', 'false')

        return False

    def check_condition(self, cond_node, statement_name: str):
        if cond_node is None:
            return

        if not self.is_essentially_boolean(cond_node):
            line = CParserService.adjust_line(cond_node.coord.line) if cond_node.coord else 1
            col = cond_node.coord.column if cond_node.coord else 1
            snippet = self.source_lines[line - 1].strip() if line - 1 < len(self.source_lines) else ""

            # Deduce a helpful suggested fix
            # E.g., if condition is a variable 'x', suggest 'x != 0'
            cond_str = snippet
            # Try to isolate the condition in the parenthesis of if/while
            import re
            match = re.search(r"(?:if|while|for)\s*\((.*)\)", snippet)
            if match:
                cond_str = match.group(1).strip()
            
            # Type-aware condition rewrite logic:
            # - Pointers (* or ptr in name/type) -> ptr != NULL
            # - Boolean/flags (bool or flag in name/type) -> flag == true
            # - Numeric values -> count != 0
            if isinstance(cond_node, ID):
                var_name = cond_node.name
                var_type = self.var_types.get(var_name, 'int').lower()
                if '*' in var_type or 'ptr' in var_name.lower() or 'str' in var_name.lower():
                    suggested_cond = f"{var_name} != NULL"
                elif 'bool' in var_type or 'flag' in var_name.lower():
                    suggested_cond = f"{var_name} == true"
                else:
                    suggested_cond = f"{var_name} != 0"
            else:
                if 'ptr' in cond_str.lower() or 'str' in cond_str.lower():
                    suggested_cond = f"{cond_str} != NULL"
                elif 'flag' in cond_str.lower() or 'bool' in cond_str.lower():
                    suggested_cond = f"{cond_str} == true"
                else:
                    suggested_cond = f"{cond_str} != 0"
                
            # Replace the condition in the statement snippet
            suggested_fix = snippet.replace(cond_str, suggested_cond) if cond_str in snippet else f"{suggested_cond}"
            
            reason = f"The controlling expression of the {statement_name} statement has a non-boolean type. In MISRA C:2012, conditions must evaluate to an essentially Boolean type."

            self.violations.append(RuleViolation(
                rule_number=self.rule.rule_number,
                rule_name=self.rule.rule_name,
                severity=self.rule.severity,
                category=self.rule.category,
                file=self.file_name,
                line=line,
                column=col,
                message=f"Condition of '{statement_name}' statement is not essentially Boolean.",
                code_snippet=snippet,
                reason=reason,
                suggested_fix=suggested_fix,
                confidence=1.0
            ))

    def visit_If(self, node):
        self.check_condition(node.cond, "if")
        self.generic_visit(node)

    def visit_While(self, node):
        # Skip checking 'while (1)' as a common construct for main loops,
        # but check others. Let's check everything, and if it's 'while (1)', it's a violation unless it is 'while (true)'.
        # Actually, let's check it strictly.
        self.check_condition(node.cond, "while")
        self.generic_visit(node)

    def visit_DoWhile(self, node):
        self.check_condition(node.cond, "do-while")
        self.generic_visit(node)

    def visit_For(self, node):
        if node.cond:
            self.check_condition(node.cond, "for")
        self.generic_visit(node)

class Rule_14_4(BaseRule):
    @property
    def rule_number(self) -> str:
        return "14.4"

    @property
    def rule_name(self) -> str:
        return "Condition shall be essentially Boolean"

    @property
    def severity(self) -> str:
        return "Required"

    @property
    def category(self) -> str:
        return "Control Flow"

    @property
    def description(self) -> str:
        return "The controlling expression of an if-statement or an iteration-statement shall have essentially Boolean type."

    def analyze(self, ast, source_code: str, file_name: str) -> list[RuleViolation]:
        source_lines = source_code.splitlines()
        visitor = BooleanConditionVisitor(self, source_lines, file_name)
        visitor.visit(ast)
        return visitor.violations

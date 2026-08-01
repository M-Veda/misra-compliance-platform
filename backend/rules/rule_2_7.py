from backend.rules.base import BaseRule
from backend.models.violation import RuleViolation
from backend.services.parser import CParserService
from pycparser.c_ast import NodeVisitor, FuncDef, ID

class ParameterUsageVisitor(NodeVisitor):
    def __init__(self):
        self.used_names = set()

    def visit_ID(self, node):
        self.used_names.add(node.name)
        self.generic_visit(node)

class Rule_2_7(BaseRule):
    @property
    def rule_number(self) -> str:
        return "2.7"

    @property
    def rule_name(self) -> str:
        return "Unused function parameter"

    @property
    def severity(self) -> str:
        return "Advisory"

    @property
    def category(self) -> str:
        return "Unused Code"

    @property
    def description(self) -> str:
        return "There shall be no unused parameters in functions."

    def analyze(self, ast, source_code: str, file_name: str) -> list[RuleViolation]:
        violations = []
        source_lines = source_code.splitlines()

        class FunctionVisitor(NodeVisitor):
            def visit_FuncDef(self, node):
                # Check if there are parameters
                if node.decl.type and hasattr(node.decl.type, 'args') and node.decl.type.args:
                    params = node.decl.type.args.params or []
                    # Get all parameter names (excluding anonymous parameters like void)
                    param_names = []
                    param_nodes = []
                    for p in params:
                        if p.name:
                            param_names.append(p.name)
                            param_nodes.append(p)
                    
                    if param_names:
                        # Find all variable usages in the function body
                        usage_visitor = ParameterUsageVisitor()
                        usage_visitor.visit(node.body)
                        
                        # Find unused parameters
                        for p_node, p_name in zip(param_nodes, param_names):
                            if p_name not in usage_visitor.used_names:
                                line = CParserService.adjust_line(p_node.coord.line) if p_node.coord else 1
                                col = p_node.coord.column if p_node.coord else 1
                                snippet = source_lines[line - 1].strip() if line - 1 < len(source_lines) else ""
                                
                                # Suggested fix: add (void)param_name; at the beginning of the function body
                                body_line = CParserService.adjust_line(node.body.coord.line) if node.body.coord else line
                                indent = "    "
                                # Look at the first line of the function body to get indentation
                                if body_line - 1 < len(source_lines):
                                    match = re.match(r"^(\s*)", source_lines[body_line - 1])
                                    if match:
                                        indent = match.group(1) + "    "
                                
                                suggested_fix = f"(void){p_name};"
                                reason = f"Function parameter '{p_name}' is declared but never read or referenced in the function body."
                                
                                violations.append(RuleViolation(
                                    rule_number="2.7",
                                    rule_name="Unused function parameter",
                                    severity="Advisory",
                                    category="Unused Code",
                                    file=file_name,
                                    line=line,
                                    column=col,
                                    message=f"Parameter '{p_name}' is unused.",
                                    code_snippet=snippet,
                                    reason=reason,
                                    suggested_fix=suggested_fix,
                                    confidence=1.0
                                ))
                
                # Continue searching inside this function for nested functions (though not standard C)
                self.generic_visit(node)

        import re
        visitor = FunctionVisitor()
        visitor.visit(ast)
        return violations

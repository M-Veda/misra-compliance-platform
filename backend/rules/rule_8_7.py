from backend.rules.base import BaseRule
from backend.models.violation import RuleViolation
from backend.services.parser import CParserService
from pycparser.c_ast import NodeVisitor, Decl, FuncDef, ID, Typedef

class GlobalVarUsageVisitor(NodeVisitor):
    def __init__(self, target_vars):
        self.target_vars = target_vars
        # Map of var_name -> set of function names where it is used
        self.usage_map = {name: set() for name in target_vars}
        self.current_function = None

    def visit_FuncDef(self, node):
        prev_func = self.current_function
        self.current_function = node.decl.name
        self.generic_visit(node)
        self.current_function = prev_func

    def visit_ID(self, node):
        if node.name in self.target_vars:
            if self.current_function:
                self.usage_map[node.name].add(self.current_function)
            else:
                # Referenced in global scope (e.g. in initializer of another global)
                self.usage_map[node.name].add("__global__")
        self.generic_visit(node)

class Rule_8_7(BaseRule):
    @property
    def rule_number(self) -> str:
        return "8.7"

    @property
    def rule_name(self) -> str:
        return "Objects should have block scope whenever possible"

    @property
    def severity(self) -> str:
        return "Advisory"

    @property
    def category(self) -> str:
        return "Declarations"

    @property
    def description(self) -> str:
        return "An object with external linkage shall have file scope or block scope if it is only referenced in a single function."

    def analyze(self, ast, source_code: str, file_name: str) -> list[RuleViolation]:
        violations = []
        source_lines = source_code.splitlines()

        # Find global variables with external linkage
        # A global variable is a Decl at the top level (ast.ext) that is not a function declaration, not static, and not a typedef
        global_vars = {}
        for ext in ast.ext:
            if isinstance(ext, Decl) and not isinstance(ext.type, Typedef):
                # Check if it's not a function declaration
                type_name = ext.type.__class__.__name__
                if type_name != 'FuncDecl':
                    is_static = ext.storage and "static" in ext.storage
                    is_extern = ext.storage and "extern" in ext.storage
                    if not is_static and not is_extern:
                        global_vars[ext.name] = ext

        if not global_vars:
            return []

        # Track usage of each global variable across function definitions
        visitor = GlobalVarUsageVisitor(list(global_vars.keys()))
        visitor.visit(ast)

        # Identify global variables used in exactly one function
        for var_name, functions in visitor.usage_map.items():
            if len(functions) == 1 and "__global__" not in functions:
                func_name = list(functions)[0]
                decl_node = global_vars[var_name]
                
                line = CParserService.adjust_line(decl_node.coord.line) if decl_node.coord else 1
                col = decl_node.coord.column if decl_node.coord else 1
                snippet = source_lines[line - 1].strip() if line - 1 < len(source_lines) else ""
                
                reason = f"Global variable '{var_name}' is declared at file scope with external linkage, but it is only referenced inside the function '{func_name}'."
                
                # Suggested fix: make it static or move it inside the function
                # We can suggest adding 'static' to the declaration, or moving it. Let's suggest making it static at file scope as a simple patch, or making it static inside the block scope.
                # Actually, adding "static" to the declaration at the global scope removes the external linkage, making it internal linkage, which satisfies Rule 8.7 (since 8.7 is about objects with external linkage).
                # Alternatively, we can suggest moving it inside the function. Let's suggest adding "static" as it is the safest patch.
                suggested_fix = f"static {snippet}"
                
                violations.append(RuleViolation(
                    rule_number="8.7",
                    rule_name="Objects should have block scope whenever possible",
                    severity="Advisory",
                    category="Declarations",
                    file=file_name,
                    line=line,
                    column=col,
                    message=f"Global variable '{var_name}' is only referenced in function '{func_name}' and should have block scope or internal linkage.",
                    code_snippet=snippet,
                    reason=reason,
                    suggested_fix=suggested_fix,
                    confidence=1.0
                ))

        return violations

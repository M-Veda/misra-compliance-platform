from backend.rules.base import BaseRule
from backend.models.violation import RuleViolation
from backend.services.parser import CParserService
from pycparser.c_ast import NodeVisitor, FuncDef, Decl, FuncDecl

class Rule_8_4(BaseRule):
    @property
    def rule_number(self) -> str:
        return "8.4"

    @property
    def rule_name(self) -> str:
        return "Function prototype required"

    @property
    def severity(self) -> str:
        return "Required"

    @property
    def category(self) -> str:
        return "Declarations"

    @property
    def description(self) -> str:
        return "A compatible declaration shall be visible when an object or function with external linkage is defined."

    def analyze(self, ast, source_code: str, file_name: str) -> list[RuleViolation]:
        violations = []
        source_lines = source_code.splitlines()

        # Track declarations (prototypes) seen before definitions
        declared_functions = set()
        
        # We traverse the top-level items of the translation unit
        for ext in ast.ext:
            if isinstance(ext, Decl):
                # Check if it's a function declaration (prototype) and not a definition
                if isinstance(ext.type, FuncDecl):
                    declared_functions.add(ext.name)
            
            elif isinstance(ext, FuncDef):
                func_name = ext.decl.name
                
                # Check if the function is static or main
                is_static = ext.decl.storage and "static" in ext.decl.storage
                if is_static or func_name == "main":
                    continue
                
                # If there's no prototype visible prior to this definition, it's a violation
                if func_name not in declared_functions:
                    line = CParserService.adjust_line(ext.coord.line) if ext.coord else 1
                    col = ext.coord.column if ext.coord else 1
                    snippet = source_lines[line - 1].strip() if line - 1 < len(source_lines) else ""
                    
                    # Construct suggested fix: prepend a prototype
                    # Let's extract the return type and parameter list from the function declaration
                    # A simple approximation: find the function header line and append a semicolon
                    func_header = snippet
                    if "{" in func_header:
                        func_header = func_header.split("{")[0].strip()
                    else:
                        # Grab lines until we see a '{' (for multi-line function definitions)
                        lines_to_search = source_lines[line-1 : line+2]
                        header_str = " ".join(lines_to_search)
                        if "{" in header_str:
                            func_header = header_str.split("{")[0].strip()
                        else:
                            func_header = snippet.strip()
                    
                    # Ensure it ends with a semicolon
                    if not func_header.endswith(";"):
                        func_header = func_header + ";"
                    
                    suggested_fix = f"static {snippet}" # Alternatively make it static
                    # Let's suggest prepending the prototype
                    reason = f"Function '{func_name}' has external linkage but no visible prototype declaration in this translation unit."
                    
                    violations.append(RuleViolation(
                        rule_number="8.4",
                        rule_name="Function prototype required",
                        severity="Required",
                        category="Declarations",
                        file=file_name,
                        line=line,
                        column=col,
                        message=f"Function '{func_name}' defined without a visible prototype.",
                        code_snippet=snippet,
                        reason=reason,
                        suggested_fix=f"{func_header}\n{snippet}", # Suggest prepending prototype before the definition
                        confidence=1.0
                    ))
                
                # Also add this function definition to declared functions in case there are subsequent definitions/usages
                declared_functions.add(func_name)
                
        return violations

from backend.rules.base import BaseRule
from backend.models.violation import RuleViolation
from backend.services.parser import CParserService
from pycparser.c_ast import NodeVisitor, Decl, Assignment, Return, ID, Constant, Cast, FuncCall, IdentifierType
import re

# Essential type categories as defined by MISRA C:2012
class EssentialType:
    CATEGORY_BOOLEAN = "Boolean"
    CATEGORY_CHARACTER = "Character"
    CATEGORY_SIGNED = "Signed"
    CATEGORY_UNSIGNED = "Unsigned"
    CATEGORY_FLOATING = "Floating"

    def __init__(self, category: str, width: int):
        self.category = category
        self.width = width  # in bits (8, 16, 32, 64)

    def is_narrower_than(self, other) -> bool:
        """
        Returns True if this type is narrower than the other (fewer bits).
        """
        return self.width < other.width

    def __eq__(self, other):
        if not isinstance(other, EssentialType):
            return False
        return self.category == other.category and self.width == other.width

    def __str__(self):
        return f"{self.category}({self.width}bit)"

# Map standard types to their essential type categories and widths
TYPE_MAPPING = {
    # Boolean
    'bool': (EssentialType.CATEGORY_BOOLEAN, 1),
    '_Bool': (EssentialType.CATEGORY_BOOLEAN, 1),
    
    # Character
    'char': (EssentialType.CATEGORY_CHARACTER, 8),
    
    # Signed Integer
    'signed char': (EssentialType.CATEGORY_SIGNED, 8),
    'int8_t': (EssentialType.CATEGORY_SIGNED, 8),
    'short': (EssentialType.CATEGORY_SIGNED, 16),
    'short int': (EssentialType.CATEGORY_SIGNED, 16),
    'signed short': (EssentialType.CATEGORY_SIGNED, 16),
    'int16_t': (EssentialType.CATEGORY_SIGNED, 16),
    'int': (EssentialType.CATEGORY_SIGNED, 32),
    'signed int': (EssentialType.CATEGORY_SIGNED, 32),
    'int32_t': (EssentialType.CATEGORY_SIGNED, 32),
    'long': (EssentialType.CATEGORY_SIGNED, 32),
    'signed long': (EssentialType.CATEGORY_SIGNED, 32),
    'long long': (EssentialType.CATEGORY_SIGNED, 64),
    'signed long long': (EssentialType.CATEGORY_SIGNED, 64),
    'int64_t': (EssentialType.CATEGORY_SIGNED, 64),
    
    # Unsigned Integer
    'unsigned char': (EssentialType.CATEGORY_UNSIGNED, 8),
    'uint8_t': (EssentialType.CATEGORY_UNSIGNED, 8),
    'unsigned short': (EssentialType.CATEGORY_UNSIGNED, 16),
    'uint16_t': (EssentialType.CATEGORY_UNSIGNED, 16),
    'unsigned int': (EssentialType.CATEGORY_UNSIGNED, 32),
    'uint32_t': (EssentialType.CATEGORY_UNSIGNED, 32),
    'unsigned long': (EssentialType.CATEGORY_UNSIGNED, 32),
    'unsigned long long': (EssentialType.CATEGORY_UNSIGNED, 64),
    'uint64_t': (EssentialType.CATEGORY_UNSIGNED, 64),
    
    # Floating Point
    'float': (EssentialType.CATEGORY_FLOATING, 32),
    'double': (EssentialType.CATEGORY_FLOATING, 64),
    'long double': (EssentialType.CATEGORY_FLOATING, 128),
}

def clean_type_name(type_node) -> str:
    if type_node is None:
        return 'int'
    if hasattr(type_node, 'type'):
        return clean_type_name(type_node.type)
    if isinstance(type_node, IdentifierType):
        return " ".join(type_node.names)
    return 'int'

class EssentialTypeEvaluator:
    def __init__(self, var_types, func_return_types):
        self.var_types = var_types
        self.func_return_types = func_return_types

    def get_essential_type(self, type_str: str) -> EssentialType:
        # Match type category and width
        cleaned = type_str.replace("signed", "").replace("unsigned", "").strip()
        is_unsigned_flag = "unsigned" in type_str or "uint" in type_str
        
        # Check direct mapping
        if type_str in TYPE_MAPPING:
            cat, width = TYPE_MAPPING[type_str]
            return EssentialType(cat, width)
            
        # Heuristics for pointer types
        if "*" in type_str:
            # Pointers are treated as unsigned/address types in C, but in MISRA they represent their own category.
            # For simplicity in assignments, we can map them to 32/64 bit address width.
            return EssentialType(EssentialType.CATEGORY_UNSIGNED, 64)

        if is_unsigned_flag:
            return EssentialType(EssentialType.CATEGORY_UNSIGNED, 32)
        return EssentialType(EssentialType.CATEGORY_SIGNED, 32)

    def evaluate(self, node) -> EssentialType:
        """
        Evaluate the essential type of an expression node.
        """
        if node is None:
            return EssentialType(EssentialType.CATEGORY_SIGNED, 32)

        if isinstance(node, Cast):
            t_str = clean_type_name(node.to_type)
            return self.get_essential_type(t_str)

        if isinstance(node, ID):
            t_str = self.var_types.get(node.name, 'int')
            return self.get_essential_type(t_str)

        if isinstance(node, FuncCall):
            if isinstance(node.name, ID):
                t_str = self.func_return_types.get(node.name.name, 'int')
                return self.get_essential_type(t_str)
            return EssentialType(EssentialType.CATEGORY_SIGNED, 32)

        if isinstance(node, Constant):
            if node.type == 'int':
                val_str = str(node.value).lower()
                # Determine category and width from suffix
                if 'u' in val_str:
                    width = 64 if 'll' in val_str or 'l' in val_str else 32
                    return EssentialType(EssentialType.CATEGORY_UNSIGNED, width)
                else:
                    # Check if constant fits in char/short (MISRA exception for constant initializers)
                    try:
                        val = int(node.value, 0)
                        if -128 <= val <= 127:
                            return EssentialType(EssentialType.CATEGORY_SIGNED, 8)
                        elif -32768 <= val <= 32767:
                            return EssentialType(EssentialType.CATEGORY_SIGNED, 16)
                    except ValueError:
                        pass
                    return EssentialType(EssentialType.CATEGORY_SIGNED, 32)
            elif node.type == 'double':
                val_str = str(node.value).lower()
                width = 32 if val_str.endswith('f') else 64
                return EssentialType(EssentialType.CATEGORY_FLOATING, width)
            elif node.type == 'char':
                return EssentialType(EssentialType.CATEGORY_CHARACTER, 8)

        # Binary operations (Integer Promotions)
        if hasattr(node, 'left') and hasattr(node, 'right'):
            t_left = self.evaluate(node.left)
            t_right = self.evaluate(node.right)
            
            # Category rules:
            # If both are floating, result is floating
            # If one is floating, result is floating
            # If they are different categories, we use the wider one
            cat = t_left.category
            if t_left.category == EssentialType.CATEGORY_FLOATING or t_right.category == EssentialType.CATEGORY_FLOATING:
                cat = EssentialType.CATEGORY_FLOATING
            elif t_left.category != t_right.category:
                # Promotion of mixed types (e.g. signed and unsigned)
                if t_left.category == EssentialType.CATEGORY_UNSIGNED or t_right.category == EssentialType.CATEGORY_UNSIGNED:
                    cat = EssentialType.CATEGORY_UNSIGNED
            
            # Width rule (integer promotions):
            # In C, integer operations promote types narrower than 32-bit to 32-bit.
            width = max(t_left.width, t_right.width)
            if width < 32 and cat in (EssentialType.CATEGORY_SIGNED, EssentialType.CATEGORY_UNSIGNED):
                width = 32 # promoted to int width
                
            return EssentialType(cat, width)

        if hasattr(node, 'expr'):
            return self.evaluate(node.expr)

        return EssentialType(EssentialType.CATEGORY_SIGNED, 32)

class EssentialTypeVisitor(NodeVisitor):
    def __init__(self, rule, source_lines, file_name):
        self.rule = rule
        self.source_lines = source_lines
        self.file_name = file_name
        self.violations = []
        self.var_types = {}
        self.func_return_types = {}
        self.current_function = None

    def visit_FuncDef(self, node):
        func_name = node.decl.name
        ret_type = clean_type_name(node.decl.type.type)
        self.func_return_types[func_name] = ret_type
        
        prev_func = self.current_function
        self.current_function = func_name
        
        # Parameters
        if node.decl.type and hasattr(node.decl.type, 'args') and node.decl.type.args:
            for p in node.decl.type.args.params or []:
                if p.name:
                    p_type = clean_type_name(p.type)
                    self.var_types[p.name] = p_type
                    
        self.generic_visit(node)
        self.current_function = prev_func

    def visit_Decl(self, node):
        # Record variable type
        if node.name and not isinstance(node.type, type(None)):
            if node.type.__class__.__name__ != 'FuncDecl':
                v_type = clean_type_name(node.type)
                self.var_types[node.name] = v_type
                
                # Check for narrowing in initialization
                if node.init and not isinstance(node.init, Cast):
                    evaluator = EssentialTypeEvaluator(self.var_types, self.func_return_types)
                    lhs_type = evaluator.get_essential_type(v_type)
                    rhs_type = evaluator.evaluate(node.init)
                    
                    # Narrowing assignment violation
                    # 1. RHS width is greater than LHS width
                    # 2. Or, different categories (e.g. signed vs unsigned)
                    if (rhs_type.width > lhs_type.width) or (rhs_type.category != lhs_type.category):
                        # Special check: allow constant integer values to assign to narrow types if they fit
                        fits = False
                        if isinstance(node.init, Constant) and node.init.type in ('int', 'char') and lhs_type.category in (EssentialType.CATEGORY_SIGNED, EssentialType.CATEGORY_UNSIGNED, EssentialType.CATEGORY_CHARACTER):
                            try:
                                val = int(node.init.value, 0) if node.init.type == 'int' else (ord(node.init.value.strip("'")[0]) if len(node.init.value.strip("'")) > 0 else 0)
                                if lhs_type.category in (EssentialType.CATEGORY_SIGNED, EssentialType.CATEGORY_CHARACTER):
                                    if lhs_type.width == 8 and -128 <= val <= 127: fits = True
                                    elif lhs_type.width == 16 and -32768 <= val <= 32767: fits = True
                                elif lhs_type.category == EssentialType.CATEGORY_UNSIGNED:
                                    if lhs_type.width == 8 and 0 <= val <= 255: fits = True
                                    elif lhs_type.width == 16 and 0 <= val <= 65535: fits = True
                            except ValueError:
                                pass
                        if fits:
                            self.generic_visit(node)
                            return

                        line = CParserService.adjust_line(node.coord.line) if node.coord else 1
                        col = node.coord.column if node.coord else 1
                        snippet = self.source_lines[line - 1].strip() if line - 1 < len(self.source_lines) else ""
                        
                        init_text = snippet.split("=")[-1]
                        comment = ""
                        if "/*" in init_text:
                            c_idx = init_text.find("/*")
                            comment = " " + init_text[c_idx:].strip()
                            init_text = init_text[:c_idx]
                        elif "//" in init_text:
                            c_idx = init_text.find("//")
                            comment = " " + init_text[c_idx:].strip()
                            init_text = init_text[:c_idx]
                        init_expr = init_text.strip().rstrip(";")
                        
                        lhs_decl = snippet.split("=")[0].strip()
                        suggested_fix = f"{lhs_decl} = ({v_type}){init_expr};{comment}"
                        
                        self.violations.append(RuleViolation(
                            rule_number=self.rule.rule_number,
                            rule_name=self.rule.rule_name,
                            severity=self.rule.severity,
                            category=self.rule.category,
                            file=self.file_name,
                            line=line,
                            column=col,
                            message=f"Implicit conversion from '{rhs_type}' to narrower/different '{lhs_type}'.",
                            code_snippet=snippet,
                            reason=f"The variable '{node.name}' of essential type '{lhs_type}' is initialized with an expression of type '{rhs_type}' which is wider or has a different category. To comply with MISRA Rule 10.3, an explicit cast is required.",
                            suggested_fix=suggested_fix,
                            confidence=1.0
                        ))
                            
        self.generic_visit(node)

    def visit_Assignment(self, node):
        self.generic_visit(node)
        
        # Check for narrowing in assignment
        if isinstance(node.lvalue, ID) and not isinstance(node.rvalue, Cast):
            var_name = node.lvalue.name
            v_type = self.var_types.get(var_name)
            
            if v_type:
                evaluator = EssentialTypeEvaluator(self.var_types, self.func_return_types)
                lhs_type = evaluator.get_essential_type(v_type)
                rhs_type = evaluator.evaluate(node.rvalue)
                
                if (rhs_type.width > lhs_type.width) or (rhs_type.category != lhs_type.category):
                    # Special check: allow constant integer values to assign to narrow types if they fit
                    if isinstance(node.rvalue, Constant) and node.rvalue.type in ('int', 'char') and lhs_type.category in (EssentialType.CATEGORY_SIGNED, EssentialType.CATEGORY_UNSIGNED, EssentialType.CATEGORY_CHARACTER):
                        try:
                            val = int(node.rvalue.value, 0) if node.rvalue.type == 'int' else (ord(node.rvalue.value.strip("'")[0]) if len(node.rvalue.value.strip("'")) > 0 else 0)
                            if lhs_type.category in (EssentialType.CATEGORY_SIGNED, EssentialType.CATEGORY_CHARACTER):
                                if lhs_type.width == 8 and -128 <= val <= 127: return
                                if lhs_type.width == 16 and -32768 <= val <= 32767: return
                            elif lhs_type.category == EssentialType.CATEGORY_UNSIGNED:
                                if lhs_type.width == 8 and 0 <= val <= 255: return
                                if lhs_type.width == 16 and 0 <= val <= 65535: return
                        except ValueError:
                            pass

                    line = CParserService.adjust_line(node.coord.line) if node.coord else 1
                    col = node.coord.column if node.coord else 1
                    snippet = self.source_lines[line - 1].strip() if line - 1 < len(self.source_lines) else ""
                    
                    parts = snippet.split("=")
                    if len(parts) >= 2:
                        lhs_part = parts[0]
                        rhs_part = "=".join(parts[1:])
                        comment = ""
                        if "/*" in rhs_part:
                            c_idx = rhs_part.find("/*")
                            comment = " " + rhs_part[c_idx:].strip()
                            rhs_part = rhs_part[:c_idx]
                        elif "//" in rhs_part:
                            c_idx = rhs_part.find("//")
                            comment = " " + rhs_part[c_idx:].strip()
                            rhs_part = rhs_part[:c_idx]
                        rhs_expr = rhs_part.strip().rstrip(";")
                        suggested_fix = f"{lhs_part}= ({v_type}){rhs_expr};{comment}"
                    else:
                        suggested_fix = f"{var_name} = ({v_type}){snippet.split('=')[-1].strip()}"
                        
                    self.violations.append(RuleViolation(
                        rule_number=self.rule.rule_number,
                        rule_name=self.rule.rule_name,
                        severity=self.rule.severity,
                        category=self.rule.category,
                        file=self.file_name,
                        line=line,
                        column=col,
                        message=f"Implicit conversion from '{rhs_type}' to narrower/different '{lhs_type}'.",
                        code_snippet=snippet,
                        reason=f"Assigning an expression of essential type '{rhs_type}' to variable '{var_name}' of narrower/different essential type '{lhs_type}' requires an explicit cast to comply with MISRA Rule 10.3.",
                        suggested_fix=suggested_fix,
                        confidence=1.0
                    ))

    def visit_Return(self, node):
        self.generic_visit(node)
        
        # Check for narrowing in return statements
        if node.expr and self.current_function and not isinstance(node.expr, Cast):
            ret_type = self.func_return_types.get(self.current_function)
            if ret_type and ret_type != 'void':
                evaluator = EssentialTypeEvaluator(self.var_types, self.func_return_types)
                lhs_type = evaluator.get_essential_type(ret_type)
                rhs_type = evaluator.evaluate(node.expr)
                
                if (rhs_type.width > lhs_type.width) or (rhs_type.category != lhs_type.category):
                    line = CParserService.adjust_line(node.coord.line) if node.coord else 1
                    col = node.coord.column if node.coord else 1
                    snippet = self.source_lines[line - 1].strip() if line - 1 < len(self.source_lines) else ""
                    
                    match = re.search(r"return\s+(.+);", snippet)
                    if match:
                        expr_str = match.group(1)
                        suggested_fix = f"return ({ret_type}){expr_str};"
                    else:
                        suggested_fix = f"return ({ret_type}){snippet.replace('return', '').strip()}"
                        
                    self.violations.append(RuleViolation(
                        rule_number=self.rule.rule_number,
                        rule_name=self.rule.rule_name,
                        severity=self.rule.severity,
                        category=self.rule.category,
                        file=self.file_name,
                        line=line,
                        column=col,
                        message=f"Implicit conversion in return from '{rhs_type}' to '{lhs_type}'.",
                        code_snippet=snippet,
                        reason=f"Function '{self.current_function}' returns type '{ret_type}' (essential type '{lhs_type}'), but the return statement evaluates to type '{rhs_type}' without a cast, violating MISRA Rule 10.3.",
                        suggested_fix=suggested_fix,
                        confidence=1.0
                    ))

class Rule_10_3(BaseRule):
    @property
    def rule_number(self) -> str:
        return "10.3"

    @property
    def rule_name(self) -> str:
        return "Implicit narrowing conversion"

    @property
    def severity(self) -> str:
        return "Required"

    @property
    def category(self) -> str:
        return "Types"

    @property
    def description(self) -> str:
        return "The value of an expression shall not be assigned to an object with a narrower essential type or of a different essential type category without an explicit cast."

    def analyze(self, ast, source_code: str, file_name: str) -> list[RuleViolation]:
        source_lines = source_code.splitlines()
        visitor = EssentialTypeVisitor(self, source_lines, file_name)
        visitor.visit(ast)
        return visitor.violations

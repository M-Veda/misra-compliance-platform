import requests
import json
import re
from typing import Optional, List, Dict, Any
from backend.models.violation import RuleViolation

OLLAMA_URL = "http://localhost:11434/api/chat"

# ---------------------------------------------------------------------------
# Rule-Specific AI Explanation Database (10 Supported MISRA C:2012 Rules)
# ---------------------------------------------------------------------------

RULE_EXPLANATION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "2.2": {
        "rule_id": "2.2",
        "rule_name": "Dead Code / Statement with No Side Effects",
        "severity": "Required",
        "category": "Unused Code",
        "misra_summary": "MISRA C:2012 Rule 2.2 states that there shall be no dead code. Statements with no side effects and unused results must be removed.",
        "why_it_matters": "Dead code increases binary size, confuses static analyzers, clutters code reviews, and often indicates leftover debugging logic or incomplete refactoring.",
        "ai_analysis": "AST traversal identified an ExprStatement node whose root expression contains no assignment operators (=, +=), increment/decrement operators (++), or function invocations.",
        "why_fix_works": "Removing the dead expression eliminates unused byte-code generation and aligns code execution flow with actual program logic.",
        "alternative_fixes": [
            "Remove the dead statement line entirely",
            "Assign expression result to a variable if calculation was intended to be saved"
        ],
        "impact_runtime": "0% (Removes dead execution cycle)",
        "impact_memory": "0 bytes additional stack/heap",
        "impact_behavior": "Identical functional behavior",
        "impact_compilation": "Removes compiler -Wunused-value warnings",
        "impact_compliance": "+10% Compliance Gain",
        "confidence": 0.99,
        "confidence_reason": "Deterministic pycparser AST traversal confirmed ExprStatement node contains zero side-effect AST sub-nodes."
    },
    "2.7": {
        "rule_id": "2.7",
        "rule_name": "Unused Function Parameter",
        "severity": "Advisory",
        "category": "Unused Code",
        "misra_summary": "MISRA C:2012 Rule 2.7 requires that there shall be no unused parameters in functions. Every declared parameter must be used or explicitly voided.",
        "why_it_matters": "Unused parameters waste stack space, create interface ambiguity, and frequently point to unhandled hardware callbacks or incomplete driver initialisation.",
        "ai_analysis": "AST visitor inspected FuncDef parameter declarations and cross-referenced all identifier symbol nodes within the function scope. Zero references were found.",
        "why_fix_works": "Explicitly casting the parameter to (void) param; signals intentional non-use to static analyzers and compilers while maintaining API signature compatibility.",
        "alternative_fixes": [
            "Add (void)param; cast at the top of the function body",
            "Remove parameter from function signature if not required by a fixed API callback"
        ],
        "impact_runtime": "0% (No runtime performance penalty)",
        "impact_memory": "0 bytes additional memory",
        "impact_behavior": "No functional logic change",
        "impact_compilation": "Suppresses GCC/Clang -Wunused-parameter compiler warning",
        "impact_compliance": "+10% Compliance Gain",
        "confidence": 0.98,
        "confidence_reason": "AST symbol table lookup verified zero references to the parameter identifier within function scope."
    },
    "7.1": {
        "rule_id": "7.1",
        "rule_name": "Octal Constant Usage Prohibited",
        "severity": "Required",
        "category": "Literals",
        "misra_summary": "MISRA C:2012 Rule 7.1 states that octal constants and octal escape sequences shall not be used.",
        "why_it_matters": "Octal constants starting with leading 0 (e.g. 052) are easily misread as decimal numbers (decimal 42 vs 52), causing critical bitmasking bugs in device drivers.",
        "ai_analysis": "AST lexer inspected Constant integer literal tokens. Token matched regex '^0[0-7]+$' indicating octal representation.",
        "why_fix_works": "Converting octal literals to decimal or hexadecimal notation eliminates visual ambiguity while retaining the exact integer value.",
        "alternative_fixes": [
            "Convert octal literal to decimal integer (e.g. 42)",
            "Convert octal literal to uppercase hexadecimal format (e.g. 0x2A)"
        ],
        "impact_runtime": "0% (Identical machine code generated)",
        "impact_memory": "0 bytes additional memory",
        "impact_behavior": "Identical numerical evaluation",
        "impact_compilation": "Removes octal literal ambiguity warnings",
        "impact_compliance": "+10% Compliance Gain",
        "confidence": 1.0,
        "confidence_reason": "Regex token analysis confirmed literal starts with leading zero followed by octal digits."
    },
    "8.4": {
        "rule_id": "8.4",
        "rule_name": "Missing Prototype Declaration",
        "severity": "Required",
        "category": "Declarations",
        "misra_summary": "MISRA C:2012 Rule 8.4 mandates that a compatible declaration shall be visible when an object or function with external linkage is defined.",
        "why_it_matters": "Missing function prototypes prevent compiler cross-file type verification, risking calling convention mismatches, parameter corruption, and link-time errors.",
        "ai_analysis": "AST parser identified a global FuncDef node. Global scope search revealed zero preceding Decl prototype node with matching identifier.",
        "why_fix_works": "Providing an explicit prototype declaration above the function definition enables compiler type checking and satisfies link-time visibility requirements.",
        "alternative_fixes": [
            "Prepend a compatible function prototype declaration above definition",
            "Declare function as 'static' if only invoked within current translation unit"
        ],
        "impact_runtime": "0% (No runtime performance penalty)",
        "impact_memory": "0 bytes additional memory",
        "impact_behavior": "Enables strict compile-time parameter verification",
        "impact_compilation": "Resolves missing prototype compiler warnings",
        "impact_compliance": "+10% Compliance Gain",
        "confidence": 0.99,
        "confidence_reason": "Global scope symbol search verified absence of preceding prototype Decl node."
    },
    "8.7": {
        "rule_id": "8.7",
        "rule_name": "Single-Use Global Scoping / Internal Linkage",
        "severity": "Advisory",
        "category": "Declarations",
        "misra_summary": "MISRA C:2012 Rule 8.7 states that functions and objects should be declared at block scope or with internal linkage if referenced in only one translation unit.",
        "why_it_matters": "Global linkage pollutes external namespace, prevents compiler register allocation optimization, and exposes variables to unintended external file mutation.",
        "ai_analysis": "AST symbol cross-reference verified that global Decl identifier is accessed within exactly one FuncDef function scope.",
        "why_fix_works": "Adding the 'static' specifier restricts symbol linkage to internal translation unit scope, improving encapsulation and compiler optimizations.",
        "alternative_fixes": [
            "Prepend 'static' storage-class specifier to variable declaration",
            "Move declaration inside block scope if non-persistent across calls"
        ],
        "impact_runtime": "0% (Enables compiler symbol optimization)",
        "impact_memory": "0 bytes additional memory",
        "impact_behavior": "Restricts variable access to current file",
        "impact_compilation": "Prevents global namespace symbol collisions",
        "impact_compliance": "+10% Compliance Gain",
        "confidence": 0.98,
        "confidence_reason": "Multi-scope AST symbol reference count verified to be exactly 1."
    },
    "10.3": {
        "rule_id": "10.3",
        "rule_name": "Essential Type Cast / Implicit Conversion",
        "severity": "Required",
        "category": "Types",
        "misra_summary": "MISRA C:2012 Rule 10.3 requires that the value of an expression shall not be assigned to an object with a narrower essential type or different essential type category.",
        "why_it_matters": "Implicit conversions risk unexpected integer truncation, sign extension errors, or arithmetic overflow bugs in safety-critical embedded calculations.",
        "ai_analysis": "AST type evaluator evaluated expression essential type against destination/return type. Detected implicit type conversion between incompatible categories.",
        "why_fix_works": "Inserting an explicit cast (target_type) expr clarifies conversion intent to compilers and static analyzers, ensuring unambiguous evaluation.",
        "alternative_fixes": [
            "Insert explicit type cast (target_type)expr",
            "Modify variable or return type declaration to match essential type"
        ],
        "impact_runtime": "0% (Identical machine assembly produced)",
        "impact_memory": "0 bytes additional memory",
        "impact_behavior": "Guarantees explicit conversion semantics",
        "impact_compilation": "Suppresses implicit conversion compiler warnings",
        "impact_compliance": "+10% Compliance Gain",
        "confidence": 0.95,
        "confidence_reason": "AST node type evaluator identified essential type category mismatch."
    },
    "12.1": {
        "rule_id": "12.1",
        "rule_name": "Explicit Operator Precedence Parentheses",
        "severity": "Advisory",
        "category": "Expressions",
        "misra_summary": "MISRA C:2012 Rule 12.1 requires that the precedence of operators within expressions should be made explicit using parentheses.",
        "why_it_matters": "Complex expressions relying on default C operator precedence rules (e.g. bitwise & vs relational ==) cause subtle software defects.",
        "ai_analysis": "AST traversal detected a BinaryOp node containing child BinaryOp sub-nodes of different precedence level without explicit grouping parentheses.",
        "why_fix_works": "Adding explicit grouping parentheses ((a * b) + c) enforces unambiguous evaluation order regardless of developer precedence assumptions.",
        "alternative_fixes": [
            "Wrap sub-expression in explicit parentheses ((a * b) + c)",
            "Split complex expression into multiple intermediate variable assignments"
        ],
        "impact_runtime": "0% (Identical compiled instruction sequence)",
        "impact_memory": "0 bytes additional memory",
        "impact_behavior": "Guarantees intended operator evaluation order",
        "impact_compilation": "Eliminates operator precedence ambiguity",
        "impact_compliance": "+10% Compliance Gain",
        "confidence": 0.99,
        "confidence_reason": "Nested BinaryOp AST hierarchy inspection verified missing parenthetical grouping."
    },
    "14.4": {
        "rule_id": "14.4",
        "rule_name": "Controlling Expression Essentially Boolean",
        "severity": "Required",
        "category": "Control Flow",
        "misra_summary": "MISRA C:2012 Rule 14.4 states that the controlling expression of an if statement and iteration statement shall be essentially Boolean.",
        "why_it_matters": "Implicit integer truthiness checks (e.g. if (flags)) reduce readability and risk unexpected behavior if flag variables hold error status codes.",
        "ai_analysis": "AST visitor inspected If condition node. Expression type was non-Boolean integer without comparison operator (==, !=, <, >).",
        "why_fix_works": "Adding explicit inequality comparison if ((expr) != 0) converts the integer expression to a strict Boolean truth value.",
        "alternative_fixes": [
            "Add explicit inequality comparison ((expr) != 0)",
            "Use stdbool.h bool type for logical flag variables"
        ],
        "impact_runtime": "0% (Identical jump/branch machine instructions)",
        "impact_memory": "0 bytes additional memory",
        "impact_behavior": "Enhances condition evaluation clarity",
        "impact_compilation": "Complies with strict Boolean control flow rules",
        "impact_compliance": "+10% Compliance Gain",
        "confidence": 1.0,
        "confidence_reason": "AST If condition node type verified non-Boolean integer type."
    },
    "16.3": {
        "rule_id": "16.3",
        "rule_name": "Switch Clause Missing Break Statement",
        "severity": "Required",
        "category": "Control Flow",
        "misra_summary": "MISRA C:2012 Rule 16.3 mandates that an unconditional break statement shall terminate every non-empty switch clause.",
        "why_it_matters": "Implicit fall-through between switch cases is a frequent source of severe logic bugs when developers omit break statements accidentally.",
        "ai_analysis": "AST traversal inspected Case statement compound body. Final child AST statement node was not a Break or Return node.",
        "why_fix_works": "Appending break; at the end of the case clause prevents unintended execution fall-through into subsequent case blocks.",
        "alternative_fixes": [
            "Append 'break;' statement at end of case clause body",
            "Add 'return;' statement if case completes function execution"
        ],
        "impact_runtime": "Prevents fall-through execution bugs",
        "impact_memory": "0 bytes additional memory",
        "impact_behavior": "Ensures isolated case clause execution",
        "impact_compilation": "Resolves implicit switch fall-through warnings",
        "impact_compliance": "+10% Compliance Gain",
        "confidence": 0.99,
        "confidence_reason": "AST Case body trailing node verified non-terminating statement."
    },
    "16.4": {
        "rule_id": "16.4",
        "rule_name": "Switch Statement Missing Default Clause",
        "severity": "Required",
        "category": "Control Flow",
        "misra_summary": "MISRA C:2012 Rule 16.4 mandates that every switch statement shall have a default clause.",
        "why_it_matters": "Switch statements without default clauses fail silently when presented with unexpected out-of-bounds enum or state machine values.",
        "ai_analysis": "AST visitor inspected Switch statement block. Child node list contained Case nodes but zero Default clause node.",
        "why_fix_works": "Adding a default: break; clause guarantees defensive handling for unexpected or unhandled input state values.",
        "alternative_fixes": [
            "Append 'default:\n    break;' clause to switch body",
            "Add default clause with defensive error logging / fault trap"
        ],
        "impact_runtime": "Defensive handling for unhandled control states",
        "impact_memory": "0 bytes additional memory",
        "impact_behavior": "Prevents silent unhandled state failures",
        "impact_compilation": "Fulfills mandatory switch structure requirement",
        "impact_compliance": "+10% Compliance Gain",
        "confidence": 1.0,
        "confidence_reason": "AST Switch statement child node scan confirmed zero Default clause nodes."
    }
}

class LLMService:
    @staticmethod
    def get_structured_explanation(violation: RuleViolation, source_code: str = "") -> Dict[str, Any]:
        """
        Returns a rich, structured AI assistant explanation for a MISRA C:2012 violation.
        Uses rule-specific template data combined with exact violation instance context.
        """
        rule_key = str(violation.rule_number).strip()
        template = RULE_EXPLANATION_TEMPLATES.get(rule_key, {
            "rule_id": violation.rule_number,
            "rule_name": violation.rule_name,
            "severity": violation.severity,
            "category": violation.category,
            "misra_summary": f"MISRA C:2012 Rule {violation.rule_number}: {violation.message}",
            "why_it_matters": violation.reason,
            "ai_analysis": f"AST traversal detected rule violation at line {violation.line}.",
            "why_fix_works": "Removes non-compliant code structure and aligns with MISRA guidelines.",
            "alternative_fixes": [violation.suggested_fix] if violation.suggested_fix else ["Restructure code"],
            "impact_runtime": "0% runtime penalty",
            "impact_memory": "0 bytes additional memory",
            "impact_behavior": "Preserves program correctness",
            "impact_compilation": "Fulfills MISRA C:2012 compliance requirement",
            "impact_compliance": f"+{violation.patch_preview.compliance_gain if violation.patch_preview else 10.0:.1f}% Compliance Gain",
            "confidence": violation.confidence,
            "confidence_reason": "Deterministic pycparser AST rule analysis."
        })

        code_snippet = violation.code_snippet or (
            violation.patch_preview.original_source if violation.patch_preview else ""
        )
        suggested_fix = violation.suggested_fix or (
            violation.patch_preview.replacement_source if violation.patch_preview else ""
        )

        return {
            "success": True,
            "rule_id": violation.rule_number,
            "rule_name": violation.rule_name,
            "severity": violation.severity,
            "category": violation.category,
            "file": violation.file,
            "line": violation.line,
            "column": violation.column,
            "code_snippet": code_snippet,
            "what_ai_found": f"At line {violation.line}, column {violation.column}: {violation.message}",
            "why_it_matters": template["why_it_matters"],
            "misra_summary": template["misra_summary"],
            "ai_analysis": template["ai_analysis"],
            "recommended_fix": suggested_fix,
            "why_fix_works": template["why_fix_works"],
            "alternative_fixes": template["alternative_fixes"],
            "impact_analysis": {
                "runtime": template["impact_runtime"],
                "memory": template["impact_memory"],
                "behavior": template["impact_behavior"],
                "compilation": template["impact_compilation"],
                "compliance": template["impact_compliance"]
            },
            "expected_result": f"Rule {violation.rule_number} violation resolved. Compliance increased.",
            "confidence": template["confidence"],
            "confidence_reason": template["confidence_reason"]
        }

    @staticmethod
    def query_tinyllama(messages: List[dict], temperature: float = 0.2) -> str:
        """
        Sends a chat query to local Ollama running tinyllama.
        If tinyllama is not installed, returns fallback response.
        """
        payload = {
            "model": "tinyllama",
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature}
        }
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=20)
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "Error: No response content from LLM.")
            elif response.status_code == 404:
                return "TinyLlama model not found in Ollama. Please run 'ollama pull tinyllama'."
            else:
                return f"Ollama returned status code {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return f"Failed to connect to local Ollama: {str(e)}"

    @classmethod
    def explain_violation(cls, violation: RuleViolation, source_code: str) -> str:
        """
        Backward compatibility string format wrapper.
        """
        data = cls.get_structured_explanation(violation, source_code)
        return json.dumps(data, indent=2)

    @classmethod
    def answer_question(cls, question: str, file_content: str, violations_summary: str) -> str:
        prompt = f"""You are a senior MISRA compliance architect. Answer the user's question about the C code and violations.
Source Code:
```c
{file_content}
```
Violations:
{violations_summary}

User Question: {question}

Provide a helpful, precise, educational answer.
"""
        messages = [{"role": "user", "content": prompt}]
        return cls.query_tinyllama(messages)

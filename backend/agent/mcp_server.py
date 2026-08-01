import sys
import os
# Add parent directory to path to ensure backend modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional
from backend.services.parser import CParserService
from backend.rules import ALL_RULES
from backend.services.llm import LLMService
from backend.services.patch import PatchService
from backend.report.generator import ReportGenerator
from backend.models.violation import RuleViolation

# Create MCP server instance
mcp = FastMCP("MISRAComplianceAgent")

# Store the temporary uploaded file content in memory
# Map of file_name -> content
uploaded_files: Dict[str, str] = {}

@mcp.tool()
def upload_file(file_name: str, content: str) -> Dict[str, Any]:
    """
    Saves a C source file temporarily in memory for analysis.
    """
    uploaded_files[file_name] = content
    return {
        "success": True,
        "message": f"File '{file_name}' uploaded successfully.",
        "file_name": file_name,
        "size_bytes": len(content.encode('utf-8'))
    }

@mcp.tool()
def analyze_code(source_code: str, file_name: str = "source.c") -> Dict[str, Any]:
    """
    Parses a C source file and runs the deterministic rule engine to detect all MISRA C:2012 violations.
    Designed to minimize false positives.
    """
    # 1. Parse AST
    ast, err = CParserService.parse_code(source_code, file_name)
    if err:
        return {
            "success": False,
            "error": err,
            "violations": [],
            "compliance_score": 0.0
        }

    # 2. Run deterministic rule checkers
    all_violations: List[RuleViolation] = []
    for rule in ALL_RULES:
        try:
            violations = rule.analyze(ast, source_code, file_name)
            all_violations.extend(violations)
        except Exception as e:
            # Prevent single rule failure from breaking the analysis
            pass

    # 3. Calculate Compliance Score
    # Score starts at 100%. Each unique rule violated reduces it.
    # We implement: Score = 100 - (unique rules violated * 10). Max deduction is 100.
    violated_rules = set(v.rule_number for v in all_violations)
    compliance_score = max(0.0, 100.0 - (len(violated_rules) * 10.0))

    return {
        "success": True,
        "file_name": file_name,
        "violations": [v.model_dump() for v in all_violations],
        "compliance_score": compliance_score
    }

@mcp.tool()
def detect_rule(rule_number: str, source_code: str, file_name: str = "source.c") -> Dict[str, Any]:
    """
    Runs a single specific MISRA rule check on the source code.
    """
    ast, err = CParserService.parse_code(source_code, file_name)
    if err:
        return {"success": False, "error": err, "violations": []}

    target_rule = next((r for r in ALL_RULES if r.rule_number == rule_number), None)
    if not target_rule:
        return {"success": False, "error": f"Rule {rule_number} is not implemented. Supported rules are: 2.2, 2.7, 7.1, 8.4, 8.7, 10.3, 12.1, 14.4, 16.3, 16.4.", "violations": []}

    violations = target_rule.analyze(ast, source_code, file_name)
    return {
        "success": True,
        "rule_number": rule_number,
        "violations": [v.model_dump() for v in violations]
    }

@mcp.tool()
def explain_violation(
    rule_number: str,
    rule_name: str,
    severity: str,
    message: str,
    code_snippet: str,
    reason: str,
    suggested_fix: str,
    source_code: str
) -> Dict[str, Any]:
    """
    Queries TinyLlama to generate a human-friendly explanation of why the code violates
    the MISRA rule, and why the suggested fix is compliant.
    """
    # Construct a dummy violation object
    violation = RuleViolation(
        rule_number=rule_number,
        rule_name=rule_name,
        severity=severity,
        category="General",
        file="source.c",
        line=1,
        column=1,
        message=message,
        code_snippet=code_snippet,
        reason=reason,
        suggested_fix=suggested_fix,
        confidence=1.0
    )
    explanation = LLMService.explain_violation(violation, source_code)
    return {
        "success": True,
        "explanation": explanation
    }

@mcp.tool()
def generate_patch(
    source_code: str,
    rule_number: str,
    line: int,
    column: int,
    suggested_fix: str,
    message: str = ""
) -> Dict[str, Any]:
    """
    Generates a patch preview for the specified violation without saving to disk.
    Allows users to preview exactly how the file changes before applying.
    """
    violation = RuleViolation(
        rule_number=rule_number,
        rule_name="",
        severity="",
        category="",
        file="",
        line=line,
        column=column,
        message=message,
        code_snippet="",
        reason="",
        suggested_fix=suggested_fix,
        confidence=1.0
    )
    preview = PatchService.generate_preview(source_code, violation, "Accept")
    return {
        "success": True,
        "preview_code": preview
    }

@mcp.tool()
def apply_patch(
    source_code: str,
    rule_number: str,
    line: int,
    column: int,
    suggested_fix: str,
    decision: str,
    manual_code: Optional[str] = None,
    message: str = ""
) -> Dict[str, Any]:
    """
    Applies the patch decision (Accept, Reject, Skip, Manual Fix) to the source code.
    """
    violation = RuleViolation(
        rule_number=rule_number,
        rule_name="",
        severity="",
        category="",
        file="",
        line=line,
        column=column,
        message=message,
        code_snippet="",
        reason="",
        suggested_fix=suggested_fix,
        confidence=1.0
    )
    modified = PatchService.generate_preview(source_code, violation, decision, manual_code)
    return {
        "success": True,
        "modified_code": modified
    }

@mcp.tool()
def generate_report(
    file_name: str,
    original_code: str,
    corrected_code: str,
    violations: List[Dict[str, Any]],
    decisions: Dict[str, str],
    compliance_score: float
) -> Dict[str, Any]:
    """
    Generates a structured compliance report in JSON format.
    """
    violation_objs = [RuleViolation(**v) for v in violations]
    report = ReportGenerator.generate_json_report(
        file_name=file_name,
        original_code=original_code,
        corrected_code=corrected_code,
        violations=violation_objs,
        decisions=decisions,
        compliance_score=compliance_score
    )
    return {
        "success": True,
        "report": report
    }

@mcp.tool()
def export_pdf(
    file_name: str,
    violations: List[Dict[str, Any]],
    decisions: Dict[str, str],
    compliance_score: float,
    corrected_code: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Generates and saves a high-quality PDF compliance report to the local filesystem.
    """
    violation_objs = [RuleViolation(**v) for v in violations]
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        ReportGenerator.generate_pdf_report(
            file_name=file_name,
            violations=violation_objs,
            decisions=decisions,
            compliance_score=compliance_score,
            corrected_code=corrected_code,
            output_path=output_path
        )
        return {
            "success": True,
            "message": f"PDF report exported to {output_path}",
            "file_path": output_path
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to export PDF: {str(e)}"
        }

if __name__ == "__main__":
    # Start FastMCP server using stdio transport
    mcp.run("stdio")

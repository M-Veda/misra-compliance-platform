from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import hashlib
import re

# ---------------------------------------------------------------------------
# Stable violation ID helper — location-independent, semantic-content-based
# ---------------------------------------------------------------------------

def generate_stable_id(
    rule_number: str,
    ast_node_type: str,
    scope_name: str,
    snippet: str,
) -> str:
    """
    Compute a location-independent stable ID for a violation.

    Format:  {rule_number}_{ast_node_type}_{scope_name}_{sha256_8chars}

    The sha256 is taken over the *normalized* snippet (whitespace collapsed,
    leading/trailing stripped) so that minor re-indentation after patches
    does not change the ID.

    Examples
    --------
    Rule 14.4 violation inside function 'main' on an 'If' node:
        "14_4_If_main_a3f9c12d"

    Rule 2.2 dead code at global scope:
        "2_2_Decl___global___b74e3a11"
    """
    # Normalise snippet: collapse all whitespace sequences to a single space
    normalised = re.sub(r'\s+', ' ', snippet.strip())
    digest = hashlib.sha256(normalised.encode('utf-8', errors='replace')).hexdigest()[:8]
    # Sanitise each component so the ID is filesystem-safe
    safe_rule   = rule_number.replace('.', '_')
    safe_node   = re.sub(r'[^A-Za-z0-9_]', '_', ast_node_type)
    safe_scope  = re.sub(r'[^A-Za-z0-9_]', '_', scope_name) if scope_name else '__global__'
    return f"{safe_rule}_{safe_node}_{safe_scope}_{digest}"


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------

from enum import Enum

class PatchType(str, Enum):
    AUTO_PATCH = "AUTO_PATCH"
    TEMPLATE_PATCH = "TEMPLATE_PATCH"
    AI_SUGGESTED_PATCH = "AI_SUGGESTED_PATCH"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"

class PatchPreview(BaseModel):
    # Mandatory 17 Fields
    violation_id: str = ""
    rule_number: str = ""
    file: str = ""
    line: int = 1
    column: int = 1
    original_start_line: int = 1
    original_end_line: int = 1
    original_source: str = ""
    replacement_source: str = ""
    unified_diff: str = ""
    explanation: str = ""
    confidence: float = 1.0
    patch_type: PatchType = PatchType.AUTO_PATCH
    applies_cleanly: bool = True
    can_autopatch: bool = True
    affected_lines: List[int] = Field(default_factory=list)
    compliance_gain: float = 10.0

    # Fields for backward compatibility and extra metadata
    rule_name: str = ""
    original_snippet: str = ""
    proposed_snippet: str = ""
    diff: str = ""
    expected_compliance_improvement: float = 10.0
    no_patch_reason: str = ""

class RuleViolation(BaseModel):
    rule_number: str = Field(..., description="The MISRA rule number, e.g., '2.2'")
    rule_name: str = Field(..., description="The name of the MISRA rule")
    severity: str = Field(..., description="Severity level: Mandatory, Required, or Advisory")
    category: str = Field(..., description="Category of the rule")
    file: str = Field(..., description="Name of the file containing the violation")
    line: int = Field(..., description="1-based line number in the source file")
    column: int = Field(..., description="1-based column number in the source file")
    message: str = Field(..., description="Detailed diagnostic message")
    code_snippet: str = Field(..., description="The offending code snippet")
    reason: str = Field(..., description="Explanation of why this violates the rule")
    suggested_fix: str = Field(..., description="A code replacement snippet to fix the violation")
    confidence: float = Field(1.0, description="Confidence score of the detector (1.0 for deterministic)")

    # Semantic AST context & exact AST node range coordinates
    ast_node_type: str = Field("Unknown", description="AST node type (e.g. If, While, Decl, FuncDef)")
    scope_name: str = Field("__global__", description="Enclosing function/scope name")
    ast_start_line: int = Field(1, description="1-based start line of AST node range")
    ast_end_line: int = Field(1, description="1-based end line of AST node range")
    ast_start_col: int = Field(1, description="1-based start column of AST node range")
    ast_end_col: int = Field(1, description="1-based end column of AST node range")

    # Structured preview object attached to every violation
    patch_preview: Optional[PatchPreview] = None
    stable_id: Optional[str] = Field(None, description="Location-independent stable identifier")

    def model_post_init(self, __context: Any) -> None:
        if not self.stable_id:
            self.stable_id = generate_stable_id(
                rule_number=self.rule_number,
                ast_node_type=self.ast_node_type,
                scope_name=self.scope_name,
                snippet=self.code_snippet,
            )


class AnalysisResult(BaseModel):
    file_name: str
    source_code: str
    violations: List[RuleViolation]
    compliance_score: float

class PatchRequest(BaseModel):
    source_code: str
    violation: RuleViolation
    decision: str  # 'Accept', 'Reject', 'Skip', 'Manual'
    manual_code: Optional[str] = None

class PatchResponse(BaseModel):
    success: bool
    modified_code: str
    can_autopatch: bool = True
    patch_actually_changed: bool = False
    no_patch_reason: str = ""
    error: Optional[str] = None
    patch_preview: Optional[PatchPreview] = None


class BulkPatchRequest(BaseModel):
    source_code: str
    violations: List[RuleViolation]

class BulkPatchResponse(BaseModel):
    success: bool
    modified_code: str
    ops_applied: int = 0
    ops_skipped_already_applied: int = 0
    ops_rejected_validation: int = 0
    ops_rejected_overlap: int = 0
    parse_valid: bool = True
    conflicts: List[str] = []
    error: Optional[str] = None

class ReportRequest(BaseModel):
    file_name: str
    original_code: str
    corrected_code: str
    violations: List[RuleViolation]
    decisions: Dict[str, str] = {}  # Map of violation stable_id -> decision ('Accept', 'Reject', etc.)
    remaining_violations_count: int = 0
    compliance_score: float

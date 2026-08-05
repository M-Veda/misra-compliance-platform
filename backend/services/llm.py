"""
Lightweight Backend LLM Orchestration Layer.
Communicates exclusively via Model Context Protocol (MCP) Client.
Contains zero direct REST dependencies, model names, prompt strings, or Ollama URLs.
"""

import json
from typing import Dict, Any, Optional
from backend.models.violation import RuleViolation
from backend.mcp.client import MCPClient

# Centralized singleton MCP Client instance
_mcp_client = MCPClient()

class LLMService:
    """
    Lightweight orchestration service for FastAPI backend.
    Delegates AI capabilities (explanations, Q&A, patch reviews) to the MCP Client.
    """
    @classmethod
    def get_structured_explanation(cls, violation: RuleViolation, source_code: str = "") -> Dict[str, Any]:
        """
        Requests MISRA violation explanation via MCP Client tool 'generate_misra_explanation'.
        """
        violation_dict = {
            "rule_number": violation.rule_number,
            "rule_name": violation.rule_name,
            "severity": violation.severity,
            "category": violation.category,
            "file": violation.file,
            "line": violation.line,
            "column": violation.column,
            "message": violation.message,
            "reason": violation.reason,
            "code_snippet": violation.code_snippet or (
                violation.patch_preview.original_source if violation.patch_preview else ""
            ),
            "suggested_fix": violation.suggested_fix or (
                violation.patch_preview.replacement_source if violation.patch_preview else ""
            )
        }

        # Delegate exclusively to MCP Client tool execution
        return _mcp_client.generate_misra_explanation(
            violation_data=violation_dict,
            source_code=source_code
        )

    @classmethod
    def explain_violation(cls, violation: RuleViolation, source_code: str) -> str:
        """
        Backward compatibility string format wrapper around MCP response.
        """
        data = cls.get_structured_explanation(violation, source_code)
        return json.dumps(data, indent=2)

    @classmethod
    def answer_question(cls, question: str, file_content: str, violations_summary: str) -> str:
        """
        Requests code Q&A response via MCP Client tool 'answer_code_question'.
        """
        res = _mcp_client.answer_code_question(
            question=question,
            file_content=file_content,
            violations_summary=violations_summary
        )
        if res.get("success"):
            return res.get("answer", "")
        else:
            return res.get("answer", f"MCP AI Error: {res.get('error')}")

"""
Centralized Prompt Management Layer for MCP AI Capabilities.
Loads standards-based Markdown prompt templates dynamically from mcp_server/prompts/
and formats them with runtime context parameters.
"""

import os
import logging
from typing import Dict, Any

logger = logging.getLogger("mcp_prompt_manager")

class PromptManager:
    """
    Centralized prompt manager responsible for template loading,
    variable interpolation, and standards-based system prompt management.
    """
    SYSTEM_PROMPT_EXPERT = (
        "You are an expert ISO 26262 / DO-178C Safety-Critical C Systems Engineer "
        "and MISRA C:2012 Compliance Auditor. Respond strictly with valid JSON."
    )
    SYSTEM_PROMPT_QA = (
        "You are an expert MISRA C:2012 Safety-Critical C Engineering Assistant. "
        "Provide direct, technical, and accurate answers."
    )

    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            templates_dir = os.path.join(os.path.dirname(__file__), "prompts")
        self.templates_dir = os.path.abspath(templates_dir)
        self._cache: Dict[str, str] = {}

    def get_template(self, template_name: str) -> str:
        """
        Loads a markdown prompt template file by name.
        """
        if template_name in self._cache:
            return self._cache[template_name]

        filename = f"{template_name}.md" if not template_name.endswith(".md") else template_name
        filepath = os.path.join(self.templates_dir, filename)

        if not os.path.exists(filepath):
            logger.error(f"Prompt template file not found: {filepath}")
            raise FileNotFoundError(f"Prompt template file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        self._cache[template_name] = content
        return content

    def build_misra_explanation_prompt(self, violation_data: Dict[str, Any], source_code: str = "") -> str:
        """
        Builds a structured MISRA violation explanation prompt from template.
        """
        template = self.get_template("misra_explanation")
        return template.format(
            rule_number=violation_data.get("rule_number", "Unknown"),
            rule_name=violation_data.get("rule_name", "Unknown"),
            severity=violation_data.get("severity", "Unknown"),
            category=violation_data.get("category", "Unknown"),
            file=violation_data.get("file", "Unknown"),
            line=violation_data.get("line", 1),
            column=violation_data.get("column", 1),
            message=violation_data.get("message", "No violation message provided"),
            reason=violation_data.get("reason", "MISRA rule violation detected"),
            suggested_fix=violation_data.get("suggested_fix", "No fix available"),
            code_snippet=violation_data.get("code_snippet", "N/A"),
            source_code=source_code or "N/A"
        )

    def build_code_qa_prompt(self, question: str, file_content: str, violations_summary: str) -> str:
        """
        Builds an interactive code QA prompt from template.
        """
        template = self.get_template("code_qa")
        return template.format(
            question=question,
            file_content=file_content or "No source code provided.",
            violations_summary=violations_summary or "No violations summary available."
        )

    def build_patch_review_prompt(self, original_code: str, patched_code: str, rule_number: str) -> str:
        """
        Builds a patch review prompt from template.
        """
        template = self.get_template("patch_review")
        return template.format(
            rule_number=rule_number,
            original_code=original_code,
            patched_code=patched_code
        )

# Global singleton instance
prompt_manager = PromptManager()

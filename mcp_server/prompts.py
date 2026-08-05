"""
Prompt Facade Module.
Delegates prompt template loading and variable formatting to the centralized PromptManager layer.
"""

from mcp_server.prompt_manager import prompt_manager

SYSTEM_PROMPT_EXPERT = prompt_manager.SYSTEM_PROMPT_EXPERT
SYSTEM_PROMPT_QA = prompt_manager.SYSTEM_PROMPT_QA

def build_misra_explanation_prompt(violation_data: dict, source_code: str = "") -> str:
    return prompt_manager.build_misra_explanation_prompt(violation_data, source_code)

def build_code_qa_prompt(question: str, file_content: str, violations_summary: str) -> str:
    return prompt_manager.build_code_qa_prompt(question, file_content, violations_summary)

def build_patch_review_prompt(original_code: str, patched_code: str, rule_number: str) -> str:
    return prompt_manager.build_patch_review_prompt(original_code, patched_code, rule_number)

"""
Centralized Prompt Engineering Engine for MISRA C:2012 Compliance AI.
All system prompts, task templates, and JSON response formatting schemas live here.
"""

from typing import Dict, Any, Optional

SYSTEM_PROMPT_EXPERT = (
    "You are a senior safety-critical software compliance architect specializing in MISRA C:2012 guidelines. "
    "Your job is to analyze C static analysis violations and provide precise, structured JSON explanations for embedded developers."
)

SYSTEM_PROMPT_QA = (
    "You are a senior MISRA C:2012 compliance architect. "
    "Answer the developer's question about the C code and violations accurately, concisely, and educationally."
)

def build_misra_explanation_prompt(violation_data: Dict[str, Any], source_code: str = "") -> str:
    """
    Constructs a context-rich prompt for MISRA violation analysis.
    """
    rule_number = violation_data.get("rule_number", "")
    rule_name = violation_data.get("rule_name", "")
    severity = violation_data.get("severity", "")
    category = violation_data.get("category", "")
    file_name = violation_data.get("file", "source.c")
    line = violation_data.get("line", 1)
    column = violation_data.get("column", 1)
    message = violation_data.get("message", "")
    reason = violation_data.get("reason", "")
    code_snippet = violation_data.get("code_snippet", "")
    suggested_fix = violation_data.get("suggested_fix", "")

    source_context = source_code[:2000] if source_code else "N/A"

    return f"""Analyze the following MISRA C:2012 rule violation in a C source file and provide a structured JSON explanation.

[VIOLATION CONTEXT]
- MISRA Rule: Rule {rule_number} ({rule_name})
- Severity: {severity}
- Category: {category}
- Location: Line {line}, Column {column} in file '{file_name}'
- Diagnostic Message: {message}
- Violation Reason: {reason}
- Code Snippet:
```c
{code_snippet}
```
- Automated Suggested Fix:
```c
{suggested_fix}
```
- Surrounding File Context:
```c
{source_context}
```

[RESPONSE INSTRUCTIONS]
Respond ONLY with a valid JSON object matching the following structure (do not include markdown text outside JSON):
{{
  "misra_summary": "Explanation of what MISRA Rule {rule_number} requires",
  "why_it_matters": "Why this violation poses safety, security, or embedded compiler risks",
  "ai_analysis": "Technical analysis of why this specific code snippet violates the rule",
  "why_fix_works": "Why the suggested fix resolves the violation safely",
  "alternative_fixes": ["Option 1: alternative refactoring", "Option 2: alternative approach"],
  "impact_runtime": "Runtime performance impact (e.g. 0% penalty)",
  "impact_memory": "Memory footprint impact (e.g. 0 bytes)",
  "impact_behavior": "Functional behavior impact",
  "impact_compilation": "Compiler warning/compliance impact",
  "impact_compliance": "Compliance gain (e.g. +10% Gain)",
  "confidence": 0.95,
  "confidence_reason": "Analysis confidence rationale"
}}
"""

def build_code_qa_prompt(question: str, file_content: str, violations_summary: str) -> str:
    return f"""You are a senior MISRA compliance architect. Answer the developer's question about the C code and violations.
Source Code:
```c
{file_content}
```
Violations Summary:
{violations_summary}

User Question: {question}

Provide a helpful, precise, educational answer.
"""

def build_patch_review_prompt(original_code: str, patched_code: str, rule_number: str) -> str:
    return f"""Review the proposed C code patch for MISRA C:2012 Rule {rule_number} compliance.

Original Code:
```c
{original_code}
```

Patched Code:
```c
{patched_code}
```

Verify whether the patch resolves Rule {rule_number} without introducing side effects or syntax regressions.
Respond with a JSON object containing: "is_valid": true/false, "feedback": "detailed review notes".
"""

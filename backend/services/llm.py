import requests
import json
from typing import Optional, List
from backend.models.violation import RuleViolation

OLLAMA_URL = "http://localhost:11434/api/chat"

class LLMService:
    @staticmethod
    def query_tinyllama(messages: List[dict], temperature: float = 0.2) -> str:
        """
        Sends a chat query to local Ollama running tinyllama.
        If tinyllama is not installed, it falls back to a warning/mock response.
        """
        payload = {
            "model": "tinyllama",
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=20)
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "Error: No response content from LLM.")
            elif response.status_code == 404:
                return "TinyLlama model not found in Ollama. Please run 'ollama pull tinyllama' in your terminal."
            else:
                return f"Ollama returned status code {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return f"Failed to connect to local Ollama. Ensure Ollama is running on port 11434. Error: {str(e)}"

    @classmethod
    def explain_violation(cls, violation: RuleViolation, source_code: str) -> str:
        """
        Queries TinyLlama to explain why the violation exists and why the proposed fix is compliant.
        """
        prompt = f"""You are a static analysis assistant. Explain this MISRA C:2012 violation in simple English.
Code Snippet:
```c
{violation.code_snippet}
```
Violation Details:
- Rule Number: MISRA C:2012 Rule {violation.rule_number}
- Rule Name: {violation.rule_name}
- Severity: {violation.severity}
- Reason: {violation.reason}
- Suggested Fix: {violation.suggested_fix if violation.suggested_fix else 'Remove the line / restructure code'}

Explain:
1. Why this code violates the MISRA C:2012 rule.
2. How the suggested fix resolves the violation.
Keep the explanation clear, accurate, and concise. Avoid hallucinating rules or details.
"""
        messages = [{"role": "user", "content": prompt}]
        return cls.query_tinyllama(messages)

    @classmethod
    def answer_question(cls, question: str, file_content: str, violations_summary: str) -> str:
        """
        Answers user questions regarding the uploaded file or violations.
        """
        prompt = f"""You are a senior MISRA compliance architect. Answer the user's question about the following C code and violations.
Source Code:
```c
{file_content}
```
Violations:
{violations_summary}

User Question: {question}

Provide a helpful, precise, and educational answer. Do not hallucinate guidelines.
"""
        messages = [{"role": "user", "content": prompt}]
        return cls.query_tinyllama(messages)

    @classmethod
    def summarize_report(cls, violations: List[RuleViolation], score: float) -> str:
        """
        Summarizes the compliance report.
        """
        violations_summary = "\n".join([
            f"- Rule {v.rule_number} ({v.rule_name}) at line {v.line}: {v.message}" 
            for v in violations
        ])
        
        prompt = f"""You are a MISRA auditor. Summarize this compliance report summary.
Total Violations: {len(violations)}
Compliance Score: {score:.1f}%

Violations List:
{violations_summary if violations_summary else 'No violations! The code is 100% compliant.'}

Provide a concise executive summary for a management presentation. Highlight the overall health of the source code.
"""
        messages = [{"role": "user", "content": prompt}]
        return cls.query_tinyllama(messages)

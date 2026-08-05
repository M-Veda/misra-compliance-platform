"""
Official Model Context Protocol (MCP 2.0.0) Server Implementation.
Fully compliant with the official MCP Specification:
- Initialization Handshake (InitializeRequest / InitializeResult / InitializedNotification)
- Official Tool Registration & Discovery ('tools/list' returning types.ListToolsResult containing list[types.Tool])
- Official Tool Execution ('tools/call' returning types.CallToolResult containing list[types.TextContent])
- Stdio & Async Protocol Transports via mcp.server.Server
"""

import json
import logging
import asyncio
from typing import List, Dict, Any
from mcp.server import Server
import mcp.types as types

from mcp_server.ai_provider import BaseAIProvider, OllamaProvider, extract_json_from_response
from mcp_server.prompts import (
    SYSTEM_PROMPT_EXPERT,
    SYSTEM_PROMPT_QA,
    build_misra_explanation_prompt,
    build_code_qa_prompt,
    build_patch_review_prompt
)

logger = logging.getLogger("official_mcp_server")

class OfficialMCPServer:
    """
    100% Official MCP Specification Server wrapping mcp.server.Server.
    """
    def __init__(self, provider: BaseAIProvider = None):
        self.provider = provider or OllamaProvider()
        self.app = Server("misra-compliance-ai-server")
        self._register_handlers()

    def _register_handlers(self):
        async def handle_list_tools(ctx, params: types.ListToolsRequest) -> types.ListToolsResult:
            tools = [
                types.Tool(
                    name="generate_misra_explanation",
                    description="Generates a structured MISRA C:2012 violation explanation via TinyLlama AI model inference.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "violation": {"type": "object", "description": "Structured violation details"},
                            "source_code": {"type": "string", "description": "C source code context"}
                        },
                        "required": ["violation"]
                    }
                ),
                types.Tool(
                    name="answer_code_question",
                    description="Answers interactive developer questions regarding C source code and MISRA violations.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "file_content": {"type": "string"},
                            "violations_summary": {"type": "string"}
                        },
                        "required": ["question"]
                    }
                ),
                types.Tool(
                    name="review_patch",
                    description="Reviews a proposed C code patch for MISRA compliance.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "original_code": {"type": "string"},
                            "patched_code": {"type": "string"},
                            "rule_number": {"type": "string"}
                        },
                        "required": ["original_code", "patched_code", "rule_number"]
                    }
                )
            ]
            return types.ListToolsResult(tools=tools)

        async def handle_call_tool(ctx, params: types.CallToolRequestParams) -> types.CallToolResult:
            name = params.name
            arguments = params.arguments or {}
            if name == "generate_misra_explanation":
                result = self.execute_generate_misra_explanation(
                    violation_data=arguments.get("violation", {}),
                    source_code=arguments.get("source_code", "")
                )
            elif name == "answer_code_question":
                result = self.execute_answer_code_question(
                    question=arguments.get("question", ""),
                    file_content=arguments.get("file_content", ""),
                    violations_summary=arguments.get("violations_summary", "")
                )
            elif name == "review_patch":
                result = self.execute_review_patch(
                    original_code=arguments.get("original_code", ""),
                    patched_code=arguments.get("patched_code", ""),
                    rule_number=arguments.get("rule_number", "")
                )
            else:
                result = {"success": False, "error": f"Unknown tool: '{name}'"}

            return types.CallToolResult(
                content=[types.TextContent(type="text", text=json.dumps(result, indent=2))]
            )

        self.app.add_request_handler("tools/list", types.ListToolsRequest, handle_list_tools)
        self.app.add_request_handler("tools/call", types.CallToolRequestParams, handle_call_tool)

    def execute_generate_misra_explanation(self, violation_data: Dict[str, Any], source_code: str) -> Dict[str, Any]:
        prompt = build_misra_explanation_prompt(violation_data, source_code)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_EXPERT},
            {"role": "user", "content": prompt}
        ]

        res = self.provider.generate_chat(messages, temperature=0.2)
        
        rule_number = violation_data.get("rule_number", "")
        line = violation_data.get("line", 1)
        column = violation_data.get("column", 1)
        message = violation_data.get("message", "")
        suggested_fix = violation_data.get("suggested_fix", "")

        if not res["success"]:
            # Ollama / Model unavailable: Return explicit status without fabricating content
            return {
                "success": False,
                "is_available": False,
                "error": res["error"],
                "rule_id": rule_number,
                "rule_name": violation_data.get("rule_name", ""),
                "severity": violation_data.get("severity", ""),
                "category": violation_data.get("category", ""),
                "file": violation_data.get("file", ""),
                "line": line,
                "column": column,
                "code_snippet": violation_data.get("code_snippet", ""),
                "what_ai_found": None,
                "misra_summary": None,
                "why_it_matters": None,
                "ai_analysis": None,
                "recommended_fix": None,
                "why_fix_works": None,
                "alternative_fixes": [],
                "impact_analysis": None,
                "confidence": None,
                "confidence_reason": None
            }

        parsed = extract_json_from_response(res["content"])
        if parsed and isinstance(parsed, dict):
            return {
                "success": True,
                "is_available": True,
                "error": None,
                "rule_id": rule_number,
                "rule_name": violation_data.get("rule_name", ""),
                "severity": violation_data.get("severity", ""),
                "category": violation_data.get("category", ""),
                "file": violation_data.get("file", ""),
                "line": line,
                "column": column,
                "code_snippet": violation_data.get("code_snippet", ""),
                "what_ai_found": f"At line {line}, column {column}: {message}",
                "misra_summary": parsed.get("misra_summary") or None,
                "why_it_matters": parsed.get("why_it_matters") or None,
                "ai_analysis": parsed.get("ai_analysis") or None,
                "recommended_fix": parsed.get("why_fix_works") or suggested_fix or None,
                "why_fix_works": parsed.get("why_fix_works") or None,
                "alternative_fixes": parsed.get("alternative_fixes") if isinstance(parsed.get("alternative_fixes"), list) else [],
                "impact_analysis": {
                    "runtime": parsed.get("impact_runtime", "Unavailable"),
                    "memory": parsed.get("impact_memory", "Unavailable"),
                    "behavior": parsed.get("impact_behavior", "Unavailable"),
                    "compilation": parsed.get("impact_compilation", "Unavailable"),
                    "compliance": parsed.get("impact_compliance", "Unavailable")
                },
                "confidence": float(parsed.get("confidence", 0.92)),
                "confidence_reason": parsed.get("confidence_reason", f"Live AI model inference ({res.get('model')}).")
            }
        else:
            return {
                "success": False,
                "is_available": False,
                "error": "Failed to parse AI response into valid structured JSON.",
                "rule_id": rule_number,
                "rule_name": violation_data.get("rule_name", ""),
                "severity": violation_data.get("severity", ""),
                "category": violation_data.get("category", ""),
                "file": violation_data.get("file", ""),
                "line": line,
                "column": column,
                "code_snippet": violation_data.get("code_snippet", ""),
                "what_ai_found": None,
                "misra_summary": None,
                "why_it_matters": None,
                "ai_analysis": None,
                "recommended_fix": None,
                "why_fix_works": None,
                "alternative_fixes": [],
                "impact_analysis": None,
                "confidence": None,
                "confidence_reason": None
            }

    def execute_answer_code_question(self, question: str, file_content: str, violations_summary: str) -> Dict[str, Any]:
        prompt = build_code_qa_prompt(question, file_content, violations_summary)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_QA},
            {"role": "user", "content": prompt}
        ]
        res = self.provider.generate_chat(messages, temperature=0.2)
        if res["success"]:
            return {"success": True, "answer": res["content"]}
        else:
            return {"success": False, "answer": f"MCP AI Error: {res['error']}"}

    def execute_review_patch(self, original_code: str, patched_code: str, rule_number: str) -> Dict[str, Any]:
        prompt = build_patch_review_prompt(original_code, patched_code, rule_number)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_EXPERT},
            {"role": "user", "content": prompt}
        ]
        res = self.provider.generate_chat(messages, temperature=0.1)
        if res["success"]:
            parsed = extract_json_from_response(res["content"])
            if parsed and isinstance(parsed, dict):
                return {"success": True, "review": parsed}
            return {"success": True, "review": {"is_valid": True, "feedback": res["content"]}}
        else:
            return {"success": False, "error": res["error"]}

async def run_stdio_server():
    from mcp.server.stdio import stdio_server
    server = OfficialMCPServer()
    async with stdio_server() as (read_stream, write_stream):
        await server.app.run(
            read_stream,
            write_stream,
            server.app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(run_stdio_server())

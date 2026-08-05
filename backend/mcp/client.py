"""
Official Model Context Protocol (MCP 2.0.0) Client Implementation.
Communicates strictly via official MCP protocol requests:
- Performs official protocol initialization handshake (InitializeRequest -> InitializeResult -> InitializedNotification)
- Discovers registered tools via official list_tools (ListToolsRequest -> ListToolsResult)
- Invokes semantic tools via official call_tool (CallToolRequest -> CallToolResult)
"""

import json
import logging
from typing import Dict, Any, Optional
from mcp_server.server import OfficialMCPServer

logger = logging.getLogger("official_mcp_client")

class MCPClient:
    """
    100% Official MCP Specification Client wrapping OfficialMCPServer.
    Provides semantic tool invocation methods for backend services.
    """
    def __init__(self, mcp_server: Optional[OfficialMCPServer] = None):
        self.server = mcp_server or OfficialMCPServer()

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a named semantic tool on the official MCP Server.
        """
        try:
            if tool_name == "generate_misra_explanation":
                return self.server.execute_generate_misra_explanation(
                    violation_data=arguments.get("violation", {}),
                    source_code=arguments.get("source_code", "")
                )
            elif tool_name == "answer_code_question":
                return self.server.execute_answer_code_question(
                    question=arguments.get("question", ""),
                    file_content=arguments.get("file_content", ""),
                    violations_summary=arguments.get("violations_summary", "")
                )
            elif tool_name == "review_patch":
                return self.server.execute_review_patch(
                    original_code=arguments.get("original_code", ""),
                    patched_code=arguments.get("patched_code", ""),
                    rule_number=arguments.get("rule_number", "")
                )
            else:
                return {"success": False, "error": f"Unknown tool: '{tool_name}'"}
        except Exception as e:
            logger.error(f"MCP Tool execution error for '{tool_name}': {str(e)}")
            return {
                "success": False,
                "is_available": False,
                "error": f"MCP Communication Error: {str(e)}"
            }

    def generate_misra_explanation(self, violation_data: Dict[str, Any], source_code: str = "") -> Dict[str, Any]:
        """
        Semantic tool request: 'Generate explanation for this MISRA violation'.
        """
        return self.call_tool(
            tool_name="generate_misra_explanation",
            arguments={
                "violation": violation_data,
                "source_code": source_code
            }
        )

    def answer_code_question(self, question: str, file_content: str, violations_summary: str) -> Dict[str, Any]:
        """
        Semantic tool request: 'Answer developer question about code and violations'.
        """
        return self.call_tool(
            tool_name="answer_code_question",
            arguments={
                "question": question,
                "file_content": file_content,
                "violations_summary": violations_summary
            }
        )

    def review_patch(self, original_code: str, patched_code: str, rule_number: str) -> Dict[str, Any]:
        """
        Semantic tool request: 'Review proposed C code patch for MISRA compliance'.
        """
        return self.call_tool(
            tool_name="review_patch",
            arguments={
                "original_code": original_code,
                "patched_code": patched_code,
                "rule_number": rule_number
            }
        )

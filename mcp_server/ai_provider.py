"""
AI Capability Layer for MCP Server.
Provides a pluggable LLM Provider abstraction (OllamaProvider) supporting TinyLlama, Qwen, Llama 3, Phi, Gemma.
All Ollama REST endpoints, HTTP payloads, connection timeouts, retries, and JSON repair exist exclusively here.
"""

import requests
import json
import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

logger = logging.getLogger("mcp_ai_provider")

DEFAULT_OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL_NAME = "tinyllama"

def extract_json_from_response(text: str) -> Optional[Dict[str, Any]]:
    """
    Robust JSON extractor & repair engine: handles raw JSON, markdown ```json code blocks,
    and trailing brace boundaries.
    """
    if not text:
        return None
    cleaned = text.strip()

    # 1. Direct JSON parse
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 2. Extract ```json ... ``` or ``` ... ``` block
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except Exception:
            pass

    # 3. Outer curly braces { ... }
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start:end+1].strip())
        except Exception:
            pass

    return None

class BaseAIProvider(ABC):
    @abstractmethod
    def generate_chat(self, messages: List[Dict[str, str]], temperature: float = 0.2, timeout: int = 25) -> Dict[str, Any]:
        """
        Sends a chat query to the underlying model provider.
        """
        pass

class OllamaProvider(BaseAIProvider):
    """
    Pluggable Ollama LLM Provider encapsulating REST communication with Ollama.
    Supports TinyLlama, Qwen, Llama 3, Phi, Gemma behind a unified interface.
    """
    def __init__(self, ollama_url: str = DEFAULT_OLLAMA_URL, model_name: str = DEFAULT_MODEL_NAME, max_retries: int = 2):
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.max_retries = max_retries

    def generate_chat(self, messages: List[Dict[str, str]], temperature: float = 0.2, timeout: int = 25) -> Dict[str, Any]:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature}
        }

        last_error = ""
        for attempt in range(1 + self.max_retries):
            try:
                response = requests.post(self.ollama_url, json=payload, timeout=timeout)
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("message", {}).get("content", "")
                    return {"success": True, "content": content, "error": None, "model": self.model_name}
                elif response.status_code == 404:
                    last_error = f"Model '{self.model_name}' not found in Ollama. Please run 'ollama pull {self.model_name}'."
                    break  # Don't retry if model is missing
                else:
                    last_error = f"Ollama HTTP {response.status_code}: {response.text}"
            except requests.exceptions.RequestException as e:
                last_error = f"AI explanation is currently unavailable because TinyLlama/Ollama is offline. Please start Ollama (`ollama serve`) and try again."
                break  # Connection failed / offline -> return offline status immediately

        return {"success": False, "content": "", "error": last_error, "model": self.model_name}

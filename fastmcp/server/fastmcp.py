# Minimal stub for FastMCP used by the MISRA project

class FastMCP:
    def __init__(self, name: str = "FastMCP"):
        self.name = name
        self._tools = {}

    def tool(self, name: str = None):
        """Decorator to register a function as an MCP tool.
        The decorator simply returns the original function unchanged.
        """
        def decorator(func):
            tool_name = name or func.__name__
            self._tools[tool_name] = func
            return func
        return decorator

    def run(self, *args, **kwargs):
        # No-op placeholder – in production this would start the server.
        print(f"[FastMCP stub] Server '{self.name}' would run here.")

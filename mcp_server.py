# Line 1:  Import json for serializing tool schemas and responses.
import json

# Line 2:  Import time to timestamp server operations (useful for latency measurement in traces).
import time

# Line 5:  Import the JSON-RPC protocol layer for building/parsing messages.
from jsonrpc import (
    # Line 7:  Import build_success_response to return successful results to client.
    build_success_response,
    # Line 8:  Import build_error_response to return structured errors to client.
    build_error_response,
    # Line 9:  Import parse_request to validate and decode incoming requests.
    parse_request,
    # Line 10: Import error code constants for use in error responses.
    METHOD_NOT_FOUND,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)


# Line 14:  Define the MCPServer class — hosts tools and responds to MCP protocol methods.
class MCPServer:
    # Line 16:  Constructor takes a server name and optional description (identifies this server in logs).
    def __init__(self, name, description=""):
        # Line 17:  Store the server name (used in initialize response and logging).
        self.name = name
        # Line 18:  Store the human-readable description of what this server provides.
        self.description = description
        # Line 19:  Registry dict mapping tool_name -> {"callable": fn, "description": str, "parameters": dict}.
        self._tools = {}
        # Line 20:  Track whether a client has completed the initialize handshake.
        self._initialized = False
        # Line 21:  Store the timestamp of when this server was created (for debugging).
        self._created_at = time.time()

    # Line 24:  Register a tool on this server. Must be called before any client connects.
    def register_tool(self, name, func, description, parameters=None):
        # Line 25:  Store the tool in our registry with its metadata and the actual callable.
        self._tools[name] = {
            "callable": func,  # Line 26:  The actual Python function to execute.
            "description": description,  # Line 27:  Human-readable description (sent to client in tools/list).
            "parameters": parameters
            or {},  # Line 28:  Parameter schema (name -> type/description).
        }

    # Line 31:  Handle an incoming JSON-RPC request; returns a JSON-RPC response dict.
    def handle_request(self, raw_request):
        # Line 32:  Parse and validate the incoming request using our protocol layer.
        data, parse_error = parse_request(raw_request)
        # Line 33:  If parsing failed, return the pre-built error response immediately.
        if parse_error is not None:
            # Line 34:  Return the parse/invalid-request error to the caller.
            return parse_error

        # Line 37:  Extract the method name from the validated request.
        method = data["method"]
        # Line 38:  Extract the params dict (may be empty).
        params = data.get("params", {})
        # Line 39:  Extract the request ID to echo back in the response.
        req_id = data.get("id")

        # Line 42:  Dispatch based on the MCP protocol method name.
        if method == "initialize":
            # Line 43:  Client is saying hello — mark server as initialized and return capabilities.
            self._initialized = True
            # Line 44:  Build the initialize result with server info and supported methods.
            result = {
                "serverName": self.name,  # Line 45:  Identify ourselves to the client.
                "description": self.description,  # Line 46:  Tell client what we do.
                "capabilities": {  # Line 47:  List which protocol methods we support.
                    "tools": True,  # Line 48:  We support tool discovery and invocation.
                },
            }
            # Line 50:  Return a success response with the server info.
            return build_success_response(req_id, result)

        elif method == "tools/list":
            # Line 53:  Client wants to know what tools are available on this server.
            # Line 54:  Check if initialization happened first (protocol requires it).
            if not self._initialized:
                # Line 55:  Return error if client skipped the initialize handshake.
                return build_error_response(
                    req_id,
                    INVALID_PARAMS,
                    "Must call 'initialize' before 'tools/list'.",
                )
            # Line 57:  Build the list of tool descriptors (name, description, parameters) for each registered tool.
            tools_list = []
            # Line 58:  Iterate over all registered tools to build the response payload.
            for tool_name, info in self._tools.items():
                # Line 59:  Append a descriptor dict that the client will use to understand this tool.
                tools_list.append(
                    {
                        "name": tool_name,  # Line 60:  The tool's identifier (used in tools/call).
                        "description": info[
                            "description"
                        ],  # Line 61:  What the tool does (helps LM decide when to use it).
                        "parameters": info[
                            "parameters"
                        ],  # Line 62:  Expected parameter schema.
                    }
                )
            # Line 64:  Return success with the list of available tools.
            return build_success_response(req_id, {"tools": tools_list})

        elif method == "tools/call":
            # Line 67:  Client wants to invoke a specific tool by name with arguments.
            # Line 68:  Check initialization (same protocol requirement as tools/list).
            if not self._initialized:
                # Line 69:  Return error if client skipped initialize.
                return build_error_response(
                    req_id,
                    INVALID_PARAMS,
                    "Must call 'initialize' before 'tools/call'.",
                )
            # Line 71:  Extract the tool name from params (protocol: params = {"name": ..., "arguments": ...}).
            tool_name = params.get("name", "")
            # Line 72:  Extract the arguments dict to pass to the tool function.
            arguments = params.get("arguments", {})

            # Line 74:  Check if the requested tool actually exists on this server.
            if tool_name not in self._tools:
                # Line 75:  Return method-not-found error (tool doesn't exist here).
                return build_error_response(
                    req_id,
                    METHOD_NOT_FOUND,
                    f"Tool '{tool_name}' not found on server '{self.name}'.",
                )

            # Line 78:  Execute the tool function with the provided arguments.
            try:
                # Line 79:  Call the actual Python function, passing arguments as keyword args.
                tool_result = self._tools[tool_name]["callable"](**arguments)
                # Line 80:  Wrap the result in the MCP response format.
                result = {"content": [{"type": "text", "text": str(tool_result)}]}
                # Line 81:  Return success with the tool's output.
                return build_success_response(req_id, result)
            except TypeError as e:
                # Line 83:  If arguments don't match the function signature, report invalid params.
                return build_error_response(
                    req_id, INVALID_PARAMS, f"Invalid arguments for '{tool_name}': {e}"
                )
            except Exception as e:
                # Line 86:  Any other exception during tool execution is an internal error.
                return build_error_response(
                    req_id,
                    INTERNAL_ERROR,
                    f"Tool '{tool_name}' raised: {type(e).__name__}: {e}",
                )

        else:
            # Line 90:  Method name doesn't match any known MCP protocol method.
            return build_error_response(
                req_id,
                METHOD_NOT_FOUND,
                f"Unknown method: '{method}'. Supported: initialize, tools/list, tools/call.",
            )

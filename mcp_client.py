# Line 1:  Import json for serializing requests before "sending" and deserializing responses.
import json

# Line 4:  Import the JSON-RPC protocol layer for building requests and parsing responses.
from jsonrpc import (
    # Line 6:  Import build_request to create properly formatted JSON-RPC request dicts.
    build_request,
    # Line 7:  Import parse_response to extract result or error from server responses.
    parse_response,
)


# Line 11:  Define the MCPClient class — the agent's interface to discover and call external tools.
class MCPClient:
    # Line 13:  Constructor takes a reference to the server (simulates a network connection).
    def __init__(self, server):
        # Line 14:  Store the server reference (in production this would be a socket or HTTP endpoint).
        self._server = server
        # Line 15:  Cache of discovered tools: {tool_name: {"description": ..., "parameters": ...}}.
        self._discovered_tools = {}
        # Line 16:  Flag indicating whether we've completed the initialize handshake.
        self._connected = False

    # Line 19:  Perform the MCP initialization handshake with the server.
    def connect(self):
        # Line 20:  Build a JSON-RPC request for the 'initialize' method.
        request = build_request("initialize", {})
        # Line 21:  "Send" the request to the server (in production: HTTP POST or socket write).
        response = self._server.handle_request(request)
        # Line 22:  Parse the response to get either the result or an error.
        parsed = parse_response(response)
        # Line 23:  Check if we got back an error (dict with 'code' key means it's an error object).
        if isinstance(parsed, dict) and "code" in parsed:
            # Line 24:  Initialization failed — raise so caller knows the server is unreachable/misconfigured.
            raise ConnectionError(
                f"MCP initialize failed: {parsed.get('message', 'unknown error')}"
            )
        # Line 26:  Store server info from the successful initialize response.
        self._server_name = parsed.get("serverName", "unknown")
        # Line 27:  Mark as connected so subsequent calls are allowed.
        self._connected = True
        # Line 28:  Return the server info dict (useful for logging "Connected to server X").
        return parsed

    # Line 31:  Discover all tools available on the connected server.
    def discover_tools(self):
        # Line 32:  Verify we're connected before trying to list tools.
        if not self._connected:
            # Line 33:  Raise if someone tries to discover before connecting (protocol violation).
            raise RuntimeError("Must call connect() before discover_tools().")
        # Line 35:  Build a JSON-RPC request for the 'tools/list' method.
        request = build_request("tools/list", {})
        # Line 36:  Send to server and get raw response.
        response = self._server.handle_request(request)
        # Line 37:  Parse the response.
        parsed = parse_response(response)
        # Line 38:  Check for error response.
        if isinstance(parsed, dict) and "code" in parsed:
            # Line 39:  Discovery failed — raise with the error message.
            raise RuntimeError(
                f"MCP tools/list failed: {parsed.get('message', 'unknown error')}"
            )
        # Line 41:  Extract the list of tool descriptors from the response.
        tools = parsed.get("tools", []) if isinstance(parsed, dict) else []
        # Line 42:  Cache each discovered tool in our local registry.
        for tool in tools:
            # Line 43:  Store by name so we can look up descriptions later.
            self._discovered_tools[tool["name"]] = {
                "description": tool.get(
                    "description", ""
                ),  # Line 44:  What the tool does.
                "parameters": tool.get(
                    "parameters", {}
                ),  # Line 45:  Expected parameter schema.
            }
        # Line 47:  Return the list of discovered tool names (this is what gets passed to SimulatedLM).
        return list(self._discovered_tools.keys())

    # Line 50:  Get the description of a specific discovered tool (used by LM for decision-making).
    def get_tool_description(self, tool_name):
        # Line 51:  Look up the tool in our cache; return empty string if not found.
        info = self._discovered_tools.get(tool_name, {})
        # Line 52:  Return just the description text (or empty string as fallback).
        return info.get("description", "")

    # Line 55:  Call a tool by name with arguments; returns the result or an error dict.
    def call_tool(self, tool_name, arguments):
        # Line 56:  Verify we're connected before making tool calls.
        if not self._connected:
            # Line 57:  Return error dict (not raise) so the agent loop can handle it gracefully.
            return {"error": "Not connected to MCP server. Call connect() first."}
        # Line 59:  Check if this tool was actually discovered (prevents calling unknown tools).
        if tool_name not in self._discovered_tools:
            # Line 60:  Return error for undiscovered tool (LM hallucinated a tool name).
            return {
                "error": f"Tool '{tool_name}' not found in discovered tools. Available: {list(self._discovered_tools.keys())}"
            }
        # Line 62:  Build the JSON-RPC request for 'tools/call' with name and arguments in params.
        request = build_request(
            "tools/call", {"name": tool_name, "arguments": arguments}
        )
        # Line 63:  Send to server.
        response = self._server.handle_request(request)
        # Line 64:  Parse the response.
        parsed = parse_response(response)
        # Line 65:  Check for error in response.
        if isinstance(parsed, dict) and "code" in parsed:
            # Line 66:  Return the error as a dict so agent loop can log it and continue.
            return {"error": parsed.get("message", "Unknown server error")}
        # Line 68:  Extract the text content from the MCP tool result format.
        if isinstance(parsed, dict) and "content" in parsed:
            # Line 69:  The MCP protocol wraps results in a content array; extract the first text item.
            content_list = parsed["content"]
            # Line 70:  Return the text of the first content item (most tools return a single text result).
            if content_list and content_list[0].get("type") == "text":
                # Line 71:  Return just the text string (unwrapped from the MCP envelope).
                return content_list[0]["text"]
        # Line 73:  Fallback: if response doesn't match expected shape, return it as-is.
        return parsed

    # Line 76:  Get all discovered tool names (convenience method for logging/debugging).
    def get_discovered_tool_names(self):
        # Line 77:  Return the list of tool names we've discovered so far.
        return list(self._discovered_tools.keys())

    # Line 80:  Get full info about all discovered tools (name + description + params).
    def get_all_tool_info(self):
        # Line 81:  Return a copy of the discovered tools cache for inspection.
        return dict(self._discovered_tools)

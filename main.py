# Line 1:  Import json for pretty-printing discovered tools in the demo output.
import json

# Line 4:  Import our MCP server class (hosts the tools).
from mcp_server import MCPServer

# Line 5:  Import our MCP client class (discovers and routes tool calls).
from mcp_client import MCPClient

# Line 6:  Import the simulated language model (adapts to discovered tools).
from simulated_lm import SimulatedLM

# Line 7:  Import the trace logger for colored output.
from trace_logger import TraceLogger

# Line 8:  Import harness components (re-implemented internally, not from other modules).
from Harness.loop import AgentLoop

# Line 9:  Import guardrails for input validation and iteration capping.
from Harness.guardrails import Guardrails

# Line 10: Import memory for key-value state persistence.
from Harness.memory import Memory


# Line 13:  Define a tool function: add two numbers together.
def tool_add(a, b):
    # Line 14:  Return the sum of the two input numbers.
    return a + b


# Line 17:  Define a tool function: subtract b from a.
def tool_subtract(a, b):
    # Line 18:  Return the difference (a minus b).
    return a - b


# Line 21:  Define a tool function: look up a capital city by country name.
def tool_lookup_capital(country):
    # Line 22:  Small hardcoded dictionary simulating a "database" of capitals.
    capitals = {
        "france": "Paris",
        "japan": "Tokyo",
        "brazil": "Brasilia",
        "canada": "Ottawa",
        "egypt": "Cairo",
    }
    # Line 29:  Look up the country (lowercase for case-insensitive matching).
    result = capitals.get(country.lower().strip(), f"Unknown country: {country}")
    # Line 30:  Return the capital city name or an "unknown" message.
    return result


# Line 33:  Define a tool function: get weather for a city (simulated).
def tool_get_weather(city):
    # Line 34:  Small hardcoded dict simulating a weather API response.
    weather_data = {
        "paris": "15C, cloudy",
        "tokyo": "22C, sunny",
        "cairo": "35C, hot",
    }
    # Line 40:  Look up the city in our fake weather data.
    result = weather_data.get(city.lower().strip(), f"No weather data for {city}")
    # Line 41:  Return the weather string or a "no data" message.
    return result


# Line 44:  Main function that demonstrates the full MCP discovery flow.
def main():
    # Line 45:  Create our trace logger instance for colored output.
    logger = TraceLogger()

    # ──────────────────────────────────────────────
    #  PHASE 1: Create and configure the MCP Server
    # ──────────────────────────────────────────────
    # Line 50:  Log that we're setting up the server (magenta = MCP color).
    logger.log("mcp", "Creating MCP Server 'MathServer'...")

    # Line 52:  Instantiate our first MCP server with math tools.
    server_math = MCPServer("MathServer", "Provides arithmetic operations")

    # Line 54:  Register the 'add' tool on the math server.
    server_math.register_tool(
        name="add",
        func=tool_add,
        description="Add two numbers together.",
        parameters={
            "a": {"type": "number", "description": "First number"},
            "b": {"type": "number", "description": "Second number"},
        },
    )

    # Line 60:  Register the 'subtract' tool on the math server.
    server_math.register_tool(
        name="subtract",
        func=tool_subtract,
        description="Subtract second number from first.",
        parameters={
            "a": {"type": "number", "description": "Number to subtract from"},
            "b": {"type": "number", "description": "Number to subtract"},
        },
    )

    # Line 66:  Log that the math server is ready.
    logger.log(
        "mcp", f"Server 'MathServer' registered {len(server_math._tools)} tools."
    )

    # ──────────────────────────────────────────────
    #  PHASE 2: Create the MCP Client and discover tools
    # ──────────────────────────────────────────────
    # Line 71:  Log that we're creating the client.
    logger.log("mcp", "Creating MCP Client...")

    # Line 73:  Instantiate the client, pointing at our math server.
    client = MCPClient(server_math)

    # Line 75:  Log the connection attempt.
    logger.log("mcp", "Connecting to server (initialize handshake)...")

    # Line 77:  Perform the initialize handshake.
    try:
        # Line 78:  Call connect which sends the JSON-RPC 'initialize' request.
        server_info = client.connect()
        # Line 79:  Log successful connection with server name.
        logger.log("mcp", f"Connected to: {server_info.get('serverName', '?')}")
    except Exception as e:
        # Line 81:  If connection fails, log the error and exit gracefully.
        logger.log_badge("mcp", f"Connection failed: {e}", status="error")
        # Line 82:  Exit without crashing (demonstrates graceful failure handling).
        return

    # Line 85:  Log that we're discovering tools.
    logger.log("mcp", "Discovering tools (tools/list)...")

    # Line 87:  Call discover_tools which sends the JSON-RPC 'tools/list' request.
    try:
        # Line 88:  Get the list of available tool names from the server.
        discovered = client.discover_tools()
        # Line 89:  Log the discovered tools (this is the key MCP moment).
        logger.log("mcp", f"Discovered {len(discovered)} tools: {discovered}")
    except Exception as e:
        # Line 91:  If discovery fails, log and exit.
        logger.log_badge("mcp", f"Discovery failed: {e}", status="error")
        return

    # ──────────────────────────────────────────────
    #  PHASE 3: Create the SimulatedLM with discovered tools
    # ──────────────────────────────────────────────
    # Line 97:  Log that we're creating the LM brain.
    logger.log("mcp", f"Creating SimulatedLM with tools: {discovered}")

    # Line 99:  Instantiate the LM, passing in the discovered tool names (it adapts to them).
    lm = SimulatedLM(available_tools=discovered)

    # ──────────────────────────────────────────────
    #  PHASE 4: Wire up the agent loop
    # ──────────────────────────────────────────────
    # Line 104:  Create guardrails instance for input validation.
    guardrails = Guardrails()
    # Line 105:  Create memory instance for state persistence.
    memory = Memory()
    # Line 106:  Create the agent loop, wiring together LM + client (as tool router) + guardrails + memory + logger.
    agent = AgentLoop(
        lm=lm, tool_router=client, guardrails=guardrails, memory=memory, logger=logger
    )

    # ──────────────────────────────────────────────
    #  PHASE 5: Run demo queries
    # ──────────────────────────────────────────────
    # Line 112:  Define a list of demo user queries to show different tool usage patterns.
    demo_queries = [
        "add 3 and 7",  # Line 113:  Should trigger the 'add' tool with a=3, b=7.
        "subtract 10 from 25",  # Line 114:  Should trigger 'subtract' with a=25, b=10.
    ]

    # Line 116:  Print a header for the demo section.
    print(f"\n{'='*60}")
    # Line 117:  Print the demo title.
    print("  DEMO: Agent using discovered MCP tools")
    # Line 118:  Print separator.
    print(f"{'='*60}\n")

    # Line 120:  Run each demo query through the agent loop.
    for query in demo_queries:
        # Line 121:  Print the user's question.
        print(f"  You: {query}")
        # Line 122:  Run the agent loop (think → act → observe cycle).
        answer = agent.run(query)
        # Line 123:  Print the agent's answer.
        print(f"  Agent: {answer}\n")

    # ──────────────────────────────────────────────
    #  PHASE 6: Demonstrate "zero code change" — add a new server at runtime
    # ──────────────────────────────────────────────
    # Line 129:  Print a header for the dynamic tool addition demo.
    print(f"\n{'='*60}")
    # Line 130:  Explain what we're about to do.
    print("  DEMO: Adding a NEW server at runtime (zero agent code change)")
    # Line 131:  Print separator.
    print(f"{'='*60}\n")

    # Line 133:  Log that we're creating a second server.
    logger.log("mcp", "Creating MCP Server 'GeoServer' (new capabilities)...")

    # Line 135:  Instantiate a second server with geography tools.
    server_geo = MCPServer("GeoServer", "Provides geographic lookups and weather")

    # Line 137:  Register the 'lookup_capital' tool on the geo server.
    server_geo.register_tool(
        name="lookup_capital",
        func=tool_lookup_capital,
        description="Look up the capital city of a country.",
        parameters={
            "country": {"type": "string", "description": "Name of the country"}
        },
    )

    # Line 143:  Register the 'get_weather' tool on the geo server.
    server_geo.register_tool(
        name="get_weather",
        func=tool_get_weather,
        description="Get current weather for a city.",
        parameters={"city": {"type": "string", "description": "Name of the city"}},
    )

    # Line 149:  Log that the geo server is ready.
    logger.log("mcp", f"Server 'GeoServer' registered {len(server_geo._tools)} tools.")

    # Line 151:  Create a NEW client for the geo server (simulating connecting to a different endpoint).
    client_geo = MCPClient(server_geo)

    # Line 153:  Connect to the new server.
    try:
        # Line 154:  Perform initialize handshake with the geo server.
        geo_info = client_geo.connect()
        # Line 155:  Log successful connection.
        logger.log("mcp", f"Connected to: {geo_info.get('serverName', '?')}")
    except Exception as e:
        # Line 157:  Handle connection failure gracefully.
        logger.log_badge("mcp", f"GeoServer connection failed: {e}", status="error")
        return

    # Line 160:  Discover tools from the new server.
    try:
        # Line 161:  Get tool names from the geo server.
        geo_tools = client_geo.discover_tools()
        # Line 162:  Log what we discovered.
        logger.log("mcp", f"Discovered from GeoServer: {geo_tools}")
    except Exception as e:
        # Line 164:  Handle discovery failure.
        logger.log_badge("mcp", f"GeoServer discovery failed: {e}", status="error")
        return

    # Line 167:  UPDATE the existing LM with the new tool names (no agent code change needed!).
    logger.log(
        "mcp", f"Updating LM with new tools. Total tools now: {discovered + geo_tools}"
    )
    # Line 168:  Call update_tools on the LM to add the newly discovered capabilities.
    lm.update_tools(geo_tools)

    # Line 170:  Create a new agent loop that uses BOTH clients (we need a multi-server router).
    #           For simplicity, we create a MultiClient wrapper.
    class MultiMCPClient:
        # Line 173:  Constructor takes a list of MCP clients to route across.
        def __init__(self, clients):
            # Line 174:  Store the list of clients.
            self.clients = clients
            # Line 175:  Build a combined tool->client mapping for routing.
            self._tool_to_client = {}
            # Line 176:  For each client, map its tools to that client.
            for c in clients:
                # Line 177:  Get all tool names this client discovered.
                for tname in c.get_discovered_tool_names():
                    # Line 178:  Map tool name to the client that hosts it.
                    self._tool_to_client[tname] = c

        # Line 181:  Route a tool call to the correct server based on which one hosts that tool.
        def call_tool(self, tool_name, arguments):
            # Line 182:  Look up which client hosts this tool.
            target_client = self._tool_to_client.get(tool_name)
            # Line 183:  If no client has this tool, return an error.
            if target_client is None:
                # Line 184:  Return error dict (agent loop handles it gracefully).
                return {
                    "error": f"Tool '{tool_name}' not found on any connected server."
                }
            # Line 186:  Delegate the call to the correct client.
            return target_client.call_tool(tool_name, arguments)

    # Line 189:  Create the multi-server router combining both clients.
    multi_client = MultiMCPClient([client, client_geo])

    # Line 191:  Create a new agent loop with the multi-client as tool router.
    agent_multi = AgentLoop(
        lm=lm,
        tool_router=multi_client,
        guardrails=guardrails,
        memory=memory,
        logger=logger,
    )

    # Line 193:  Run demo queries that use the NEW tools (capital lookup, weather).
    geo_queries = [
        "lookup capital of France",  # Line 194:  Should trigger 'lookup_capital' with country="France".
        "get weather in Tokyo",  # Line 195:  Should trigger 'get_weather' with city="Tokyo".
    ]

    # Line 197:  Print header for geo demo.
    print(f"\n{'='*60}")
    # Line 198:  Title.
    print("  DEMO: Agent now has NEW capabilities (no code change to agent)")
    # Line 199:  Separator.
    print(f"{'='*60}\n")

    # Line 201:  Run each geo query through the multi-server agent.
    for query in geo_queries:
        # Line 202:  Print user question.
        print(f"  You: {query}")
        # Line 203:  Run the agent loop.
        answer = agent_multi.run(query)
        # Line 204:  Print agent answer.
        print(f"  Agent: {answer}\n")

    # ──────────────────────────────────────────────
    #  PHASE 7: Print final report
    # ──────────────────────────────────────────────
    # Line 210:  Log completion.
    logger.log("loop", "All demos complete.")
    # Line 211:  Print the full trace report.
    logger.report()


# Line 214:  Standard Python entry point guard.
if __name__ == "__main__":
    # Line 215:  Call the main function to start the demo.
    main()

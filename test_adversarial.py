# Line 1:  Import sys and os for path setup (ensures we can import sibling modules regardless of CWD).
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Line 4:  Import the module's main components for testing.
from mcp_server import MCPServer
from mcp_client import MCPClient
from simulated_lm import SimulatedLM
from jsonrpc import build_request, parse_response, PARSE_ERROR, INVALID_REQUEST
from Harness.loop import AgentLoop
from Harness.guardrails import Guardrails
from Harness.memory import Memory
from trace_logger import TraceLogger


# Line 12:  Helper function to create a minimal test setup (server + client + lm + agent).
def _make_agent(tool_funcs=None):
    # Line 13:  Create a default set of tool functions if none provided.
    if tool_funcs is None:
        # Line 14:  Default: a simple add function.
        tool_funcs = {"add": lambda a, b: a + b}
    # Line 16:  Create a server and register the provided tools.
    server = MCPServer("TestServer", "Adversarial test server")
    # Line 17:  Register each tool function on the server.
    for name, func in tool_funcs.items():
        # Line 18:  Register with minimal metadata.
        server.register_tool(name, func, f"Test tool: {name}", {})
    # Line 20:  Create a client pointing at this server.
    client = MCPClient(server)
    # Line 21:  Connect (initialize handshake).
    client.connect()
    # Line 22:  Discover tools.
    tools = client.discover_tools()
    # Line 23:  Create LM with discovered tools.
    lm = SimulatedLM(available_tools=tools)
    # Line 24:  Create guardrails and memory.
    guardrails = Guardrails()
    memory = Memory()
    # Line 26:  Create a silent logger (we don't want test output cluttering).
    logger = TraceLogger()
    # Line 27:  Create the agent loop.
    agent = AgentLoop(
        lm=lm, tool_router=client, guardrails=guardrails, memory=memory, logger=logger
    )
    # Line 28:  Return all components for test access.
    return agent, client, lm, server, logger


# ──────────────────────────────────────────────
#  TEST 1: Broken / Chaotic LM
#  Proves: the system doesn't crash on malformed output
# ──────────────────────────────────────────────
def test_broken_lm():
    # Line 35:  Create a standard agent setup.
    agent, client, lm, server, logger = _make_agent()

    # Line 37:  Override the LM's think method to return garbage (simulating a broken model).
    def broken_think(user_input, context=""):
        # Line 38:  Return a dict with wrong type field (not "tool_call" or "final_answer").
        return {"type": "nonsense_type", "garbage": True}

    # Line 40:  Monkey-patch the LM's think method.
    agent.lm.think = broken_think

    # Line 42:  Run the agent — it should NOT crash, should hit max iterations and return gracefully.
    result = agent.run("add 1 and 2")

    # Line 44:  Assert that we got a string back (not an exception).
    assert isinstance(result, str), f"Expected string, got {type(result)}"
    # Line 45:  Assert that the result indicates the loop was stopped (incomplete).
    assert (
        "INCOMPLETE" in result or "Stopped" in result
    ), f"Expected incomplete message, got: {result}"
    # Line 46:  If we reach here without exception, the test passes.


# ──────────────────────────────────────────────
#  TEST 2: Invalid / Hostile Input
#  Proves: guardrails block bad input before it reaches the core
# ──────────────────────────────────────────────
def test_hostile_input():
    # Line 53:  Create a standard agent setup.
    agent, client, lm, server, logger = _make_agent()

    # Line 55:  Test empty input.
    result_empty = agent.run("")
    # Line 56:  Empty input should be rejected by guardrails.
    assert "REJECTED" in result_empty, f"Empty input not blocked: {result_empty}"

    # Line 58:  Test oversized input (exceeds MAX_INPUT_LENGTH of 500).
    huge_input = "x" * 1000
    # Line 59:  Run with the oversized input.
    result_huge = agent.run(huge_input)
    # Line 60:  Should be rejected for being too long.
    assert "REJECTED" in result_huge, f"Oversized input not blocked: {result_huge}"

    # Line 62:  Test forbidden pattern (code injection attempt).
    hostile = "add 1 and __import__('os').system('rm -rf /')"
    # Line 63:  Run with the hostile input.
    result_hostile = agent.run(hostile)
    # Line 64:  Should be blocked by pattern matching.
    assert "REJECTED" in result_hostile, f"Hostile input not blocked: {result_hostile}"


# ──────────────────────────────────────────────
#  TEST 3: Tool Execution Failure
#  Proves: a failing tool doesn't crash the loop; error is handled
# ──────────────────────────────────────────────
def test_tool_failure():
    # Line 71:  Define a tool that always raises an exception.
    def exploding_tool(a, b):
        # Line 72:  Always raise to simulate a crash in tool execution.
        raise RuntimeError("Simulated tool explosion!")

    # Line 74:  Create agent with the exploding tool registered.
    agent, client, lm, server, logger = _make_agent(tool_funcs={"add": exploding_tool})

    # Line 76:  Run a query that will trigger the exploding tool.
    result = agent.run("add 5 and 3")

    # Line 78:  Result should be a string (not an exception propagating up).
    assert isinstance(result, str), f"Expected string result, got {type(result)}"
    # Line 79:  The result should either indicate failure or be a final answer mentioning the error.
    #          (The LM sees the error in context and produces a final answer about it.)
    assert (
        "explosion" in result.lower()
        or "failed" in result.lower()
        or "INCOMPLETE" in result
    ), f"Tool failure not handled gracefully: {result}"


# ──────────────────────────────────────────────
#  TEST 4: Infinite Loop / Max Iterations
#  Proves: the iteration guardrail stops runaway loops
# ──────────────────────────────────────────────
def test_infinite_loop():
    # Line 88:  Create a standard agent setup.
    agent, client, lm, server, logger = _make_agent()

    # Line 90:  Override think to ALWAYS return a tool_call (never gives final_answer).
    def infinite_think(user_input, context=""):
        # Line 91:  Always try to call 'add' regardless of context (simulates a stuck LM).
        return {"type": "tool_call", "tool": "add", "args": {"a": 1, "b": 2}}

    # Line 93:  Monkey-patch the LM.
    agent.lm.think = infinite_think

    # Line 95:  Run the agent — it must hit the iteration cap and stop.
    result = agent.run("add 1 and 2")

    # Line 97:  Must be a string (no crash).
    assert isinstance(result, str), f"Expected string, got {type(result)}"
    # Line 98:  Must indicate it was stopped by the iteration cap.
    assert (
        "INCOMPLETE" in result or "Stopped" in result
    ), f"Max iterations not enforced: {result}"


# ──────────────────────────────────────────────
#  TEST 5: Server returns malformed JSON-RPC response
#  Proves: client handles garbage server responses without crashing
# ──────────────────────────────────────────────
def test_module_specific():
    # Line 107:  Create a server that returns malformed responses (simulates a broken/malicious server).
    class BrokenServer:
        # Line 109:  Simulate a server that returns garbage for any request.
        def __init__(self):
            # Line 110:  No real state needed.
            pass

        # Line 112:  Return a malformed response (not valid JSON-RPC at all).
        def handle_request(self, raw):
            # Line 113:  Return a string that is not valid JSON (simulates network corruption).
            return "THIS IS NOT VALID JSON {{{"

    # Line 116:  Create a client pointing at the broken server.
    broken_client = MCPClient(BrokenServer())

    # Line 118:  Attempt to connect — should raise ConnectionError (not crash with TypeError etc.).
    try:
        # Line 119:  Try to initialize.
        broken_client.connect()
        # Line 120:  If we get here, the connection somehow succeeded (shouldn't happen with garbage).
        assert False, "BrokenServer.connect() should have raised ConnectionError"
    except ConnectionError as e:
        # Line 122:  Expected: ConnectionError with a clear message.
        assert (
            "initialize failed" in str(e).lower() or "not valid" in str(e).lower()
        ), f"Unexpected error message: {e}"
    except Exception as e:
        # Line 125:  If some other exception type is raised, that's a bug (should be ConnectionError).
        assert (
            False
        ), f"Wrong exception type from broken server: {type(e).__name__}: {e}"

    # Line 128:  Also test: what if server returns valid JSON but wrong structure?
    class WeirdServer:
        # Line 130:  Returns valid JSON but not a proper JSON-RPC response.
        def handle_request(self, raw):
            # Line 131:  Return a dict that has no 'result' or 'error' field.
            return {"something_else": True}

    # Line 134:  Create client for the weird server.
    weird_client = MCPClient(WeirdServer())

    # Line 136:  Connect should "succeed" (no error key) but with empty/odd result.
    try:
        # Line 137:  Attempt connection.
        info = weird_client.connect()
        # Line 138:  It shouldn't crash, but the info will be odd (no 'serverName').
        assert True  # Line 139:  If we get here without exception, that's acceptable.
    except Exception as e:
        # Line 141:  If it does raise, make sure it's a clean error not a crash.
        assert isinstance(
            e, (ConnectionError, RuntimeError)
        ), f"Unexpected exception: {type(e).__name__}"


# ──────────────────────────────────────────────
#  RUNNER
# ──────────────────────────────────────────────
if __name__ == "__main__":
    # Line 148:  Define ANSI codes for pass/fail badges (green bg + white fg / red bg + white fg).
    GREEN_BG = "\033[42;37m"  # Line 149:  Green background, white foreground for PASS.
    RED_BG = "\033[41;37m"  # Line 150:  Red background, white foreground for FAIL.
    RESET = "\033[0m"  # Line 151:  Reset terminal to default colors after badge.
    # Line 152:  Define the list of tests to run (name + function).
    tests = [
        ("Broken LM / Chaotic output", test_broken_lm),
        ("Hostile / Invalid input", test_hostile_input),
        ("Tool execution failure", test_tool_failure),
        ("Infinite loop / Max iterations", test_infinite_loop),
        ("Malformed JSON-RPC response", test_module_specific),
    ]
    # Line 158:  Track how many tests pass.
    passed = 0
    # Line 159:  Iterate through all tests and run them.
    for name, fn in tests:
        # Line 160:  Wrap each test in try/except to catch any unexpected failures.
        try:
            # Line 161:  Execute the test function.
            fn()
            # Line 162:  Print PASS with green background + white foreground badge.
            print(f"  {GREEN_BG}PASS{RESET}  {name}")
            # Line 163:  Increment passed counter.
            passed += 1
        except Exception as e:
            # Line 165:  Print FAIL with red background + white foreground badge.
            print(f"  {RED_BG}FAIL{RESET}  {name}: {e}")
    # Line 167:  Print summary line.
    print(f"\n  {passed}/{len(tests)} tests passed.")
    # Line 168:  If any test failed, exit with non-zero code (for CI integration).
    if passed < len(tests):
        # Line 169:  Exit with status 1 to signal failure.
        sys.exit(1)

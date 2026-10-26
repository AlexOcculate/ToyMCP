# ToyMCP — Tool Discovery via Protocol (JSON-RPC)

> **Module #2** in the TOYAGENTS curriculum. The agent doesn't know what tools exist until it *asks* a server. Add a server = new capabilities, zero agent code change.

**Prerequisite:** understand [ToyA2A](https://github.com/AlexOcculate/TOYAGENTS/tree/main/ToyA2A) (message passing + delegation).

---

## What Is This?

Imagine walking into a restaurant where the menu is not printed in your hand — instead, you ask a waiter "what do you have?" and they tell you. That's what this module teaches: **the agent asks an external server what tools are available, then uses them.** The protocol between them is JSON-RPC (the same shape used by real MCP servers).

The key insight: in Module #0, tools were hardcoded inside the agent. Here, tools live on a *server* that the agent discovers at runtime. You can plug in a whole new server with brand-new tools and the agent's code doesn't change — it just asks again and finds more options.

**Analogy:** Think of it like USB. Your computer (agent) doesn't have a hardcoded list of every device ever made. When you plug in a printer, the OS sends a "hello" message, the printer says "I'm a printer, here's what I can do," and now your computer knows how to talk to it. No driver update needed — just discovery.

---

## Folder Structure

```
ToyMCP/
├── main.py                  # Entry point: wires server, client, LM, and agent loop
├── jsonrpc.py               # JSON-RPC 2.0 protocol layer (request/response framing)
├── mcp_server.py            # MCP Server: hosts tools, responds to protocol methods
├── mcp_client.py            # MCP Client: discovers tools, routes calls via protocol
├── simulated_lm.py          # SimulatedLM: adapts to discovered tool names at runtime
├── trace_logger.py          # ANSI-colored trace logger for all components
├── test_adversarial.py      # Adversarial tests proving system survives failure
└── harness/
    ├── __init__.py          # Makes harness a package
    ├── loop.py              # Agent loop (think → act → observe)
    ├── guardrails.py        # Input validation + max-iteration cap
    └── memory.py            # Simple key-value memory store
```

---

## Dependencies

**External:** None. Pure Python standard library only.

**Stdlib modules used:** `json`, `uuid`, `time`, `re`

**Internal import graph:**

```
main.py
├── mcp_server.py ──► jsonrpc.py
├── mcp_client.py ──► jsonrpc.py
├── simulated_lm.py
├── trace_logger.py
└── harness/
    ├── loop.py
    ├── guardrails.py
    └── memory.py
```

No circular imports. `jsonrpc.py` is a leaf (imports nothing internal). `mcp_server.py` and `mcp_client.py` both depend on it but not on each other.

---

## Execution

```bash
# Run the main demo (shows full MCP discovery flow + dynamic server addition)
python main.py

# Run adversarial tests (proves system survives failure conditions)
python test_adversarial.py
```

No installation needed. No virtual environment required. Just Python 3.8+.

---

## Expected Output

Running `python main.py` produces:

```
[0.000s] [MCP       ] Creating MCP Server 'MathServer'...
[0.001s] [MCP       ] Server 'MathServer' registered 2 tools.
[0.001s] [MCP       ] Creating MCP Client...
[0.001s] [MCP       ] Connecting to server (initialize handshake)...
[0.001s] [MCP       ] Connected to: MathServer
[0.001s] [MCP       ] Discovering tools (tools/list)...
[0.001s] [MCP       ] Discovered 2 tools: ['add', 'subtract']
[0.001s] [MCP       ] Creating SimulatedLM with tools: ['add', 'subtract']

============================================================
  DEMO: Agent using discovered MCP tools
============================================================

  You: add 3 and 7
[0.002s] [LOOP      ] START: "add 3 and 7"
[0.002s] [LOOP      ] Iteration 1
[0.002s] [LM        ] Decision: {"type": "tool_call", "tool": "add", "args": {"a": 3, "b": 7}}
[0.002s] [TOOLS     ] CALL: add({"a": 3, "b": 7})
[0.002s] [TOOLS     ] RESULT: 10
[0.002s] [LOOP      ] Iteration 2
[0.002s] [LM        ] Decision: {"type": "final_answer", "text": "Based on my tool call, the result is: 10"}
[0.002s] [LOOP      ] FINAL: "Based on my tool call, the result is: 10"
  Agent: Based on my tool call, the result is: 10

  You: subtract 10 from 25
  Agent: Based on my tool call, the result is: -15

============================================================
  DEMO: Adding a NEW server at runtime (zero agent code change)
============================================================

[0.003s] [MCP       ] Creating MCP Server 'GeoServer' (new capabilities)...
[0.003s] [MCP       ] Connected to: GeoServer
[0.004s] [MCP       ] Discovered from GeoServer: ['lookup_capital', 'get_weather']
[0.004s] [MCP       ] Updating LM with new tools. Total tools now: ['add', 'subtract', 'lookup_capital', 'get_weather']

  You: lookup capital of France
  Agent: Based on my tool call, the result is: Paris

  You: get weather in Tokyo
  Agent: Based on my tool call, the result is: 22C, sunny

============================================================
  TRACE REPORT (34 entries)
============================================================
  ...
```

Running `python test_adversarial.py` produces:

```
  PASS  Broken LM / Chaotic output
  PASS  Hostile / Invalid input
  PASS  Tool execution failure
  PASS  Infinite loop / Max iterations
  PASS  Malformed JSON-RPC response

  5/5 tests passed.
```

---

## Architecture Diagram

```
+------------------------------------------------------------------+
|                        main.py (wiring)                          |
+------------------------------------------------------------------+
        |                           |                          |
        v                           v                          v
+---------------+        +----------------+        +------------------+
|  MCPServer    |        |   MCPClient    |        |   SimulatedLM    |
|  (hosts tools)|        |  (discovers &  |        |  (decides which  |
|               |        |   routes)      |        |   tool to call)  |
+---------------+        +----------------+        +------------------+
        ^                           |                          |
        |                           v                          |
        |                    +----------------+                |
        |                    |   jsonrpc.py   |                |
        |                    | (protocol layer|                |
        |                    |  build/parse)  |                |
        |                    +----------------+                |
        |                                                      |
        |         +--------------------------------------------+
        |         |
        v         v
+----------------------------------------------------------+
|                   AgentLoop (harness/loop.py)            |
|                                                          |
|   user_input --> [guardrails] --> LM.think()             |
|                                    |                     |
|                    +---------------+---------------+     |
|                    |                               |     |
|              tool_call                        final_answer|
|                    |                               |     |
|                    v                               v     |
|            client.call_tool()                return text |
|                    |                                  |
|                    v                                  |
|            server.handle_request()                    |
|                    |                                  |
|                    v                                  |
|            tool function executes                     |
|                    |                                  |
|                    v                                  |
|            result back to LM (context)  <-------------+
+----------------------------------------------------------+
```

**Reading the diagram:** The AgentLoop is the engine room. It asks the LM "what should I do?" If the LM says "call a tool," the loop hands that request to the MCPClient, which speaks JSON-RPC to the MCPServer. The server runs the actual Python function and sends the result back. The loop feeds the result into context and asks the LM again. This repeats until the LM says "here's my final answer."

**Key separation:** The Server *defines* tools. The Client *discovers and routes*. The AgentLoop *decides when to call*. None of them need to know about the others' internals — only the protocol message shape matters.

---

## State Machine Diagram

```
                    +------------------+
                    |    IDLE          |
                    | (waiting for     |
                    |  user input)     |
                    +------------------+
                          |
                          | user_input arrives
                          v
                    +------------------+
                    | VALIDATING       |
                    | (guardrails check|
                    |  length, patterns|
                    |  emptiness)      |
                    +------------------+
                      /        \
                     /          \
              BLOCKED/            \VALID
                     v              v
             +------------+   +------------------+
             | REJECTED   |   |    THINKING      |
             | (return    |   |  (LM decides:    |
             |  error msg)|   |   tool_call or   |
             +------------+   |   final_answer)   |
                              +------------------+
                                /        \
                               /          \
                        tool_call/          \final_answer
                               v              v
                       +------------+   +------------------+
                       |  ROUTING   |   |    DONE          |
                       | (client    |   |  (return answer  |
                       |  sends     |   |   to user)       |
                       |  JSON-RPC  |   +------------------+
                       |  request)  |
                       +------------+
                            |
                            v
                    +------------------+         +------------------+
                    |  AWAITING        |----yes--|  STOPPED         |
                    |  RESULT          |         | (hit max iter    |
                    |                  |         |  cap, return     |
                    | (server executes |         |  incomplete msg) |
                    |  tool, sends     |         +------------------+
                    |  response)       |
                    +------------------+
                       /        \
                      /          \
               success/          \error
                      v              v
             +------------------+   +------------------+
             | OBSERVING        |   |  OBSERVING       |
             | (result added to |   |  (error added to |
             |  context)        |   |   context)       |
             +------------------+   +------------------+
                    \                  /
                     \                /
                      v              v
                   +------------------+
                   |    THINKING      |  <-- loop back here
                   |  (next iteration)|
                   +------------------+
```

**State descriptions:**

| State           | What happens                     | Exit condition                   |
| --------------- | -------------------------------- | -------------------------------- |
| IDLE            | Waiting for user input           | Input arrives                    |
| VALIDATING      | Guardrails check the input       | Pass or block                    |
| REJECTED        | Input was blocked                | Return error string (terminal)   |
| THINKING        | LM produces a decision dict      | tool_call or final_answer        |
| ROUTING         | Client sends JSON-RPC to server  | Server responds                  |
| AWAITING RESULT | Waiting for server response      | Response received                |
| OBSERVING       | Result/error appended to context | Next iteration starts            |
| DONE            | Final answer produced            | Return to user (terminal)        |
| STOPPED         | Max iterations hit               | Return incomplete msg (terminal) |

**The loop:** THINKING → ROUTING → AWAITING → OBSERVING → THINKING → ... until final_answer or max iterations.

---

## File Reference

### `main.py`

The entry point and demo script. It creates two MCP servers (one with math tools, one with geography/weather tools), connects clients to them, discovers tools, wires up the SimulatedLM and AgentLoop, then runs demo queries. The second half of the file demonstrates the key insight: adding a new server at runtime without modifying any agent code. It also defines a small `MultiMCPClient` wrapper that routes tool calls to the correct server based on which one hosts that tool.

### `jsonrpc.py`

The protocol layer. This is the "wire format" — the shape of messages that travel between client and server. It provides four functions: `build_request` (create a properly formatted JSON-RPC 2.0 request), `build_success_response` and `build_error_response` (create valid responses), and `parse_request` / `parse_response` (validate and decode incoming messages). In production, these would serialize to bytes and go over a socket or HTTP. Here they pass dicts in-process, but the structure is identical.

**Analogy:** This file is like the postal service's envelope format. It doesn't care what's inside the letter — it just makes sure the envelope has the right fields (sender, recipient, tracking number) so the mail system can route it.

### `mcp_server.py`

The server that *hosts* tools. You register Python functions on it with a name, description, and parameter schema. It responds to three protocol methods: `initialize` (handshake — "hello, I'm ready"), `tools/list` ("here's everything I can do"), and `tools/call` ("go ahead, run that function for me"). It enforces the protocol rule that you must initialize before doing anything else. Tool execution errors are caught and returned as structured JSON-RPC error responses — the server never crashes.

### `mcp_client.py`

The client that the agent uses to talk to servers. It has three main methods: `connect()` (perform the initialize handshake), `discover_tools()` (ask the server what's available and cache the results), and `call_tool(name, args)` (route a specific tool invocation). The client maintains a local cache of discovered tools so it can validate that the LM isn't hallucinating tool names. If you try to call a tool the server doesn't have, you get a clean error dict back instead of a crash.

**Analogy:** The client is like a phone operator. You tell it "I need to reach the weather service," and it looks up which extension that is, dials it, passes your message along, and brings back the answer. It doesn't do the weather forecasting itself — it just connects you.

### `simulated_lm.py`

The "brain." In a real system this would be GPT-4 or Claude. Here it's keyword matching. The critical design choice: it receives its list of available tools as a constructor argument (from MCP discovery). It builds a keyword map from those tool names at runtime. If you add new tools and call `update_tools()`, it rebuilds the map — no code changes needed. This proves the LM doesn't have hardcoded knowledge of what tools exist; it learns them from the protocol.

### `trace_logger.py`

Colored terminal output for debugging. Each component (guardrails, LM, tools, loop, MCP) gets its own color so you can visually follow the flow in a dense trace. It also has a `report()` method that prints the full execution log after the run completes — useful for reviewing what happened without scrolling through live output.

### `harness/loop.py`

The agent loop: the think-act-observe cycle. It takes user input, validates it through guardrails, then enters a while-loop where it asks the LM for a decision. If the decision is a tool call, it routes it through the tool router (MCP client) and appends the result to context. If the decision is a final answer, it returns. If it hits the max iteration cap, it stops gracefully. This file is identical in structure to Module #0's loop — the only difference is what "tool_router" points to.

### `harness/guardrails.py`

Input validation and safety limits. Blocks empty input, oversized input (>500 chars), and known hostile patterns (shell commands, code injection, SQL injection). Also provides the max-iteration check that prevents infinite loops. Think of it as airport security — it checks your luggage before you board, so dangerous things never reach the plane.

### `harness/memory.py`

A simple key-value store with timestamps and insertion-order tracking. In this module it's available to tools but not heavily exercised (the demo tools are stateless). It exists because any real agent needs persistent state, and keeping it in the harness means future modules can use it without modification.

### `test_adversarial.py`

Five tests that prove the system survives failure: a broken LM that returns garbage, hostile user input, a tool that crashes, an infinite loop, and a server that returns malformed JSON-RPC. Each test asserts that the system produces a graceful error message rather than crashing with an unhandled exception. Run it after any code change to confirm you haven't broken fault tolerance.

---

## What This Teaches

| Concept                     | Where to look                         | Key insight                                                                                                        |
| --------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Protocol separation         | `jsonrpc.py`                          | The "shape" of messages is independent of what's inside them. Change the tools without changing the protocol.      |
| Discovery at runtime        | `mcp_client.py` → `discover_tools()`  | The agent doesn't know its capabilities until it asks. This is how you add features without redeploying the agent. |
| Server defines, client uses | `mcp_server.py` vs `mcp_client.py`    | Two separate roles. A server can host 1 tool or 100 — the client doesn't care.                                     |
| LM adapts to tools          | `simulated_lm.py` → `update_tools()`  | The brain learns what it can do from the environment, not from hardcoded knowledge.                                |
| Multi-server routing        | `main.py` → `MultiMCPClient`          | When you have multiple servers, routing is just a name-to-client lookup table.                                     |
| Graceful failure            | `test_adversarial.py`                 | A broken server, a crashing tool, or a confused LM should produce an error message — never a stack trace.          |
| Handshake before action     | `mcp_server.py` → `_initialized` flag | You must say "hello" before asking for the menu. Prevents unauthenticated access.                                  |

---

## How This Connects to Real MCP

In production, Model Context Protocol (MCP) servers run as separate processes communicating over stdio or HTTP. The message format is identical to what you see here — JSON-RPC 2.0 with the same method names (`initialize`, `tools/list`, `tools/call`). The only difference is the transport:

| This module                          | Production MCP                               |
| ------------------------------------ | -------------------------------------------- |
| Dict passed in-process               | JSON serialized over stdio pipe or HTTP POST |
| `server.handle_request(dict)`        | Server reads from stdin / receives HTTP body |
| `client._server.handle_request(req)` | Client writes to stdout / sends HTTP request |

If you understand this module, you can read a real MCP server's source code and recognize every pattern. The protocol is the same; only the plumbing changes.

---

## Parent Curriculum

This is Module #2 in the **TOYAGENTS** series:

- [TOYAGENTS on GitHub](https://github.com/AlexOcculate/TOYAGENTS)
- Previous: [Module #1 — ToyA2A (Message passing + delegation)](https://github.com/AlexOcculate/TOYAGENTS/tree/main/ToyA2A)
- Next: [Module #3 — ToyBrain (Wire-level API mechanics)](https://github.com/AlexOcculate/TOYAGENTS/tree/main/ToyBrain)
- 
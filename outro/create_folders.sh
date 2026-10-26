#!/bin/bash

# chmod +x screate_folders.sh

touch main.py                  # Entry point: wires server, client, LM, and agent loop
touch jsonrpc.py               # JSON-RPC 2.0 protocol layer (request/response framing)
touch mcp_server.py            # MCP Server: hosts tools, responds to protocol methods
touch mcp_client.py            # MCP Client: discovers tools, routes calls via protocol
touch simulated_lm.py          # SimulatedLM: adapts to discovered tool names at runtime
touch trace_logger.py          # ANSI-colored trace logger for all components
touch test_adversarial.py      # Adversarial tests proving system survives failure
touch README.md                # Documentation
mkdir -p  Harness/
touch Harness/__init__.py          # Makes harness a package
touch Harness/loop.py              # Agent loop (think → act → observe)
touch Harness/guardrails.py        # Input validation + max-iteration cap
touch Harness/memory.py            # Simple key-value memory store
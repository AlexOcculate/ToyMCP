# Line 1:  Import json for serializing tool calls in trace logs.
import json


# Line 4:  Define the AgentLoop class — the core think-act-observe cycle.
class AgentLoop:
    # Line 6:  Constructor wires up all dependencies the loop needs to function.
    def __init__(self, lm, tool_router, guardrails, memory, logger):
        # Line 7:  Store the language model (brain) that decides what to do next.
        self.lm = lm
        # Line 8:  Store the tool router — in this module it's the MCP client.
        self.tool_router = tool_router
        # Line 9:  Store guardrails for input validation and iteration capping.
        self.guardrails = guardrails
        # Line 10:  Store memory so tools can persist state across iterations.
        self.memory = memory
        # Line 11:  Store the trace logger for colored output of every step.
        self.logger = logger

    # Line 14:  Run the agent loop for a single user message; returns the final answer string.
    def run(self, user_input):
        # Line 15:  Validate input through guardrails before doing any work.
        valid, reason = self.guardrails.validate_input(user_input)
        # Line 16:  If input failed validation, log it and return an error message (no crash).
        if not valid:
            # Line 17:  Log the block with guardrail color (red).
            self.logger.log("guardrails", f"BLOCKED: {reason}")
            # Line 18:  Return a user-friendly rejection message instead of crashing.
            return f"[REJECTED] {reason}"

        # Line 20:  Log that we're starting the loop for this input (green = loop color).
        self.logger.log("loop", f'START: "{user_input}"')

        # Line 22:  Initialize iteration counter to track how many think-act cycles we've done.
        iteration = 0
        # Line 23:  Initialize context string that accumulates tool results for the LM to see.
        context = ""

        # Line 25:  Main loop: keep going until LM says "done" or we hit the iteration cap.
        while True:
            # Line 26:  Increment iteration counter at the start of each cycle.
            iteration += 1
            # Line 27:  Check if we've exceeded the max iterations (infinite loop protection).
            if self.guardrails.should_stop(iteration):
                # Line 28:  Log that we're force-stopping due to iteration cap.
                self.logger.log(
                    "loop",
                    f"STOPPED: hit max iterations ({self.guardrails.max_iterations()})",
                )
                # Line 29:  Return a partial answer indicating the loop was cut short.
                return f"[INCOMPLETE] Stopped after {iteration} iterations without final answer."

            # Line 31:  Log current iteration number so you can follow the trace.
            self.logger.log("loop", f"Iteration {iteration}")

            # Line 33:  THINK: Ask the LM what to do given user input + accumulated context.
            decision = self.lm.think(user_input, context)
            # Line 34:  Log the LM's decision (cyan = LM color).
            self.logger.log("lm", f"Decision: {json.dumps(decision)}")

            # Line 36:  Check what type of decision the LM made.
            decision_type = decision.get("type", "final_answer")

            # Line 38:  If LM wants to call a tool, route it and get the result.
            if decision_type == "tool_call":
                # Line 39:  Extract the tool name from the decision dict.
                tool_name = decision.get("tool", "")
                # Line 40:  Extract the arguments dict for the tool call.
                args = decision.get("args", {})
                # Line 41:  Log which tool is being called (yellow = tools color).
                self.logger.log("tools", f"CALL: {tool_name}({json.dumps(args)})")

                # Line 43:  ACT: Route the tool call through the MCP client (protocol layer).
                result = self.tool_router.call_tool(tool_name, args)

                # Line 45:  Check if the tool call failed (MCP client returns error dict on failure).
                if isinstance(result, dict) and "error" in result:
                    # Line 46:  Log the tool execution error.
                    self.logger.log("tools", f"ERROR: {result['error']}")
                    # Line 47:  Append the error to context so LM can react to it (maybe retry or give up).
                    context += f"\n[Tool '{tool_name}' failed: {result['error']}]"
                else:
                    # Line 49:  Tool succeeded — log the result.
                    self.logger.log("tools", f"RESULT: {result}")
                    # Line 50:  Append the successful result to context for the LM's next thinking step.
                    context += f"\n[Tool '{tool_name}' returned: {result}]"

            # Line 53:  If LM produced a final answer, we're done — return it.
            elif decision_type == "final_answer":
                # Line 54:  Extract the answer text from the decision dict.
                answer = decision.get("text", "")
                # Line 55:  Log the final answer (green = loop/complete color).
                self.logger.log("loop", f'FINAL: "{answer}"')
                # Line 56:  Return the answer to the caller (main.py prints it to user).
                return answer

            # Line 59:  If decision type is something unexpected, log a warning and continue.
            else:
                # Line 60:  Log unknown decision type so developers can debug LM output format issues.
                self.logger.log(
                    "lm",
                    f"WARNING: Unknown decision type '{decision_type}', continuing.",
                )
                # Line 61:  Add a note to context so LM knows its last output was malformed.
                context += "\n[Warning: your last response had an unrecognized type. Use 'tool_call' or 'final_answer.']"

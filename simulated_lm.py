# Line 1:  Import json for building structured decision responses.
import json


# Line 4:  Define the SimulatedLM class — a keyword-matching "brain" that adapts to discovered tools.
class SimulatedLM:
    # Line 6:  Constructor takes the list of available tool names (from MCP discovery).
    def __init__(self, available_tools=None):
        # Line 7:  Store which tools this LM is allowed to call (set dynamically after discovery).
        self.available_tools = available_tools or []
        # Line 8:  Build a keyword-to-tool mapping based on the discovered tool names.
        #          This is the "adaptation" — the LM doesn't hardcode tool names; it learns them.
        self._keyword_map = self._build_keyword_map(self.available_tools)

    # Line 12:  Update the set of available tools (called when a new server is added).
    def update_tools(self, new_tool_names):
        # Line 13:  Merge new tool names with existing ones (deduplicate using a set).
        self.available_tools = list(set(self.available_tools + new_tool_names))
        # Line 14:  Rebuild the keyword map to include the newly discovered tools.
        self._keyword_map = self._build_keyword_map(self.available_tools)

    # Line 17:  Build a mapping from keywords in tool names/descriptions to tool names.
    def _build_keyword_map(self, tool_names):
        # Line 18:  Initialize an empty dict for keyword -> tool_name mappings.
        keyword_map = {}
        # Line 19:  For each tool name, extract meaningful keywords from it.
        for tool_name in tool_names:
            # Line 20:  Split the tool name on underscores to get individual words.
            parts = tool_name.lower().split("_")
            # Line 21:  Map each significant word (len > 2) to this tool name.
            for part in parts:
                # Line 22:  Skip very short fragments that are likely noise (like "a", "to", etc.).
                if len(part) > 2 and part not in ("get", "set", "the", "and"):
                    # Line 23:  Register this keyword as a trigger for this tool.
                    keyword_map[part] = tool_name
            # Line 25:  Also map the full tool name itself (for exact matches).
            keyword_map[tool_name.lower()] = tool_name
        # Line 27:  Return the complete keyword map for matching user input against tools.
        return keyword_map

    # Line 30:  Main thinking function: given user input and context, produce a decision dict.
    def think(self, user_input, context=""):
        # Line 31:  Combine user input and context into one searchable string (lowercase for matching).
        combined_text = (user_input + " " + context).lower()

        # Line 33:  Check if context already contains a tool result (means we already called a tool).
        has_tool_result = "[Tool '" in context and "returned:" in context

        # Line 35:  If we already have a tool result in context, it's time to give the final answer.
        if has_tool_result:
            # Line 36:  Extract the tool result text from context (between "returned:" and "]").
            result_start = context.find("returned:") + len("returned:")
            # Line 37:  Find the closing bracket to extract just the result value.
            result_end = context.find("]", result_start)
            # Line 38:  Get the actual result text (strip whitespace).
            tool_result_text = (
                context[result_start:result_end].strip()
                if result_end > result_start
                else ""
            )
            # Line 39:  Compose a final answer that incorporates the tool result.
            answer = f"Based on my tool call, the result is: {tool_result_text}"
            # Line 40:  Return the final_answer decision type.
            return {"type": "final_answer", "text": answer}

        # Line 43:  No tool result yet — try to match user input to one of our available tools.
        matched_tool = None
        # Line 44:  Check each keyword in our map against the combined input text.
        for keyword, tool_name in self._keyword_map.items():
            # Line 45:  If the keyword appears in the user's input, we have a match.
            if keyword in combined_text:
                # Line 46:  Record the first matching tool (could improve with scoring later).
                matched_tool = tool_name
                # Line 47:  Stop at first match for simplicity (toy project).
                break

        # Line 50:  If we found a matching tool, build a tool_call decision.
        if matched_tool is not None:
            # Line 51:  Extract arguments from the user input based on the tool's expected parameters.
            args = self._extract_args(user_input, matched_tool)
            # Line 52:  Return the tool_call decision with tool name and extracted arguments.
            return {"type": "tool_call", "tool": matched_tool, "args": args}

        # Line 55:  No tool matched — this is a general question we can answer directly.
        # Line 56:  Provide a simple acknowledgment as the final answer.
        answer = f'I don\'t have a tool for that. You asked: "{user_input}". Available tools: {self.available_tools}'
        # Line 57:  Return as final_answer since no tool is applicable.
        return {"type": "final_answer", "text": answer}

    # Line 60:  Extract arguments from user input for a given tool (simple numeric/string extraction).
    def _extract_args(self, user_input, tool_name):
        # Line 61:  Initialize an empty args dict to populate.
        args = {}
        # Line 62:  Get the parameter schema for this tool from our discovered info.
        #          (In a real system, this would come from the MCP tools/list response.)
        param_names = self._get_param_names(tool_name)

        # Line 65:  Try to extract numeric values from the input (for math tools).
        import re

        # Line 66:  Find all numbers (integers and decimals) in the user input.
        numbers = re.findall(r"-?\d+\.?\d*", user_input)

        # Line 68:  If the tool expects numeric parameters, fill them with extracted numbers.
        if param_names:
            # Line 69:  For each expected parameter, try to assign a number from the input.
            for i, param_name in enumerate(param_names):
                # Line 70:  If we have enough numbers, assign the next one.
                if i < len(numbers):
                    # Line 71:  Try to convert to int first, fall back to float, then string.
                    try:
                        # Line 72:  Attempt integer conversion (most common for toy math tools).
                        args[param_name] = int(numbers[i])
                    except ValueError:
                        # Line 74:  If not a clean int, try float.
                        try:
                            # Line 75:  Convert to floating point number.
                            args[param_name] = float(numbers[i])
                        except ValueError:
                            # Line 77:  Last resort: keep as string.
                            args[param_name] = numbers[i]
                else:
                    # Line 80:  Not enough numbers in input; use default of 0 for missing params.
                    args[param_name] = 0

        # Line 83:  If no parameter names are known, try a generic "query" param for lookup tools.
        if not param_names and tool_name.startswith(("lookup", "get_", "search")):
            # Line 84:  Use the entire user input (minus command words) as the query string.
            args["query"] = user_input.strip()

        # Line 86:  Return the extracted arguments dict.
        return args

    # Line 89:  Get parameter names for a tool based on its name pattern (simplified schema inference).
    def _get_param_names(self, tool_name):
        # Line 90:  For math tools (add, subtract, multiply), expect two numeric params.
        if tool_name in ("add", "subtract", "multiply", "divide"):
            # Line 91:  Return the standard a/b parameter names for binary math operations.
            return ["a", "b"]
        # Line 93:  For weather tools, expect a location/city parameter.
        if "weather" in tool_name:
            # Line 94:  Return "city" as the expected parameter name.
            return ["city"]
        # Line 96:  For capital lookup, expect a country name parameter.
        if "capital" in tool_name:
            # Line 97:  Return "country" as the expected parameter name.
            return ["country"]
        # Line 99:  For memory tools, expect key and value parameters.
        if "memory_store" in tool_name:
            # Line 100:  Memory store needs both a key and a value.
            return ["key", "value"]
        if "memory_recall" in tool_name:
            # Line 102:  Memory recall just needs the key to look up.
            return ["key"]
        # Line 104:  Unknown tool pattern — return empty list (no params expected).
        return []

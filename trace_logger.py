# Line 1:  Import time for timestamping log entries.
import time


# Line 4:  Define ANSI color codes as constants (no external packages needed for terminal colors).
class Colors:
    # Line 6:  Reset code to return terminal to default colors after a colored segment.
    RESET = "\033[0m"
    # Line 8:  Bold text modifier.
    BOLD = "\033[1m"
    # Line 10:  Foreground colors for different components.
    RED = "\033[91m"  # Line 11:  Guardrails (blocks, rejections).
    CYAN = "\033[96m"  # Line 12:  LM decisions and MCP protocol messages.
    YELLOW = "\033[93m"  # Line 13:  Tool calls and results.
    GREEN = "\033[92m"  # Line 14:  Loop lifecycle (start, stop, final answer).
    MAGENTA = "\033[95m"  # Line 15:  MCP-specific messages (server/client interaction).
    BLUE = "\033[94m"  # Line 16:  Memory operations.
    WHITE = "\033[97m"  # Line 17:  General info / neutral messages.
    # Line 19:  Background colors for status badges.
    BG_GREEN = (
        "\033[42;30m"  # Line 20:  Light green background + black text (success/valid).
    )
    BG_RED = (
        "\033[41;37m"  # Line 21:  Light red background + white text (blocked/error).
    )
    BG_YELLOW = "\033[43;30m"  # Line 22:  Light yellow background + black text (warning/stopped).


# Line 25:  Define the TraceLogger class — collects and displays colored execution traces.
class TraceLogger:
    # Line 27:  Constructor initializes an empty log buffer.
    def __init__(self):
        # Line 28:  Store log entries as a list of (timestamp, component, message) tuples.
        self.entries = []
        # Line 29:  Track whether we've started a new "session" (for report formatting).
        self.session_start = None

    # Line 32:  Map component names to their ANSI color codes.
    def _get_color(self, component):
        # Line 33:  Dict mapping each component type to its assigned color.
        color_map = {
            "guardrails": Colors.RED,  # Line 34:  Guardrail actions are red (safety).
            "lm": Colors.CYAN,  # Line 35:  LM decisions are cyan (intelligence).
            "tools": Colors.YELLOW,  # Line 36:  Tool execution is yellow (action).
            "loop": Colors.GREEN,  # Line 37:  Loop lifecycle is green (flow).
            "mcp": Colors.MAGENTA,  # Line 38:  MCP protocol messages are magenta (protocol layer).
            "memory": Colors.BLUE,  # Line 39:  Memory operations are blue (state).
        }
        # Line 41:  Return the color for this component, or white if unknown.
        return color_map.get(component, Colors.WHITE)

    # Line 44:  Log a single entry with component name and message.
    def log(self, component, message):
        # Line 45:  Get current timestamp for this entry.
        ts = time.time()
        # Line 46:  If this is the first entry in the session, record the start time.
        if self.session_start is None:
            # Line 47:  Set session start to now (used for relative timing in reports).
            self.session_start = ts
        # Line 49:  Store the entry in our buffer.
        self.entries.append((ts, component, message))
        # Line 50:  Print the colored entry immediately to terminal (real-time feedback).
        color = self._get_color(component)
        # Line 51:  Format with timestamp offset, colored component tag, and message.
        offset = ts - self.session_start
        # Line 52:  Build the display string with ANSI codes.
        line = f"{Colors.BOLD}[{offset:.3f}s]{Colors.RESET} {color}[{component.upper():<10}]{Colors.RESET} {message}"
        # Line 53:  Print to stdout (flush=True ensures it appears immediately in terminal).
        print(line, flush=True)

    # Line 56:  Log a status badge (colored background for valid/blocked/stopped indicators).
    def log_badge(self, component, message, status="valid"):
        # Line 57:  Determine which background color to use based on status.
        if status == "valid" or status == "success":
            # Line 58:  Green background for positive outcomes.
            bg = Colors.BG_GREEN
        elif status == "blocked" or status == "error":
            # Line 60:  Red background for negative outcomes.
            bg = Colors.BG_RED
        else:
            # Line 62:  Yellow background for warnings and stops.
            bg = Colors.BG_YELLOW
        # Line 64:  Get the component's foreground color for the tag.
        color = self._get_color(component)
        # Line 65:  Build the badge line with colored background status indicator.
        ts = time.time()
        # Line 66:  Calculate offset from session start.
        offset = (ts - self.session_start) if self.session_start else 0
        # Line 67:  Format and print the badge.
        line = f"{Colors.BOLD}[{offset:.3f}s]{Colors.RESET} {color}[{component.upper():<10}]{Colors.RESET} {bg}{message}{Colors.RESET}"
        # Line 68:  Store in buffer and print.
        self.entries.append((ts, component, message))
        print(line, flush=True)

    # Line 71:  Print a full report of all logged entries (called after execution completes).
    def report(self):
        # Line 72:  Print a separator line to visually mark the start of the report.
        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        # Line 73:  Print the report header.
        print(
            f"{Colors.BOLD}  TRACE REPORT ({len(self.entries)} entries){Colors.RESET}"
        )
        # Line 74:  Print another separator.
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        # Line 75:  Iterate through all entries and print them with full formatting.
        for ts, component, message in self.entries:
            # Line 76:  Calculate relative time offset.
            offset = (ts - self.session_start) if self.session_start else 0
            # Line 77:  Get the component color.
            color = self._get_color(component)
            # Line 78:  Format and print each entry in the report.
            print(
                f"  {offset:>7.3f}s  {color}[{component.upper():<10}]{Colors.RESET}  {message}"
            )
        # Line 80:  Print closing separator.
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")

    # Line 83:  Clear all logged entries (useful between test cases).
    def clear(self):
        # Line 84:  Empty the entries list.
        self.entries = []
        # Line 85:  Reset session start time.
        self.session_start = None

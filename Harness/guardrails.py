# Line 1:  Import re for pattern-based input validation (detecting hostile patterns).
import re

# Line 4:  Define constants for guardrail limits — these are the "safety rails" of the system.
MAX_INPUT_LENGTH = 500  # Line 5:  Maximum characters allowed in a user message (prevents memory abuse).
MAX_ITERATIONS = 10  # Line 6:  Maximum think-act-observe cycles before we force-stop (prevents infinite loops).
FORBIDDEN_PATTERNS = [  # Line 7:  List of regex patterns that indicate hostile/malicious input.
    r"rm\s+-rf",  # Line 8:  Block shell commands that recursively delete files.
    r"__import__",  # Line 9:  Block Python's dynamic import (code injection vector).
    r"eval\s*\(",  # Line 10: Block eval() calls (arbitrary code execution).
    r"exec\s*\(",  # Line 11: Block exec() calls (arbitrary code execution).
    r";\s*DROP",  # Line 12: Block SQL injection attempts (DROP TABLE, etc.).
]


# Line 16:  Define the Guardrails class — a gatekeeper that validates input before it reaches the agent.
class Guardrails:
    # Line 18:  Constructor takes no args; limits are class-level constants defined above.
    def __init__(self):
        # Line 19:  Compile all forbidden patterns once for efficiency (avoids recompiling per check).
        self._compiled_patterns = [re.compile(p) for p in FORBIDDEN_PATTERNS]

    # Line 22:  Validate a user input string; returns (is_valid: bool, reason: str).
    def validate_input(self, text):
        # Line 23:  If input is None or empty, it's invalid (agent needs something to work with).
        if not text or not text.strip():
            # Line 24:  Return invalid with a clear reason so the caller can log it.
            return False, "Input is empty or whitespace-only."
        # Line 26:  Check if input exceeds the maximum allowed length (DoS protection).
        if len(text) > MAX_INPUT_LENGTH:
            # Line 27:  Return invalid with the specific length violation reason.
            return False, f"Input too long ({len(text)} chars, max {MAX_INPUT_LENGTH})."
        # Line 29:  Check each forbidden pattern against the input text.
        for pattern in self._compiled_patterns:
            # Line 30:  If any forbidden pattern matches, the input is hostile.
            if pattern.search(text):
                # Line 31:  Return invalid and name which pattern triggered the block.
                return False, f"Blocked by pattern: {pattern.pattern}"
        # Line 33:  All checks passed — input is safe to process.
        return True, "OK"

    # Line 36:  Check whether we've hit the iteration cap; returns True if we should stop.
    def should_stop(self, current_iteration):
        # Line 37:  If current iteration count meets or exceeds our cap, it's time to halt.
        return current_iteration >= MAX_ITERATIONS

    # Line 40:  Return the max iterations constant (useful for logging "stopped at N/MAX").
    def max_iterations(self):
        # Line 41:  Simply return the class-level constant so callers don't need to import it.
        return MAX_ITERATIONS

"""Sandbox Guard - Command filtering middleware for safety."""

import re
from dataclasses import dataclass
from typing import Callable

from openhands.sdk import Event


@dataclass
class SandboxViolation:
    """Represents a sandbox policy violation."""

    command: str
    matched_pattern: str
    message: str


class SandboxGuard:
    """Middleware that intercepts terminal commands and checks against a blacklist.

    The SandboxGuard provides a safety layer by filtering commands before
    they are executed, preventing potentially destructive operations.
    """

    # Default dangerous commands that should be blocked
    DEFAULT_BLACKLIST = [
        r"rm\s+-rf\s+/\s*$",  # rm -rf /
        r"rm\s+-rf\s+/\*",  # rm -rf /*
        r"rm\s+-rf\s+~",  # rm -rf ~
        r"rm\s+-rf\s+\$HOME",  # rm -rf $HOME
        r"mkfs\.",  # mkfs.* commands
        r"dd\s+.*of=/dev/",  # dd to device files
        r">\s*/dev/sd[a-z]",  # Overwrite disk devices
        r"chmod\s+-R\s+777\s+/",  # Dangerous chmod on root
        r"chown\s+-R\s+.*\s+/\s*$",  # chown on root
        r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",  # Fork bomb
        r"wget.*\|.*sh",  # Download and execute
        r"curl.*\|.*sh",  # Download and execute
        r"curl.*\|.*bash",  # Download and execute
    ]

    def __init__(
        self,
        blacklist: list[str] | None = None,
        on_violation: Callable[[SandboxViolation], None] | None = None,
    ):
        """Initialize the sandbox guard.

        Args:
            blacklist: List of regex patterns for commands to block.
                       If None, uses DEFAULT_BLACKLIST.
            on_violation: Callback function called when a violation is detected.
        """
        patterns = blacklist if blacklist is not None else self.DEFAULT_BLACKLIST
        self._patterns = [re.compile(p, re.IGNORECASE) for p in patterns]
        self._raw_patterns = patterns
        self._on_violation = on_violation
        self._violations: list[SandboxViolation] = []

    @property
    def violations(self) -> list[SandboxViolation]:
        """Get all recorded violations."""
        return self._violations.copy()

    def check_command(self, command: str) -> SandboxViolation | None:
        """Check if a command violates the sandbox policy.

        Args:
            command: The command string to check

        Returns:
            SandboxViolation if blocked, None if allowed
        """
        for pattern, raw_pattern in zip(self._patterns, self._raw_patterns):
            if pattern.search(command):
                violation = SandboxViolation(
                    command=command,
                    matched_pattern=raw_pattern,
                    message=f"Command blocked by sandbox guard: matches '{raw_pattern}'",
                )
                self._violations.append(violation)

                if self._on_violation:
                    self._on_violation(violation)

                return violation

        return None

    def is_allowed(self, command: str) -> bool:
        """Check if a command is allowed.

        Args:
            command: The command string to check

        Returns:
            True if allowed, False if blocked
        """
        return self.check_command(command) is None

    def filter_event(self, event: Event) -> Event | None:
        """Filter an event, blocking TerminalAction events with forbidden commands.

        This can be used as an event callback/filter in the conversation.

        Args:
            event: The event to filter

        Returns:
            The event if allowed, None if blocked
        """
        # Check if this is a terminal action event
        if hasattr(event, "command"):
            command = getattr(event, "command", "")
            if command and not self.is_allowed(command):
                return None

        return event

    def add_pattern(self, pattern: str) -> None:
        """Add a new pattern to the blacklist.

        Args:
            pattern: Regex pattern to add
        """
        self._patterns.append(re.compile(pattern, re.IGNORECASE))
        self._raw_patterns.append(pattern)

    def clear_violations(self) -> None:
        """Clear the recorded violations."""
        self._violations.clear()

    @classmethod
    def from_config(cls, command_blacklist: list[str]) -> "SandboxGuard":
        """Create a SandboxGuard from configuration.

        Args:
            command_blacklist: List of command patterns from config

        Returns:
            A configured SandboxGuard instance
        """
        # Combine default and config blacklists
        combined = cls.DEFAULT_BLACKLIST + command_blacklist
        return cls(blacklist=combined)


class SandboxError(Exception):
    """Exception raised when a sandbox violation occurs."""

    def __init__(self, violation: SandboxViolation):
        self.violation = violation
        super().__init__(violation.message)

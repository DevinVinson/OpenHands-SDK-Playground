"""Event formatting utilities for OpenHands Lab."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from openhands.sdk import Event


@dataclass
class FormattedEvent:
    """A formatted event for display in UI."""

    timestamp: str
    event_type: str
    role: str  # "agent", "user", "system", "tool"
    content: str
    raw_data: dict[str, Any] | None = None


class EventFormatter:
    """Formats SDK events for display in the UI."""

    # Map event types to roles
    ROLE_MAP = {
        "MessageEvent": "user",
        "ThinkEvent": "agent",
        "ActionEvent": "agent",
        "ObservationEvent": "tool",
        "SystemEvent": "system",
        "ErrorEvent": "system",
    }

    def format(self, event: Event) -> FormattedEvent:
        """Format a single event for display.

        Args:
            event: The SDK event to format

        Returns:
            A formatted event ready for display
        """
        event_type = type(event).__name__
        role = self._get_role(event_type)
        content = self._extract_content(event)
        raw_data = event.model_dump() if hasattr(event, "model_dump") else None

        return FormattedEvent(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            event_type=event_type,
            role=role,
            content=content,
            raw_data=raw_data,
        )

    def _get_role(self, event_type: str) -> str:
        """Determine the role based on event type."""
        for key, role in self.ROLE_MAP.items():
            if key in event_type:
                return role
        return "system"

    def _extract_content(self, event: Event) -> str:
        """Extract displayable content from an event."""
        # Try common content attributes
        if hasattr(event, "content"):
            return str(event.content)
        if hasattr(event, "message"):
            return str(event.message)
        if hasattr(event, "text"):
            return str(event.text)
        if hasattr(event, "thought"):
            return str(event.thought)

        # Check for to_llm_content (Observation types)
        if hasattr(event, "to_llm_content"):
            try:
                content_parts = event.to_llm_content
                texts = []
                for part in content_parts:
                    if hasattr(part, "text"):
                        texts.append(part.text)
                if texts:
                    return "\n".join(texts)
            except Exception:
                pass

        # Fall back to string representation
        return str(event)


def format_event_for_display(event: Event) -> FormattedEvent:
    """Convenience function to format a single event.

    Args:
        event: The SDK event to format

    Returns:
        A formatted event ready for display
    """
    formatter = EventFormatter()
    return formatter.format(event)

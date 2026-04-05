"""Session management for OpenHands Lab."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import SecretStr

from openhands.sdk import (
    LLM,
    Agent,
    Conversation,
    ConversationCallbackType,
    Event,
    LocalWorkspace,
    Tool,
)
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.terminal import TerminalTool

from lab.core.config import AgentConfig, ConfigLoader, LabConfig
from lab.tools import ToolLoader


class EventTracer:
    """Collects events from a conversation for session tracing."""

    def __init__(self):
        self.events: list[dict[str, Any]] = []
        self.start_time: datetime = datetime.now()

    def __call__(self, event: Event) -> None:
        """Callback to capture events."""
        self.events.append({
            "timestamp": datetime.now().isoformat(),
            "type": type(event).__name__,
            "data": event.model_dump() if hasattr(event, "model_dump") else str(event),
        })

    def to_dict(self) -> dict[str, Any]:
        """Export trace as a dictionary."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "event_count": len(self.events),
            "events": self.events,
        }


class LabSession:
    """A single agent session wrapping the OpenHands SDK Conversation.

    LabSession provides:
    - Configuration-driven agent setup
    - Event tracing for auditability
    - Session lifecycle management
    """

    def __init__(
        self,
        agent_config: AgentConfig,
        settings: LabConfig,
        workspace_dir: str | Path | None = None,
        session_id: str | None = None,
        callbacks: list[ConversationCallbackType] | None = None,
    ):
        self.agent_config = agent_config
        self.settings = settings
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.workspace_dir = Path(workspace_dir or settings.runtime.working_dir)
        self.tracer = EventTracer()

        # Combine user callbacks with our tracer
        self._callbacks = [self.tracer]
        if callbacks:
            self._callbacks.extend(callbacks)

        # Initialize components
        self._llm: LLM | None = None
        self._agent: Agent | None = None
        self._conversation: Conversation | None = None
        self._workspace: LocalWorkspace | None = None

    @property
    def llm(self) -> LLM:
        """Get or create the LLM instance."""
        if self._llm is None:
            api_key = os.getenv(self.settings.llm.api_key_env)
            if not api_key:
                raise ValueError(
                    f"API key not found in environment variable: "
                    f"{self.settings.llm.api_key_env}"
                )

            # Priority: env var > agent config > settings.yaml
            model = (
                os.getenv("LLM_MODEL")
                or self.agent_config.model
                or self.settings.llm.model
            )
            base_url = os.getenv("LLM_BASE_URL") or self.settings.llm.base_url

            self._llm = LLM(
                model=model,
                api_key=SecretStr(api_key),
                base_url=base_url,
            )
        return self._llm

    @property
    def workspace(self) -> LocalWorkspace:
        """Get or create the workspace."""
        if self._workspace is None:
            self._workspace = LocalWorkspace(working_dir=self.workspace_dir)
        return self._workspace

    @property
    def agent(self) -> Agent:
        """Get or create the agent instance."""
        if self._agent is None:
            tools = self._resolve_tools()
            self._agent = Agent(
                llm=self.llm,
                tools=tools,
                system_message=self.agent_config.system_prompt or None,
            )
        return self._agent

    @property
    def conversation(self) -> Conversation:
        """Get or create the conversation instance."""
        if self._conversation is None:
            self._conversation = Conversation(
                agent=self.agent,
                workspace=self.workspace,
                callbacks=self._callbacks,
            )
        return self._conversation

    def _resolve_tools(self) -> list[Tool]:
        """Resolve tool configurations to Tool instances."""
        tools = []
        tool_map = {
            "terminal": TerminalTool.name,
            "file_editor": FileEditorTool.name,
            "task_tracker": TaskTrackerTool.name,
        }

        for tool_config in self.agent_config.tools:
            if not tool_config.enabled:
                continue

            # Map common names to SDK tool names
            tool_name = tool_map.get(tool_config.name, tool_config.name)
            tools.append(Tool(name=tool_name))

        # Default tools if none specified
        if not tools:
            tools = [
                Tool(name=TerminalTool.name),
                Tool(name=FileEditorTool.name),
                Tool(name=TaskTrackerTool.name),
            ]

        return tools

    def send_message(self, message: str) -> None:
        """Send a message to the agent."""
        self.conversation.send_message(message)

    def run(self) -> None:
        """Run the agent until completion."""
        self.conversation.run()

    def save_trace(self, output_dir: str | Path | None = None) -> Path:
        """Save the session trace to a JSON file.

        Args:
            output_dir: Directory to save the trace. Defaults to .oh-lab/

        Returns:
            Path to the saved trace file
        """
        output_dir = Path(output_dir or self.settings.session_log_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        trace_file = output_dir / f"session_{self.session_id}_trace.json"
        trace_data = {
            "session_id": self.session_id,
            "agent": self.agent_config.name,
            "workspace": str(self.workspace_dir),
            **self.tracer.to_dict(),
        }

        with open(trace_file, "w") as f:
            json.dump(trace_data, f, indent=2, default=str)

        return trace_file

    def close(self) -> None:
        """Clean up session resources."""
        if self._conversation is not None:
            # Save trace before closing
            self.save_trace()


class SessionManager:
    """Manages multiple lab sessions with configuration loading."""

    def __init__(self, config_dir: str | Path = "config"):
        self.config = ConfigLoader(config_dir)
        self._sessions: dict[str, LabSession] = {}
        self.tool_loader = ToolLoader()
        self.tool_loader.scan_and_load()

    @property
    def settings(self) -> LabConfig:
        """Get global settings."""
        return self.config.settings

    @property
    def agents(self) -> dict[str, AgentConfig]:
        """Get all available agents."""
        return self.config.agents

    def create_session(
        self,
        agent_name: str,
        workspace_dir: str | Path | None = None,
        session_id: str | None = None,
        callbacks: list[ConversationCallbackType] | None = None,
    ) -> LabSession:
        """Create a new session for an agent.

        Args:
            agent_name: Name of the agent to use
            workspace_dir: Working directory for the session
            session_id: Optional session identifier
            callbacks: Optional event callbacks

        Returns:
            A new LabSession instance
        """
        agent_config = self.config.get_agent(agent_name)
        session = LabSession(
            agent_config=agent_config,
            settings=self.settings,
            workspace_dir=workspace_dir,
            session_id=session_id,
            callbacks=callbacks,
        )

        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> LabSession | None:
        """Get an existing session by ID."""
        return self._sessions.get(session_id)

    def close_session(self, session_id: str) -> None:
        """Close and remove a session."""
        session = self._sessions.pop(session_id, None)
        if session:
            session.close()

    def close_all(self) -> None:
        """Close all sessions."""
        for session_id in list(self._sessions.keys()):
            self.close_session(session_id)

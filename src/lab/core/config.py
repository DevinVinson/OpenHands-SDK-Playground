"""Configuration loading and parsing for OpenHands Lab."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ToolConfig(BaseModel):
    """Configuration for a single tool."""

    name: str
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Configuration for an agent (persona + toolset)."""

    name: str
    description: str = ""
    system_prompt: str = ""
    tools: list[ToolConfig] = Field(default_factory=list)
    model: str | None = None


class LLMSettings(BaseModel):
    """LLM configuration settings."""

    model: str = "anthropic/claude-sonnet-4-5-20250929"
    api_key_env: str = "LLM_API_KEY"
    base_url: str | None = None
    temperature: float = 0.0
    max_tokens: int = 4096


class RuntimeSettings(BaseModel):
    """Runtime environment settings."""

    environment: str = "local"  # "local" or "docker"
    working_dir: str = "."
    docker_image: str | None = None
    command_blacklist: list[str] = Field(default_factory=list)


class LabConfig(BaseModel):
    """Global lab configuration."""

    llm: LLMSettings = Field(default_factory=LLMSettings)
    runtime: RuntimeSettings = Field(default_factory=RuntimeSettings)
    session_log_dir: str = ".oh-lab"


class ConfigLoader:
    """Loads and parses YAML configuration files for OpenHands Lab."""

    def __init__(self, config_dir: str | Path = "config"):
        self.config_dir = Path(config_dir)
        self._agents: dict[str, AgentConfig] = {}
        self._settings: LabConfig | None = None

    @property
    def settings(self) -> LabConfig:
        """Get global settings, loading from file if needed."""
        if self._settings is None:
            self._settings = self._load_settings()
        return self._settings

    @property
    def agents(self) -> dict[str, AgentConfig]:
        """Get all agents, loading from file if needed."""
        if not self._agents:
            self._agents = self._load_agents()
        return self._agents

    def _load_settings(self) -> LabConfig:
        """Load settings from settings.yaml."""
        settings_path = self.config_dir / "settings.yaml"
        if not settings_path.exists():
            return LabConfig()

        with open(settings_path) as f:
            data = yaml.safe_load(f) or {}

        return LabConfig(**data)

    def _load_agents(self) -> dict[str, AgentConfig]:
        """Load agents from agents.yaml."""
        agents_path = self.config_dir / "agents.yaml"
        if not agents_path.exists():
            return {}

        with open(agents_path) as f:
            data = yaml.safe_load(f) or {}

        agents = {}
        for name, config in data.get("agents", {}).items():
            # Parse tools list
            tools = []
            for tool_data in config.get("tools", []):
                if isinstance(tool_data, str):
                    tools.append(ToolConfig(name=tool_data))
                elif isinstance(tool_data, dict):
                    tools.append(ToolConfig(**tool_data))

            agents[name] = AgentConfig(
                name=name,
                description=config.get("description", ""),
                system_prompt=config.get("system_prompt", ""),
                tools=tools,
                model=config.get("model"),
            )

        return agents

    def get_agent(self, name: str) -> AgentConfig:
        """Get a specific agent by name.

        Args:
            name: The agent identifier

        Returns:
            The agent configuration

        Raises:
            KeyError: If the agent doesn't exist
        """
        if name not in self.agents:
            available = list(self.agents.keys())
            raise KeyError(
                f"Agent '{name}' not found. Available: {available}"
            )
        return self.agents[name]

    def reload(self) -> None:
        """Force reload of all configuration files."""
        self._settings = None
        self._agents = {}

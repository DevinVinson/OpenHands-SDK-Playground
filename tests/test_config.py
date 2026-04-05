"""Tests for configuration loading."""

import tempfile
from pathlib import Path

import pytest
import yaml

from lab.core.config import ConfigLoader, LabConfig, AgentConfig


class TestConfigLoader:
    """Tests for ConfigLoader."""

    def test_default_settings(self):
        """Test that default settings are returned when no file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ConfigLoader(config_dir=tmpdir)
            settings = loader.settings

            assert isinstance(settings, LabConfig)
            assert settings.llm.model == "anthropic/claude-sonnet-4-5-20250929"
            assert settings.runtime.environment == "local"

    def test_load_settings_from_file(self):
        """Test loading settings from a YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            settings_file = config_dir / "settings.yaml"

            settings_data = {
                "llm": {
                    "model": "gpt-4",
                    "api_key_env": "OPENAI_API_KEY",
                },
                "runtime": {
                    "environment": "docker",
                    "docker_image": "python:3.12",
                },
            }

            with open(settings_file, "w") as f:
                yaml.dump(settings_data, f)

            loader = ConfigLoader(config_dir=tmpdir)
            settings = loader.settings

            assert settings.llm.model == "gpt-4"
            assert settings.llm.api_key_env == "OPENAI_API_KEY"
            assert settings.runtime.environment == "docker"
            assert settings.runtime.docker_image == "python:3.12"

    def test_load_agents(self):
        """Test loading agents from a YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            agents_file = config_dir / "agents.yaml"

            agents_data = {
                "agents": {
                    "test-case": {
                        "description": "Test agent",
                        "system_prompt": "You are a test assistant.",
                        "tools": ["terminal", "file_editor"],
                        "model": "claude-3-opus",
                    }
                }
            }

            with open(agents_file, "w") as f:
                yaml.dump(agents_data, f)

            loader = ConfigLoader(config_dir=tmpdir)
            agents = loader.agents

            assert "test-case" in agents
            agent = agents["test-case"]
            assert agent.name == "test-case"
            assert agent.description == "Test agent"
            assert agent.system_prompt == "You are a test assistant."
            assert len(agent.tools) == 2
            assert agent.model == "claude-3-opus"

    def test_get_agent(self):
        """Test getting a specific agent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            agents_file = config_dir / "agents.yaml"

            agents_data = {
                "agents": {
                    "existing": {"description": "Exists"},
                }
            }

            with open(agents_file, "w") as f:
                yaml.dump(agents_data, f)

            loader = ConfigLoader(config_dir=tmpdir)

            # Should work for existing agent
            agent = loader.get_agent("existing")
            assert agent.name == "existing"

            # Should raise KeyError for non-existing agent
            with pytest.raises(KeyError):
                loader.get_agent("non-existing")

    def test_reload(self):
        """Test configuration reload."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            settings_file = config_dir / "settings.yaml"

            # Initial settings
            with open(settings_file, "w") as f:
                yaml.dump({"llm": {"model": "model-v1"}}, f)

            loader = ConfigLoader(config_dir=tmpdir)
            assert loader.settings.llm.model == "model-v1"

            # Update settings
            with open(settings_file, "w") as f:
                yaml.dump({"llm": {"model": "model-v2"}}, f)

            # Reload
            loader.reload()
            assert loader.settings.llm.model == "model-v2"

    def test_tools_config_parsing(self):
        """Test parsing tools with different formats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            agents_file = config_dir / "agents.yaml"

            agents_data = {
                "agents": {
                    "mixed-tools": {
                        "tools": [
                            "terminal",  # Simple string
                            {"name": "file_editor", "enabled": True},  # Dict
                            {"name": "disabled_tool", "enabled": False},
                        ],
                    }
                }
            }

            with open(agents_file, "w") as f:
                yaml.dump(agents_data, f)

            loader = ConfigLoader(config_dir=tmpdir)
            agent = loader.get_agent("mixed-tools")

            assert len(agent.tools) == 3
            assert agent.tools[0].name == "terminal"
            assert agent.tools[0].enabled is True
            assert agent.tools[1].name == "file_editor"
            assert agent.tools[1].enabled is True
            assert agent.tools[2].name == "disabled_tool"
            assert agent.tools[2].enabled is False

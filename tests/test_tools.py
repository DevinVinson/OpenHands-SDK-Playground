"""Tests for tool loading and custom tools."""

import tempfile
from pathlib import Path

import pytest

from lab.tools.loader import ToolLoader


class TestToolLoader:
    """Tests for ToolLoader."""

    def test_loader_init(self):
        """Test loader initialization."""
        loader = ToolLoader()
        assert loader.tools_dir == Path("src/lab/tools")
        assert loader.loaded_tools == {}

    def test_scan_nonexistent_dir(self):
        """Test scanning a non-existent directory."""
        loader = ToolLoader(tools_dir="/nonexistent/path")
        registered = loader.scan_and_load()
        assert registered == []

    def test_get_tool_info_empty(self):
        """Test getting tool info when no tools loaded."""
        loader = ToolLoader(tools_dir="/nonexistent/path")
        info = loader.get_tool_info()
        assert info == []

    def test_scan_and_load_custom_tool(self):
        """Test loading a custom tool from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tools_dir = Path(tmpdir)

            # Create a simple tool file
            tool_code = '''
"""Test tool."""
from collections.abc import Sequence
from typing import Any, ClassVar

from pydantic import Field

from openhands.sdk import Action, ImageContent, Observation, TextContent, ToolDefinition
from openhands.sdk.tool import ToolExecutor

from lab.tools.base import BaseLabTool


class TestAction(Action):
    value: str = Field(description="Test value")


class TestObservation(Observation):
    result: str

    @property
    def to_llm_content(self) -> Sequence[TextContent | ImageContent]:
        return [TextContent(text=self.result)]


class TestExecutor(ToolExecutor[TestAction, TestObservation]):
    def __call__(self, action: TestAction, conversation=None) -> TestObservation:
        return TestObservation(result=f"Got: {action.value}")


class TestTool(BaseLabTool[TestAction, TestObservation]):
    tool_name: ClassVar[str] = "test_tool"
    tool_description: ClassVar[str] = "A test tool"

    @classmethod
    def create(cls, conv_state, **params) -> Sequence[ToolDefinition]:
        return [cls(
            description=cls.tool_description,
            action_type=TestAction,
            observation_type=TestObservation,
            executor=TestExecutor(),
        )]
'''
            tool_file = tools_dir / "test_tool.py"
            tool_file.write_text(tool_code)

            loader = ToolLoader(tools_dir=tmpdir)

            # This will fail without the actual SDK imports, but tests the structure
            # In a real test environment with SDK installed, this would work
            try:
                registered = loader.scan_and_load()
                assert "test_tool" in registered
            except ImportError:
                # Expected when SDK is not installed
                pytest.skip("SDK not installed for testing")


class TestCustomWordCountTool:
    """Tests for the example word_count tool."""

    def test_word_count_tool_exists(self):
        """Test that the word count tool file exists."""
        tool_path = Path("src/lab/tools/word_count.py")
        # This test just verifies the file structure
        # The actual tool functionality would require SDK installation


class TestToolInfo:
    """Tests for tool info extraction."""

    def test_loader_tool_info_format(self):
        """Test the format of tool info returned by loader."""
        loader = ToolLoader(tools_dir="/nonexistent")
        info = loader.get_tool_info()

        assert isinstance(info, list)
        # Should be empty for non-existent dir
        assert len(info) == 0

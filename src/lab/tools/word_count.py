"""Example custom tool: Word count in files."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

from pydantic import Field

from openhands.sdk import Action, ImageContent, Observation, TextContent, ToolDefinition
from openhands.sdk.tool import ToolExecutor

from lab.tools.base import BaseLabTool


class WordCountAction(Action):
    """Action for counting words in a file."""
    
    model_config = {"revalidate_instances": "never"}

    path: str = Field(description="Path to the file to count words in")


class WordCountObservation(Observation):
    """Observation with word count results."""
    
    model_config = {"revalidate_instances": "never"}

    path: str
    word_count: int
    line_count: int
    char_count: int
    error: str | None = None

    @property
    def to_llm_content(self) -> Sequence[TextContent | ImageContent]:
        if self.error:
            return [TextContent(text=f"Error: {self.error}")]
        return [
            TextContent(
                text=(
                    f"File: {self.path}\n"
                    f"Words: {self.word_count}\n"
                    f"Lines: {self.line_count}\n"
                    f"Characters: {self.char_count}"
                )
            )
        ]


class WordCountExecutor(ToolExecutor[WordCountAction, WordCountObservation]):
    """Executor that counts words in files."""

    def __init__(self, working_dir: str | Path):
        self.working_dir = Path(working_dir)

    def __call__(
        self, action: WordCountAction, conversation: Any = None
    ) -> WordCountObservation:
        file_path = self.working_dir / action.path

        try:
            content = file_path.read_text()
            return WordCountObservation(
                path=action.path,
                word_count=len(content.split()),
                line_count=len(content.splitlines()),
                char_count=len(content),
            )
        except FileNotFoundError:
            return WordCountObservation(
                path=action.path,
                word_count=0,
                line_count=0,
                char_count=0,
                error=f"File not found: {action.path}",
            )
        except Exception as e:
            return WordCountObservation(
                path=action.path,
                word_count=0,
                line_count=0,
                char_count=0,
                error=str(e),
            )


class WordCountTool(BaseLabTool[WordCountAction, WordCountObservation]):
    """Count words, lines, and characters in a file."""

    tool_name: ClassVar[str] = "word_count"
    tool_description: ClassVar[str] = (
        "Count the number of words, lines, and characters in a file. "
        "Useful for getting quick statistics about text files."
    )

    @classmethod
    def create(
        cls, conv_state: Any, **params: Any
    ) -> Sequence[ToolDefinition[Any, Any]]:
        executor = WordCountExecutor(working_dir=conv_state.workspace.working_dir)
        return [
            cls(
                description=cls.tool_description,
                action_type=WordCountAction,
                observation_type=WordCountObservation,
                executor=executor,
            )
        ]

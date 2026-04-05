"""Base class for custom Lab tools."""

from abc import abstractmethod
from collections.abc import Sequence
from typing import Any, ClassVar, TypeVar

from pydantic import Field

from openhands.sdk import Action, Observation, ToolDefinition
from openhands.sdk.tool import ToolExecutor


ActionT = TypeVar("ActionT", bound=Action)
ObservationT = TypeVar("ObservationT", bound=Observation)


class BaseLabTool(ToolDefinition[ActionT, ObservationT]):
    """Abstract base class for custom OpenHands Lab tools.

    Custom tools should inherit from this class and implement:
    - action_cls: The Action class for input parameters
    - observation_cls: The Observation class for output
    - create(): Factory method to create tool instances

    Example:
        class MyAction(Action):
            query: str = Field(description="Search query")

        class MyObservation(Observation):
            results: list[str]

            @property
            def to_llm_content(self):
                return [TextContent(text="\\n".join(self.results))]

        class MyTool(BaseLabTool[MyAction, MyObservation]):
            tool_name: ClassVar[str] = "my_tool"
            tool_description: ClassVar[str] = "Search for something"

            @classmethod
            def create(cls, conv_state, **params):
                executor = MyExecutor()
                return [cls(
                    description=cls.tool_description,
                    action_type=MyAction,
                    observation_type=MyObservation,
                    executor=executor,
                )]
    """

    # Class-level attributes that subclasses should define
    tool_name: ClassVar[str] = ""
    tool_description: ClassVar[str] = ""

    @classmethod
    @abstractmethod
    def create(
        cls, conv_state: Any, **params: Any
    ) -> Sequence["ToolDefinition[Any, Any]"]:
        """Factory method to create tool instances.

        Args:
            conv_state: The conversation state containing workspace info
            **params: Additional parameters for tool configuration

        Returns:
            A sequence of tool definition instances
        """
        ...

    @classmethod
    def get_name(cls) -> str:
        """Get the tool name for registration."""
        return cls.tool_name or cls.__name__

    @classmethod
    def get_description(cls) -> str:
        """Get the tool description."""
        return cls.tool_description or cls.__doc__ or ""

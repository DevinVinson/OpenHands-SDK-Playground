"""SDK tool for fetching fresh content from GitHub."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, ClassVar

from pydantic import Field

from openhands.sdk import Action, ImageContent, Observation, TextContent, ToolDefinition
from openhands.sdk.tool import ToolExecutor

from lab.tools.base import BaseLabTool
from lab.utils.sdk_examples import (
    DEFAULT_GITHUB_OWNER,
    DEFAULT_GITHUB_REF,
    DEFAULT_GITHUB_REPO,
    GitHubExamplesClient,
    GitHubFetchError,
)


class GitHubFetchAction(Action):
    """Action for listing GitHub directories or fetching text files."""
    
    model_config = {"revalidate_instances": "never"}

    mode: str = Field(
        default="list",
        description="Fetch mode: 'list' for directory listings or 'get_text' for file contents",
    )
    path: str = Field(description="Repository path to fetch")
    owner: str = Field(default=DEFAULT_GITHUB_OWNER, description="GitHub repository owner")
    repo: str = Field(default=DEFAULT_GITHUB_REPO, description="GitHub repository name")
    ref: str = Field(default=DEFAULT_GITHUB_REF, description="Git ref to fetch from")


class GitHubFetchObservation(Observation):
    """Observation describing fetched GitHub content."""
    
    model_config = {"revalidate_instances": "never"}

    mode: str
    path: str
    owner: str
    repo: str
    ref: str
    entries: list[dict[str, Any]] = Field(default_factory=list)
    file_content: str | None = None
    error: str | None = None

    @property
    def to_llm_content(self) -> Sequence[TextContent | ImageContent]:
        if self.error:
            return [TextContent(text=f"GitHub fetch failed for {self.path}: {self.error}")]

        if self.mode == "list":
            lines = [f"- {entry['path']} ({entry['type']})" for entry in self.entries]
            summary = "\n".join(lines[:50]) if lines else "(empty directory)"
            return [TextContent(text=f"Fetched {len(self.entries)} entries from {self.path}:\n{summary}")]

        preview = (self.file_content or "")[:2000]
        return [TextContent(text=f"Fetched file {self.path}:\n{preview}")]


class GitHubFetcherExecutor(ToolExecutor[GitHubFetchAction, GitHubFetchObservation]):
    """Executor for live GitHub fetch operations."""

    def __call__(
        self, action: GitHubFetchAction, conversation: Any = None
    ) -> GitHubFetchObservation:
        client = GitHubExamplesClient(
            owner=action.owner,
            repo=action.repo,
            ref=action.ref,
        )

        try:
            if action.mode == "list":
                entries = client.list_directory(action.path)
                return GitHubFetchObservation(
                    mode=action.mode,
                    path=action.path,
                    owner=action.owner,
                    repo=action.repo,
                    ref=action.ref,
                    entries=entries,
                )
            if action.mode == "get_text":
                file_content = client.get_file_text(action.path)
                return GitHubFetchObservation(
                    mode=action.mode,
                    path=action.path,
                    owner=action.owner,
                    repo=action.repo,
                    ref=action.ref,
                    file_content=file_content,
                )
            return GitHubFetchObservation(
                mode=action.mode,
                path=action.path,
                owner=action.owner,
                repo=action.repo,
                ref=action.ref,
                error=f"Unsupported mode: {action.mode}",
            )
        except GitHubFetchError as exc:
            return GitHubFetchObservation(
                mode=action.mode,
                path=action.path,
                owner=action.owner,
                repo=action.repo,
                ref=action.ref,
                error=str(exc),
            )


class GitHubFetcherTool(BaseLabTool[GitHubFetchAction, GitHubFetchObservation]):
    """Fetch fresh directory listings and file contents from GitHub."""

    tool_name: ClassVar[str] = "github_fetcher"
    tool_description: ClassVar[str] = (
        "Fetch a fresh directory listing or text file from a GitHub repository. "
        "Useful for exploring upstream examples or source files."
    )

    @classmethod
    def create(
        cls, conv_state: Any, **params: Any
    ) -> Sequence[ToolDefinition[Any, Any]]:
        return [
            cls(
                description=cls.tool_description,
                action_type=GitHubFetchAction,
                observation_type=GitHubFetchObservation,
                executor=GitHubFetcherExecutor(),
            )
        ]

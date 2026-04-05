"""SDK tool for importing upstream OpenHands SDK examples into the playground."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

from pydantic import Field

from openhands.sdk import Action, ImageContent, Observation, TextContent, ToolDefinition
from openhands.sdk.tool import ToolExecutor

from lab.tools.base import BaseLabTool
from lab.tools.github_fetcher import GitHubFetchAction, GitHubFetcherExecutor
from lab.utils.sdk_examples import (
    CatalogExample,
    DEFAULT_EXAMPLES_ROOT,
    DEFAULT_GITHUB_OWNER,
    DEFAULT_GITHUB_REF,
    DEFAULT_GITHUB_REPO,
    DEFAULT_INSTALL_ROOT,
    GitHubFetchError,
    build_human_label,
    install_catalog_example,
    match_catalog_example,
)


class ImportSdkExampleAction(Action):
    """Action for listing or importing upstream SDK examples."""
    
    model_config = {"revalidate_instances": "never"}

    example_query: str | None = Field(
        default=None,
        description="Human-readable example to import, like 'Hello World' or 'Agent Delegation'",
    )
    destination_root: str = Field(
        default=DEFAULT_INSTALL_ROOT,
        description="Directory where imported examples should be installed",
    )
    overwrite: bool = Field(
        default=False,
        description="Whether to overwrite an already-installed example",
    )
    owner: str = Field(default=DEFAULT_GITHUB_OWNER, description="GitHub repository owner")
    repo: str = Field(default=DEFAULT_GITHUB_REPO, description="GitHub repository name")
    ref: str = Field(default=DEFAULT_GITHUB_REF, description="Git ref to fetch from")
    examples_root: str = Field(
        default=DEFAULT_EXAMPLES_ROOT,
        description="Upstream examples directory to inspect",
    )


class ImportSdkExampleObservation(Observation):
    """Observation for SDK example catalog and installation results."""
    
    model_config = {"revalidate_instances": "never"}

    catalog_fetched_at: str
    available_examples: list[str] = Field(default_factory=list)
    matched_example: str | None = None
    source_url: str | None = None
    installed_paths: list[str] = Field(default_factory=list)
    manifest_path: str | None = None
    status_message: str = ""
    error: str | None = None

    @property
    def to_llm_content(self) -> Sequence[TextContent | ImageContent]:
        if self.error:
            return [TextContent(text=f"SDK example import failed: {self.error}")]

        lines = [self.status_message]
        if self.matched_example:
            lines.append(f"Matched example: {self.matched_example}")
        if self.source_url:
            lines.append(f"Source: {self.source_url}")
        if self.installed_paths:
            lines.append("Installed paths:")
            lines.extend(f"- {path}" for path in self.installed_paths)
        elif self.available_examples:
            lines.append("Available examples:")
            lines.extend(f"- {label}" for label in self.available_examples[:50])

        return [TextContent(text="\n".join(lines))]


class ImportSdkExampleExecutor(
    ToolExecutor[ImportSdkExampleAction, ImportSdkExampleObservation]
):
    """Executor for importing SDK examples into the local playground."""

    def __init__(self, working_dir: str | Path):
        self.working_dir = Path(working_dir)
        self.github_fetcher = GitHubFetcherExecutor()

    def __call__(
        self, action: ImportSdkExampleAction, conversation: Any = None
    ) -> ImportSdkExampleObservation:
        fetched_at = self._timestamp()
        try:
            catalog = self._build_catalog(action)
        except GitHubFetchError as exc:
            return ImportSdkExampleObservation(
                catalog_fetched_at=fetched_at,
                status_message="Unable to fetch SDK examples.",
                error=str(exc),
            )

        if not action.example_query:
            return ImportSdkExampleObservation(
                catalog_fetched_at=fetched_at,
                available_examples=[example.label for example in catalog],
                status_message="Fetched the latest SDK examples catalog.",
            )

        matched, candidates = match_catalog_example(
            action.example_query,
            catalog,
        )
        if matched is None:
            available = [example.label for example in candidates] or [
                example.label for example in catalog[:50]
            ]
            return ImportSdkExampleObservation(
                catalog_fetched_at=fetched_at,
                available_examples=available,
                status_message=(
                    "Fetched the latest SDK examples catalog, but the selection was missing or ambiguous."
                ),
                error=(
                    f"Could not uniquely match '{action.example_query}'. "
                    "Refine the query using one of the returned example names."
                ),
            )

        try:
            installed_paths, manifest_path = install_catalog_example(
                client=self._client_for(action),
                example=matched,
                destination_root=self.working_dir / action.destination_root,
                overwrite=action.overwrite,
            )
        except (GitHubFetchError, FileExistsError, ValueError) as exc:
            return ImportSdkExampleObservation(
                catalog_fetched_at=fetched_at,
                available_examples=[example.label for example in catalog[:50]],
                matched_example=matched.label,
                source_url=matched.source_url,
                status_message="Fetched the latest SDK examples catalog.",
                error=str(exc),
            )

        return ImportSdkExampleObservation(
            catalog_fetched_at=fetched_at,
            available_examples=[example.label for example in catalog[:50]],
            matched_example=matched.label,
            source_url=matched.source_url,
            installed_paths=[str(path) for path in installed_paths if path != manifest_path],
            manifest_path=str(manifest_path),
            status_message="Imported the requested SDK example into the local playground.",
        )

    def _timestamp(self) -> str:
        from datetime import UTC, datetime

        return datetime.now(UTC).isoformat()

    def _build_catalog(self, action: ImportSdkExampleAction) -> list[CatalogExample]:
        # Compose with the github_fetcher tool to guarantee a fresh top-level fetch
        top_level = self.github_fetcher(
            GitHubFetchAction(
                mode="list",
                path=action.examples_root,
                owner=action.owner,
                repo=action.repo,
                ref=action.ref,
            )
        )
        if top_level.error:
            raise GitHubFetchError(top_level.error)

        catalog: list[CatalogExample] = []
        for category in top_level.entries:
            if category.get("type") != "dir":
                continue

            children = self.github_fetcher(
                GitHubFetchAction(
                    mode="list",
                    path=category["path"],
                    owner=action.owner,
                    repo=action.repo,
                    ref=action.ref,
                )
            )
            if children.error:
                raise GitHubFetchError(children.error)

            for item in children.entries:
                if item.get("type") not in {"file", "dir"}:
                    continue
                catalog.append(
                    CatalogExample(
                        label=build_human_label(category["name"], item["name"]),
                        category=category["name"],
                        short_name=item["name"],
                        relative_path=item["path"],
                        example_type=item["type"],
                        source_url=item.get("html_url", ""),
                    )
                )

        return sorted(catalog, key=lambda item: item.label.lower())

    def _client_for(self, action: ImportSdkExampleAction):
        from lab.utils.sdk_examples import GitHubExamplesClient

        return GitHubExamplesClient(
            owner=action.owner,
            repo=action.repo,
            ref=action.ref,
        )


class ImportSdkExampleTool(
    BaseLabTool[ImportSdkExampleAction, ImportSdkExampleObservation]
):
    """Import fresh OpenHands SDK examples into the local playground."""

    tool_name: ClassVar[str] = "import_sdk_example"
    tool_description: ClassVar[str] = (
        "Fetch the latest OpenHands SDK examples catalog from GitHub and install a selected example "
        "into the local playground so it can be inspected and run."
    )

    @classmethod
    def create(
        cls, conv_state: Any, **params: Any
    ) -> Sequence[ToolDefinition[Any, Any]]:
        executor = ImportSdkExampleExecutor(working_dir=conv_state.workspace.working_dir)
        return [
            cls(
                description=cls.tool_description,
                action_type=ImportSdkExampleAction,
                observation_type=ImportSdkExampleObservation,
                executor=executor,
            )
        ]

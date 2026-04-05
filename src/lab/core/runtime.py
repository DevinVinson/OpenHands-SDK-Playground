"""Runtime factory for workspace creation."""

from pathlib import Path
from typing import Any

from openhands.sdk import LocalWorkspace, Workspace

from lab.core.config import RuntimeSettings


class RuntimeFactory:
    """Factory for creating workspace instances based on configuration.

    Supports creating LocalWorkspace (for local development) or
    DockerWorkspace (for sandboxed execution) based on settings.
    """

    def __init__(self, settings: RuntimeSettings):
        self.settings = settings

    def create_workspace(
        self,
        working_dir: str | Path | None = None,
        **kwargs: Any,
    ) -> Workspace:
        """Create a workspace instance based on configuration.

        Args:
            working_dir: Override the default working directory
            **kwargs: Additional arguments passed to workspace constructor

        Returns:
            A Workspace instance (LocalWorkspace or DockerWorkspace)

        Raises:
            ValueError: If the configured environment is not supported
        """
        work_dir = Path(working_dir or self.settings.working_dir)

        if self.settings.environment == "local":
            return self._create_local_workspace(work_dir, **kwargs)
        elif self.settings.environment == "docker":
            return self._create_docker_workspace(work_dir, **kwargs)
        else:
            raise ValueError(
                f"Unsupported environment: {self.settings.environment}. "
                f"Expected 'local' or 'docker'."
            )

    def _create_local_workspace(
        self, working_dir: Path, **kwargs: Any
    ) -> LocalWorkspace:
        """Create a local workspace."""
        return LocalWorkspace(working_dir=working_dir, **kwargs)

    def _create_docker_workspace(
        self, working_dir: Path, **kwargs: Any
    ) -> Workspace:
        """Create a Docker workspace.

        Note: Requires openhands-workspace package with Docker support.
        """
        try:
            from openhands.workspace.docker import DockerWorkspace
        except ImportError:
            raise ImportError(
                "Docker workspace support requires 'openhands-workspace' "
                "package with Docker extras. Install with: "
                "pip install openhands-workspace[docker]"
            )

        image = self.settings.docker_image or "python:3.12-slim"
        return DockerWorkspace(
            working_dir=working_dir,
            image=image,
            **kwargs,
        )

    @property
    def is_sandboxed(self) -> bool:
        """Check if the runtime uses sandboxed execution."""
        return self.settings.environment == "docker"

"""File watcher for hot-reloading tools."""

from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from lab.tools.loader import ToolLoader


class ToolFileHandler(FileSystemEventHandler):
    """Handles file system events for tool hot-reloading."""

    def __init__(
        self,
        loader: ToolLoader,
        on_reload: Callable[[list[str]], None] | None = None,
    ):
        self.loader = loader
        self.on_reload = on_reload

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = Path(str(event.src_path))
        if file_path.suffix != ".py":
            return

        # Skip non-tool files
        if file_path.name.startswith("_") or file_path.name in (
            "base.py",
            "loader.py",
        ):
            return

        print(f"[Hot-reload] Detected change in: {file_path.name}")
        reloaded = self.loader.reload_tool(file_path)

        if reloaded:
            print(f"[Hot-reload] Reloaded tools: {', '.join(reloaded)}")
            if self.on_reload:
                self.on_reload(reloaded)

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = Path(str(event.src_path))
        if file_path.suffix != ".py":
            return

        if file_path.name.startswith("_"):
            return

        print(f"[Hot-reload] New tool file detected: {file_path.name}")
        reloaded = self.loader.reload_tool(file_path)

        if reloaded:
            print(f"[Hot-reload] Loaded new tools: {', '.join(reloaded)}")
            if self.on_reload:
                self.on_reload(reloaded)


class ToolWatcher:
    """Watches the tools directory for changes and hot-reloads tools.

    Uses watchdog to monitor file system changes and automatically
    reload modified tools.
    """

    def __init__(
        self,
        loader: ToolLoader,
        on_reload: Callable[[list[str]], None] | None = None,
    ):
        self.loader = loader
        self.on_reload = on_reload
        self._observer: Observer | None = None
        self._running = False

    @property
    def is_running(self) -> bool:
        """Check if the watcher is running."""
        return self._running

    def start(self) -> None:
        """Start watching for file changes."""
        if self._running:
            return

        if not self.loader.tools_dir.exists():
            print(f"Warning: Tools directory does not exist: {self.loader.tools_dir}")
            return

        handler = ToolFileHandler(self.loader, self.on_reload)
        self._observer = Observer()
        self._observer.schedule(handler, str(self.loader.tools_dir), recursive=False)
        self._observer.start()
        self._running = True

        print(f"[Hot-reload] Watching for changes in: {self.loader.tools_dir}")

    def stop(self) -> None:
        """Stop watching for file changes."""
        if not self._running or self._observer is None:
            return

        self._observer.stop()
        self._observer.join()
        self._observer = None
        self._running = False

        print("[Hot-reload] Stopped watching for changes")

    def __enter__(self) -> "ToolWatcher":
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()

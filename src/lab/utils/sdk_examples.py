"""Helpers for working with upstream OpenHands SDK examples."""

from __future__ import annotations

import base64
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import error, parse, request


DEFAULT_GITHUB_OWNER = "OpenHands"
DEFAULT_GITHUB_REPO = "software-agent-sdk"
DEFAULT_GITHUB_REF = "main"
DEFAULT_EXAMPLES_ROOT = "examples"
DEFAULT_INSTALL_ROOT = "examples/sdk"
MANIFEST_FILENAME = ".sdk_examples_manifest.json"


class GitHubFetchError(RuntimeError):
    """Raised when a GitHub fetch operation fails."""


@dataclass(slots=True)
class CatalogExample:
    """A single installable SDK example."""

    label: str
    category: str
    short_name: str
    relative_path: str
    example_type: str
    source_url: str


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def humanize_slug(slug: str) -> str:
    """Convert file or directory slugs into readable titles."""
    value = slug.rsplit(".", 1)[0]
    value = re.sub(r"^\d+_", "", value)
    value = value.replace("_", " ").replace("-", " ")
    words = [word for word in value.split() if word]

    acronyms = {
        "sdk": "SDK",
        "llm": "LLM",
        "mcp": "MCP",
        "oauth": "OAuth",
        "json": "JSON",
        "openai": "OpenAI",
        "github": "GitHub",
        "acp": "ACP",
    }
    return " ".join(acronyms.get(word.lower(), word.capitalize()) for word in words)


def build_human_label(category_slug: str, example_slug: str) -> str:
    """Build a readable label from category and example slugs."""
    return f"{humanize_slug(category_slug)} / {humanize_slug(example_slug)}"


def match_catalog_example(
    query: str, catalog: list[CatalogExample]
) -> tuple[CatalogExample | None, list[CatalogExample]]:
    """Resolve a user query against the example catalog."""
    normalized_query = _normalize(query)
    if not normalized_query:
        return None, []

    exact_matches = []
    partial_matches = []
    for example in catalog:
        haystacks = [
            example.label,
            example.short_name,
            example.relative_path,
            Path(example.relative_path).name,
        ]
        normalized_haystacks = [_normalize(value) for value in haystacks]

        if normalized_query in normalized_haystacks:
            exact_matches.append(example)
            continue

        if any(normalized_query in value for value in normalized_haystacks):
            partial_matches.append(example)

    if len(exact_matches) == 1:
        return exact_matches[0], exact_matches
    if len(exact_matches) > 1:
        return None, exact_matches
    if len(partial_matches) == 1:
        return partial_matches[0], partial_matches

    return None, partial_matches


class GitHubExamplesClient:
    """Minimal GitHub API client for fetching SDK examples."""

    def __init__(
        self,
        owner: str = DEFAULT_GITHUB_OWNER,
        repo: str = DEFAULT_GITHUB_REPO,
        ref: str = DEFAULT_GITHUB_REF,
    ):
        self.owner = owner
        self.repo = repo
        self.ref = ref

    def _contents_url(self, path: str) -> str:
        encoded_path = parse.quote(path.strip("/"))
        return (
            f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{encoded_path}"
            f"?ref={parse.quote(self.ref)}"
        )

    def _request_json(self, url: str) -> Any:
        req = request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "openhands-sdk-playground",
            },
        )
        try:
            with request.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise GitHubFetchError(f"GitHub request failed: {exc.code} {url}") from exc
        except error.URLError as exc:
            raise GitHubFetchError(f"GitHub request failed: {exc.reason}") from exc

    def _request_text(self, url: str) -> str:
        req = request.Request(
            url,
            headers={"User-Agent": "openhands-sdk-playground"},
        )
        try:
            with request.urlopen(req) as response:
                return response.read().decode("utf-8")
        except error.HTTPError as exc:
            raise GitHubFetchError(f"GitHub request failed: {exc.code} {url}") from exc
        except error.URLError as exc:
            raise GitHubFetchError(f"GitHub request failed: {exc.reason}") from exc

    def list_directory(self, path: str) -> list[dict[str, Any]]:
        """Fetch a directory listing from GitHub."""
        payload = self._request_json(self._contents_url(path))
        if not isinstance(payload, list):
            raise GitHubFetchError(f"Expected a directory listing for '{path}'")
        return payload

    def get_file_text(self, path: str) -> str:
        """Fetch a UTF-8 text file from GitHub."""
        payload = self._request_json(self._contents_url(path))
        if not isinstance(payload, dict) or payload.get("type") != "file":
            raise GitHubFetchError(f"Expected a file at '{path}'")

        encoded = payload.get("content")
        if encoded:
            return base64.b64decode(encoded).decode("utf-8")

        download_url = payload.get("download_url")
        if not download_url:
            raise GitHubFetchError(f"File '{path}' did not include downloadable content")
        return self._request_text(download_url)

    def build_catalog(
        self, examples_root: str = DEFAULT_EXAMPLES_ROOT
    ) -> list[CatalogExample]:
        """Fetch and flatten the latest example catalog."""
        categories = self.list_directory(examples_root)
        catalog: list[CatalogExample] = []

        for category in categories:
            if category.get("type") != "dir":
                continue

            category_name = category["name"]
            category_path = category["path"]
            for item in self.list_directory(category_path):
                item_type = item.get("type")
                if item_type not in {"file", "dir"}:
                    continue

                item_name = item["name"]
                label = build_human_label(category_name, item_name)
                catalog.append(
                    CatalogExample(
                        label=label,
                        category=humanize_slug(category_name),
                        short_name=humanize_slug(item_name),
                        relative_path=item["path"],
                        example_type=item_type,
                        source_url=item.get("html_url", ""),
                    )
                )

        return sorted(catalog, key=lambda example: example.label.lower())


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _write_manifest_entry(
    install_root: Path,
    example: CatalogExample,
    installed_paths: list[Path],
) -> Path:
    manifest_path = install_root / MANIFEST_FILENAME
    payload: dict[str, Any]
    if manifest_path.exists():
        payload = json.loads(manifest_path.read_text())
    else:
        payload = {"imports": []}

    entry = {
        "label": example.label,
        "category": example.category,
        "short_name": example.short_name,
        "relative_path": example.relative_path,
        "example_type": example.example_type,
        "source_url": example.source_url,
        "installed_paths": [str(path.relative_to(install_root)) for path in installed_paths],
        "imported_at": _now_iso(),
    }

    imports = [item for item in payload.get("imports", []) if item.get("relative_path") != example.relative_path]
    imports.append(entry)
    payload["imports"] = sorted(imports, key=lambda item: item["label"].lower())

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, indent=2))
    return manifest_path


def install_catalog_example(
    client: GitHubExamplesClient,
    example: CatalogExample,
    destination_root: str | Path = DEFAULT_INSTALL_ROOT,
    overwrite: bool = False,
) -> tuple[list[Path], Path]:
    """Install an upstream example into the local playground."""
    install_root = Path(destination_root)
    relative_install_path = _install_relative_path(example.relative_path)
    destination = install_root / relative_install_path

    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"Destination already exists: {destination}. Pass overwrite=True to replace it."
        )

    installed_paths: list[Path] = []

    if example.example_type == "file":
        content = client.get_file_text(example.relative_path)
        _ensure_parent(destination)
        destination.write_text(content)
        installed_paths.append(destination)
    elif example.example_type == "dir":
        installed_paths.extend(
            _install_directory(
                client=client,
                remote_path=example.relative_path,
                destination_root=install_root,
                overwrite=overwrite,
            )
        )
    else:
        raise ValueError(f"Unsupported example type: {example.example_type}")

    manifest_path = _write_manifest_entry(install_root, example, installed_paths)
    installed_paths.append(manifest_path)
    return installed_paths, manifest_path


def _install_directory(
    client: GitHubExamplesClient,
    remote_path: str,
    destination_root: Path,
    overwrite: bool,
) -> list[Path]:
    installed_paths: list[Path] = []
    for item in client.list_directory(remote_path):
        item_type = item.get("type")
        destination = destination_root / _install_relative_path(item["path"])

        if item_type == "dir":
            destination.mkdir(parents=True, exist_ok=True)
            installed_paths.extend(
                _install_directory(
                    client=client,
                    remote_path=item["path"],
                    destination_root=destination_root,
                    overwrite=overwrite,
                )
            )
            continue

        if item_type != "file":
            continue

        if destination.exists() and not overwrite:
            raise FileExistsError(
                f"Destination already exists: {destination}. Pass overwrite=True to replace it."
            )

        content = client.get_file_text(item["path"])
        _ensure_parent(destination)
        destination.write_text(content)
        installed_paths.append(destination)

    return installed_paths


def _install_relative_path(remote_path: str) -> Path:
    path = Path(remote_path)
    if path.parts and path.parts[0] == DEFAULT_EXAMPLES_ROOT:
        return Path(*path.parts[1:])
    return path


def serialize_catalog(catalog: list[CatalogExample]) -> list[dict[str, Any]]:
    """Convert the catalog to JSON-friendly dictionaries."""
    return [asdict(example) for example in catalog]
